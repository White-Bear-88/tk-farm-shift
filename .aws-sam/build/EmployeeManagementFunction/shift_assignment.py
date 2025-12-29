import json
import boto3
import os
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

# Support local dynamodb endpoint
_dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT')
if _dynamodb_endpoint:
    dynamodb = boto3.resource('dynamodb', endpoint_url=_dynamodb_endpoint)
else:
    dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'POST' and path == '/shifts/generate-monthly':
            return generate_monthly_shifts(event)
        elif http_method == 'GET' and '/shifts/by-month/' in path:
            month = path.split('/')[-1]
            return get_shifts_by_month(month)
        elif http_method == 'POST' and path == '/shifts/assign':
            return assign_shifts(event)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def generate_monthly_shifts(event):
    """月間シフト自動生成
    Supports preview mode: if data['preview'] is True, do not write or delete anything; just return generated shifts for review.
    Prevent generation for past months.
    """
    try:
        data = json.loads(event['body'])
        month = data['month']  # "2024-12" format
        overwrite = data.get('overwrite', True)  # デフォルトで上書き
        preview = data.get('preview', False)

        # Prevent generation for past months (relative to current year-month)
        year, month_num = map(int, month.split('-'))
        from datetime import datetime as _dt
        now = _dt.now()
        if (year, month_num) < (now.year, now.month):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '過去の月の生成はできません'})
            }

        days_in_month = calendar.monthrange(year, month_num)[1]
        
        generated_shifts = []
        
        # Only delete or write when not previewing
        if not preview and overwrite:
            delete_existing_shifts_for_month(month)
        
        # リクエストに要求人数が含まれていればそれを優先して使用（フロントの設定が未保存の場合にも対応）
        requirements = data.get('requirements') or get_requirements_for_month(month)
        
        # 従業員リストを取得
        employees = get_available_employees()
        
        for day in range(1, days_in_month + 1):
            date = f"{month}-{day:02d}"
            
            # 日別設定があるかチェック
            daily_reqs = get_daily_requirements(date)
            if daily_reqs:
                day_requirements = daily_reqs
            else:
                day_requirements = requirements
            
            # その日のシフトを生成
            day_shifts = generate_day_shifts(date, day_requirements, employees, not preview)
            generated_shifts.extend(day_shifts)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': f'Generated {len(generated_shifts)} shifts for {month}',
                'shifts': generated_shifts,
                'preview': preview
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'シフト生成エラー: {str(e)}'})
        }

def delete_existing_shifts_for_month(month):
    """月の既存シフトを削除"""
    year, month_num = map(int, month.split('-'))
    days_in_month = calendar.monthrange(year, month_num)[1]
    
    for day in range(1, days_in_month + 1):
        date = f"{month}-{day:02d}"
        
        # その日のシフトを取得
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': f'SHIFT#{date}'}
        )
        
        # 一括削除
        with table.batch_writer() as batch:
            for item in response['Items']:
                batch.delete_item(
                    Key={'PK': item['PK'], 'SK': item['SK']}
                )

def get_shifts_by_month(month):
    """月別シフト取得
    Also cleans duplicate assignments where same employee has multiple roles on a given date by keeping the first and deleting others.
    """
    year, month_num = map(int, month.split('-'))
    days_in_month = calendar.monthrange(year, month_num)[1]
    
    all_shifts = []
    
    for day in range(1, days_in_month + 1):
        date = f"{month}-{day:02d}"
        
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': f'SHIFT#{date}'}
        )
        
        seen_employees = set()
        for item in response['Items']:
            employee_id = item['SK'].split('#')[1]
            task_type = item['SK'].split('#')[2]
            if employee_id in seen_employees:
                # Duplicate: delete this entry to clean data
                try:
                    table.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
                except Exception:
                    pass
                continue
            seen_employees.add(employee_id)
            shift = {
                'date': date,
                'employee_id': employee_id,
                'task_type': task_type,
                'start_time': item['start_time'],
                'end_time': item['end_time'],
                'status': item.get('status', 'scheduled')
            }
            all_shifts.append(shift)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(all_shifts)
    }

def get_requirements_for_month(month):
    """月別またはグローバルデフォルト人数設定を取得"""
    # 月別設定を試行
    try:
        response = table.get_item(
            Key={'PK': 'REQUIREMENTS', 'SK': f'MONTH#{month}'}
        )
        if 'Item' in response:
            return response['Item']['requirements']
    except:
        pass
    
    # グローバルデフォルト設定を取得
    try:
        response = table.get_item(
            Key={'PK': 'REQUIREMENTS', 'SK': 'GLOBAL_DEFAULT'}
        )
        if 'Item' in response:
            return response['Item']['requirements']
    except:
        pass
    
    # デフォルト値
    return {'milking': 2, 'feeding': 1, 'cleaning': 1, 'patrol': 1}

def get_daily_requirements(date):
    """日別人数設定を取得"""
    try:
        response = table.get_item(
            Key={'PK': 'REQUIREMENTS', 'SK': f'DAILY#{date}'}
        )
        if 'Item' in response:
            return response['Item']['requirements']
    except:
        pass
    return None

def generate_day_shifts(date, requirements, employees, overwrite=True):
    """1日分のシフトを生成"""
    shifts = []
    
    task_schedules = {
        'milking': [('05:00', '07:00')],
        'feeding': [('08:00', '09:00')],
        'cleaning': [('10:00', '11:30')],
        'patrol': [('14:00', '14:30')]
    }
    
    for task_type, count in requirements.items():
        if count <= 0:
            continue
            
        # スキルを持つ従業員をフィルタ
        skilled_employees = [emp for emp in employees if task_type in emp.get('skills', [])]
        
        # 必要人数分割り当て
        for i in range(min(count, len(skilled_employees))):
            employee = skilled_employees[i]
            times = task_schedules.get(task_type, [('09:00', '17:00')])
            start_time, end_time = times[0]
            
            shift = {
                'date': date,
                'employee_id': employee['id'],
                'task_type': task_type,
                'start_time': start_time,
                'end_time': end_time
            }
            
            # 冪等性を保つための保存
            if save_shift_assignment_safe(shift, overwrite):
                shifts.append(shift)
    
    return shifts

def employee_has_shift_on_date(date, employee_id):
    """Return True if the employee already has any shift on the given date."""
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': f'SHIFT#{date}'}
        )
        for item in response['Items']:
            if item['SK'].startswith(f'EMP#{employee_id}#'):
                return True
        return False
    except Exception:
        # Conservatively return True to avoid accidental double assignment on error
        return True


def save_shift_assignment_safe(assignment, overwrite=True):
    """冪等性を保つシフト保存
    Prevent assigning the same employee to more than one task on the same date.
    """
    # Check duplicate assignment for same employee/date
    if employee_has_shift_on_date(assignment['date'], assignment['employee_id']):
        # There's already a shift for this employee this date — skip/save prevented
        return False

    pk = f"SHIFT#{assignment['date']}"
    sk = f"EMP#{assignment['employee_id']}#{assignment['task_type']}"
    
    item = {
        'PK': pk,
        'SK': sk,
        'GSI1PK': assignment['employee_id'],
        'GSI1SK': assignment['date'],
        'GSI2PK': assignment['task_type'],
        'GSI2SK': f"{assignment['date']}#{assignment['employee_id']}",
        'start_time': assignment['start_time'],
        'end_time': assignment['end_time'],
        'status': 'auto_assigned',
        'created_at': datetime.now().isoformat()
    }
    
    try:
        if overwrite:
            # 上書きモード：無条件で保存
            table.put_item(Item=item)
        else:
            # 新規作成モード：既存しない場合のみ保存
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(PK)'
            )
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        # 既に存在する場合はスキップ
        return False
    except Exception as e:
        print(f"Error saving shift: {e}")
        return False

def assign_shifts(event):
    """日別シフト割り当て"""
    data = json.loads(event['body'])
    date = data['date']
    required_tasks = data['required_tasks']
    
    available_employees = get_available_employees()
    existing_shifts = get_existing_shifts(date)
    
    assignments = auto_assign_shifts(date, required_tasks, available_employees, existing_shifts)
    
    for assignment in assignments:
        save_shift_assignment(assignment)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': f'Successfully assigned {len(assignments)} shifts',
            'assignments': assignments
        })
    }

def get_available_employees():
    """利用可能な従業員リストを取得"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': 'EMPLOYEE'}
    )
    
    employees = []
    for item in response['Items']:
        employees.append({
            'id': item['SK'],
            'name': item.get('name', ''),
            'skills': item.get('skills', []),
            'max_hours_per_day': item.get('max_hours_per_day', 8)
        })
    
    return employees

def get_existing_shifts(date):
    """既存のシフトを取得"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f'SHIFT#{date}'}
    )
    
    existing = defaultdict(list)
    for item in response['Items']:
        employee_id = item['SK'].split('#')[1]
        existing[employee_id].append({
            'task_type': item['SK'].split('#')[2],
            'start_time': item['start_time'],
            'end_time': item['end_time']
        })
    
    return existing

def auto_assign_shifts(date, required_tasks, available_employees, existing_shifts):
    """シフト自動割り当てロジック"""
    assignments = []
    
    # 作業時間帯の定義
    task_schedules = {
        'milking': [('05:00', '07:00'), ('17:00', '19:00')],
        'feeding': [('08:00', '10:00'), ('16:00', '17:00')],
        'cleaning': [('10:00', '12:00'), ('14:00', '16:00')],
        'patrol': [('13:00', '14:00'), ('20:00', '21:00')]
    }
    
    for task_req in required_tasks:
        task_type = task_req['task_type']
        required_count = task_req['count']
        
        # スキルを持つ従業員をフィルタ
        skilled_employees = [emp for emp in available_employees 
                           if task_type in emp.get('skills', [])]
        
        # 既に割り当て済みでない従業員を選択
        available_for_task = [emp for emp in skilled_employees 
                            if not is_employee_busy(emp['id'], task_type, existing_shifts, task_schedules)]
        
        # 必要人数分割り当て
        assigned_count = 0
        for employee in available_for_task[:required_count]:
            for start_time, end_time in task_schedules.get(task_type, [('09:00', '17:00')]):
                if not has_time_conflict(employee['id'], start_time, end_time, existing_shifts):
                    assignment = {
                        'date': date,
                        'employee_id': employee['id'],
                        'employee_name': employee['name'],
                        'task_type': task_type,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                    assignments.append(assignment)
                    
                    # 既存シフトに追加（重複チェック用）
                    existing_shifts[employee['id']].append({
                        'task_type': task_type,
                        'start_time': start_time,
                        'end_time': end_time
                    })
                    
                    assigned_count += 1
                    break
            
            if assigned_count >= required_count:
                break
    
    return assignments

def is_employee_busy(employee_id, task_type, existing_shifts, task_schedules):
    """従業員が忙しいかチェック"""
    employee_shifts = existing_shifts.get(employee_id, [])
    task_times = task_schedules.get(task_type, [])
    
    for shift in employee_shifts:
        for start_time, end_time in task_times:
            if has_time_overlap(shift['start_time'], shift['end_time'], start_time, end_time):
                return True
    return False

def has_time_conflict(employee_id, start_time, end_time, existing_shifts):
    """時間の重複をチェック"""
    employee_shifts = existing_shifts.get(employee_id, [])
    
    for shift in employee_shifts:
        if has_time_overlap(shift['start_time'], shift['end_time'], start_time, end_time):
            return True
    return False

def has_time_overlap(start1, end1, start2, end2):
    """時間の重複判定"""
    start1_dt = datetime.strptime(start1, '%H:%M').time()
    end1_dt = datetime.strptime(end1, '%H:%M').time()
    start2_dt = datetime.strptime(start2, '%H:%M').time()
    end2_dt = datetime.strptime(end2, '%H:%M').time()
    
    return not (end1_dt <= start2_dt or end2_dt <= start1_dt)

def save_shift_assignment(assignment):
    """シフト割り当てをDynamoDBに保存（互換性のため保持）"""
    return save_shift_assignment_safe(assignment, overwrite=True)