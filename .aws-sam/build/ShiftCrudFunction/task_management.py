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
        method = event['httpMethod']
        
        if method == 'GET':
            return get_tasks()
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_tasks():
    """作業種別一覧を取得"""
    response = table.scan(
        FilterExpression='begins_with(PK, :pk)',
        ExpressionAttributeValues={':pk': 'TASK#'}
    )
    
    tasks = []
    for item in response['Items']:
        if item['SK'] == 'CONFIG':
            tasks.append({
                'id': item['PK'].split('#')[1],
                'name': item['name'],
                'description': item.get('description', ''),
                'estimated_duration': item.get('estimated_duration', 60),
                'required_skills': item.get('required_skills', []),
                'priority': item.get('priority', 'medium'),
                'frequency': item.get('frequency', 'daily')
            })
    
    # 優先度順にソート
    priority_order = {'high': 1, 'medium': 2, 'low': 3}
    tasks.sort(key=lambda x: priority_order.get(x['priority'], 2))
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(tasks)
    }