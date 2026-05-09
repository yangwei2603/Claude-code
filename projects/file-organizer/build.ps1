# ==============================================================================
# file-organizer-agent 构建脚本 - Windows (Onefile 便携模式)
# 使用 PowerShell
# ==============================================================================

param(
    [switch]$Clean,
    [switch]$DepsOnly,
    [switch]$All
)

$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ProjectRoot = $PSScriptRoot

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $colors = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "White" = [ConsoleColor]::White
    }
    Write-Host "[Windows] $Message" -ForegroundColor $colors[$Color]
}

# 创建输出目录
if (-not (Test-Path "$ProjectRoot\dist")) {
    New-Item -ItemType Directory -Path "$ProjectRoot\dist" | Out-Null
}

# 清理之前的构建
function Clean-Build {
    Write-ColorOutput "清理之前的构建..." "Yellow"

    $itemsToRemove = @("build", "dist", "*.spec", "*.pyc")
    foreach ($item in $itemsToRemove) {
        Get-ChildItem -Path $ProjectRoot -Filter $item -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }

    Get-ChildItem -Path $ProjectRoot -Directory -Filter "__pycache__" -Recurse |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-ColorOutput "清理完成" "Green"
}

# 安装依赖
function Install-Deps {
    Write-ColorOutput "安装构建依赖..." "Yellow"
    pip install pyinstaller flask flask-cors pyyaml python-docx PyPDF2 openpyxl python-pptx striprtf
    Write-ColorOutput "依赖安装完成" "Green"
}

# 执行构建
function Build-App {
    Write-ColorOutput "开始构建 Windows 版本 (Onefile)..." "Green"

    # 使用 spec 文件构建 Onefile 模式
    pyinstaller file-organizer-agent.spec --noconfirm

    # 创建 zip 包（包含可执行文件和默认配置）
    $exePath = "$ProjectRoot\dist\FileOrganizerAgent.exe"
    if (Test-Path $exePath) {
        $packDir = "$ProjectRoot\dist\FileOrganizerAgent-win"
        New-Item -ItemType Directory -Path $packDir -Force | Out-Null
        Copy-Item $exePath "$packDir\"
        # 创建默认配置文件（首次运行需要）
        "{}" | Out-File -FilePath "$packDir\config.json" -Encoding UTF8
        $zipPath = "$ProjectRoot\dist\FileOrganizerAgent-win-${Timestamp}.zip"
        Compress-Archive -Path "$packDir\*" -DestinationPath $zipPath -Force
        Remove-Item -Path $packDir -Recurse -Force
        Write-ColorOutput "Windows 构建完成: $zipPath" "Green"
        Write-ColorOutput "直接运行: .\dist\FileOrganizerAgent.exe --web" "Green"
    } else {
        Write-ColorOutput "错误: 未找到生成的可执行文件" "Red"
    }
}

# 主逻辑
if ($Clean) {
    Clean-Build
} elseif ($DepsOnly) {
    Install-Deps
} elseif ($All) {
    Clean-Build
    Install-Deps
    Build-App
} else {
    Build-App
}
