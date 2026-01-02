import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def decimal_default(obj):
    """JSON serialization for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'GET' and path == '/tasks':
            return get_all_tasks()
        elif http_method == 'POST' and path == '/tasks':
            return create_task(event)
        elif http_method == 'GET' and '/tasks/' in path:
            task_type = path.split('/')[-1]
            return get_task(task_type)
        elif http_method == 'PUT' and '/tasks/' in path:
            task_type = path.split('/')[-1]
            return update_task(task_type, event)
        elif http_method == 'DELETE' and '/tasks/' in path:
            task_type = path.split('/')[-1]
            return delete_task(task_type)
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

def get_all_tasks():
    try:
        # 新しいデータ構造に対応: TASK#で始まるPKをスキャン
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'TASK#'}
        )
        
        tasks = []
        for item in response['Items']:
            if item['SK'] == 'CONFIG':
                task = {
                    'task_type': item.get('task_type', item['PK'].split('#')[1]),
                    'name': item.get('name', ''),
                    'description': item.get('description', ''),
                    'duration_minutes': item.get('duration_minutes', 60),
                    'required_people': item.get('required_people', 1),
                    'priority': item.get('priority', 'medium'),
                    'recommended_start_time': item.get('recommended_start_time', ''),
                    'recommended_end_time': item.get('recommended_end_time', ''),
                    'morning_start_time': item.get('morning_start_time', ''),
                    'morning_end_time': item.get('morning_end_time', ''),
                    'afternoon_start_time': item.get('afternoon_start_time', ''),
                    'afternoon_end_time': item.get('afternoon_end_time', '')
                }
                tasks.append(task)
        
        # IDでソート
        tasks.sort(key=lambda x: int(x['task_type']) if x['task_type'].isdigit() else 999)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(tasks, default=decimal_default)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def create_task(event):
    try:
        data = json.loads(event['body'])
        task_type = data.get('task_type')
        
        if not task_type:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'task_type is required'})
            }
        
        item = {
            'PK': f'TASK#{task_type}',
            'SK': 'CONFIG',
            'task_type': task_type,
            'name': data['name'],
            'description': data.get('description', ''),
            'duration_minutes': data.get('duration_minutes', 60),
            'required_people': data.get('required_people', 1),
            'priority': data.get('priority', 'medium'),
            'recommended_start_time': data.get('recommended_start_time', ''),
            'recommended_end_time': data.get('recommended_end_time', ''),
            'morning_start_time': data.get('morning_start_time', ''),
            'morning_end_time': data.get('morning_end_time', ''),
            'afternoon_start_time': data.get('afternoon_start_time', ''),
            'afternoon_end_time': data.get('afternoon_end_time', '')
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '作業種別を作成しました', 'task_type': task_type})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_task(task_type):
    try:
        response = table.get_item(
            Key={'PK': f'TASK#{task_type}', 'SK': 'CONFIG'}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '作業種別が見つかりません'})
            }
        
        item = response['Item']
        task = {
            'task_type': item.get('task_type', task_type),
            'name': item.get('name', ''),
            'description': item.get('description', ''),
            'duration_minutes': item.get('duration_minutes', 60),
            'required_people': item.get('required_people', 1),
            'priority': item.get('priority', 'medium'),
            'recommended_start_time': item.get('recommended_start_time', ''),
            'recommended_end_time': item.get('recommended_end_time', ''),
            'morning_start_time': item.get('morning_start_time', ''),
            'morning_end_time': item.get('morning_end_time', ''),
            'afternoon_start_time': item.get('afternoon_start_time', ''),
            'afternoon_end_time': item.get('afternoon_end_time', '')
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(task, default=decimal_default)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def update_task(task_type, event):
    try:
        data = json.loads(event['body'])
        
        # 既存データを取得してマージ
        response = table.get_item(
            Key={'PK': f'TASK#{task_type}', 'SK': 'CONFIG'}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '作業種別が見つかりません'})
            }
        
        item = response['Item']
        item.update({
            'name': data.get('name', item.get('name')),
            'description': data.get('description', item.get('description', '')),
            'duration_minutes': data.get('duration_minutes', item.get('duration_minutes', 60)),
            'required_people': data.get('required_people', item.get('required_people', 1)),
            'priority': data.get('priority', item.get('priority', 'medium')),
            'recommended_start_time': data.get('recommended_start_time', item.get('recommended_start_time', '')),
            'recommended_end_time': data.get('recommended_end_time', item.get('recommended_end_time', '')),
            'morning_start_time': data.get('morning_start_time', item.get('morning_start_time', '')),
            'morning_end_time': data.get('morning_end_time', item.get('morning_end_time', '')),
            'afternoon_start_time': data.get('afternoon_start_time', item.get('afternoon_start_time', '')),
            'afternoon_end_time': data.get('afternoon_end_time', item.get('afternoon_end_time', ''))
        })
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '作業種別を更新しました'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def delete_task(task_type):
    try:
        table.delete_item(
            Key={'PK': f'TASK#{task_type}', 'SK': 'CONFIG'}
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '作業種別を削除しました'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }