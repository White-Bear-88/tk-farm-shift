# ダミ�EチE�Eタ登録スクリプト
# API Gateway URLを設定してください
$API_BASE = "https://mxh6g7opm2.execute-api.ap-northeast-1.amazonaws.com/dev"

Write-Host "酪農シフト管琁E��スチE�� - ダミ�EチE�Eタ登録開姁E -ForegroundColor Green

# 従業員チE�Eタ
$employees = @(
    @{
        employee_id = "001"
        name = "田中太郁E
        phone = "090-1234-5678"
        email = "tanaka@farm.com"
        skills = @("milking", "feeding")
        vacation_days = 20
    },
    @{
        employee_id = "002"
        name = "佐藤花孁E
        phone = "090-2345-6789"
        email = "sato@farm.com"
        skills = @("cleaning", "patrol")
        vacation_days = 18
    },
    @{
        employee_id = "003"
        name = "鈴木次郁E
        phone = "090-3456-7890"
        email = "suzuki@farm.com"
        skills = @("milking", "cleaning", "patrol")
        vacation_days = 22
    },
    @{
        employee_id = "004"
        name = "高橋美咲"
        phone = "090-4567-8901"
        email = "takahashi@farm.com"
        skills = @("feeding", "cleaning")
        vacation_days = 20
    },
    @{
        employee_id = "005"
        name = "山田健一"
        phone = "090-5678-9012"
        email = "yamada@farm.com"
        skills = @("milking", "feeding", "patrol")
        vacation_days = 25
    }
)

# 従業員登録
Write-Host "従業員チE�Eタを登録中..." -ForegroundColor Yellow
foreach ($emp in $employees) {
    try {
        $body = $emp | ConvertTo-Json -Depth 3
        $response = Invoke-RestMethod -Uri "$API_BASE/employees" -Method POST -ContentType "application/json" -Body $body
        Write-Host "✁E従業員 $($emp.name) を登録しました" -ForegroundColor Green
    }
    catch {
        Write-Host "✁E従業員 $($emp.name) の登録に失敁E $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 作業種別チE�Eタ
$tasks = @(
    @{
        task_type = "milking"
        name = "搾乳"
        description = "牛�E搾乳作業"
        duration_minutes = 120
        required_people = 2
        priority = "high"
        recommended_start_time = "05:00"
        recommended_end_time = "07:00"
    },
    @{
        task_type = "feeding"
        name = "給餁E
        description = "牛への餌やめE
        duration_minutes = 60
        required_people = 1
        priority = "high"
        recommended_start_time = "08:00"
        recommended_end_time = "09:00"
    },
    @{
        task_type = "cleaning"
        name = "渁E��"
        description = "牛�Eの渁E��作業"
        duration_minutes = 90
        required_people = 1
        priority = "medium"
        recommended_start_time = "10:00"
        recommended_end_time = "11:30"
    },
    @{
        task_type = "patrol"
        name = "見回めE
        description = "牛�E健康状態確誁E
        duration_minutes = 30
        required_people = 1
        priority = "medium"
        recommended_start_time = "14:00"
        recommended_end_time = "14:30"
    }
)

# 作業種別登録
Write-Host "作業種別チE�Eタを登録中..." -ForegroundColor Yellow
foreach ($task in $tasks) {
    try {
        $body = $task | ConvertTo-Json -Depth 3
        $response = Invoke-RestMethod -Uri "$API_BASE/tasks" -Method POST -ContentType "application/json" -Body $body
        Write-Host "✁E作業種別 $($task.name) を登録しました" -ForegroundColor Green
    }
    catch {
        Write-Host "✁E作業種別 $($task.name) の登録に失敁E $($_.Exception.Message)" -ForegroundColor Red
    }
}

# サンプルシフトチE�Eタ�E�今日から1週間�E�E�EWrite-Host "サンプルシフトチE�Eタを登録中..." -ForegroundColor Yellow
$today = Get-Date
for ($i = 0; $i -lt 7; $i++) {
    $date = ($today.AddDays($i)).ToString("yyyy-MM-dd")
    
    # 朝�E搾乳シフト
    $morningShifts = @(
        @{
            date = $date
            employee_id = "001"
            task_type = "milking"
            start_time = "05:00"
            end_time = "07:00"
            status = "scheduled"
        },
        @{
            date = $date
            employee_id = "003"
            task_type = "milking"
            start_time = "05:00"
            end_time = "07:00"
            status = "scheduled"
        }
    )
    
    # 給餌シフト
    $feedingShift = @{
        date = $date
        employee_id = "002"
        task_type = "feeding"
        start_time = "08:00"
        end_time = "09:00"
        status = "scheduled"
    }
    
    # 渁E��シフト
    $cleaningShift = @{
        date = $date
        employee_id = "004"
        task_type = "cleaning"
        start_time = "10:00"
        end_time = "11:30"
        status = "scheduled"
    }
    
    # 見回りシフト
    $patrolShift = @{
        date = $date
        employee_id = "005"
        task_type = "patrol"
        start_time = "14:00"
        end_time = "14:30"
        status = "scheduled"
    }
    
    # 全シフトを登録
    $allShifts = $morningShifts + $feedingShift + $cleaningShift + $patrolShift
    
    foreach ($shift in $allShifts) {
        try {
            $body = $shift | ConvertTo-Json -Depth 3
            $response = Invoke-RestMethod -Uri "$API_BASE/shifts" -Method POST -ContentType "application/json" -Body $body
            Write-Host "✁E$date のシフト ($($shift.employee_id) - $($shift.task_type)) を登録しました" -ForegroundColor Green
        }
        catch {
            Write-Host "✁E$date のシフト登録に失敁E $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "ダミ�EチE�Eタ登録完亁E��E -ForegroundColor Green
Write-Host "Web アプリケーションで確認してください: $API_BASE/" -ForegroundColor Cyan
