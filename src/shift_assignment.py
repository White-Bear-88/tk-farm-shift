import json
import boto3
import os
from datetime import datetime, timedelta
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        data = json.loads(event['body'])
        date = data['date']
        required_tasks = data['required_tasks']  # [{'task_type': 'milking', 'count': 2}, ...]
        
        # 利用可能な従業員を取得
        available_employees = get_available_employees(date)
        
        # 既存のシフトを確認
        existing_shifts = get_existing_shifts(date)
        
        # 自動割り当てロジック
        assignments = auto_assign_shifts(date, required_tasks, available_employees, existing_shifts)
        
        # DynamoDBに保存
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
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_available_employees(date):
    """利用可能な従業員リストを取得"""
    response = table.scan(
        FilterExpression='begins_with(PK, :pk)',
        ExpressionAttributeValues={':pk': 'EMP#'}
    )
    
    employees = []
    for item in response['Items']:
        if item['SK'] == 'PROFILE':
            employees.append({
                'id': item['PK'].split('#')[1],
                'name': item['name'],
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
    """シフト割り当てをDynamoDBに保存"""
    item = {
        'PK': f"SHIFT#{assignment['date']}",
        'SK': f"EMP#{assignment['employee_id']}#{assignment['task_type']}",
        'GSI1PK': assignment['employee_id'],
        'GSI1SK': assignment['date'],
        'GSI2PK': assignment['task_type'],
        'GSI2SK': f"{assignment['date']}#{assignment['employee_id']}",
        'start_time': assignment['start_time'],
        'end_time': assignment['end_time'],
        'status': 'auto_assigned',
        'created_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=item)