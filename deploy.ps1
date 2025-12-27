# 酪農シフト管理システム PowerShell デプロイスクリプト

param(
    [string]$Environment = "dev"
)

$STACK_NAME = "dairy-shift-management-$Environment"
$TEMPLATE_FILE = "dairy-shift-management.yaml"

Write-Host "=== 酪農シフト管理システムのデプロイを開始します ===" -ForegroundColor Green
Write-Host "環境: $Environment"
Write-Host "スタック名: $STACK_NAME"

# SAM CLIの確認
try {
    sam --version | Out-Null
} catch {
    Write-Host "エラー: SAM CLIがインストールされていません" -ForegroundColor Red
    Write-Host "インストール方法: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
}

# AWS CLIの確認
try {
    aws --version | Out-Null
} catch {
    Write-Host "エラー: AWS CLIがインストールされていません" -ForegroundColor Red
    exit 1
}

# AWS認証情報の確認
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "エラー: AWS認証情報が設定されていません" -ForegroundColor Red
    Write-Host "aws configure を実行してください"
    exit 1
}

Write-Host "=== 依存関係のインストール ===" -ForegroundColor Yellow
Set-Location src
pip install -r requirements.txt -t .
Set-Location ..

Write-Host "=== SAMビルド ===" -ForegroundColor Yellow
sam build --template-file $TEMPLATE_FILE

Write-Host "=== SAMデプロイ ===" -ForegroundColor Yellow
sam deploy `
    --template-file $TEMPLATE_FILE `
    --stack-name $STACK_NAME `
    --parameter-overrides Environment=$Environment `
    --capabilities CAPABILITY_IAM `
    --confirm-changeset `
    --resolve-s3

Write-Host "=== 初期データのセットアップ ===" -ForegroundColor Yellow
python setup_data.py

Write-Host "=== デプロイ完了 ===" -ForegroundColor Green
Write-Host "API Gateway URL を確認してください:"
$apiUrl = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
    --output text

Write-Host $apiUrl -ForegroundColor Cyan

Write-Host ""
Write-Host "=== 次のステップ ===" -ForegroundColor Green
Write-Host "1. API Gateway URLをフロントエンドアプリケーションに設定"
Write-Host "2. 従業員データの追加登録"
Write-Host "3. シフト作成テスト"