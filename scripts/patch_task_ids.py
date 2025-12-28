"""Patch script to convert existing TASK items' SK to a generated task_id based on task name.
Usage:
  python scripts/patch_task_ids.py [--apply]
Default is dry-run; use --apply to perform moves.
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

def to_task_id(name):
    mapping = {
        '搾乳': 'milking',
        '給餌': 'feeding',
        '清掃': 'cleaning',
        '見回り': 'patrol',
        '点検': 'maintenance',
        '健康チェック': 'health_check'
    }
    if not name:
        return ''
    if name in mapping:
        return mapping[name]
    try:
        import unicodedata
        norm = unicodedata.normalize('NFKD', name)
        ascii_only = ''.join([c for c in norm if ord(c) < 128])
        slug = ''.join([c if c.isalnum() else '_' for c in ascii_only]).strip('_').lower()
        if slug:
            return slug
    except Exception:
        pass
    return ''.join([c if c.isalnum() else '_' for c in name]).strip('_').lower()


def scan_tasks():
    res = table.query(KeyConditionExpression='PK = :pk', ExpressionAttributeValues={':pk': 'TASK'})
    items = res.get('Items', [])
    return items


def main(apply=False):
    items = scan_tasks()
    changes = []
    for it in items:
        old_sk = it['SK']
        name = it.get('name') or ''
        new_sk = to_task_id(name)
        if not new_sk:
            print(f"Skipping {old_sk}: cannot generate new id from name='{name}'")
            continue
        if new_sk == old_sk:
            continue
        # check if new exists
        existing = table.get_item(Key={'PK': 'TASK', 'SK': new_sk})
        if 'Item' in existing:
            print(f"Conflict: target SK {new_sk} already exists; skipping {old_sk}")
            continue
        changes.append((old_sk, new_sk, it))

    if not changes:
        print('No changes necessary')
        return

    print('Planned changes:')
    for old_sk, new_sk, it in changes:
        print(f"  {old_sk} -> {new_sk} (name='{it.get('name', '')}')")

    if not apply:
        print('\nDry run complete. Re-run with --apply to perform changes.')
        return

    print('\nApplying changes...')
    for old_sk, new_sk, it in changes:
        new_item = it.copy()
        new_item['SK'] = new_sk
        table.put_item(Item=new_item)
        table.delete_item(Key={'PK': 'TASK', 'SK': old_sk})
        print(f"Applied: {old_sk} -> {new_sk}")

    print('Done')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    main(apply=args.apply)