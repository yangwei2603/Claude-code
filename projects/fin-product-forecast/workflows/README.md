# Agent-Skill 工作流使用指南

## 概述

本项目采用 **Plan → Explore → Implement → Review → Simplify** 闭环开发流程。

## 工作流阶段

### 1. Plan (规划)
**触发**: 复杂任务开始前
**命令**: `/plan` 或进入 Plan Mode

```bash
# 示例：规划新功能
/plan
```

### 2. Explore (探索)
**触发**: 需要理解代码库时
**命令**: 使用 Explore Agent

```bash
# 研究 fx_system/backend 架构
/research fx_system/backend
```

### 3. Implement (实现)
**触发**: 编码阶段
**操作**: 直接编写代码

### 4. Review (审查)
**触发**: 代码提交后
**命令**: `/review`

```bash
# 代码审查
/review

# 安全审查
/security-review
```

### 5. Simplify (优化)
**触发**: 功能完成后
**命令**: `/simplify`

```bash
# 代码优化
/simplify
```

## 自动化配置

### 定时任务
使用 `/loop` 设置定时检查：

```bash
# 每10分钟检查一次 PR 状态
/loop 10m /babysit-prs

# 每小时检查一次部署状态
/loop 60m /check-deploy
```

### 调度任务
使用 `/cron` 设置定时任务：

```bash
# 每天早上9点运行代码审计
/cron "0 9 * * 1-5" /code-audit
```

## 快速开始

```bash
# 1. 进入项目目录
cd /Users/fox/GitHub/openclaw-home-pc

# 2. 初始化项目 (如需)
/init

# 3. 开始工作流
/plan  # 规划任务

# 4. 实施
/implement

# 5. 审查
/review

# 6. 优化
/simplify
```

## 相关文件

- `workflows/agent-skill-workflow.json` - 工作流配置
- `CLAUDE.md` - 项目文档
- `openclaw.json` - Agent 配置
