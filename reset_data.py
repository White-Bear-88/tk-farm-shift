import boto3
import json
from datetime import datetime

def reset_data(table_name):
    """既存データを削除して新しい連番IDでデータを再作成"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    print("既存データを削除中...")
    
    # 既存の作業種別とシフトデータを削除
    scan_response = table.scan()
    items_to_delete = []
    
    for item in scan_response['Items']:
        pk = item['PK']
        sk = item['SK']
        
        # 作業種別、シフト、要件データを削除対象に
        if (pk.startswith('TASK#') or 
            pk.startswith('SHIFT#') or 
            pk.startswith('REQ#')):
            items_to_delete.append({'PK': pk, 'SK': sk})
    
    # バッチ削除
    if items_to_delete:
        with table.batch_writer() as batch:
            for item in items_to_delete:
                batch.delete_item(Key=item)
        print(f"削除したアイテム数: {len(items_to_delete)}")
    
    print("新しいデータを作成中...")
    
    # 従業員データ（既存のまま）
    employees = [
        {
            'PK': 'EMP#001',
            'SK': 'PROFILE',
            'employee_id': '001',
            'name': '田中太郎',
            'skills': ['1', '2', '3'],  # 連番IDに変更
            'max_hours_per_day': 8,
            'phone': '090-1234-5678',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#002',
            'SK': 'PROFILE',
            'employee_id': '002',
            'name': '佐藤花子',
            'skills': ['1', '4', '3'],  # 連番IDに変更
            'max_hours_per_day': 6,
            'phone': '090-2345-6789',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#003',
            'SK': 'PROFILE',
            'employee_id': '003',
            'name': '鈴木一郎',
            'skills': ['2', '3', '4'],  # 連番IDに変更
            'max_hours_per_day': 8,
            'phone': '090-3456-7890',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#004',
            'SK': 'PROFILE',
            'employee_id': '004',
            'name': '山田美咲',
            'skills': ['1', '2', '4'],
            'max_hours_per_day': 7,
            'phone': '090-4567-8901',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#005',
            'SK': 'PROFILE',
            'employee_id': '005',
            'name': '高橋健太',
            'skills': ['1', '3', '4'],
            'max_hours_per_day': 8,
            'phone': '090-5678-9012',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#006',
            'SK': 'PROFILE',
            'employee_id': '006',
            'name': '伊藤由美',
            'skills': ['2', '3'],
            'max_hours_per_day': 6,
            'phone': '090-6789-0123',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#007',
            'SK': 'PROFILE',
            'employee_id': '007',
            'name': '渡辺大輔',
            'skills': ['1', '2', '3', '4'],
            'max_hours_per_day': 8,
            'phone': '090-7890-1234',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#008',
            'SK': 'PROFILE',
            'employee_id': '008',
            'name': '中村あかり',
            'skills': ['1', '4'],
            'max_hours_per_day': 5,
            'phone': '090-8901-2345',
            'created_at': datetime.now().isoformat()
        },
        {
            'PK': 'EMP#009',
            'SK': 'PROFILE',
            'employee_id': '009',
            'name': '小林正樹',
            'skills': ['2', '3', '4'],
            'max_hours_per_day': 8,
            'phone': '090-9012-3456',
            'created_at': datetime.now().isoformat()
        }
    ]
    
    # 作業種別データ（連番IDに変更）
    tasks = [
        {
            'PK': 'TASK#1',
            'SK': 'CONFIG',
            'name': '搾乳',
            'description': '牛の搾乳作業',
            'estimated_duration': 120,
            'required_skills': ['1'],
            'priority': 'high',
            'frequency': 'twice_daily',
            'recommended_start_time': '05:00',
            'recommended_end_time': '07:00',
            'morning_start_time': '05:00',
            'morning_end_time': '07:00',
            'afternoon_start_time': '16:00',
            'afternoon_end_time': '18:00',
            'required_people': 2
        },
        {
            'PK': 'TASK#2',
            'SK': 'CONFIG',
            'name': '給餌',
            'description': '牛への餌やり',
            'estimated_duration': 90,
            'required_skills': ['2'],
            'priority': 'high',
            'frequency': 'twice_daily',
            'recommended_start_time': '08:00',
            'recommended_end_time': '09:30',
            'morning_start_time': '08:00',
            'morning_end_time': '09:30',
            'afternoon_start_time': '15:00',
            'afternoon_end_time': '16:30',
            'required_people': 1
        },
        {
            'PK': 'TASK#3',
            'SK': 'CONFIG',
            'name': '清掃',
            'description': '牛舎の清掃作業',
            'estimated_duration': 60,
            'required_skills': ['3'],
            'priority': 'medium',
            'frequency': 'daily',
            'recommended_start_time': '10:00',
            'recommended_end_time': '11:00',
            'morning_start_time': '10:00',
            'morning_end_time': '11:00',
            'afternoon_start_time': '14:00',
            'afternoon_end_time': '15:00',
            'required_people': 1
        },
        {
            'PK': 'TASK#4',
            'SK': 'CONFIG',
            'name': '見回り',
            'description': '牛の健康チェック',
            'estimated_duration': 30,
            'required_skills': ['4'],
            'priority': 'medium',
            'frequency': 'twice_daily',
            'recommended_start_time': '12:00',
            'recommended_end_time': '12:30',
            'morning_start_time': '12:00',
            'morning_end_time': '12:30',
            'afternoon_start_time': '17:00',
            'afternoon_end_time': '17:30',
            'required_people': 1
        }
    ]
    
    # データを一括挿入
    with table.batch_writer() as batch:
        for employee in employees:
            batch.put_item(Item=employee)
        
        for task in tasks:
            batch.put_item(Item=task)
    
    print(f"新しいデータを {table_name} に挿入しました")
    print(f"従業員: {len(employees)}人")
    print(f"作業種別: {len(tasks)}種類")

if __name__ == '__main__':
    reset_data('dairy-shifts-dev')