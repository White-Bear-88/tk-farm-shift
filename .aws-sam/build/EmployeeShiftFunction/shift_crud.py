import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        method = event['httpMethod']
        path = event['path']
        
        if method == 'GET' and '/shifts/' in path:
            return get_shifts_by_date(event)
        elif method == 'POST' and path == '/shifts':
            return create_shift(event)
        elif method == 'PUT' and '/shifts/' in path:
            return update_shift(event)
        elif method == 'DELETE' and '/shifts/' in path:
            return delete_shift(event)
        
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

def get_shifts_by_date(event):
    date = event['pathParameters']['date']
    
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f'SHIFT#{date}'}
    )
    
    shifts = []
    for item in response['Items']:
        shifts.append({
            'employee_id': item['SK'].split('#')[1],
            'task_type': item['SK'].split('#')[2],
            'start_time': item['start_time'],
            'end_time': item['end_time'],
            'status': item.get('status', 'scheduled')
        })
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(shifts, default=str)
    }

def create_shift(event):
    data = json.loads(event['body'])
    
    item = {
        'PK': f"SHIFT#{data['date']}",
        'SK': f"EMP#{data['employee_id']}#{data['task_type']}",
        'GSI1PK': data['employee_id'],
        'GSI1SK': data['date'],
        'GSI2PK': data['task_type'],
        'GSI2SK': f"{data['date']}#{data['employee_id']}",
        'start_time': data['start_time'],
        'end_time': data['end_time'],
        'status': 'scheduled',
        'created_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Shift created successfully'})
    }

def update_shift(event):
    shift_id = event['pathParameters']['id']
    data = json.loads(event['body'])
    
    # Parse shift_id to get PK and SK
    parts = shift_id.split('#')
    pk = f"SHIFT#{parts[1]}"
    sk = f"EMP#{parts[2]}#{parts[3]}"
    
    update_expression = "SET "
    expression_values = {}
    
    for key, value in data.items():
        update_expression += f"{key} = :{key}, "
        expression_values[f":{key}"] = value
    
    update_expression = update_expression.rstrip(', ')
    
    table.update_item(
        Key={'PK': pk, 'SK': sk},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Shift updated successfully'})
    }

def delete_shift(event):
    shift_id = event['pathParameters']['id']
    
    # Parse shift_id to get PK and SK
    parts = shift_id.split('#')
    pk = f"SHIFT#{parts[1]}"
    sk = f"EMP#{parts[2]}#{parts[3]}"
    
    table.delete_item(Key={'PK': pk, 'SK': sk})
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Shift deleted successfully'})
    }