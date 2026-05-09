#!/bin/bash
# ==============================================================================
# file-organizer-agent 构建脚本
# 支持 macOS 和 Windows (通过 PyInstaller) - Onefile 便携模式
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 平台检测
PLATFORM=$(uname -s)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo_color() {
    echo -e "${2}[${PLATFORM}] ${1}${NC}"
}

# 创建输出目录
mkdir -p dist

# 安装依赖
install_deps() {
    echo_color "安装构建依赖..." "$YELLOW"
    pip install pyinstaller flask flask-cors pyyaml python-docx PyPDF2 openpyxl python-pptx striprtf
}

# 清理之前的构建
clean() {
    echo_color "清理之前的构建..." "$YELLOW"
    rm -rf build dist *.spec
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
}

# 构建 macOS
build_macos() {
    echo_color "开始构建 macOS 版本 (Onefile)..." "$GREEN"

    # Onefile 模式会在 dist/ 下生成单一可执行文件
    pyinstaller file-organizer-agent.spec --noconfirm

    # macOS 上给可执行文件添加执行权限
    if [ -f "dist/FileOrganizerAgent" ]; then
        chmod +x "dist/FileOrganizerAgent"
    fi

    # 创建 zip 包（包含可执行文件和默认配置）
    cd dist
    if [ -f "FileOrganizerAgent" ]; then
        # 创建目录结构用于打包
        mkdir -p "FileOrganizerAgent-macos"
        cp "FileOrganizerAgent" "FileOrganizerAgent-macos/"
        # 创建默认配置文件（首次运行需要）
        echo '{}' > "FileOrganizerAgent-macos/config.json"
        zip -r "FileOrganizerAgent-macos-${TIMESTAMP}.zip" "FileOrganizerAgent-macos"
        rm -rf "FileOrganizerAgent-macos"
        echo_color "macOS 构建完成: dist/FileOrganizerAgent-macos-${TIMESTAMP}.zip" "$GREEN"
        echo_color "直接运行: ./dist/FileOrganizerAgent --web" "$GREEN"
    fi
    cd ..
}

# 构建函数
build() {
    case "$PLATFORM" in
        Darwin)
            build_macos
            ;;
        Linux)
            echo_color "Linux 构建暂不支持（需要 wine）" "$YELLOW"
            ;;
        MINGW*|CYGWIN*|MSYS*)
            echo_color "开始构建 Windows 版本 (Onefile)..." "$GREEN"
            pyinstaller file-organizer-agent.spec --noconfirm

            cd dist
            if [ -f "FileOrganizerAgent.exe" ]; then
                mkdir -p "FileOrganizerAgent-win"
                cp "FileOrganizerAgent.exe" "FileOrganizerAgent-win/"
                echo {} > "FileOrganizerAgent-win\config.json"
                powershell -Command "Compress-Archive -Path 'FileOrganizerAgent-win\*' -DestinationPath 'FileOrganizerAgent-win-${TIMESTAMP}.zip' -Force"
                rm -rf "FileOrganizerAgent-win"
                echo_color "Windows 构建完成: dist/FileOrganizerAgent-win-${TIMESTAMP}.zip" "$GREEN"
                echo_color "直接运行: .\dist\FileOrganizerAgent.exe --web" "$GREEN"
            fi
            cd ..
            ;;
        *)
            echo_color "未知平台: $PLATFORM" "$RED"
            exit 1
            ;;
    esac
}

# 显示用法
usage() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  clean     清理之前的构建文件"
    echo "  deps      仅安装依赖"
    echo "  build     执行构建（默认）"
    echo "  all       清理 + 安装依赖 + 构建"
    echo ""
    echo "示例:"
    echo "  $0 all      # 执行完整构建流程"
    echo "  $0 clean     # 仅清理"
    echo "  $0 build     # 仅构建"
    echo ""
    echo "输出:"
    echo "  macOS: dist/FileOrganizerAgent-macos-YYYYMMDD_HHMMSS.zip"
    echo "  Windows: dist/FileOrganizerAgent-win-YYYYMMDD_HHMMSS.zip"
}

# 主逻辑
case "${1:-build}" in
    clean)
        clean
        ;;
    deps)
        install_deps
        ;;
    build)
        build
        ;;
    all)
        clean
        install_deps
        build
        ;;
    *)
        usage
        exit 1
        ;;
esac
