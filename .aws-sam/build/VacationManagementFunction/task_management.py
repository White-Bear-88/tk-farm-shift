import json
import boto3
import os
from decimal import Decimal

# Support local dynamodb endpoint
_dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT')
if _dynamodb_endpoint:
    dynamodb = boto3.resource('dynamodb', endpoint_url=_dynamodb_endpoint)
else:
    dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table(os.environ['TABLE_NAME'])

def decimal_default(obj):
    """JSON serialization for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        method = event['httpMethod']
        path = event.get('path', '')
        
        if method == 'GET':
            if '/tasks/' in path:
                # 個別作業種別取得
                task_id = path.split('/')[-1]
                return get_task(task_id)
            else:
                # 作業種別一覧取得
                return get_tasks()
        elif method == 'POST':
            return create_task(json.loads(event['body']))
        elif method == 'PUT':
            task_id = path.split('/')[-1]
            return update_task(task_id, json.loads(event['body']))
        elif method == 'DELETE':
            task_id = path.split('/')[-1]
            return delete_task(task_id)
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_tasks():
    """作業種別一覧を取得"""
    response = table.scan(
        FilterExpression='begins_with(PK, :pk)',
        ExpressionAttributeValues={':pk': 'TASK#'}
    )
    
    tasks = []
    for item in response['Items']:
        if item['SK'] == 'CONFIG':
            # デバッグ用ログ
            print(f"Processing item: {item}")
            
            task_type = item.get('task_type')
            if not task_type:
                # task_typeがない場合はPKから抽出
                task_type = item['PK'].split('#')[1]
                print(f"No task_type field, using PK: {task_type}")
            
            task = {
                'task_type': task_type,
                'name': item['name'],
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
            print(f"Created task: {task}")
            tasks.append(task)
    
    # IDでソート
    tasks.sort(key=lambda x: int(x['task_type']) if x['task_type'].isdigit() else 999)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(tasks, default=decimal_default)
    }

def get_task(task_id):
    """個別作業種別を取得"""
    try:
        response = table.get_item(
            Key={
                'PK': f'TASK#{task_id}',
                'SK': 'CONFIG'
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Task not found'})
            }
        
        item = response['Item']
        task = {
            'task_type': item.get('task_type', task_id),
            'name': item['name'],
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

def create_task(data):
    """作業種別を作成"""
    try:
        task_type = data['task_type']
        
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
            'afternoon_end_time': data.get('afternoon_end_time', ''),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', '')
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Task created successfully', 'task_type': task_type})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def update_task(task_id, data):
    """作業種別を更新"""
    try:
        # 既存データを取得
        response = table.get_item(
            Key={
                'PK': f'TASK#{task_id}',
                'SK': 'CONFIG'
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Task not found'})
            }
        
        # 既存データとマージ
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
            'body': json.dumps({'message': 'Task updated successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def delete_task(task_id):
    """作業種別を削除"""
    try:
        table.delete_item(
            Key={
                'PK': f'TASK#{task_id}',
                'SK': 'CONFIG'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Task deleted successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }