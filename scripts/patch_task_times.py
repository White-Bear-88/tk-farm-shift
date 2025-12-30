"""Patch script to convert old task data to new format with separate morning/afternoon times.
Old format: recommended_start_time, recommended_end_time
New format: morning_start_time, morning_end_time, afternoon_start_time, afternoon_end_time

Usage:
  python scripts/patch_task_times.py [--apply]
Default is dry-run; use --apply to perform updates.
"""
import boto3
import os
import json
import argparse
import sys

TABLE = os.environ.get('TABLE_NAME')
if not TABLE:
    print('Please set TABLE_NAME env var to your DynamoDB table')
    sys.exit(1)

_dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT')
if _dynamodb_endpoint:
    dynamodb = boto3.resource('dynamodb', endpoint_url=_dynamodb_endpoint)
else:
    dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table(TABLE)


def scan_tasks():
    """Scan all TASK items from DynamoDB."""
    response = table.scan()
    items = response.get('Items', [])
    
    # Continue scanning if there are more pages
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    # Filter only TASK items
    tasks = [item for item in items if item.get('PK') == 'TASK']
    return tasks


def needs_patch(task):
    """Check if task needs patching (has old format but not new format)."""
    has_old_format = 'recommended_start_time' in task or 'recommended_end_time' in task
    has_new_format = 'morning_start_time' in task or 'afternoon_start_time' in task
    
    # Needs patch if it has old format but not new format
    return has_old_format and not has_new_format


def patch_task(task, apply=False):
    """Patch a task to add morning/afternoon times based on recommended times."""
    task_type = task.get('SK')
    name = task.get('name', 'Unknown')
    
    # Get old times
    recommended_start = task.get('recommended_start_time', '')
    recommended_end = task.get('recommended_end_time', '')
    
    # Create update with new fields
    update_data = {
        'PK': task['PK'],
        'SK': task['SK'],
        'morning_start_time': recommended_start,
        'morning_end_time': recommended_end,
        'afternoon_start_time': '',  # Empty by default
        'afternoon_end_time': '',    # Empty by default
    }
    
    print(f"Task: {name} ({task_type})")
    print(f"  Old: recommended_start_time={recommended_start}, recommended_end_time={recommended_end}")
    print(f"  New: morning={recommended_start}~{recommended_end}, afternoon=(未設定)")
    
    if apply:
        try:
            # Update the item with new fields
            update_expression = "SET morning_start_time = :morning_start, morning_end_time = :morning_end, afternoon_start_time = :afternoon_start, afternoon_end_time = :afternoon_end"
            expression_attribute_values = {
                ':morning_start': recommended_start,
                ':morning_end': recommended_end,
                ':afternoon_start': '',
                ':afternoon_end': ''
            }
            
            table.update_item(
                Key={'PK': task['PK'], 'SK': task['SK']},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            print(f"  ✓ Updated")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    else:
        print(f"  (dry-run, not applied)")
    
    print()
    return True


def main():
    parser = argparse.ArgumentParser(description='Patch task times to new format')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Task Time Patch Script")
    print("=" * 60)
    print(f"Mode: {'APPLY CHANGES' if args.apply else 'DRY RUN (use --apply to update)'}")
    print()
    
    tasks = scan_tasks()
    print(f"Found {len(tasks)} total tasks")
    print()
    
    tasks_to_patch = [t for t in tasks if needs_patch(t)]
    
    if not tasks_to_patch:
        print("No tasks need patching. All tasks already have new format or have no time data.")
        return
    
    print(f"Found {len(tasks_to_patch)} tasks that need patching:")
    print("-" * 60)
    
    success_count = 0
    for task in tasks_to_patch:
        if patch_task(task, apply=args.apply):
            success_count += 1
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  Tasks needing patch: {len(tasks_to_patch)}")
    print(f"  Successfully processed: {success_count}")
    
    if not args.apply:
        print()
        print("This was a DRY RUN. Use --apply to actually update the database.")


if __name__ == '__main__':
    main()
