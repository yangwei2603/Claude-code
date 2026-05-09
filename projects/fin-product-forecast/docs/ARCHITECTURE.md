# 系统架构

## 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    用户层                             │
│         浏览器（fx_system 前端） / 飞书推送            │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / 消息
┌──────────────────────▼──────────────────────────────┐
│                   服务层 (fx_system)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  data_sources │  │  modeling.py │  │  server.py │ │
│  │  数据采集模块  │  │   预测建模    │  │  HTTP API  │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                │         │
│  ┌──────▼─────────────────▼────────────────▼──────┐ │
│  │              SQLite 数据库 (fx_data.sqlite3)     │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
                        ▲
┌───────────────────────┼─────────────────────────────┐
│                   数据源层                            │
│  FRED（美联储） / ECB（欧央行）/ Bank of Canada       │
└─────────────────────────────────────────────────────┘
```

## 模块职责

### fx_system/ — 核心预测引擎

| 文件 | 职责 |
|------|------|
| `backend/server.py` | HTTP 服务，路由 /api/ingest、/api/train、/api/rates |
| `backend/data_sources.py` | 多源数据拉取（FRED、ECB、Bank of Canada） |
| `backend/modeling.py` | 预测模型：线性回归趋势预测 + KMeans 市场状态聚类 |
| `frontend/index.html` | 浏览器端行情可视化 |
| `fx_data.sqlite3` | 存储历史行情数据 |

### tools/ — 量化工具集

| 文件 | 职责 |
|------|------|
| `fx_quant_strategy.py` | 量化回测脚本：波动率目标仓位 + 杠杆管理 |
| `fx_code_audit.py` | 代码质量与安全审计 |
| `desktop_organizer.py` | 桌面文件自动整理工具 |

### agents/ — AI Agent 配置

- `agents/main/`：主 Agent 工作空间（auth-profiles.json、models.json）
- `agents/main/sessions/`：多轮会话历史（JSONL 格式）
- 支持 main / coder / finops-expert 多 Agent 协作

### workflows/ — 工作流编排

- `workflows/agent-skill-workflow.json`：工作流定义
- `cron/jobs.json`：定时任务配置
- 支持飞书（Feishu）消息推送集成

## 数据流向

```
外部数据源（FRED/ECB/BOC）
        ↓
data_sources.py（HTTP 请求）
        ↓
SQLite 数据库（fx_data.sqlite3）
        ↓
modeling.py（训练 + 预测）
        ↓
server.py（API 输出）
        ↓
frontend（可视化）/ 飞书（预警推送）
```

## 技术栈

- **后端**：Python 原生 HTTP（无框架依赖）
- **数据库**：SQLite3
- **机器学习**：scikit-learn（KMeans）、numpy、pandas
- **前端**：原生 HTML + JavaScript
- **消息推送**：飞书 Webhook
- **Agent**：DeepSeek API（cherry-deepseek/deepseek-chat）
