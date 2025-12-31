#!/usr/bin/env python3
"""
DynamoDB全体の#文字を_に置換するスクリプト
"""

import boto3
import json
from decimal import Decimal

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')

def scan_and_fix_all_data():
    """全データの#を_に置換"""
    try:
        # 全データをスキャン
        response = table.scan()
        items = response.get('Items', [])
        
        # ページネーション対応
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        print(f"Found {len(items)} total items")
        
        updated_count = 0
        
        for item in items:
            updates_needed = {}
            
            # 全ての属性をチェック
            for key, value in item.items():
                if key in ['PK', 'SK']:  # キー属性はスキップ
                    continue
                    
                if isinstance(value, str) and '#' in value:
                    updates_needed[key] = value.replace('#', '_')
            
            # 更新が必要な場合のみ実行
            if updates_needed:
                print(f"Updating item PK={item['PK']}, SK={item['SK']}")
                for key, new_value in updates_needed.items():
                    print(f"  {key}: {item[key]} -> {new_value}")
                
                # UpdateExpressionを構築
                update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in updates_needed.keys()])
                expression_values = {f":{k}": v for k, v in updates_needed.items()}
                
                table.update_item(
                    Key={'PK': item['PK'], 'SK': item['SK']},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )
                
                updated_count += 1
        
        print(f"Updated {updated_count} items successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting global # to _ replacement...")
    scan_and_fix_all_data()
    print("Fix completed!")