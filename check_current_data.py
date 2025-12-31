#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現在の作業種別データを確認
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

def check_current_data():
    """現在のデータを詳細確認"""
    print("=== 現在のデータ確認 ===")
    
    # 作業種別データを取得
    try:
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'TASK#'}
        )
        tasks = response.get('Items', [])
        
        print(f"作業種別数: {len(tasks)}")
        print("\n詳細:")
        for task in tasks:
            print(f"PK: {task['PK']}")
            print(f"SK: {task['SK']}")
            print(f"task_type: {task.get('task_type', 'なし')}")
            print(f"name: {task.get('name', 'なし')}")
            print("---")
            
    except Exception as e:
        print(f"エラー: {e}")
    
    # 従業員のスキルも確認
    try:
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'EMP#'}
        )
        employees = response.get('Items', [])
        
        print(f"\n従業員数: {len(employees)}")
        print("\n従業員のスキル:")
        for emp in employees:
            skills = emp.get('skills', [])
            print(f"{emp.get('name', emp['PK'])}: {skills}")
            
    except Exception as e:
        print(f"従業員データエラー: {e}")

if __name__ == '__main__':
    check_current_data()