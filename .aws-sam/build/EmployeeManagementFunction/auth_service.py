import json
import boto3
import os
import time
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
        elif method == 'GET' and '/auth/user-by-sub/' in path:
            sub = path.split('/')[-1]
            return get_user_by_sub(sub)
        elif method == 'POST' and path == '/auth/check-user':
            return check_user_exists(json.loads(event['body']))
        elif method == 'POST' and path == '/auth/cognite-login':
            return cognite_login(json.loads(event['body']))
        elif method == 'POST' and path == '/auth/cognite-register':
            return cognite_register(json.loads(event['body']))
        elif method == 'POST' and path == '/auth/employee-register':
            return employee_register(json.loads(event['body']))
        elif method == 'POST' and path == '/auth/admin-change-password':
            return admin_change_password(json.loads(event['body']))
        elif method == 'GET' and path == '/auth/me':
            return get_current_user(event)
        
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
        
        # 簡易トークン処理（開発環境用）
        if not token.startswith('cognite_token_'):
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token'})
            }
        
        # トークンからユーザーIDを抽出
        try:
            parts = token.split('_')
            cognite_user_id = parts[2] if len(parts) > 2 else None
        except:
            cognite_user_id = None
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
        
        # 簡易トークン処理（開発環境用）
        if not token.startswith('cognite_token_'):
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token'})
            }
        
        # トークンからユーザーIDを抽出
        try:
            parts = token.split('_')
            cognite_user_id = parts[2] if len(parts) > 2 else None
        except:
            cognite_user_id = None
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

def check_user_exists(data):
    """メールアドレスでユーザーの存在を確認"""
    try:
        email = data.get('email')
        if not email:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # CogniteIDユーザーをメールアドレスで検索
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': email
            }
        )
        
        exists = len(response['Items']) > 0
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'exists': exists})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def cognite_login(data):
    """メールアドレス+パスワードでCognite認証ログイン"""
    try:
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # メールアドレスでユーザーを検索
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': email
            }
        )
        
        # 開発用管理者アカウントの特別処理
        if email == 'admin@example.com':
            if len(response['Items']) == 0:
                # 開発用管理者アカウントが存在しない場合は作成
                cognite_user_id = 'admin001'
                
                from datetime import datetime
                admin_item = {
                    'PK': f'COGNITE_USER#{cognite_user_id}',
                    'SK': 'PROFILE',
                    'cognite_user_id': cognite_user_id,
                    'email': email,
                    'name': '管理者',
                    'password': password,
                    'role': 'admin',
                    'employee_id': '',
                    'is_active': True,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                table.put_item(Item=admin_item)
                
                # JWTトークンを生成
                token = f"cognite_token_{cognite_user_id}_{int(time.time())}"
                
                user_profile = {
                    'cognite_user_id': cognite_user_id,
                    'name': '管理者',
                    'email': email,
                    'role': 'admin',
                    'is_active': True,
                    'employee_info': None
                }
                
                return {
                    'statusCode': 200,
                    'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                    'body': json.dumps({
                        'success': True,
                        'token': token,
                        'user': user_profile
                    }, default=decimal_default)
                }
            else:
                # 既存の管理者アカウントのロールを確認・更新
                user_item = response['Items'][0]
                if user_item.get('role') != 'admin':
                    user_item['role'] = 'admin'
                    table.put_item(Item=user_item)
        
        if len(response['Items']) == 0:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'User not found'})
            }
        
        user_item = response['Items'][0]
        
        # パスワードチェック（簡易実装）
        stored_password = user_item.get('password', '')
        if stored_password != password:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Invalid password'})
            }
        
        # ユーザー情報を取得
        cognite_user = {
            'cognite_user_id': user_item['PK'].split('#')[1],
            'name': user_item.get('name', ''),
            'email': user_item.get('email', ''),
            'role': user_item.get('role', 'employee'),
            'employee_id': user_item.get('employee_id', ''),
            'is_active': user_item.get('is_active', True)
        }
        
        # 従業員情報を取得
        employee_info = None
        if cognite_user.get('employee_id'):
            employee_info = get_employee_by_id(cognite_user['employee_id'])
        
        # JWTトークンを生成（簡易版）
        token = f"cognite_token_{cognite_user['cognite_user_id']}_{int(time.time())}"
        
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
                'success': True,
                'token': token,
                'user': user_profile
            }, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def cognite_register(data):
    """新規Cogniteユーザー登録"""
    try:
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        
        if not email or not name or not password:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Email, name, and password are required'})
            }
        
        # 既存ユーザーチェック
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': email
            }
        )
        
        if len(response['Items']) > 0:
            return {
                'statusCode': 409,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'User already exists'})
            }
        
        # 新しいCogniteIDを生成
        import random
        import string
        cognite_user_id = 'usr' + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # 新規ユーザーを作成
        from datetime import datetime
        item = {
            'PK': f'COGNITE_USER#{cognite_user_id}',
            'SK': 'PROFILE',
            'cognite_user_id': cognite_user_id,
            'email': email,
            'name': name,
            'password': password,  # 開発環境では平文保存（本番ではハッシュ化が必要）
            'role': 'employee',  # デフォルトは従業員
            'employee_id': '',  # 後で管理者が設定
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({
                'success': True,
                'cognite_user_id': cognite_user_id,
                'message': 'User created successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def employee_register(data):
    """従業員登録申請（管理者承認待ち状態で作成）"""
    try:
        email = data.get('email')
        name = data.get('name')
        kana_name = data.get('kana_name')
        phone = data.get('phone')
        password = data.get('password')
        
        if not all([email, name, kana_name, phone, password]):
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'All fields are required'})
            }
        
        # 既存ユーザーチェック
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': email
            }
        )
        
        if len(response['Items']) > 0:
            return {
                'statusCode': 409,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'User already exists'})
            }
        
        # 従業員IDを生成
        import random
        import string
        employee_id = ''.join(random.choices(string.digits, k=3))
        
        # 重複チェック
        while True:
            existing = table.get_item(
                Key={'PK': 'EMPLOYEE', 'SK': employee_id}
            )
            if 'Item' not in existing:
                break
            employee_id = ''.join(random.choices(string.digits, k=3))
        
        # CogniteIDを生成
        cognite_user_id = 'usr' + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        from datetime import datetime
        
        # 従業員レコードを作成（承認待ち状態）
        employee_item = {
            'PK': 'EMPLOYEE',
            'SK': employee_id,
            'employee_id': employee_id,
            'name': name,
            'kana_name': kana_name,
            'phone': phone,
            'email': email,
            'skills': [],
            'vacation_days': 20,
            'status': 'PENDING_APPROVAL',  # 承認待ち
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # CogniteIDユーザーレコードを作成（非アクティブ状態）
        cognite_item = {
            'PK': f'COGNITE_USER#{cognite_user_id}',
            'SK': 'PROFILE',
            'cognite_user_id': cognite_user_id,
            'email': email,
            'name': name,
            'password': password,
            'role': 'employee',
            'employee_id': employee_id,
            'is_active': False,  # 非アクティブ
            'status': 'PENDING_APPROVAL',  # 承認待ち
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # データベースに保存
        table.put_item(Item=employee_item)
        table.put_item(Item=cognite_item)
        
        return {
            'statusCode': 201,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({
                'success': True,
                'employee_id': employee_id,
                'cognite_user_id': cognite_user_id,
                'message': 'Employee registration submitted for approval'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def admin_change_password(data):
    """管理者によるパスワード変更"""
    try:
        target_email = data.get('target_email')
        new_password = data.get('new_password')
        admin_token = data.get('admin_token')
        
        if not all([target_email, new_password, admin_token]):
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Target email, new password, and admin token are required'})
            }
        
        # 管理者権限を確認
        if not admin_token.startswith('cognite_token_'):
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Invalid admin token'})
            }
        
        # トークンから管理者IDを取得
        try:
            parts = admin_token.split('_')
            admin_user_id = parts[2] if len(parts) > 2 else None
        except:
            admin_user_id = None
            
        if not admin_user_id:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Invalid admin token'})
            }
        
        # 管理者情報を取得
        admin_user = get_cognite_user_by_id(admin_user_id)
        if not admin_user or admin_user.get('role') != 'admin':
            return {
                'statusCode': 403,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Admin privileges required'})
            }
        
        # 対象ユーザーを検索
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': target_email
            }
        )
        
        if len(response['Items']) == 0:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Target user not found'})
            }
        
        user_item = response['Items'][0]
        
        # パスワードを更新
        from datetime import datetime
        user_item['password'] = new_password
        user_item['updated_at'] = datetime.now().isoformat()
        
        table.put_item(Item=user_item)
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({
                'success': True,
                'message': 'Password updated successfully by admin'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def get_current_user(event):
    """現在のユーザー情報を取得（JWTからsubを抽出）"""
    try:
        # AuthorizationヘッダーからJWTトークンを取得
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Authorization header required'})
            }
        
        token = auth_header.replace('Bearer ', '')
        
        # 簡易トークン処理（開発環境用）
        if not token.startswith('cognite_token_'):
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token'})
            }
        
        # トークンからユーザーIDを抽出
        try:
            parts = token.split('_')
            sub = parts[2] if len(parts) > 2 else None
        except:
            sub = None
        if not sub:
            return {
                'statusCode': 401,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Invalid token: no sub claim'})
            }
        
        # subでユーザー情報を取得
        return get_user_by_sub(sub)
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_user_by_sub(sub):
    """subをキーにCogniteIDユーザーを検索"""
    try:
        # CogniteIDユーザーを検索
        response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{sub}',
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
        cognite_user = {
            'cognite_user_id': item['PK'].split('#')[1],
            'name': item.get('name', ''),
            'email': item.get('email', ''),
            'role': item.get('role', 'employee'),
            'employee_id': item.get('employee_id', ''),
            'is_active': item.get('is_active', True)
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