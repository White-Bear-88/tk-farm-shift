import json
import boto3
import os
from decimal import Decimal

# Cognito Identity Provider client
cognito_client = boto3.client('cognito-idp')

# DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def get_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def decimal_default(obj):
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
        
        if method == 'GET' and path == '/cognito-admin/users':
            return list_cognito_users()
        elif method == 'POST' and path == '/cognito-admin/approve':
            return approve_user(json.loads(event['body']))
        elif method == 'POST' and path == '/cognito-admin/reject':
            return reject_user(json.loads(event['body']))
        elif method == 'POST' and path == '/cognito-admin/disable':
            return disable_user(json.loads(event['body']))
        elif method == 'POST' and path == '/cognito-admin/enable':
            return enable_user(json.loads(event['body']))
        
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

def list_cognito_users():
    """Cognito ユーザープールのユーザー一覧を取得"""
    try:
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        if not user_pool_id:
            return {
                'statusCode': 500,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'COGNITO_USER_POOL_ID not configured'})
            }
        
        response = cognito_client.list_users(
            UserPoolId=user_pool_id,
            Limit=60
        )
        
        users = []
        for user in response['Users']:
            user_info = {
                'username': user['Username'],
                'user_status': user['UserStatus'],
                'enabled': user['Enabled'],
                'created_date': user['UserCreateDate'].isoformat(),
                'attributes': {}
            }
            
            # ユーザー属性を取得
            for attr in user.get('Attributes', []):
                user_info['attributes'][attr['Name']] = attr['Value']
            
            users.append(user_info)
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'users': users})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def approve_user(data):
    """ユーザーを承認（CONFIRMED状態に変更）"""
    try:
        username = data.get('username')
        if not username:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Username is required'})
            }
        
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        
        # AdminConfirmSignUp API を呼び出し
        cognito_client.admin_confirm_sign_up(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': True, 'message': 'User approved successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def reject_user(data):
    """ユーザーを拒否（削除）"""
    try:
        username = data.get('username')
        if not username:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Username is required'})
            }
        
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        
        # ユーザーを削除
        cognito_client.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': True, 'message': 'User rejected and deleted'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def disable_user(data):
    """ユーザーを無効化"""
    try:
        username = data.get('username')
        if not username:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Username is required'})
            }
        
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        
        # ユーザーを無効化
        cognito_client.admin_disable_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': True, 'message': 'User disabled successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def enable_user(data):
    """ユーザーを有効化"""
    try:
        username = data.get('username')
        if not username:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Username is required'})
            }
        
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        
        # ユーザーを有効化
        cognito_client.admin_enable_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': True, 'message': 'User enabled successfully'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }