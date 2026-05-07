---
name: financial-analysis
description: >
  通用财务数据分析。当用户提到：供应商分析、航司成本结构、报表发布清单分析、
  多维成本钻取、竞争情报、宏观经济关联、财务BI、指标下钻、环比同比分析、
  数据治理分析、数据资产分析、供应商合作评估、发票与付款匹配分析时触发。
triggers:
  - 供应商分析
  - 成本多维分析
  - 竞争情报
  - 宏观财务关联
  - 报表发布清单
  - 财务数据钻取
  - 数据资产分析
  - 航司成本结构
agent_created: true
version: 1.0
created: 2026-05-07
---

# 财务数据分析 Skill

## 能力范围

本 Skill 覆盖春秋航空财务部的通用数据分析场景，包括：
成本费用多维分析、供应商合作评估、报表发布行为分析、竞争环境关联分析。

**Phase 1 核心能力（已就绪）**
**Phase 2 能力（MCP 集成，详见 MCP 集成规范）**

---

## 一、核心分析维度

### 1. 成本费用多维分析

**分析框架**
| 维度 | 说明 | 常用分类 |
|------|------|----------|
| 科目维度 | 利润表科目（成本/费用） | 航油、维修、人力、折旧、销售、管理 |
| 部门维度 | 费用归属部门 | 按部门穿透 |
| 时间维度 | 月度/季度/年度趋势 | 环比、同比 |
| 供应商维度 | 费用对应的供应商 | 关联方 vs 非关联方 |
| 合同维度 | 合同金额 vs 执行金额 | 执行进度 |

**数据来源**
- SQL 视图：`v_clm_contract_dw`（用友 YonBIP 合同系统）
- 库：`yonbip_clm_contract`
- 关键字段：contract_amount / paid_amount / invoice_amount / vendor_name / vendor_supply_type

**分析脚本规范**
```
<主题>-<YYYYMMDD>/
├── raw/                 # 原始导出 CSV
├── cleaned_*.csv        # 清洗后数据
├── charts/              # 图表 PNG（dpi=150）
├── analysis.py          # 分析脚本
└── report_<YYYYMMDD>.md  # 分析报告
```

**分析脚本结构（标准模板）**
```python
# -*- coding: utf-8 -*-
"""
<分析主题>
日期：YYYY-MM-DD
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

# === 配置 ===
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
OUTPUT_DIR = 'charts'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 数据加载 ===
# TODO: 从 SQL 导出或 CSV 导入

# === 清洗 ===
# TODO: 去重/异常值处理

# === 分析 ===
# TODO: 分组聚合

# === 可视化 ===
# TODO: matplotlib 图表

# === 报告输出 ===
# TODO: 生成 Markdown 报告
```

### 2. 供应商分析

**分析维度**
| 分析类型 | 说明 | 关键指标 |
|----------|------|----------|
| 合作规模 | 合同金额排名 | 合同金额合计、合同数量 |
| 执行健康度 | 付款进度 vs 合同进度 | 付款率、欠票率 |
| 供应类型分布 | 关联方 vs 非关联方 | 供应类型占比 |
| 行业分布 | 按行业分类统计 | 合同数量、金额占比 |
| 合作稳定性 | 跨期合同数量 | 年度合同数、平均合同年限 |

**数据获取**
- 通过 `v_clm_contract_dw` 视图的 vendor_* 字段
- 供应商主数据关联：`iuap_apdoc_coredoc.aa_vendor`

**分析逻辑**
```python
# 供应商分析关键指标
df.groupby('vendor_name').agg(
    contract_count=('contract_id', 'count'),
    total_amount=('contract_amount', 'sum'),
    paid_amount=('paid_amount', 'sum'),
    invoice_amount=('invoice_amount', 'sum')
).assign(
    payment_rate=lambda x: x['paid_amount'] / x['total_amount'],
    invoice_gap=lambda x: x['total_amount'] - x['invoice_amount']
).sort_values('total_amount', ascending=False)
```

### 3. 报表发布清单分析

**分析维度**
| 维度 | 说明 |
|------|------|
| 发布时效 | 计划 vs 实际发布时间差 |
| 发布频率 | 各报表发布周期 |
| 责任部门 | 按部门统计发布合规率 |
| 历史趋势 | 发布准时率变化 |

### 4. 竞争情报与宏观经济关联

**竞争情报数据获取**
- 优先信源：年报、季报、交易所公告
- 航司数据库：六大航司股票代码（601111.SH / 600115.SH / 600029.SH / 600221.SH / 601021.SH / 603885.SH）

**宏观经济关联框架**
| 宏观因子 | 航司受影响渠道 | 数据来源 |
|----------|---------------|----------|
| 航油价格 | 成本端（占比 27-29%）| EIA / Brent |
| 人民币汇率 | 美元负债（汇兑损益）| 美元/人民币 |
| CPI/PPI | 成本传导 | 国家统计局 |
| 旅客周转量 | 需求端 | 民航局月报 |

**竞争情报分析流程**
1. 抓取竞对年报关键指标（营收/CASK/客座率）
2. 对比春秋航空同期数据
3. 识别差距与机会
4. 输出竞争情报摘要

---

## 二、MCP 集成规范（Phase 2）

### 2.1 neodata-financial-search 集成

**用途**：通过自然语言查询航司财务数据、宏观经济指标

**触发条件**：用户问及以下内容时加载
- "查一下 XX 航司的营收/净利润/CASK"
- "航油价格走势"
- "人民币汇率对春秋的影响"
- 任意财务数据查询

**集成方式**
```json
{
  "mcpServers": {
    "neodata-financial-search": {
      "command": "npx",
      "args": ["@neodata/mcp-financial-search@latest"]
    }
  }
}
```

**已接入**：直接调用 `neodata-financial-search` skill

### 2.2 MCP 集成检查清单

在引入新 MCP 时，评估以下维度：

| 评估项 | 说明 | 权重 |
|--------|------|------|
| 数据覆盖 | 能否覆盖春秋核心 KPI | 高 |
| 更新频率 | 实时 vs 日/周/月 | 高 |
| 权限要求 | 是否需要额外凭证 | 中 |
| 调用成本 | 免费 vs 按次付费 | 中 |
| 落地可行性 | 能否输出可操作洞察 | 高 |

---

## 三、数据字典位置

**Obsidian Vault 路径**（优先参考）
```
/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/
├── 合同系统数据字典/
├── 税务系统数据字典/
├── 财务共享数据字典/
└── 资金系统数据字典/
```

---

## 四、输出规范

### 分析报告模板
```markdown
# <分析主题>

**分析日期**：YYYY-MM-DD
**数据来源**：<原始数据文件名>
**分析人**：数字化办公室-AI

---

## 执行摘要
（1-2句话核心结论）

## 关键发现
- **发现1**: ...
- **发现2**: ...

## 详细分析
### 维度1
（图表 + 解读）

### 维度2
（图表 + 解读）

## 建议与风险
| 类型 | 内容 | 影响 |
|------|------|------|
| 机会 | ... | ... |
| 风险 | ... | ... |

---

**报告信息**
- 数据来源：<原始数据文件名>
- 分析模型：Qwen3-VL-235B-A22B-Instruct-AWQ（本地私有化部署）
- 分析人：数字化办公室-AI
- 分析日期：YYYY-MM-DD
```

---

## 五、相关 Skill

| Skill | 用途 |
|-------|------|
| `sql-generation` | SQL 查询生成、数据字典查询 |
| `neodata-financial-search` | 自然语言金融数据查询 |
| `airline-analysis` | 航司专项（年报对比/CASK分解）|
| `pptx` | 将分析报告转化为演示文稿 |
| `xlsx` | 原始数据处理 |

---

## 六、工作流总览

```
用户需求
  │
  ├─► 明确分析维度 ──► SQL查询（sql-generation skill）
  │                           │
  │                    数据导出到 raw/*.csv
  │                           │
  ├─► 成本/供应商分析 ──► analysis.py 清洗 + 分析
  │                           │
  │                    生成 charts/*.png
  │                           │
  └─► 生成报告 ─────────► report_*.md
                                │
                         输出到用户 / Obsidian Vault
```
