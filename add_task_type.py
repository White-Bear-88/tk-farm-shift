#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作業種別データにtask_typeフィールドを追加
"""

import boto3
import json
from decimal import Decimal

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')

def update_task_type_fields():
    """作業種別データにtask_typeフィールドを追加"""
    print("=== task_typeフィールドを追加 ===")
    
    try:
        # 作業種別データを取得
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'TASK#'}
        )
        tasks = response.get('Items', [])
        
        print(f"更新対象の作業種別数: {len(tasks)}")
        
        for task in tasks:
            # PKからIDを抽出 (TASK#1 → 1)
            task_id = task['PK'].replace('TASK#', '')
            
            # task_typeフィールドを追加
            try:
                table.update_item(
                    Key={
                        'PK': task['PK'],
                        'SK': task['SK']
                    },
                    UpdateExpression='SET task_type = :task_type',
                    ExpressionAttributeValues={
                        ':task_type': task_id
                    }
                )
                print(f"更新: {task.get('name', task['PK'])} → task_type: {task_id}")
                
            except Exception as e:
                print(f"更新エラー {task['PK']}: {e}")
                
    except Exception as e:
        print(f"データ取得エラー: {e}")

def verify_updates():
    """更新結果を確認"""
    print("\n=== 更新結果確認 ===")
    
    try:
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'TASK#'}
        )
        tasks = response.get('Items', [])
        
        print("更新後のデータ:")
        for task in sorted(tasks, key=lambda x: x['PK']):
            print(f"ID: {task.get('task_type', 'なし')} - {task.get('name', 'なし')}")
            
    except Exception as e:
        print(f"確認エラー: {e}")

def main():
    print("作業種別データにtask_typeフィールドを追加します。")
    
    # 確認
    confirm = input("実行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました。")
        return
    
    # task_typeフィールドを追加
    update_task_type_fields()
    
    # 結果確認
    verify_updates()
    
    print("\n完了しました。")

if __name__ == '__main__':
    main()