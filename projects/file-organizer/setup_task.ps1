# setup_task.ps1
# 数字化转型办公室 - 文件整理 Agent 安装脚本
# 功能：在 Windows 任务计划程序中创建定时任务
# 用法：以管理员身份运行此脚本
# 支持跨机器部署：复制整个 file-organizer-agent 目录到目标机器，修改 config.json，再运行本脚本

param(
    [string]$AgentDir    = $PSScriptRoot,         # Agent 目录（默认脚本所在目录）
    [string]$PythonPath  = "python",              # Python 解释器路径，如需指定请传入完整路径
    [string]$TaskName    = "DigitalOfficeOrganizer",
    [string]$Schedule    = "DAILY",               # DAILY / HOURLY / WEEKLY
    [int]   $Hour        = 8,                     # 每天几点执行（DAILY 生效）
    [int]   $IntervalMin = 60,                    # 每几分钟执行一次（HOURLY 生效）
    [string]$DayOfWeek   = "MON",                 # 星期几（WEEKLY 生效）
    [switch]$Remove                               # 传入 -Remove 则删除任务
)

$RunScript = Join-Path $AgentDir "run.py"
$LogDir    = Join-Path $AgentDir "logs"

# 确保日志目录存在
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# ---------- 删除任务 ----------
if ($Remove) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] 已删除任务: $TaskName"
    } else {
        Write-Host "[INFO] 任务不存在: $TaskName"
    }
    exit 0
}

# ---------- 检查 Python ----------
try {
    $pyVersion = & $PythonPath --version 2>&1
    Write-Host "[OK] Python: $pyVersion"
} catch {
    Write-Host "[ERROR] 找不到 Python，请安装 Python 3.8+ 或通过 -PythonPath 指定路径"
    exit 1
}

# ---------- 检查脚本 ----------
if (-not (Test-Path $RunScript)) {
    Write-Host "[ERROR] 找不到 run.py: $RunScript"
    exit 1
}

# ---------- 构建触发器 ----------
$trigger = $null
switch ($Schedule.ToUpper()) {
    "DAILY" {
        $trigger = New-ScheduledTaskTrigger -Daily -At "${Hour}:00"
        Write-Host "[INFO] 调度: 每天 ${Hour}:00"
    }
    "HOURLY" {
        # 每 N 分钟重复一次（通过 RepetitionInterval 实现）
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes $IntervalMin) -RepetitionDuration ([System.TimeSpan]::MaxValue)
        Write-Host "[INFO] 调度: 每 ${IntervalMin} 分钟"
    }
    "WEEKLY" {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At "${Hour}:00"
        Write-Host "[INFO] 调度: 每周 $DayOfWeek ${Hour}:00"
    }
    default {
        Write-Host "[ERROR] 不支持的调度类型: $Schedule（可选: DAILY / HOURLY / WEEKLY）"
        exit 1
    }
}

# ---------- 命令行参数 ----------
# 任务计划执行：增量模式 + 实际执行
$taskArgs = "`"$RunScript`" --execute --days 1"

# ---------- 操作（Action）----------
$action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument $taskArgs `
    -WorkingDirectory $AgentDir

# ---------- 运行设置 ----------
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew

# ---------- 主体（Principal）----------
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# ---------- 注册任务 ----------
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[INFO] 任务已存在，正在更新..."
    Set-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings
} else {
    Register-ScheduledTask `
        -TaskName  $TaskName `
        -Trigger   $trigger `
        -Action    $action `
        -Settings  $settings `
        -Principal $principal `
        -Description "数字化转型办公室文件自动整理 - Agent" | Out-Null
}

Write-Host ""
Write-Host "============================================"
Write-Host "  任务安装成功！"
Write-Host "  任务名: $TaskName"
Write-Host "  脚本  : $RunScript"
Write-Host "  Python: $PythonPath"
Write-Host "============================================"
Write-Host ""
Write-Host "管理命令："
Write-Host "  立即运行 : Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  查看状态 : Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  删除任务 : .\setup_task.ps1 -Remove"
Write-Host ""
Write-Host "跨机器部署步骤："
Write-Host "  1. 复制整个 file-organizer-agent 目录到目标机器"
Write-Host "  2. 修改 config.json 中的 source_dir 等路径"
Write-Host "  3. 以管理员身份运行 setup_task.ps1"
