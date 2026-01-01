import json
import boto3
import os
import jwt
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
        
        if method == 'POST' and path == '/auth/verify':
            return verify_jwt_token(json.loads(event['body']))
        elif method == 'GET' and path == '/auth/profile':
            return get_user_profile(event)
        
        return {
            'statusCode': 404,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def verify_jwt_token(data):
    """JWTトークンを検証してユーザー情報を返す"""
    try:
        token = data.get('token')
        if not token:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Token is required'})
            }
        
        # JWTトークンをデコード（検証なしでデモ用）
        # 本番環境では適切な秘密鍵で検証する必要があります
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token'})
            }
        
        cognite_user_id = decoded.get('sub')
        if not cognite_user_id:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token: no sub claim'})
            }
        
        # CogniteIDユーザー情報を取得
        cognite_user = get_cognite_user_by_id(cognite_user_id)
        if not cognite_user:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'User not found'})
            }
        
        # 従業員情報を取得（紐づけがある場合）
        employee_info = None
        if cognite_user.get('employee_id'):
            employee_info = get_employee_by_id(cognite_user['employee_id'])
        
        user_profile = {
            'cognite_user_id': cognite_user['cognite_user_id'],
            'name': cognite_user['name'],
            'email': cognite_user['email'],
            'role': cognite_user['role'],
            'is_active': cognite_user['is_active'],
            'employee_info': employee_info
        }
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({
                'valid': True,
                'user': user_profile
            }, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_user_profile(event):
    """Authorizationヘッダーからユーザープロファイルを取得"""
    try:
        # Authorizationヘッダーからトークンを取得
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Authorization header required'})
            }
        
        token = auth_header.replace('Bearer ', '')
        
        # JWTトークンをデコード
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token'})
            }
        
        cognite_user_id = decoded.get('sub')
        if not cognite_user_id:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token: no sub claim'})
            }
        
        # ユーザー情報を取得
        cognite_user = get_cognite_user_by_id(cognite_user_id)
        if not cognite_user:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'User not found'})
            }
        
        # 従業員情報を取得
        employee_info = None
        if cognite_user.get('employee_id'):
            employee_info = get_employee_by_id(cognite_user['employee_id'])
        
        user_profile = {
            'cognite_user_id': cognite_user['cognite_user_id'],
            'name': cognite_user['name'],
            'email': cognite_user['email'],
            'role': cognite_user['role'],
            'is_active': cognite_user['is_active'],
            'employee_info': employee_info
        }
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(user_profile, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_cognite_user_by_id(cognite_user_id):
    """CogniteIDでユーザー情報を取得"""
    try:
        response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{cognite_user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        return {
            'cognite_user_id': item['PK'].split('#')[1],
            'name': item.get('name', ''),
            'email': item.get('email', ''),
            'role': item.get('role', 'employee'),
            'employee_id': item.get('employee_id', ''),
            'is_active': item.get('is_active', True)
        }
        
    except Exception as e:
        print(f"Error getting cognite user: {e}")
        return None

def get_employee_by_id(employee_id):
    """従業員IDで従業員情報を取得"""
    try:
        response = table.get_item(
            Key={
                'PK': 'EMPLOYEE',
                'SK': employee_id
            }
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        return {
            'employee_id': item['SK'],
            'name': item.get('name', ''),
            'kana_name': item.get('kana_name', ''),
            'phone': item.get('phone', ''),
            'email': item.get('email', ''),
            'skills': item.get('skills', []),
            'vacation_days': int(item.get('vacation_days', 20))
        }
        
    except Exception as e:
        print(f"Error getting employee: {e}")
        return None