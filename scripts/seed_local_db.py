import os
import time
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get('TABLE_NAME', 'dairy-shifts-local')
ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')

print(f"Seeding local DynamoDB at {ENDPOINT}, table {TABLE_NAME}")

dyn = boto3.resource('dynamodb', endpoint_url=ENDPOINT, region_name='us-east-1')
client = boto3.client('dynamodb', endpoint_url=ENDPOINT, region_name='us-east-1')

# Create table if not exists
try:
    existing = client.describe_table(TableName=TABLE_NAME)
    print('Table exists')
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print('Creating table...')
        client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                { 'AttributeName': 'PK', 'KeyType': 'HASH' },
                { 'AttributeName': 'SK', 'KeyType': 'RANGE' }
            ],
            AttributeDefinitions=[
                { 'AttributeName': 'PK', 'AttributeType': 'S' },
                { 'AttributeName': 'SK', 'AttributeType': 'S' }
            ],
            ProvisionedThroughput={ 'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5 }
        )
        # wait
        print('Waiting for table to be active...')
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print('Table created')
    else:
        raise

table = dyn.Table(TABLE_NAME)

# Insert some sample employees, tasks, and a few shifts
employees = [
    {'PK':'EMP#E1','SK':'PROFILE','name':'田中太郎','skills':['milking','feeding'],'vacation_days':20},
    {'PK':'EMP#E2','SK':'PROFILE','name':'佐藤花子','skills':['feeding','cleaning'],'vacation_days':20},
]

tasks = [
    {'PK':'TASK#milking','SK':'CONFIG','name':'搾乳'},
    {'PK':'TASK#feeding','SK':'CONFIG','name':'給餌'},
]

shifts = [
    {'PK':'SHIFT#2025-12-01','SK':'EMP#E1#milking','GSI1PK':'E1','GSI1SK':'2025-12-01','GSI2PK':'milking','GSI2SK':'2025-12-01#E1','start_time':'05:00','end_time':'07:00','status':'scheduled'},
    {'PK':'SHIFT#2025-12-01','SK':'EMP#E2#feeding','GSI1PK':'E2','GSI1SK':'2025-12-01','GSI2PK':'feeding','GSI2SK':'2025-12-01#E2','start_time':'08:00','end_time':'09:00','status':'scheduled'},
]

for item in employees + tasks + shifts:
    print('Putting', item.get('PK'), item.get('SK'))
    table.put_item(Item=item)

print('Seeding complete')
