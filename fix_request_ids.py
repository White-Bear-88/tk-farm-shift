#!/usr/bin/env python3
"""
休暇申請のrequest_idから#文字を_に置換するスクリプト
"""

import boto3
import json
from decimal import Decimal

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')

def scan_and_fix_vacation_requests():
    """休暇申請データの#を_に置換"""
    try:
        # 全ての休暇申請データを取得
        response = table.scan(
            FilterExpression='begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={':sk_prefix': 'VACATION#'}
        )
        
        items = response.get('Items', [])
        print(f"Found {len(items)} vacation request items")
        
        updated_count = 0
        
        for item in items:
            old_request_id = item.get('request_id', '')
            
            if '#' in old_request_id:
                # #を_に置換
                new_request_id = old_request_id.replace('#', '_')
                
                print(f"Updating: {old_request_id} -> {new_request_id}")
                
                # アイテムを更新
                table.update_item(
                    Key={
                        'PK': item['PK'],
                        'SK': item['SK']
                    },
                    UpdateExpression='SET request_id = :new_request_id',
                    ExpressionAttributeValues={
                        ':new_request_id': new_request_id
                    }
                )
                
                updated_count += 1
        
        print(f"Updated {updated_count} items successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting vacation request ID fix...")
    scan_and_fix_vacation_requests()
    print("Fix completed!")