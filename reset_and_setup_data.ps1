# 酪農シフト管理システム - データリセット・再生成スクリプト
# 既存データを全削除して最新仕様に合わせたテストデータを作成

# 文字エンコーディング設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# API Base URL
$API_BASE = "https://mxh6g7opm2.execute-api.ap-northeast-1.amazonaws.com/dev"

Write-Host "=== 酪農シフト管理システム データリセット・再生成 ===" -ForegroundColor Green

# 1. DynamoDBテーブル全データ削除
Write-Host "1. DynamoDBテーブルの全データを削除中..." -ForegroundColor Yellow

# テーブル名を取得
$tableName = "dairy-shifts-dev"

# 全アイテムをスキャンして削除
Write-Host "   テーブル内の全データをスキャン中..."
$scanResult = aws dynamodb scan --table-name $tableName --projection-expression "PK,SK" --output json | ConvertFrom-Json

if ($scanResult.Items.Count -gt 0) {
    Write-Host "   $($scanResult.Items.Count)件のアイテムを削除中..."
    
    foreach ($item in $scanResult.Items) {
        $pk = $item.PK.S
        $sk = $item.SK.S
        aws dynamodb delete-item --table-name $tableName --key "{`"PK`":{`"S`":`"$pk`"},`"SK`":{`"S`":`"$sk`"}}" | Out-Null
    }
    Write-Host "   全データの削除が完了しました" -ForegroundColor Green
} else {
    Write-Host "   削除対象のデータがありません" -ForegroundColor Gray
}

# 2. 作業種別データ作成
Write-Host "2. 作業種別データを作成中..." -ForegroundColor Yellow

$tasks = @(
    @{
        task_type = "milking"
        name = "搾乳"
        description = "牛の搾乳作業"
        recommended_start_time = "05:00"
        recommended_end_time = "07:00"
        required_people = 2
    },
    @{
        task_type = "feeding"
        name = "給餌"
        description = "牛への餌やり"
        recommended_start_time = "08:00"
        recommended_end_time = "09:00"
        required_people = 1
    },
    @{
        task_type = "cleaning"
        name = "清掃"
        description = "牛舎の清掃作業"
        recommended_start_time = "10:00"
        recommended_end_time = "11:30"
        required_people = 1
    },
    @{
        task_type = "patrol"
        name = "見回り"
        description = "牛の健康状態確認"
        recommended_start_time = "14:00"
        recommended_end_time = "14:30"
        required_people = 1
    }
)

foreach ($task in $tasks) {
    $body = $task | ConvertTo-Json -Depth 3
    try {
        $response = Invoke-RestMethod -Uri "$API_BASE/tasks" -Method POST -ContentType "application/json" -Body $body
        Write-Host "   作業種別 '$($task.name)' を作成しました" -ForegroundColor Green
    } catch {
        Write-Host "   作業種別 '$($task.name)' の作成に失敗: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. 従業員データ作成
Write-Host "3. 従業員データを作成中..." -ForegroundColor Yellow

$employees = @(
    @{
        name = "田中太郎"
        phone = "090-1234-5678"
        email = "tanaka@example.com"
        skills = @("milking", "feeding", "cleaning")
        vacation_days = 20
    },
    @{
        name = "佐藤花子"
        phone = "090-2345-6789"
        email = "sato@example.com"
        skills = @("milking", "patrol", "cleaning")
        vacation_days = 20
    },
    @{
        name = "鈴木一郎"
        phone = "090-3456-7890"
        email = "suzuki@example.com"
        skills = @("feeding", "cleaning", "patrol")
        vacation_days = 20
    },
    @{
        name = "高橋美咲"
        phone = "090-4567-8901"
        email = "takahashi@example.com"
        skills = @("milking", "feeding")
        vacation_days = 20
    },
    @{
        name = "山田健太"
        phone = "090-5678-9012"
        email = "yamada@example.com"
        skills = @("cleaning", "patrol", "milking")
        vacation_days = 20
    }
)

foreach ($employee in $employees) {
    $body = $employee | ConvertTo-Json -Depth 3
    try {
        $response = Invoke-RestMethod -Uri "$API_BASE/employees" -Method POST -ContentType "application/json" -Body $body
        Write-Host "   従業員 '$($employee.name)' を作成しました (ID: $($response.employee_id))" -ForegroundColor Green
    } catch {
        Write-Host "   従業員 '$($employee.name)' の作成に失敗: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 4. グローバルデフォルト人数設定
Write-Host "4. グローバルデフォルト人数設定を作成中..." -ForegroundColor Yellow

$globalRequirements = @{
    milking = 2
    feeding = 1
    cleaning = 1
    patrol = 1
}

$body = $globalRequirements | ConvertTo-Json -Depth 3
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/requirements/global-default" -Method POST -ContentType "application/json" -Body $body
    Write-Host "   グローバルデフォルト人数設定を作成しました" -ForegroundColor Green
} catch {
    Write-Host "   グローバルデフォルト人数設定の作成に失敗: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. シフト確定日設定
Write-Host "5. シフト確定日設定を作成中..." -ForegroundColor Yellow

$confirmationSettings = @{
    confirmation_day = 25
}

$body = $confirmationSettings | ConvertTo-Json -Depth 3
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/settings/confirmation" -Method POST -ContentType "application/json" -Body $body
    Write-Host "   シフト確定日設定を作成しました (25日)" -ForegroundColor Green
} catch {
    Write-Host "   シフト確定日設定の作成に失敗: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. 有給デフォルト設定
Write-Host "6. 有給デフォルト設定を作成中..." -ForegroundColor Yellow

$vacationSettings = @{
    default_vacation_days = 20
}

$body = $vacationSettings | ConvertTo-Json -Depth 3
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/settings/vacation-default" -Method POST -ContentType "application/json" -Body $body
    Write-Host "   有給デフォルト設定を作成しました (20日)" -ForegroundColor Green
} catch {
    Write-Host "   有給デフォルト設定の作成に失敗: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== データリセット・再生成が完了しました ===" -ForegroundColor Green
Write-Host "作成されたデータ:" -ForegroundColor Cyan
Write-Host "- 作業種別: 4種類 (搾乳、給餌、清掃、見回り)" -ForegroundColor White
Write-Host "- 従業員: 5名 (ID: 001-005)" -ForegroundColor White
Write-Host "- グローバルデフォルト人数設定" -ForegroundColor White
Write-Host "- シフト確定日設定 (25日)" -ForegroundColor White
Write-Host "- 有給デフォルト設定 (20日)" -ForegroundColor White
Write-Host ""
Write-Host "Webアプリケーションでシステムをテストできます。" -ForegroundColor Green