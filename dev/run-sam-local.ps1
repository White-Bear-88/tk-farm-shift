# Start DynamoDB Local, seed data, then run SAM local API
Write-Output 'Starting DynamoDB Local (docker-compose up -d)'
docker-compose up -d
Write-Output 'Waiting 3s for DynamoDB Local to be ready...'
Start-Sleep -Seconds 3

# Set env vars for seeding
$env:DYNAMODB_ENDPOINT = 'http://host.docker.internal:8000'
$env:TABLE_NAME = 'dairy-shifts-local'

Write-Output 'Seeding local DynamoDB...'
python .\scripts\seed_local_db.py

Write-Output 'Starting SAM local start-api (press Ctrl+C to stop)'
# Make sure you have AWS SAM CLI installed and built
sam local start-api --env-vars dev/env.json
