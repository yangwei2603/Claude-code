#!/bin/bash
# 需求池管理系统启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
LOGFILE="${PROJECT_DIR}/logs/app.log"

# 创建日志目录
mkdir -p "${PROJECT_DIR}/logs"

echo "[$(date)] 启动需求池管理系统，端口 ${PORT}..."

# 使用 hermes venv 中的 python
PYTHON="/Users/fox/Hermes/.venv/bin/python3"

# 启动 uvicorn（后台运行，写日志）
nohup "${PYTHON}" -m uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --access-log \
    > "${LOGFILE}" 2>&1 &

echo $! > "${PROJECT_DIR}/app.pid"
echo "[$(date)] 已启动，PID: $(cat ${PROJECT_DIR}/app.pid)，日志: ${LOGFILE}"
