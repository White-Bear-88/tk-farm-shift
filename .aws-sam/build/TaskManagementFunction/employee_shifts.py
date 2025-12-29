import json
import boto3
import os
from datetime import datetime, timedelta
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
        employee_id = event['pathParameters']['id']
        query_params = event.get('queryStringParameters', {}) or {}
        
        # month, date, or explicit start/end date をサポート
        if query_params.get('month'):
            # month = "YYYY-MM"
            month_str = query_params['month']
            year, month_num = map(int, month_str.split('-'))
            last_day = calendar.monthrange(year, month_num)[1]
            start_date = f"{month_str}-01"
            end_date = f"{month_str}-{last_day:02d}"
        elif query_params.get('date'):
            start_date = end_date = query_params['date']
        else:
            start_date = query_params.get('start_date', 
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
            end_date = query_params.get('end_date', 
                datetime.now().strftime('%Y-%m-%d'))
        
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :employee_id AND GSI1SK BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':employee_id': employee_id,
                ':start_date': start_date,
                ':end_date': end_date
            }
        )
        
        shifts = []
        for item in response['Items']:
            shifts.append({
                'date': item['GSI1SK'],
                'task_type': item['SK'].split('#')[2],
                'start_time': item['start_time'],
                'end_time': item['end_time'],
                'status': item.get('status', 'scheduled'),
                'duration_hours': calculate_duration(item['start_time'], item['end_time'])
            })
        
        # フロントエンド互換性のため、シンプルにシフトの配列を返す
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(shifts, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def calculate_duration(start_time, end_time):
    """勤務時間を計算"""
    try:
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        duration = end - start
        return duration.total_seconds() / 3600
    except:
        return 0

def calculate_employee_stats(shifts):
    """従業員の統計情報を計算"""
    total_hours = sum(shift['duration_hours'] for shift in shifts)
    task_counts = {}
    
    for shift in shifts:
        task_type = shift['task_type']
        task_counts[task_type] = task_counts.get(task_type, 0) + 1
    
    return {
        'total_shifts': len(shifts),
        'total_hours': round(total_hours, 2),
        'average_hours_per_shift': round(total_hours / len(shifts), 2) if shifts else 0,
        'task_distribution': task_counts
    }