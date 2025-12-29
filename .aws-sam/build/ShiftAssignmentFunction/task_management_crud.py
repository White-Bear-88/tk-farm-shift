import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

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
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'TASK'}
        )
        
        tasks = []
        for item in response['Items']:
            task = {
                'task_type': item['SK'],
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'duration_minutes': int(item.get('duration_minutes', 60)),
                'required_people': int(item.get('required_people', 1)),
                'priority': item.get('priority', 'medium'),
                'recommended_start_time': item.get('recommended_start_time', ''),
                'recommended_end_time': item.get('recommended_end_time', '')
            }
            tasks.append(task)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(tasks)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def to_task_id(name):
    # Small mapping for known Japanese names -> ids, fallback to ASCII slug
    mapping = {
        '搾乳': 'milking',
        '給餌': 'feeding',
        '清掃': 'cleaning',
        '見回り': 'patrol',
        '点検': 'maintenance',
        '健康チェック': 'health_check'
    }
    if not name:
        return ''
    if name in mapping:
        return mapping[name]
    try:
        import unicodedata
        norm = unicodedata.normalize('NFKD', name)
        ascii_only = ''.join([c for c in norm if ord(c) < 128])
        slug = ''.join([c if c.isalnum() else '_' for c in ascii_only]).strip('_').lower()
        if slug:
            return slug
    except Exception:
        pass
    # fallback: replace non word chars
    return ''.join([c if c.isalnum() else '_' for c in name]).strip('_').lower()


def create_task(event):
    try:
        data = json.loads(event['body'])
        # If task_type not provided, generate from name
        task_type = data.get('task_type') or to_task_id(data.get('name'))
        if not task_type:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'task_type could not be generated'})
            }
        # Ensure unique task_type: if collision, append numeric suffix until unique
        base = task_type
        candidate = base
        suffix = 0
        while True:
            existing = table.get_item(Key={'PK': 'TASK', 'SK': candidate})
            if not existing.get('Item'):
                break
            suffix += 1
            candidate = f"{base}_{suffix}"

        task_type = candidate

        item = {
            'PK': 'TASK',
            'SK': task_type,
            'name': data['name'],
            'description': data.get('description', ''),
            'duration_minutes': data.get('duration_minutes', 60),
            'required_people': data.get('required_people', 1),
            'priority': data.get('priority', 'medium'),
            'recommended_start_time': data.get('recommended_start_time', ''),
            'recommended_end_time': data.get('recommended_end_time', '')
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
            Key={'PK': 'TASK', 'SK': task_type}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '作業種別が見つかりません'})
            }
        
        item = response['Item']
        task = {
            'task_type': item['SK'],
            'name': item.get('name', ''),
            'description': item.get('description', ''),
            'duration_minutes': int(item.get('duration_minutes', 60)),
            'required_people': int(item.get('required_people', 1)),
            'priority': item.get('priority', 'medium'),
            'recommended_start_time': item.get('recommended_start_time', ''),
            'recommended_end_time': item.get('recommended_end_time', '')
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(task)
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
        
        item = {
            'PK': 'TASK',
            'SK': task_type,
            'name': data['name'],
            'description': data.get('description', ''),
            'duration_minutes': data.get('duration_minutes', 60),
            'required_people': data.get('required_people', 1),
            'priority': data.get('priority', 'medium'),
            'recommended_start_time': data.get('recommended_start_time', ''),
            'recommended_end_time': data.get('recommended_end_time', '')
        }
        
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
            Key={'PK': 'TASK', 'SK': task_type}
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