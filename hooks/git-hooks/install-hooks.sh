#!/usr/bin/env bash
# ================================================================
# install-hooks.sh — 一键安装所有 Git Hooks
# 使用方法: bash hooks/git-hooks/install-hooks.sh
# ================================================================

HOOKS_DIR="$(git rev-parse --toplevel)/.git/hooks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}📦 安装 Git Hooks...${NC}"

for hook in pre-commit commit-msg pre-push; do
  src="$SCRIPT_DIR/$hook"
  dst="$HOOKS_DIR/$hook"
  
  if [ -f "$src" ]; then
    cp "$src" "$dst"
    chmod +x "$dst"
    echo -e "  ${GREEN}✓ 已安装: $hook${NC}"
  fi
done

echo -e "${GREEN}🎉 所有 Git Hooks 安装完成！${NC}"
