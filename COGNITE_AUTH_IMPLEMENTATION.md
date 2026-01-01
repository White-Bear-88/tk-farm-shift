# CogniteID認証基盤 実装完了

## 📋 実装内容

### 1. 設定値の整理
- **ファイル**: `cognite-auth-config.js`
- **機能**: 環境変数ベースの設定管理、開発/本番環境の自動判定

### 2. 本番用ログインフロー
- **ファイル**: `login.html`（修正）
- **機能**: CogniteID Implicit Flowによる認証開始
- **セキュリティ**: state/nonce パラメータによるCSRF・リプレイ攻撃対策

### 3. コールバック画面
- **ファイル**: `callback.html`（修正）
- **機能**: URLフラグメントからID_TOKENを取得、JWT解析、ユーザー情報取得

### 4. バックエンドAPI
- **ファイル**: `auth_service.py`（修正）
- **新規エンドポイント**: 
  - `GET /auth/me` - JWTからsubを抽出してユーザー情報取得
  - `GET /auth/user-by-sub/{sub}` - subでユーザー検索

### 5. 画面振り分けロジック
- **admin**: `menu.html`へ遷移
- **employee**: `employee-view.html`へ遷移
- **ロール判定**: DynamoDBの`role`フィールドに基づく

### 6. 開発用ログインとの共存
- **開発環境**: localhost判定で開発用ログインボタンを表示
- **本番環境**: CogniteIDログインのみ表示

## 🔄 認証フロー

```
1. ユーザーがlogin.htmlでログインボタンクリック
2. CogniteID認証画面にリダイレクト（state/nonce付き）
3. ユーザーがメールアドレス+パスワードで認証
4. callback.htmlにID_TOKENがフラグメントで返却
5. JWTからsubを抽出
6. /auth/user-by-sub/{sub}でDynamoDBからユーザー情報取得
7. roleに応じて画面振り分け
```

## 🔧 設定方法

### 本番環境
1. `.env.example`を参考に環境変数を設定
2. `cognite-auth-config.js`の設定値を更新
3. CogniteIDでアプリケーション登録
4. リダイレクトURIを設定

### 開発環境
- localhost判定で自動的に開発モードになります
- 開発用ログイン画面（`login-dev.html`）も利用可能

## 📁 修正ファイル一覧

### 新規作成
- `cognite-auth-config.js` - 認証設定管理
- `.env.example` - 環境変数設定例

### 修正
- `login.html` - CogniteID認証開始
- `callback.html` - ID_TOKEN処理
- `auth_service.py` - /me エンドポイント追加
- `menu.html` - 認証チェック更新
- `employee-view.html` - 認証チェック更新

## 🔐 セキュリティ機能

- **CSRF対策**: stateパラメータ検証
- **リプレイ攻撃対策**: nonceパラメータ検証
- **JWT検証**: 将来的な署名検証に対応可能な構造
- **セッション管理**: sessionStorageでstate/nonce管理

## 🚀 次のステップ

1. 実際のCogniteID設定を行う
2. JWT署名検証を本番環境で有効化
3. ユーザー登録フローの実装
4. パスワードリセット機能の追加