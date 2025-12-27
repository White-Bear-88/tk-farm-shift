import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'GET' and path == '/employees':
            return get_all_employees()
        elif http_method == 'POST' and path == '/employees':
            return create_employee(event)
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
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
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
                'phone': item.get('phone', ''),
                'email': item.get('email', ''),
                'skills': item.get('skills', []),
                'vacation_days': int(item.get('vacation_days', 20))
            }
            employees.append(employee)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(employees)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def create_employee(event):
    try:
        data = json.loads(event['body'])
        
        item = {
            'PK': 'EMPLOYEE',
            'SK': data['employee_id'],
            'name': data['name'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'skills': data.get('skills', []),
            'vacation_days': data.get('vacation_days', 20)
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '従業員を作成しました', 'employee_id': data['employee_id']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
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
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': '従業員が見つかりません'})
            }
        
        item = response['Item']
        employee = {
            'employee_id': item['SK'],
            'name': item.get('name', ''),
            'phone': item.get('phone', ''),
            'email': item.get('email', ''),
            'skills': item.get('skills', []),
            'vacation_days': int(item.get('vacation_days', 20))
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(employee)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def update_employee(employee_id, event):
    try:
        data = json.loads(event['body'])
        
        item = {
            'PK': 'EMPLOYEE',
            'SK': employee_id,
            'name': data['name'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'skills': data.get('skills', []),
            'vacation_days': data.get('vacation_days', 20)
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '従業員を更新しました'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def delete_employee(employee_id):
    try:
        table.delete_item(
            Key={'PK': 'EMPLOYEE', 'SK': employee_id}
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': '従業員を削除しました'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }