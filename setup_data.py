import boto3
import json
from datetime import datetime

def setup_initial_data(table_name):
    """初期データをセットアップ"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    # 従業員データ
    employees = [
        {
            'PK': 'EMP#001',
            'SK': 'PROFILE',
            'name': '田中太郎',
            'skills': ['milking', 'feeding', 'cleaning'],
            'max_hours_per_day': 8,
            'phone': '090-1234-5678',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#002',
            'SK': 'PROFILE',
            'name': '佐藤花子',
            'skills': ['milking', 'patrol', 'cleaning'],
            'max_hours_per_day': 6,
            'phone': '090-2345-6789',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#003',
            'SK': 'PROFILE',
            'name': '鈴木一郎',
            'skills': ['feeding', 'cleaning', 'patrol'],
            'max_hours_per_day': 8,
            'phone': '090-3456-7890',
            'created_at': datetime.now().isoformat()
        }
    ]
    
    # 作業種別データ
    tasks = [
        {
            'PK': 'TASK#milking',
            'SK': 'CONFIG',
            'name': '搾乳',
            'description': '牛の搾乳作業',
            'estimated_duration': 120,
            'required_skills': ['milking'],
            'priority': 'high',
            'frequency': 'twice_daily'
        },
        {
            'PK': 'TASK#feeding',
            'SK': 'CONFIG',
            'name': '給餌',
            'description': '牛への餌やり',
            'estimated_duration': 90,
            'required_skills': ['feeding'],
            'priority': 'high',
            'frequency': 'twice_daily'
        },
        {
            'PK': 'TASK#cleaning',
            'SK': 'CONFIG',
            'name': '清掃',
            'description': '牛舎の清掃作業',
            'estimated_duration': 60,
            'required_skills': ['cleaning'],
            'priority': 'medium',
            'frequency': 'daily'
        },
        {
            'PK': 'TASK#patrol',
            'SK': 'CONFIG',
            'name': '見回り',
            'description': '牛の健康チェック',
            'estimated_duration': 30,
            'required_skills': ['patrol'],
            'priority': 'medium',
            'frequency': 'twice_daily'
        }
    ]
    
    # データを一括挿入
    with table.batch_writer() as batch:
        for employee in employees:
            batch.put_item(Item=employee)
        
        for task in tasks:
            batch.put_item(Item=task)
    
    print(f"初期データを {table_name} に挿入しました")
    print(f"従業員: {len(employees)}人")
    print(f"作業種別: {len(tasks)}種類")

if __name__ == '__main__':
    # 使用例
    setup_initial_data('dairy-shifts-dev')