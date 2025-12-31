import json
import boto3
import os

# Support local dynamodb endpoint
_dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT')
if _dynamodb_endpoint:
    dynamodb = boto3.resource('dynamodb', endpoint_url=_dynamodb_endpoint)
else:
    dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # Requirements API
        if '/requirements/' in path:
            return handle_requirements(event, http_method, path)
        
        # Settings API
        elif '/settings/' in path:
            return handle_settings(event, http_method, path)
        
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

def handle_requirements(event, http_method, path):
    """人数設定API"""
    if 'global-default' in path:
        if http_method == 'GET':
            return get_global_default_requirements()
        elif http_method == 'POST':
            return save_global_default_requirements(event)
    
    elif '/default/' in path:
        month = path.split('/')[-1]
        if http_method == 'GET':
            return get_monthly_requirements(month)
        elif http_method == 'POST':
            return save_monthly_requirements(month, event)
    
    elif '/daily/' in path:
        date = path.split('/')[-1]
        if http_method == 'GET':
            return get_daily_requirements(date)
        elif http_method == 'POST':
            return save_daily_requirements(date, event)
    
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Requirements endpoint not found'})
    }

def handle_settings(event, http_method, path):
    """設定API"""
    if 'confirmation' in path:
        if http_method == 'GET':
            return get_confirmation_settings()
        elif http_method == 'POST':
            return save_confirmation_settings(event)
    
    elif 'vacation-default' in path:
        if http_method == 'GET':
            return get_vacation_default()
        elif http_method == 'POST':
            return save_vacation_default(event)
    
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Settings endpoint not found'})
    }

# Requirements functions
def get_global_default_requirements():
    try:
        response = table.get_item(
            Key={'PK': 'REQUIREMENTS', 'SK': 'GLOBAL_DEFAULT'}
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response['Item']['requirements'])
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({})
            }
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({})
        }

def save_global_default_requirements(event):
    try:
        data = json.loads(event['body'])
        
        item = {
            'PK': 'REQUIREMENTS',
            'SK': 'GLOBAL_DEFAULT',
            'requirements': data
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Global default requirements saved'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_monthly_requirements(month):
    try:
        response = table.get_item(
            Key={'PK': 'REQUIREMENTS', 'SK': f'MONTH#{month}'}
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response['Item']['requirements'])
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def save_monthly_requirements(month, event):
    data = json.loads(event['body'])
    
    item = {
        'PK': 'REQUIREMENTS',
        'SK': f'MONTH#{month}',
        'requirements': data
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': f'Monthly requirements for {month} saved'})
    }

def get_daily_requirements(date):
    try:
        response = table.get_item(
            Key={'PK': 'REQUIREMENTS', 'SK': f'DAILY#{date}'}
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response['Item']['requirements'])
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def save_daily_requirements(date, event):
    data = json.loads(event['body'])
    
    item = {
        'PK': 'REQUIREMENTS',
        'SK': f'DAILY#{date}',
        'requirements': data
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': f'Daily requirements for {date} saved'})
    }

# Settings functions
def get_confirmation_settings():
    try:
        response = table.get_item(
            Key={'PK': 'SETTINGS', 'SK': 'CONFIRMATION'}
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'confirmation_day': response['Item'].get('confirmation_day', 25)
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'confirmation_day': 25})
            }
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'confirmation_day': 25})
        }

def save_confirmation_settings(event):
    try:
        data = json.loads(event['body'])
        
        item = {
            'PK': 'SETTINGS',
            'SK': 'CONFIRMATION',
            'confirmation_day': data['confirmation_day']
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Confirmation settings saved'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_vacation_default():
    """休暇デフォルト設定を取得"""
    try:
        response = table.get_item(
            Key={'PK': 'SETTINGS', 'SK': 'VACATION_DEFAULT'}
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'default_vacation_days': int(response['Item'].get('default_vacation_days', 20)),
                    'annual_vacation_days': int(response['Item'].get('annual_vacation_days', 0)),
                    'monthly_vacation_limit': int(response['Item'].get('monthly_vacation_limit', 0)),
                    'paid_monthly_limit': int(response['Item'].get('paid_monthly_limit', 0)),
                    'custom_vacation_types': response['Item'].get('custom_vacation_types', [])
                })
            }
        else:
            # デフォルト値を返す
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'default_vacation_days': 20,
                    'annual_vacation_days': 0,
                    'monthly_vacation_limit': 0,
                    'paid_monthly_limit': 0,
                    'custom_vacation_types': []
                })
            }
    except Exception as e:
        print(f"Error in get_vacation_default: {str(e)}")
        # エラーが発生してもデフォルト値を返す（500エラーを避ける）
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'default_vacation_days': 20,
                'annual_vacation_days': 0,
                'monthly_vacation_limit': 0,
                'paid_monthly_limit': 0,
                'custom_vacation_types': []
            })
        }

def save_vacation_default(event):
    """休暇デフォルト設定を保存"""
    try:
        data = json.loads(event['body'])
        
        item = {
            'PK': 'SETTINGS',
            'SK': 'VACATION_DEFAULT',
            'default_vacation_days': int(data.get('default_vacation_days', 20)),
            'annual_vacation_days': int(data.get('annual_vacation_days', 0)),
            'monthly_vacation_limit': int(data.get('monthly_vacation_limit', 0)),
            'paid_monthly_limit': int(data.get('paid_monthly_limit', 0)),
            'custom_vacation_types': data.get('custom_vacation_types', [])
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Vacation default settings saved'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }