#!/usr/bin/env python3
"""
従業員データにかな氏名を追加するスクリプト
"""

import boto3
import json

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')

# 従業員のかな氏名マッピング
employee_kana_names = {
    '001': 'たなか たろう',
    '002': 'あべ まりこ',
    '003': 'つかさ えいじ',
    '006': 'いとう まさこ',
    '007': 'わたなべ けんた',
    '008': 'なかむら さくら',
    '009': 'こばやし だいすけ',
    '010': 'かとう みほ',
    '011': 'うちやま たけし'
}

def add_kana_names():
    """従業員データにかな氏名を追加"""
    try:
        # 従業員データを取得
        response = table.scan(
            FilterExpression='begins_with(PK, :pk_prefix)',
            ExpressionAttributeValues={
                ':pk_prefix': 'EMPLOYEE'
            }
        )
        
        items = response.get('Items', [])
        print(f"Found {len(items)} employee items")
        
        updated_count = 0
        
        for item in items:
            employee_id = item.get('SK', '')
            
            if employee_id in employee_kana_names:
                kana_name = employee_kana_names[employee_id]
                
                print(f"Adding kana name for {employee_id}: {item.get('name', '')} -> {kana_name}")
                
                # アイテムを更新
                table.update_item(
                    Key={
                        'PK': item['PK'],
                        'SK': item['SK']
                    },
                    UpdateExpression='SET kana_name = :kana_name',
                    ExpressionAttributeValues={
                        ':kana_name': kana_name
                    }
                )
                
                updated_count += 1
        
        print(f"Updated {updated_count} items successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting kana name addition...")
    add_kana_names()
    print("Addition completed!")