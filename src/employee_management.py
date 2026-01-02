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

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # OPTIONSリクエストのCORS対応
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        if http_method == 'GET' and path == '/employees':
            return get_all_employees()
        elif http_method == 'POST' and path == '/employees':
            return create_employee(event)
        elif http_method == 'GET' and '/employees/' in path and path.endswith('/vacation-used'):
            employee_id = path.split('/')[-2]
            return get_vacation_used(employee_id)
        elif http_method == 'GET' and '/employees/' in path:
            employee_id = path.split('/')[-1]
            return get_employee(employee_id)
        elif http_method == 'PUT' and '/employees/' in path:
            employee_id = path.split('/')[-1]
            return update_employee(employee_id, event)
        elif http_method == 'DELETE' and '/employees/' in path:
            employee_id = path.split('/')[-1]
            return delete_employee(employee_id)
        else:
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

def get_all_employees():
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'EMPLOYEE'}
        )
        
        employees = []
        for item in response['Items']:
            employee = {
                'employee_id': item['SK'],
                'name': item.get('name', ''),
                'kana_name': item.get('kana_name', ''),
                'phone': item.get('phone', ''),
                'email': item.get('email', ''),
                'skills': item.get('skills', []),
                'vacation_days': int(item.get('vacation_days', 20)),
                'cognite_user_id': item.get('cognite_user_id', ''),
                'status': item.get('status', 'ACTIVE'),
                'created_at': item.get('created_at', ''),
                'deleted': item.get('deleted', False)
            }
            employees.append(employee)
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(employees)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def create_employee(event):
    try:
        data = json.loads(event['body'])
        
        # 常に自動採番（ユーザー入力は受け付けない）
        # 既存の従業員IDを取得して最大値+1を採番
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'EMPLOYEE'},
            ProjectionExpression='SK'
        )
        
        max_id = 0
        for item in response.get('Items', []):
            try:
                # 数値として解釈できるIDの最大値を取得
                current_id = int(item['SK'])
                max_id = max(max_id, current_id)
            except (ValueError, KeyError):
                # 数値でないIDはスキップ
                pass
        
        # 次のIDを3桁ゼロ埋めで生成
        employee_id = f"{max_id + 1:03d}"
        
        from datetime import datetime
        
        item = {
            'PK': 'EMPLOYEE',
            'SK': employee_id,
            'name': data['name'],
            'kana_name': data.get('kana_name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'skills': data.get('skills', []),
            'vacation_days': data.get('vacation_days', 20),
            'cognite_user_id': data.get('cognite_user_id', ''),
            'status': 'PENDING_APPROVAL',
            'created_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'message': '従業員を作成しました', 'employee_id': employee_id})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_employee(employee_id):
    try:
        response = table.get_item(
            Key={'PK': 'EMPLOYEE', 'SK': employee_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': '従業員が見つかりません'})
            }
        
        item = response['Item']
        employee = {
            'employee_id': item['SK'],
            'name': item.get('name', ''),
            'kana_name': item.get('kana_name', ''),
            'phone': item.get('phone', ''),
            'email': item.get('email', ''),
            'skills': item.get('skills', []),
            'vacation_days': int(item.get('vacation_days', 20)),
            'cognite_user_id': item.get('cognite_user_id', ''),
            'status': item.get('status', 'ACTIVE'),
            'created_at': item.get('created_at', '')
        }
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(employee)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def update_employee(employee_id, event):
    try:
        data = json.loads(event['body'])
        
        item = {
            'PK': 'EMPLOYEE',
            'SK': employee_id,
            'name': data['name'],
            'kana_name': data.get('kana_name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'skills': data.get('skills', []),
            'vacation_days': data.get('vacation_days', 20),
            'cognite_user_id': data.get('cognite_user_id', ''),
            'status': data.get('status', 'ACTIVE'),
            'created_at': data.get('created_at', '')
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'message': '従業員を更新しました'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def delete_employee(employee_id):
    try:
        table.delete_item(
            Key={'PK': 'EMPLOYEE', 'SK': employee_id}
        )
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'message': '従業員を削除しました'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_vacation_used(employee_id):
    try:
        # 今年の有給使用日数を計算（実装簡略化のため0を返す）
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'used_days': 0})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }