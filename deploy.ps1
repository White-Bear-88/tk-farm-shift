param([string]$Environment = "dev")

$STACK_NAME = "dairy-shift-management-$Environment"
$TEMPLATE_FILE = "dairy-shift-management.yaml"

Write-Host "=== 酪農シフト管理システムのデプロイを開始します ===" -ForegroundColor Green
Write-Host "環境: $Environment"
Write-Host "スタック名: $STACK_NAME"

Write-Host "=== 前提条件チェック ===" -ForegroundColor Yellow
sam --version
aws --version
aws sts get-caller-identity

Write-Host "=== 依存関係のインストール ===" -ForegroundColor Yellow
if (Test-Path "src/requirements.txt") {
    Set-Location src
    pip install -r requirements.txt -t . --quiet
    Set-Location ..
    Write-Host "✓ 依存関係インストール完了" -ForegroundColor Green
}

Write-Host "=== SAMビルド ===" -ForegroundColor Yellow
sam build --template-file $TEMPLATE_FILE

Write-Host "=== SAMデプロイ ===" -ForegroundColor Yellow
sam deploy --template-file $TEMPLATE_FILE --stack-name $STACK_NAME --parameter-overrides Environment=$Environment --capabilities CAPABILITY_IAM --no-confirm-changeset --resolve-s3

Write-Host "=== 初期データのセットアップ ===" -ForegroundColor Yellow
if (Test-Path "setup_data.py") {
    python setup_data.py
}

Write-Host "=== デプロイ完了 ===" -ForegroundColor Green
$apiUrl = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
Write-Host "API Gateway URL: $apiUrl" -ForegroundColor Cyan