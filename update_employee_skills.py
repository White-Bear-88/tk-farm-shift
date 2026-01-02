import boto3
import json
from decimal import Decimal

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dairy-shifts-dev')  # 単一テーブル設計

# スキル変換マッピング
skill_mapping = {
    'milking': '1',
    'feeding': '2',
    'cleaning': '3',
    'patrol': '4'
}

def convert_skills(old_skills):
    """古い形式のスキルを新しい形式に変換"""
    if not old_skills:
        return []
    
    new_skills = []
    for skill in old_skills:
        # 既に数字形式の場合はそのまま
        if skill in ['1', '2', '3', '4']:
            new_skills.append(skill)
        # 文字列形式の場合は変換
        elif skill in skill_mapping:
            new_skills.append(skill_mapping[skill])
        else:
            print(f"警告: 不明なスキル '{skill}' が見つかりました")
    
    return new_skills

def update_all_employee_skills():
    """全従業員のスキルを新形式に更新"""
    try:
        # 全従業員を取得（PK='EMPLOYEE'）
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': 'EMPLOYEE'}
        )
        employees = response['Items']
        
        print(f"取得した従業員数: {len(employees)}")
        if employees:
            print(f"サンプルデータ: {json.dumps(employees[0], indent=2, default=str)}")
            print()
        
        updated_count = 0
        unchanged_count = 0
        
        for employee in employees:
            # SKが従業員ID
            employee_id = employee.get('SK', '')
            employee_name = employee.get('name', 'N/A')
            old_skills = employee.get('skills', [])
            
            if not old_skills:
                print(f"従業員 {employee_id} ({employee_name}): スキルなし")
                unchanged_count += 1
                continue
            
            # スキルを変換
            new_skills = convert_skills(old_skills)
            
            # 変更があった場合のみ更新
            if old_skills != new_skills:
                print(f"従業員 {employee_id} ({employee_name})")
                print(f"  変更前: {old_skills}")
                print(f"  変更後: {new_skills}")
                
                # DynamoDBを更新（単一テーブル設計: PK='EMPLOYEE', SK=従業員ID）
                table.update_item(
                    Key={
                        'PK': 'EMPLOYEE',
                        'SK': employee_id
                    },
                    UpdateExpression='SET skills = :skills',
                    ExpressionAttributeValues={':skills': new_skills}
                )
                updated_count += 1
            else:
                print(f"従業員 {employee_id} ({employee_name}): 既に新形式")
                unchanged_count += 1
        
        print(f"\n完了: {updated_count}件更新, {unchanged_count}件変更なし")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    print("従業員スキルデータを新形式に変換します...")
    print("変換マッピング:")
    for old, new in skill_mapping.items():
        print(f"  {old} -> {new}")
    print()
    
    confirmation = input("実行しますか？ (yes/no): ")
    if confirmation.lower() == 'yes':
        update_all_employee_skills()
    else:
        print("キャンセルしました")
