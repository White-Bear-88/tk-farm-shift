# 酪農シフト管理システム PowerShell デプロイスクリプト

param(
    [string]$Environment = "dev"
)

$STACK_NAME = "dairy-shift-management-$Environment"
$TEMPLATE_FILE = "dairy-shift-management.yaml"

Write-Host "=== 酪農シフト管理システムのデプロイを開始します ===" -ForegroundColor Green
Write-Host "環境: $Environment"
Write-Host "スタック名: $STACK_NAME"

# 前提条件チェック
Write-Host "=== 前提条件チェック ===" -ForegroundColor Yellow

try {
    sam --version | Out-Null
    Write-Host "✓ SAM CLI" -ForegroundColor Green
}
catch {
    Write-Host "✗ SAM CLIがインストールされていません" -ForegroundColor Red
    exit 1
}

try {
    aws --version | Out-Null
    Write-Host "✓ AWS CLI" -ForegroundColor Green
}
catch {
    Write-Host "✗ AWS CLIがインストールされていません" -ForegroundColor Red
    exit 1
}

try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✓ AWS認証情報" -ForegroundColor Green
}
catch {
    Write-Host "✗ AWS認証情報が設定されていません" -ForegroundColor Red
    Write-Host "aws configure を実行してください"
    exit 1
}

# 依存関係インストール
Write-Host "=== 依存関係のインストール ===" -ForegroundColor Yellow
if (Test-Path "src/requirements.txt") {
    Push-Location src
    pip install -r requirements.txt -t . --quiet
    Pop-Location
    Write-Host "✓ 依存関係インストール完了" -ForegroundColor Green
}
else {
    Write-Host "⚠ requirements.txt が見つかりません" -ForegroundColor Yellow
}

# SAMビルド
Write-Host "=== SAMビルド ===" -ForegroundColor Yellow
sam build --template-file $TEMPLATE_FILE
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ SAMビルドに失敗しました" -ForegroundColor Red
    exit 1
}
Write-Host "✓ SAMビルド完了" -ForegroundColor Green

# SAMデプロイ
Write-Host "=== SAMデプロイ ===" -ForegroundColor Yellow
sam deploy --template-file $TEMPLATE_FILE --stack-name $STACK_NAME --parameter-overrides Environment=$Environment --capabilities CAPABILITY_IAM --no-confirm-changeset --resolve-s3

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ SAMデプロイに失敗しました" -ForegroundColor Red
    exit 1
}
Write-Host "✓ SAMデプロイ完了" -ForegroundColor Green

# 初期データセットアップ
Write-Host "=== 初期データのセットアップ ===" -ForegroundColor Yellow
if (Test-Path "setup_data.py") {
    python setup_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 初期データセットアップ完了" -ForegroundColor Green
    }
    else {
        Write-Host "⚠ 初期データセットアップでエラーが発生しました" -ForegroundColor Yellow
    }
}
else {
    Write-Host "⚠ setup_data.py が見つかりません" -ForegroundColor Yellow
}

# API URL取得
Write-Host "=== デプロイ完了 ===" -ForegroundColor Green
try {
    $apiUrl = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text 2>$null
    
    if ($apiUrl -and $apiUrl -ne "None") {
        Write-Host "API Gateway URL: $apiUrl" -ForegroundColor Cyan
    }
    else {
        Write-Host "⚠ API Gateway URLが取得できませんでした" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠ API Gateway URLの取得に失敗しました" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 次のステップ ===" -ForegroundColor Green
Write-Host "1. API Gateway URLをフロントエンドアプリケーションに設定"
Write-Host "2. 従業員データの追加登録"
Write-Host "3. シフト作成テスト"