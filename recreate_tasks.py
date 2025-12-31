#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作業種別データの再作成スクリプト
文字列IDから連番IDに変更
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

def get_current_tasks():
    """現在の作業種別データを取得"""
    try:
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'TASK#'}
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"作業種別取得エラー: {e}")
        return []

def delete_old_tasks(old_tasks):
    """古い作業種別データを削除"""
    print("古い作業種別データを削除中...")
    for task in old_tasks:
        try:
            table.delete_item(
                Key={
                    'PK': task['PK'],
                    'SK': task['SK']
                }
            )
            print(f"削除: {task['PK']}")
        except Exception as e:
            print(f"削除エラー {task['PK']}: {e}")

def create_new_tasks():
    """新しい連番IDで作業種別を作成"""
    new_tasks = [
        {
            'task_id': '1',
            'name': '搾乳',
            'description': '牛の搾乳作業',
            'duration_minutes': 120,
            'required_people': 2,
            'priority': 'high',
            'recommended_start_time': '05:00',
            'recommended_end_time': '07:00',
            'morning_start_time': '05:00',
            'morning_end_time': '07:00',
            'afternoon_start_time': '17:00',
            'afternoon_end_time': '19:00'
        },
        {
            'task_id': '2',
            'name': '給餌',
            'description': '牛への餌やり作業',
            'duration_minutes': 60,
            'required_people': 1,
            'priority': 'high',
            'recommended_start_time': '08:00',
            'recommended_end_time': '09:00',
            'morning_start_time': '08:00',
            'morning_end_time': '09:00',
            'afternoon_start_time': '15:00',
            'afternoon_end_time': '16:00'
        },
        {
            'task_id': '3',
            'name': '清掃',
            'description': '牛舎の清掃作業',
            'duration_minutes': 90,
            'required_people': 1,
            'priority': 'medium',
            'recommended_start_time': '10:00',
            'recommended_end_time': '11:30',
            'morning_start_time': '10:00',
            'morning_end_time': '11:30',
            'afternoon_start_time': '14:00',
            'afternoon_end_time': '15:30'
        },
        {
            'task_id': '4',
            'name': '見回り',
            'description': '牛の健康状態確認',
            'duration_minutes': 30,
            'required_people': 1,
            'priority': 'medium',
            'recommended_start_time': '14:00',
            'recommended_end_time': '14:30',
            'morning_start_time': '11:30',
            'morning_end_time': '12:00',
            'afternoon_start_time': '16:00',
            'afternoon_end_time': '16:30'
        }
    ]
    
    print("新しい作業種別データを作成中...")
    for task in new_tasks:
        try:
            item = {
                'PK': f"TASK#{task['task_id']}",
                'SK': 'CONFIG',
                'task_type': task['task_id'],  # APIとの互換性のため
                'name': task['name'],
                'description': task['description'],
                'duration_minutes': task['duration_minutes'],
                'required_people': task['required_people'],
                'priority': task['priority'],
                'recommended_start_time': task['recommended_start_time'],
                'recommended_end_time': task['recommended_end_time'],
                'morning_start_time': task['morning_start_time'],
                'morning_end_time': task['morning_end_time'],
                'afternoon_start_time': task['afternoon_start_time'],
                'afternoon_end_time': task['afternoon_end_time'],
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
            
            table.put_item(Item=item)
            print(f"作成: {task['name']} (ID: {task['task_id']})")
            
        except Exception as e:
            print(f"作成エラー {task['name']}: {e}")

def update_employee_skills():
    """従業員のスキルを新しいIDに更新"""
    print("従業員のスキルを更新中...")
    
    # 文字列ID → 連番IDのマッピング
    skill_mapping = {
        'milking': '1',
        'feeding': '2', 
        'cleaning': '3',
        'patrol': '4'
    }
    
    try:
        # 従業員データを取得
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={':pk': 'EMP#'}
        )
        employees = response.get('Items', [])
        
        for emp in employees:
            if 'skills' in emp and emp['skills']:
                # スキルを新しいIDに変換
                new_skills = []
                for skill in emp['skills']:
                    if skill in skill_mapping:
                        new_skills.append(skill_mapping[skill])
                    else:
                        new_skills.append(skill)  # 既に数字の場合はそのまま
                
                # 従業員データを更新
                table.update_item(
                    Key={
                        'PK': emp['PK'],
                        'SK': emp['SK']
                    },
                    UpdateExpression='SET skills = :skills',
                    ExpressionAttributeValues={
                        ':skills': new_skills
                    }
                )
                print(f"従業員 {emp.get('name', emp['PK'])} のスキルを更新: {emp['skills']} → {new_skills}")
                
    except Exception as e:
        print(f"従業員スキル更新エラー: {e}")

def main():
    print("=== 作業種別データ再作成スクリプト ===")
    
    # 現在のデータを確認
    current_tasks = get_current_tasks()
    print(f"現在の作業種別数: {len(current_tasks)}")
    
    if current_tasks:
        print("\n現在の作業種別:")
        for task in current_tasks:
            print(f"- {task.get('name', 'Unknown')} (ID: {task.get('task_type', task['PK'])})")
    
    # 確認
    confirm = input("\n古いデータを削除して新しい連番IDで作り直しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました。")
        return
    
    # 古いデータを削除
    if current_tasks:
        delete_old_tasks(current_tasks)
    
    # 新しいデータを作成
    create_new_tasks()
    
    # 従業員のスキルを更新
    update_employee_skills()
    
    print("\n=== 完了 ===")
    print("作業種別データを連番IDで再作成しました。")
    print("新しいID:")
    print("1: 搾乳")
    print("2: 給餌") 
    print("3: 清掃")
    print("4: 見回り")

if __name__ == '__main__':
    main()