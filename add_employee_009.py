#!/usr/bin/env python3
"""
従業員009のデータを追加するスクリプト
"""

import boto3
import json

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')

def add_employee_009():
    """従業員009のデータを追加"""
    try:
        # 従業員009のデータ
        employee_data = {
            'PK': 'EMPLOYEE',
            'SK': '009',
            'name': '小林大輔',
            'kana_name': 'こばやし だいすけ',
            'phone': '090-9012-3456',
            'email': 'kobayashi@farm.com',
            'skills': ['milking'],
            'vacation_days': 20
        }
        
        print(f"Adding employee 009: {employee_data['name']} ({employee_data['kana_name']})")
        
        # アイテムを追加
        table.put_item(Item=employee_data)
        
        print("Employee 009 added successfully")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Adding employee 009...")
    add_employee_009()
    print("Addition completed!")