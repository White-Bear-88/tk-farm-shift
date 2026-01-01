import boto3
import json
from datetime import datetime

# DynamoDB設定
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dairy-shifts-dev')

def create_admin_cognite_user():
    """CogniteIDユーザー usr7wyygjep を管理者として作成"""
    
    cognite_user_id = 'usr7wyygjep'
    
    try:
        # 既存チェック
        response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{cognite_user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' in response:
            # 既存ユーザーのロールを更新
            item = response['Item']
            item['role'] = 'admin'
            item['updated_at'] = datetime.now().isoformat()
            table.put_item(Item=item)
            print(f"OK 既存CogniteIDユーザー {cognite_user_id} のロールを管理者に変更しました。")
        else:
            # 新規作成
            item = {
                'PK': f'COGNITE_USER#{cognite_user_id}',
                'SK': 'PROFILE',
                'cognite_user_id': cognite_user_id,
                'name': 'システム管理者',
                'email': 'admin@example.com',
                'role': 'admin',
                'employee_id': '001',  # 従業員001と紐づけ
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            table.put_item(Item=item)
            print(f"OK 新規CogniteIDユーザー {cognite_user_id} を管理者として作成しました。")
        
        print(f"  - 名前: {item.get('name', 'N/A')}")
        print(f"  - メール: {item.get('email', 'N/A')}")
        print(f"  - 紐づけ従業員ID: {item.get('employee_id', 'N/A')}")
        print(f"  - ロール: {item['role']}")
        print(f"  - ステータス: {'有効' if item.get('is_active', True) else '無効'}")
        
        return True
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("CogniteIDユーザーの作成/更新を開始...")
    success = create_admin_cognite_user()
    
    if success:
        print("\nOK 処理が完了しました。")
        print("これで usr7wyygjep で管理者としてログインできます。")
    else:
        print("\n× 処理に失敗しました。")