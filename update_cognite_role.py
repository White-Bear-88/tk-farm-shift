import boto3
import json
from datetime import datetime

# DynamoDB設定
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('DairyShiftManagement')

def update_cognite_user_role():
    """CogniteIDユーザー usr7wyygjep のロールを管理者に変更"""
    
    cognite_user_id = 'usr7wyygjep'
    
    try:
        # 既存のCogniteIDユーザーを取得
        response = table.get_item(
            Key={
                'PK': f'COGNITE_USER#{cognite_user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in response:
            print(f"× CogniteIDユーザー {cognite_user_id} が見つかりません。")
            return False
        
        # ロールを管理者に更新
        item = response['Item']
        item['role'] = 'admin'
        item['updated_at'] = datetime.now().isoformat()
        
        # DynamoDBに保存
        table.put_item(Item=item)
        
        print(f"✓ CogniteIDユーザー {cognite_user_id} のロールを管理者に変更しました。")
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
    print("CogniteIDユーザーのロール変更を開始...")
    success = update_cognite_user_role()
    
    if success:
        print("\n✓ ロール変更が完了しました。")
        print("これで usr7wyygjep で管理者としてログインできます。")
    else:
        print("\n× ロール変更に失敗しました。")