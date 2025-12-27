# 酪農シフト管理システム

AWS サーバーレスアーキテクチャを使用した酪農現場向けシフト管理アプリケーション

## アーキテクチャ概要

```
[フロントエンド] → [API Gateway] → [Lambda] → [DynamoDB]
                                      ↓
                              [CloudWatch Logs]
```

### 主要コンポーネント
- **API Gateway**: RESTful API エンドポイント
- **Lambda Functions**: ビジネスロジック処理
- **DynamoDB**: 単一テーブル設計によるデータストレージ
- **CloudFormation**: Infrastructure as Code

## 機能一覧

### シフト管理
- 日別シフト表示・作成・編集・削除
- 従業員別シフト履歴
- 自動シフト割り当て
- 作業種別管理

### 作業種別
- 搾乳 (milking)
- 給餌 (feeding)  
- 清掃 (cleaning)
- 見回り (patrol)

## データベース設計

### DynamoDB 単一テーブル構造
```
PK (Partition Key): エンティティタイプ#ID
SK (Sort Key): 関連情報#タイムスタンプ

例:
- 従業員: PK=EMP#001, SK=PROFILE
- シフト: PK=SHIFT#2024-01-15, SK=EMP#001#milking
- 作業: PK=TASK#milking, SK=CONFIG
```

### GSI (Global Secondary Index)
- **GSI1**: 従業員別検索 (PK=employee_id, SK=date)
- **GSI2**: 作業種別別検索 (PK=task_type, SK=date#employee_id)

## API エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/shifts/{date}` | 日別シフト一覧 |
| POST | `/shifts` | シフト作成 |
| PUT | `/shifts/{id}` | シフト更新 |
| DELETE | `/shifts/{id}` | シフト削除 |
| GET | `/employees/{id}/shifts` | 従業員別シフト |
| GET | `/tasks` | 作業種別一覧 |
| POST | `/shifts/assign` | 自動シフト割り当て |

## セットアップ手順

### 前提条件
- AWS CLI インストール・設定済み
- SAM CLI インストール済み
- Python 3.12+ (3.14対応)
- Git for Windows (推奨)

### Windows でのデプロイ
```cmd
REM リポジトリクローン
git clone <repository-url>
cd tk-farm

REM SAM ビルド
sam build --template-file dairy-shift-management.yaml

REM SAM デプロイ
sam deploy ^
    --template-file dairy-shift-management.yaml ^
    --stack-name dairy-shift-management-dev ^
    --parameter-overrides Environment=dev ^
    --capabilities CAPABILITY_IAM ^
    --confirm-changeset

REM 初期データセットアップ
python setup_data.py
```

### PowerShell でのデプロイ
```powershell
# リポジトリクローン
git clone <repository-url>
cd tk-farm

# SAM ビルド
sam build --template-file dairy-shift-management.yaml

# SAM デプロイ
sam deploy `
    --template-file dairy-shift-management.yaml `
    --stack-name dairy-shift-management-dev `
    --parameter-overrides Environment=dev `
    --capabilities CAPABILITY_IAM `
    --confirm-changeset

# 初期データセットアップ
python setup_data.py
```

## 使用例

### シフト作成 (PowerShell)
```powershell
$body = @{
    date = "2024-01-15"
    employee_id = "001"
    task_type = "milking"
    start_time = "05:00"
    end_time = "07:00"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api-url/dev/shifts" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### 自動シフト割り当て (PowerShell)
```powershell
$body = @{
    date = "2024-01-15"
    required_tasks = @(
        @{task_type = "milking"; count = 2},
        @{task_type = "feeding"; count = 1}
    )
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "https://api-url/dev/shifts/assign" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

## 監視・ログ

### CloudWatch Logs
- Lambda 関数ごとにロググループが自動作成
- エラー監視とパフォーマンス分析

### メトリクス
- API Gateway: リクエスト数、レスポンス時間、エラー率
- Lambda: 実行時間、エラー数、同時実行数
- DynamoDB: 読み書き容量、スロットリング

## セキュリティ

### IAM ロール
- Lambda 実行ロール: DynamoDB への最小権限アクセス
- API Gateway: CORS 設定済み

### データ保護
- DynamoDB: 保存時暗号化
- API Gateway: HTTPS 強制

## コスト最適化

### サーバーレス料金体系
- Lambda: 実行時間課金
- DynamoDB: オンデマンド課金
- API Gateway: リクエスト数課金

### 推定月額コスト (小規模農場)
- Lambda: $2-5
- DynamoDB: $5-10  
- API Gateway: $2-5
- **合計: $9-20/月**

## トラブルシューティング

### よくある問題
1. **デプロイエラー**: AWS 認証情報を確認
2. **API エラー**: CloudWatch Logs を確認
3. **DynamoDB エラー**: テーブル名・リージョンを確認

### ログ確認 (Windows)
```cmd
REM Lambda ログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/dairy"

REM 最新ログ表示
aws logs tail /aws/lambda/dairy-shift-crud-dev --follow
```

### PowerShell でのログ確認
```powershell
# Lambda ログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/dairy"

# 最新ログ表示
aws logs tail /aws/lambda/dairy-shift-crud-dev --follow
```

## 今後の拡張予定

- [ ] リアルタイム通知 (SNS/SES)
- [ ] モバイルアプリ (React Native)
- [ ] 勤怠管理機能
- [ ] レポート・分析機能
- [ ] 多言語対応