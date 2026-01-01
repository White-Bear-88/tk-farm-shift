import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

# DynamoDBクライアント
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'DairyShiftManagement')
table = dynamodb.Table(table_name)

def get_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    休暇申請管理のメインハンドラー
    """
    print(f"Event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        if http_method == 'GET' and '/vacation-requests' in path:
            # 休暇申請一覧取得
            query_params = event.get('queryStringParameters') or {}
            employee_id = query_params.get('employee_id')
            if employee_id:
                return get_vacation_requests_by_employee(employee_id)
            else:
                return get_all_vacation_requests()
        
        elif http_method == 'POST' and '/vacation-requests' in path:
            # 休暇申請作成
            return create_vacation_request(event)
        
        elif http_method == 'PUT' and '/vacation-requests/' in path:
            # 休暇申請更新（ステータス変更など）
            request_id = path.split('/vacation-requests/')[-1]
            return update_vacation_request(request_id, event)
        
        elif http_method == 'DELETE' and '/vacation-requests/' in path:
            # 休暇申請削除
            request_id = path.split('/vacation-requests/')[-1]
            return delete_vacation_request(request_id)
        
        else:
            return {
                'statusCode': 404,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': 'Not Found'})
            }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_all_vacation_requests():
    """全ての休暇申請を取得"""
    try:
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :gsi1pk',
            ExpressionAttributeValues={':gsi1pk': 'VACATION_REQUEST'}
        )
        
        items = response.get('Items', [])
        
        # 各itemにrequest_idを確実に設定
        for item in items:
            if 'request_id' not in item:
                # PKとSKからrequest_idを生成（_区切り）
                pk = item.get('PK', '')
                sk = item.get('SK', '')
                employee_id = pk.replace('EMPLOYEE#', '')
                timestamp = sk.replace('VACATION#', '')
                item['request_id'] = f'{employee_id}_{timestamp}'
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(items, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error in get_all_vacation_requests: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def get_vacation_requests_by_employee(employee_id):
    """特定従業員の休暇申請を取得"""
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'EMPLOYEE#{employee_id}',
                ':sk_prefix': 'VACATION#'
            }
        )
        
        items = response.get('Items', [])
        
        # 各itemにrequest_idを確実に設定
        for item in items:
            if 'request_id' not in item:
                # SKからタイムスタンプを抽出してrequest_idを生成（_区切り）
                sk = item.get('SK', '')
                timestamp = sk.replace('VACATION#', '')
                item['request_id'] = f'{employee_id}_{timestamp}'
        
        # 日付でソート（降順）
        items.sort(key=lambda x: x.get('start_date', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps(items, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error in get_vacation_requests_by_employee: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def create_vacation_request(event):
    """休暇申請を作成"""
    try:
        data = json.loads(event.get('body', '{}'))
        
        employee_id = data.get('employee_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date', start_date)
        vacation_type = data.get('type', 'full')
        time_type = data.get('time_type', 'full')  # 時間区分を追加
        reason = data.get('reason', '')
        status = data.get('status', 'applying')  # デフォルトは申請中
        
        if not employee_id or not start_date:
            return {
                'statusCode': 400,
                'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
                'body': json.dumps({'error': '従業員IDと開始日は必須です'})
            }
        
        # タイムスタンプをリクエストIDとして使用（#の代わりに_を使用）
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        request_id = f'{employee_id}_{timestamp}'
        
        item = {
            'PK': f'EMPLOYEE#{employee_id}',
            'SK': f'VACATION#{timestamp}',
            'GSI1PK': 'VACATION_REQUEST',
            'GSI1SK': f'{start_date}#{request_id}',
            'request_id': request_id,
            'employee_id': employee_id,
            'start_date': start_date,
            'end_date': end_date,
            'type': vacation_type,
            'time_type': time_type,  # 時間区分を保存
            'reason': reason,
            'status': status,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({
                'message': '休暇申請を作成しました',
                'request_id': request_id
            })
        }
    except Exception as e:
        print(f"Error in create_vacation_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {**{'Content-Type': 'application/json'}, **get_cors_headers()},
            'body': json.dumps({'error': str(e)})
        }

def update_vacation_request(request_id, event):
    """休暇申請を更新（ステータス変更など）"""
    try:
        data = json.loads(event.get('body', '{}'))
        
        # request_idから従業員IDとタイムスタンプを抽出（_区切り）
        parts = request_id.split('_')
        if len(parts) < 2:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '無効なリクエストIDです'})
            }
        
        employee_id = parts[0]
        timestamp = parts[1]
        
        # 更新する属性を準備
        update_expression = 'SET updated_at = :updated_at'
        expression_values = {':updated_at': datetime.now().isoformat()}
        
        if 'status' in data:
            update_expression += ', #status = :status'
            expression_values[':status'] = data['status']
        
        if 'reason' in data:
            update_expression += ', reason = :reason'
            expression_values[':reason'] = data['reason']
        
        expression_names = {'#status': 'status'} if 'status' in data else None
        
        update_params = {
            'Key': {
                'PK': f'EMPLOYEE#{employee_id}',
                'SK': f'VACATION#{timestamp}'
            },
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_names:
            update_params['ExpressionAttributeNames'] = expression_names
        
        response = table.update_item(**update_params)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': '休暇申請を更新しました',
                'item': response.get('Attributes', {})
            }, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error in update_vacation_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def delete_vacation_request(request_id):
    """休暇申請を削除"""
    try:
        # request_idから従業員IDとタイムスタンプを抽出（_区切り）
        parts = request_id.split('_')
        if len(parts) < 2:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '無効なリクエストIDです'})
            }
        
        employee_id = parts[0]
        timestamp = parts[1]
        
        table.delete_item(
            Key={
                'PK': f'EMPLOYEE#{employee_id}',
                'SK': f'VACATION#{timestamp}'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '休暇申請を削除しました'})
        }
    except Exception as e:
        print(f"Error in delete_vacation_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
