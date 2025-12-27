# 追加サンプルデータ登録スクリプト
$API_BASE = "https://mxh6g7opm2.execute-api.ap-northeast-1.amazonaws.com/dev"

Write-Host "追加サンプルデータ登録開始" -ForegroundColor Green

# 追加従業員データ
$additionalEmployees = @(
    @{
        employee_id = "006"
        name = "伊藤雅子"
        phone = "090-6789-0123"
        email = "ito@farm.com"
        skills = @("milking", "feeding", "cleaning")
        vacation_days = 21
    },
    @{
        employee_id = "007"
        name = "渡辺健太"
        phone = "090-7890-1234"
        email = "watanabe@farm.com"
        skills = @("feeding", "patrol")
        vacation_days = 19
    },
    @{
        employee_id = "008"
        name = "中村さくら"
        phone = "090-8901-2345"
        email = "nakamura@farm.com"
        skills = @("milking", "cleaning")
        vacation_days = 23
    },
    @{
        employee_id = "009"
        name = "小林大輔"
        phone = "090-9012-3456"
        email = "kobayashi@farm.com"
        skills = @("milking", "feeding", "patrol")
        vacation_days = 20
    },
    @{
        employee_id = "010"
        name = "加藤美穂"
        phone = "090-0123-4567"
        email = "kato@farm.com"
        skills = @("cleaning", "patrol")
        vacation_days = 18
    }
)

# 追加従業員登録
Write-Host "追加従業員データを登録中..." -ForegroundColor Yellow
foreach ($emp in $additionalEmployees) {
    try {
        $body = $emp | ConvertTo-Json -Depth 3
        $response = Invoke-RestMethod -Uri "$API_BASE/employees" -Method POST -ContentType "application/json" -Body $body
        Write-Host "✓ 従業員 $($emp.name) を登録しました" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ 従業員 $($emp.name) の登録に失敗: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 10月・11月のシフトデータ生成
Write-Host "10月・11月のシフトデータを登録中..." -ForegroundColor Yellow

$months = @("2024-10", "2024-11")
$employees = @("001", "002", "003", "004", "005", "006", "007", "008", "009", "010")

foreach ($month in $months) {
    $year = $month.Split('-')[0]
    $monthNum = [int]$month.Split('-')[1]
    $daysInMonth = [DateTime]::DaysInMonth($year, $monthNum)
    
    for ($day = 1; $day -le $daysInMonth; $day++) {
        $date = "$month-$('{0:D2}' -f $day)"
        
        # 朝の搾乳シフト (2人)
        $milkingEmployees = $employees | Get-Random -Count 2
        foreach ($empId in $milkingEmployees) {
            $shift = @{
                date = $date
                employee_id = $empId
                task_type = "milking"
                start_time = "05:00"
                end_time = "07:00"
                status = "scheduled"
            }
            
            try {
                $body = $shift | ConvertTo-Json -Depth 3
                Invoke-RestMethod -Uri "$API_BASE/shifts" -Method POST -ContentType "application/json" -Body $body
            } catch {
                Write-Host "✗ シフト登録エラー: $date - $empId" -ForegroundColor Red
            }
        }
        
        # 給餌シフト (1人)
        $feedingEmployee = $employees | Get-Random -Count 1
        $shift = @{
            date = $date
            employee_id = $feedingEmployee[0]
            task_type = "feeding"
            start_time = "08:00"
            end_time = "09:00"
            status = "scheduled"
        }
        
        try {
            $body = $shift | ConvertTo-Json -Depth 3
            Invoke-RestMethod -Uri "$API_BASE/shifts" -Method POST -ContentType "application/json" -Body $body
        } catch {
            Write-Host "✗ 給餌シフト登録エラー: $date" -ForegroundColor Red
        }
        
        # 清掃シフト (1人)
        $cleaningEmployee = $employees | Get-Random -Count 1
        $shift = @{
            date = $date
            employee_id = $cleaningEmployee[0]
            task_type = "cleaning"
            start_time = "10:00"
            end_time = "11:30"
            status = "scheduled"
        }
        
        try {
            $body = $shift | ConvertTo-Json -Depth 3
            Invoke-RestMethod -Uri "$API_BASE/shifts" -Method POST -ContentType "application/json" -Body $body
        } catch {
            Write-Host "✗ 清掃シフト登録エラー: $date" -ForegroundColor Red
        }
        
        # 見回りシフト (1人)
        $patrolEmployee = $employees | Get-Random -Count 1
        $shift = @{
            date = $date
            employee_id = $patrolEmployee[0]
            task_type = "patrol"
            start_time = "14:00"
            end_time = "14:30"
            status = "scheduled"
        }
        
        try {
            $body = $shift | ConvertTo-Json -Depth 3
            Invoke-RestMethod -Uri "$API_BASE/shifts" -Method POST -ContentType "application/json" -Body $body
        } catch {
            Write-Host "✗ 見回りシフト登録エラー: $date" -ForegroundColor Red
        }
    }
    
    Write-Host "✓ $month のシフトデータを登録しました" -ForegroundColor Green
}

Write-Host "追加サンプルデータ登録完了！" -ForegroundColor Green