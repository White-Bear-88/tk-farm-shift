#!/bin/bash

# 酪農シフト管理システムデプロイスクリプト

set -e

ENVIRONMENT=${1:-dev}
STACK_NAME="dairy-shift-management-${ENVIRONMENT}"
TEMPLATE_FILE="dairy-shift-management.yaml"

echo "=== 酪農シフト管理システムのデプロイを開始します ==="
echo "環境: ${ENVIRONMENT}"
echo "スタック名: ${STACK_NAME}"

# SAM CLIの確認
if ! command -v sam &> /dev/null; then
    echo "エラー: SAM CLIがインストールされていません"
    echo "インストール方法: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# AWS CLIの確認
if ! command -v aws &> /dev/null; then
    echo "エラー: AWS CLIがインストールされていません"
    exit 1
fi

# AWS認証情報の確認
if ! aws sts get-caller-identity &> /dev/null; then
    echo "エラー: AWS認証情報が設定されていません"
    echo "aws configure を実行してください"
    exit 1
fi

echo "=== 依存関係のインストール ==="
cd src
pip install -r requirements.txt -t .
cd ..

echo "=== SAMビルド ==="
sam build --template-file ${TEMPLATE_FILE}

echo "=== SAMデプロイ ==="
sam deploy \
    --template-file ${TEMPLATE_FILE} \
    --stack-name ${STACK_NAME} \
    --parameter-overrides Environment=${ENVIRONMENT} \
    --capabilities CAPABILITY_IAM \
    --confirm-changeset \
    --resolve-s3

echo "=== 初期データのセットアップ ==="
python setup_data.py

echo "=== デプロイ完了 ==="
echo "API Gateway URL を確認してください:"
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text

echo ""
echo "=== 次のステップ ==="
echo "1. API Gateway URLをフロントエンドアプリケーションに設定"
echo "2. 従業員データの追加登録"
echo "3. シフト作成テスト"