# CLAUDE.md

本文件为 Claude Code 工作时的全局配置指南。

## 项目概述

`fin-product-forecast`（金融产品预测预警系统）是为交易决策提供科学依据的量化研究与预警平台，支持汇率、商品、股票等金融产品的价格预测与风险预警。

## 核心能力

- **多源数据采集**：FRED、ECB、Bank of Canada 官方金融数据
- **预测建模**：监督学习（线性回归趋势预测）+ 无监督学习（KMeans 市场状态聚类）
- **量化回测**：波动率目标仓位、杠杆管理、交易成本建模
- **预警机制**：自定义阈值触发、飞书消息推送
- **报告输出**：可追溯的模型评估与策略分析

## 系统架构

```
fin-product-forecast/
├── fx_system/              # 汇率预测核心引擎
│   ├── backend/            # HTTP 服务（server.py + data_sources.py + modeling.py）
│   ├── frontend/           # 浏览器可视化
│   └── fx_data.sqlite3    # 历史行情数据库
├── tools/                  # 量化工具集
│   ├── fx_quant_strategy.py   # 波动率目标仓位量化回测
│   ├── fx_code_audit.py       # 代码质量审计
│   └── desktop_organizer.py   # 桌面文件整理
├── docs/                   # 项目文档
│   ├── PROJECT.md          # 项目整体说明
│   ├── ARCHITECTURE.md     # 系统架构
│   ├── API.md              # fx_system HTTP 接口文档
│   ├── QUANT_STRATEGY.md   # 量化策略说明
│   ├── GUIDE.md            # 快速入门
│   └── REPORTS/            # 历史报告
├── agents/                 # AI Agent 配置
│   └── main/               # 主 Agent 工作空间
├── workflows/              # 工作流编排
├── docs/                   # 项目文档
└── fin-product-forecast.json  # 平台配置文件
```

## 快速启动

```bash
# 启动预测服务
cd fx_system/backend
python3 server.py
# 访问 http://127.0.0.1:8010
```

## API 快速参考

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ingest` | POST | 拉取官方金融数据 |
| `/api/train` | POST | 训练模型并预测 |
| `/api/import-csv` | POST | 离线 CSV 导入 |
| `/api/rates` | GET | 查询行情 |
| `/api/model/latest` | GET | 查看最新模型参数 |

详见 `docs/API.md`。

## 量化回测

```bash
python3 tools/fx_quant_strategy.py \
  --csv reports/sample.csv \
  --out reports/output.csv \
  --lookback 20 \
  --vol-window 30 \
  --target-vol 0.10 \
  --max-leverage 2.0
```

详见 `docs/QUANT_STRATEGY.md`。

## 开发流程

闭环开发流程：**数据采集 → 建模 → 回测 → 报告 → 预警**

1. 数据采集：确认数据源可用性（`docs/API.md`）
2. 建模分析：使用 `/api/train` 训练模型
3. 回测验证：使用 `tools/fx_quant_strategy.py` 进行回测
4. 报告输出：参考 `docs/REPORTS/` 中的历史报告格式
5. 预警配置：编辑 `fin-product-forecast.json` 中的飞书配置

## 配置说明

- **fin-product-forecast.json**：平台配置（模型提供商、Agent 定义、飞书频道）
- **agents/main/agent/**：Agent 认证与模型配置
- **workflows/agent-skill-workflow.json**：工作流定义

## 重要提示

⚠️ 本系统用于**研究与决策支持**，实盘接入前必须经过：
1. 3-5 年历史数据 walk-forward 回测
2. 模拟盘 2-4 周验证
3. 极端行情压力测试
4. 仓位上限与回撤熔断机制就位
