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
        elif method == 'POST' and path == '/auth/password-reset-request':
            return password_reset_request(json.loads(event['body']))
        elif method == 'POST' and path == '/auth/password-reset':
            return password_reset(json.loads(event['body']))
        elif method == 'POST' and path == '/auth/password-reset-direct':
            return password_reset_direct(json.loads(event['body']))
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

def password_reset_request(data):
    """パスワード再設定メール送信要求"""
    try:
        email = data.get('email')
        if not email:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # ユーザー存在確認
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': email
            }
        )
        
        if len(response['Items']) == 0:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'User not found'})
            }
        
        user_item = response['Items'][0]
        cognite_user_id = user_item['PK'].split('#')[1]
        user_name = user_item.get('name', '')
        
        # リセットトークンを生成
        import random
        import string
        reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        from datetime import datetime, timedelta
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        # リセットトークンを保存
        reset_item = {
            'PK': f'PASSWORD_RESET#{reset_token}',
            'SK': 'TOKEN',
            'cognite_user_id': cognite_user_id,
            'email': email,
            'expires_at': expires_at,
            'created_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=reset_item)
        
        # メール送信
        try:
            send_password_reset_email(email, user_name, reset_token)
            return {
                'statusCode': 200,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({
                    'success': True,
                    'message': 'Password reset email sent'
                })
            }
        except Exception as email_error:
            print(f'Email sending failed: {email_error}')
            # メール送信失敗時は開発環境用のトークンを返す
            return {
                'statusCode': 200,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({
                    'success': True,
                    'message': 'Password reset email sent',
                    'dev_token': reset_token  # 開発環境用
                })
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def send_password_reset_email(email, user_name, reset_token):
    """パスワード再設定メールを送信"""
    import boto3
    from botocore.exceptions import ClientError
    
    ses_client = boto3.client('ses', region_name='ap-northeast-1')
    
    # メールの内容を作成
    reset_url = f"https://mxh6g7opm2.execute-api.ap-northeast-1.amazonaws.com/dev/password-reset.html?token={reset_token}"
    
    subject = "【酒農シフト管理システム】パスワード再設定のご案内"
    
    body_text = f"""
{user_name} 様

酒農シフト管理システムでパスワード再設定のリクエストを受け付けました。

以下のリンクをクリックして、新しいパスワードを設定してください。

{reset_url}

このリンクは1時間有効です。

もしこのメールに心当たりがない場合は、このメールを無視してください。

酒農シフト管理システム
"""
    
    body_html = f"""
<html>
<head></head>
<body>
    <h2>パスワード再設定のご案内</h2>
    <p>{user_name} 様</p>
    <p>酒農シフト管理システムでパスワード再設定のリクエストを受け付けました。</p>
    <p>以下のボタンをクリックして、新しいパスワードを設定してください。</p>
    <p style="margin: 20px 0;">
        <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">パスワードを再設定</a>
    </p>
    <p><strong>このリンクは1時間有効です。</strong></p>
    <p>もしこのメールに心当たりがない場合は、このメールを無視してください。</p>
    <hr>
    <p><small>酒農シフト管理システム</small></p>
</body>
</html>
"""
    
    # 送信者メールアドレス（環境変数から取得、デフォルト値あり）
    sender_email = os.environ.get('SENDER_EMAIL', 'noreply@example.com')
    
    try:
        response = ses_client.send_email(
            Destination={
                'ToAddresses': [email],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=sender_email,
        )
        print(f'Email sent successfully. Message ID: {response["MessageId"]}')
        return response
    except ClientError as e:
        print(f'Error sending email: {e.response["Error"]["Message"]}')
        raise e

def password_reset(data):
    """パスワード再設定実行"""
    try:
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Token and new password are required'})
            }
        
        # トークンを検証
        token_response = table.get_item(
            Key={
                'PK': f'PASSWORD_RESET#{token}',
                'SK': 'TOKEN'
            }
        )
        
        if 'Item' not in token_response:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Invalid or expired token'})
            }
        
        token_item = token_response['Item']
        
        # 有効期限をチェック
        from datetime import datetime
        expires_at = datetime.fromisoformat(token_item['expires_at'])
        if datetime.now() > expires_at:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'Token has expired'})
            }
        
        cognite_user_id = token_item['cognite_user_id']
        
        # ユーザーのパスワードを更新
        user_response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{cognite_user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'User not found'})
            }
        
        user_item = user_response['Item']
        user_item['password'] = new_password
        user_item['updated_at'] = datetime.now().isoformat()
        
        table.put_item(Item=user_item)
        
        # トークンを削除
        table.delete_item(
            Key={
                'PK': f'PASSWORD_RESET#{token}',
                'SK': 'TOKEN'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({
                'success': True,
                'message': 'Password updated successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def password_reset_direct(data):
    """直接パスワード変更（メール送信なし）"""
    try:
        email = data.get('email')
        new_password = data.get('new_password')
        
        if not email or not new_password:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Email and new password are required'})
            }
        
        # ユーザー存在確認
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND email = :email',
            ExpressionAttributeValues={
                ':pk': 'COGNITE_USER#',
                ':email': email
            }
        )
        
        if len(response['Items']) == 0:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'success': False, 'error': 'User not found'})
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
                'message': 'Password updated successfully'
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