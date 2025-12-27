import json
import boto3
import os

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
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def save_global_default_requirements(event):
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
                    'confirmation_day': response['Item'].get('confirmation_day', 25),
                    'confirmation_time': response['Item'].get('confirmation_time', '17:00')
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'confirmation_day': 25, 'confirmation_time': '17:00'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def save_confirmation_settings(event):
    data = json.loads(event['body'])
    
    item = {
        'PK': 'SETTINGS',
        'SK': 'CONFIRMATION',
        'confirmation_day': data['confirmation_day'],
        'confirmation_time': data['confirmation_time']
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Confirmation settings saved'})
    }

def get_vacation_default():
    try:
        response = table.get_item(
            Key={'PK': 'SETTINGS', 'SK': 'VACATION_DEFAULT'}
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'default_vacation_days': response['Item'].get('default_vacation_days', 20)
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'default_vacation_days': 20})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def save_vacation_default(event):
    data = json.loads(event['body'])
    
    item = {
        'PK': 'SETTINGS',
        'SK': 'VACATION_DEFAULT',
        'default_vacation_days': data['default_vacation_days']
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Vacation default settings saved'})
    }