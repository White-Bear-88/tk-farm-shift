# CogniteID認証設定ガイド

## 設定ファイル

`cognite-config.js` でCogniteIDの設定を管理します。

### 設定項目

```javascript
const COGNITE_CONFIG = {
    dev: {
        clientId: 'YOUR_COGNITE_CLIENT_ID',
        redirectUri: 'http://localhost:8080/callback.html',
        cogniteDomain: 'https://your-cognite-domain.auth.region.amazoncognito.com',
        scope: 'openid profile email'
    },
    prod: {
        clientId: 'YOUR_PROD_COGNITE_CLIENT_ID',
        redirectUri: 'https://your-domain.com/callback.html',
        cogniteDomain: 'https://your-prod-cognite-domain.auth.region.amazoncognito.com',
        scope: 'openid profile email'
    }
};
```

## セットアップ手順

### 1. CogniteID設定

1. `src/cognite-config.js` を編集
2. 開発環境と本番環境の設定を入力：
   - `clientId`: CogniteIDアプリケーションのクライアントID
   - `redirectUri`: ログイン後のリダイレクトURL
   - `cogniteDomain`: CogniteIDドメイン
   - `scope`: 要求するスコープ

### 2. CogniteIDユーザーとDynamoDB従業員の紐づけ

1. 管理者画面でCogniteIDユーザーを作成
2. `cognite_user_id` = CogniteIDの `sub` クレーム
3. `employee_id` で既存従業員と紐づけ

### 3. ログインフロー

1. **ログイン開始**: `login.html` → CogniteIDログイン画面
2. **認証**: CogniteIDで認証
3. **コールバック**: `callback.html` でJWT受け取り
4. **ユーザー検索**: JWTの `sub` でDynamoDB検索
5. **画面振り分け**: ロールに応じてメニューまたは従業員画面

## API エンドポイント

### 新規追加

- `GET /auth/user-by-sub/{sub}`: subをキーにユーザー情報取得

### 既存

- `POST /auth/verify`: JWTトークン検証
- `GET /auth/profile`: ユーザープロファイル取得

## 開発用ログイン

開発時は `login-dev.html` で簡易ログインが可能です。

## 注意事項

- 本番環境では適切なCogniteID設定が必要
- CORS設定がすべてのLambda関数に適用済み
- JWTトークンの署名検証は本番環境で有効化してください