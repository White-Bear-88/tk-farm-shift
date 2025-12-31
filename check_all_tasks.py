#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース内の全作業種別データを詳細確認
"""

import boto3
import json
from decimal import Decimal

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')

def decimal_default(obj):
    """JSON serialization for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def check_all_task_data():
    """全ての作業種別データを詳細確認"""
    print("=== 全作業種別データ詳細確認 ===")
    
    try:
        # 全てのTASK#で始まるデータを取得
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'TASK#'}
        )
        
        items = response.get('Items', [])
        print(f"見つかったTASK#データ数: {len(items)}")
        
        for item in items:
            print(f"\n--- データ詳細 ---")
            print(f"PK: {item['PK']}")
            print(f"SK: {item['SK']}")
            
            # 全フィールドを表示
            for key, value in item.items():
                if key not in ['PK', 'SK']:
                    print(f"{key}: {value}")
            
            print("-" * 30)
            
    except Exception as e:
        print(f"エラー: {e}")

def clean_old_task_data():
    """古い文字列IDの作業種別データを削除"""
    print("\n=== 古い文字列IDデータの削除 ===")
    
    # 削除対象の古いID
    old_ids = ['milking', 'feeding', 'cleaning', 'patrol']
    
    for old_id in old_ids:
        try:
            # 古いデータが存在するか確認
            response = table.get_item(
                Key={
                    'PK': f'TASK#{old_id}',
                    'SK': 'CONFIG'
                }
            )
            
            if 'Item' in response:
                print(f"古いデータ発見: TASK#{old_id}")
                print(f"データ内容: {response['Item']}")
                
                # 削除確認
                confirm = input(f"TASK#{old_id} を削除しますか？ (y/N): ")
                if confirm.lower() == 'y':
                    table.delete_item(
                        Key={
                            'PK': f'TASK#{old_id}',
                            'SK': 'CONFIG'
                        }
                    )
                    print(f"✓ 削除しました: TASK#{old_id}")
                else:
                    print(f"スキップ: TASK#{old_id}")
            else:
                print(f"古いデータなし: TASK#{old_id}")
                
        except Exception as e:
            print(f"エラー TASK#{old_id}: {e}")

if __name__ == '__main__':
    check_all_task_data()
    
    # 古いデータの削除を提案
    print("\n" + "="*50)
    clean_old_task_data()