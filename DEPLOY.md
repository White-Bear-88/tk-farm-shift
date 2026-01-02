# フロントエンド静的ホスティング デプロイ手順

## 前提条件
- AWS CLI インストール・設定済み
- Node.js 18+ インストール済み
- CDK CLI インストール済み (`npm install -g aws-cdk`)

## 1. CDK インフラデプロイ

```powershell
# CDK ディレクトリに移動
cd cdk

# 依存関係インストール
npm install

# CDK Bootstrap（初回のみ）
cdk bootstrap

# スタックデプロイ
cdk deploy

# 出力値を記録（後で GitHub Secrets に設定）
# - BucketName
# - DistributionId
# - DeployUserName
```

## 2. IAM アクセスキー作成

```powershell
# デプロイユーザーのアクセスキー作成
aws iam create-access-key --user-name tk-farm-deploy-user

# 出力されたアクセスキーとシークレットキーを記録
```

## 3. GitHub Secrets 設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を設定：

- `AWS_ACCESS_KEY_ID`: 手順2で作成したアクセスキー
- `AWS_SECRET_ACCESS_KEY`: 手順2で作成したシークレットキー  
- `S3_BUCKET_NAME`: CDK出力の BucketName
- `CLOUDFRONT_DISTRIBUTION_ID`: CDK出力の DistributionId

## 4. 初回手動デプロイ

```powershell
# フロントエンドファイルを S3 にアップロード
aws s3 sync frontend/ s3://[BucketName] --delete

# CloudFront キャッシュ無効化
aws cloudfront create-invalidation --distribution-id [DistributionId] --paths "/*"
```

## 5. 自動デプロイ確認

1. `src/` ディレクトリ内の HTML/JS/CSS ファイルを編集
2. Git にコミット・プッシュ
3. GitHub Actions が自動実行されることを確認
4. CloudFront URL でサイトが更新されることを確認

## トラブルシューティング

### CDK デプロイエラー
- AWS 認証情報を確認
- リージョンが正しく設定されているか確認

### GitHub Actions エラー
- Secrets が正しく設定されているか確認
- IAM ポリシーが正しく適用されているか確認

### CloudFront アクセスエラー
- S3 バケットポリシーが正しく設定されているか確認
- OAC が正しく設定されているか確認

## リソース削除

```powershell
# CDK スタック削除
cd cdk
cdk destroy

# IAM アクセスキー削除
aws iam delete-access-key --user-name tk-farm-deploy-user --access-key-id [AccessKeyId]
```

## コスト見積もり

### 月額コスト（小規模利用）
- S3: $1-3（ストレージ・リクエスト）
- CloudFront: $1-5（データ転送）
- **合計: $2-8/月**

### 無料枠
- S3: 5GB ストレージ、20,000 GET リクエスト
- CloudFront: 1TB データ転送、10,000,000 リクエスト