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

def get_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def decimal_default(obj):
    """JSON serialization for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        method = event['httpMethod']
        path = event.get('path', '')
        
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        if method == 'GET':
            if '/cognite-users/' in path:
                # 個別ユーザー取得
                user_id = path.split('/')[-1]
                return get_cognite_user(user_id)
            else:
                # ユーザー一覧取得
                return get_cognite_users()
        elif method == 'POST':
            return create_cognite_user(json.loads(event['body']))
        elif method == 'PUT':
            user_id = path.split('/')[-1]
            return update_cognite_user(user_id, json.loads(event['body']))
        elif method == 'DELETE':
            user_id = path.split('/')[-1]
            return delete_cognite_user(user_id)
        
        return {
            'statusCode': 405,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': 'Method not allowed'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_cognite_users():
    """CogniteIDユーザー一覧を取得"""
    try:
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'COGNITE_USER#'}
        )
        
        users = []
        for item in response['Items']:
            if item['SK'] == 'PROFILE':
                user = {
                    'cognite_user_id': item['PK'].split('#')[1],
                    'email': item.get('email', ''),
                    'name': item.get('name', ''),
                    'role': item.get('role', 'employee'),
                    'employee_id': item.get('employee_id', ''),
                    'is_active': item.get('is_active', True),
                    'created_at': item.get('created_at', ''),
                    'updated_at': item.get('updated_at', '')
                }
                users.append(user)
        
        # 作成日時でソート
        users.sort(key=lambda x: x.get('created_at', ''))
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(users, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_cognite_user(user_id):
    """個別CogniteIDユーザーを取得"""
    try:
        response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'User not found'})
            }
        
        item = response['Item']
        user = {
            'cognite_user_id': item['PK'].split('#')[1],
            'email': item.get('email', ''),
            'name': item.get('name', ''),
            'role': item.get('role', 'employee'),
            'employee_id': item.get('employee_id', ''),
            'is_active': item.get('is_active', True),
            'created_at': item.get('created_at', ''),
            'updated_at': item.get('updated_at', '')
        }
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(user, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def create_cognite_user(data):
    """CogniteIDユーザーを作成"""
    try:
        # CogniteIDを自動生成
        cognite_user_id = generate_cognite_user_id()
        
        # 既存チェック（念のため）
        existing = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{cognite_user_id}',
                'SK': 'PROFILE'
            }
        )
        
        # 重複した場合は再生成
        while 'Item' in existing:
            cognite_user_id = generate_cognite_user_id()
            existing = table.get_item(
                Key={
                    'PK': f'COGNITE_USER#{cognite_user_id}',
                    'SK': 'PROFILE'
                }
            )
        
        item = {
            'PK': f'COGNITE_USER#{cognite_user_id}',
            'SK': 'PROFILE',
            'cognite_user_id': cognite_user_id,
            'email': data.get('email', ''),
            'name': data.get('name', ''),
            'role': data.get('role', 'employee'),
            'employee_id': data.get('employee_id', ''),
            'is_active': data.get('is_active', True),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', '')
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'message': 'User created successfully', 'cognite_user_id': cognite_user_id})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def generate_cognite_user_id():
    """運用しやすいCogniteIDを自動生成"""
    import random
    import string
    
    # プレフィックス + 8桁の英数字（大文字・小文字・数字のみ）
    prefix = "usr"
    chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    random_part = ''.join(random.choices(chars, k=8))
    
    return f"{prefix}{random_part}"

def update_cognite_user(user_id, data):
    """CogniteIDユーザーを更新"""
    try:
        # 既存データを取得
        response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'User not found'})
            }
        
        # 既存データとマージ
        item = response['Item']
        item.update({
            'email': data.get('email', item.get('email', '')),
            'name': data.get('name', item.get('name', '')),
            'role': data.get('role', item.get('role', 'employee')),
            'employee_id': data.get('employee_id', item.get('employee_id', '')),
            'is_active': data.get('is_active', item.get('is_active', True)),
            'updated_at': data.get('updated_at', '')
        })
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'message': 'User updated successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def delete_cognite_user(user_id):
    """CogniteIDユーザーを削除"""
    try:
        table.delete_item(
            Key={
                'PK': f'COGNITE_USER#{user_id}',
                'SK': 'PROFILE'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'message': 'User deleted successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }