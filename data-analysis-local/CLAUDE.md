# CLAUDE.md — data-analysis-local 工作区

> 本地数据分析工作区，用于春秋航空财务部成本分析、供应商合同分析、财务报表等数据分析任务。
> 详细分析流程参见 `../skills/domain/data-analysis/SKILL.md`。

---

## 目录结构

```
data-analysis-local/
├── <主题>-<YYYYMMDD>/                 # 每次分析任务独立目录
│   ├── raw/                          # 原始数据文件
│   ├── cleaned_*.csv                 # 清洗后数据
│   ├── analyze_*.py                  # 分析脚本
│   ├── charts/                       # 可视化图表（PNG, dpi=150）
│   └── report_*.md                   # 分析报告
├── CLAUDE.md                         # 本文件
└── README.md                         # 工作区概览
```

---

## 本地模型约束（硬约束 — 无例外）

涉及内部/私有/财务数据的分析任务**必须**使用本地大模型，不得使用云端 API。

### 触发关键词

以下任一关键词出现时，强制进入本地模型模式：

本地模型、本地数据、内部数据、私有化、涉密、财务数据、航班收益、供应商、成本、合同

### 调用方式

```python
# 通过工作区根目录的 llm_client 调用
# llm_client 位置：../agents/orchestration/llm_client.py
from agents.orchestration.llm_client import llm

response = llm.chat(prompt, model="local")
```

> **注意**：运行分析脚本时需确保 Python path 包含工作区根目录（`Claude Code/`），
> 或在脚本中通过 `sys.path.append` 添加。

### 严格禁止

- ❌ 手工编写分析结论（摘要、发现、风险、建议等）
- ❌ 复制粘贴旧报告内容作为新分析结论
- ❌ 将内部财务数据发送到云端 API
- ❌ 本地模型不可达时尝试调用云端模型（直接终止任务）

分析内容**必须**由本地模型生成，人工仅负责审核和调整。

---

## 本地模型调用失败处理

| 情况 | 处理方式 |
|------|---------|
| 本地模型不可达 | 直接终止任务，不尝试云端模型 |
| API key 未配置 | 立即停止，等待用户配置 |
| 超时/报错 | 记录错误，不回退到云端 |

**硬约束**：任何涉及内部/私有/财务数据的分析任务，必须使用本地大模型。本地模型不可用时，任务终止，不得降级到云端。

---

## 报告输出规范

### 输出格式（必须询问用户）

生成报告前，**必须先询问用户**选择输出格式：

| 格式 | 说明 |
|------|------|
| Markdown | 直接保存 `.md` 文件 |
| PDF | `pandoc -s --pdf-engine=xelatex report.md -o report.pdf` |
| Word | `pandoc -s report.md -o report.docx` |

### ⭐ 交互式 HTML 报告（首选，优先推荐）

**必须作为所有数据分析报告的标准输出格式**，要求：

#### 核心要求

1. **数据嵌入**：所有数据必须内嵌到 HTML 中（JSON 直接写入 JS 变量），禁止外部依赖文件
2. **跨平台兼容**：纯浏览器运行，Windows / macOS / Linux 均可直接双击打开，无需服务器
3. **Tab 导航**：动态调整，根据分析内容定制，始终包含：
   - **总览**（KPI卡片 + 风险预警 + 分布图）
   - **多维度下钻**（按分析主题切分，如按月/按部门/按创建人/按状态等维度，支持 drill-down）
   - **明细**（可筛选/搜索的完整数据表，支持行展开查看完整字段）
   > 注：Tab 名称和数量随分析内容调整，如"供应商分析"可能包含"供应商排名/执行健康度/行业分布/明细"，但总览+维度下钻+明细三层结构不变。
4. **行展开功能**：每行数据可点击展开，查看完整字段（业务现状、需求描述、期望效果等）
5. **筛选与搜索**：支持多条件过滤和全文搜索

#### 技术规范

```
生成流程：
1. 解析原始数据 → Python dict
2. 生成 data.json（含 records + stats）
3. 生成 index.html（含完整 JS + 内嵌数据）
4. 打包为独立 .html（数据内嵌，不依赖外部文件）

文件名规范：
- 服务器版：index.html（需同目录 data.json）
- 独立版：<主题>分析报告-独立版.html（数据全内嵌）
```

#### HTML 交互规范（必须实现）

| 功能 | 实现要求 |
|------|---------|
| Tab 切换 | 点击切换，内容区显示/隐藏，无刷新 |
| 行展开 | 点击 ▶ 按钮展开详情行，显示业务现状/需求描述/期望效果 |
| 排序 | 点击列头排序，↑/↓ 指示方向 |
| 筛选 | 下拉选择 + 条件组合，支持多字段同时过滤 |
| 搜索 | 实时全文搜索（编号 + 名称），延迟 300ms |
| KPI 卡片 | 显示核心指标（总数/激活/积压/过期） |
| 风险预警 | 高/中/低三级，用颜色区分（红/橙/绿） |
| 柱状图/饼图 | CSS 实现，不得依赖外部图表库 |
| 响应式布局 | 支持 1280px 及以上屏幕 |

#### 独立运行检查清单

- [ ] HTML 文件独立运行，无外部 fetch dependency
- [ ] 数据全部内嵌在 JS 变量中
- [ ] 双击在 Chrome/Edge/Safari 中均可打开
- [ ] 无 404 资源请求

### 报告头格式

每份报告必须包含以下信息：

```
作者：数字化办公室-AI分析师
日期：YYYY-MM-DD
数据来源：<原始数据文件名>
分析模型：报告底部注明使用的本地模型名称
```

### Obsidian 同步

报告生成后，询问用户是否需要同步到 Obsidian。

同步目标路径（可按实际环境调整）：

```
~/Documents/Obsidian Vault/自动笔记/04-创新应用/02-智能分析/<主题>/
```

---

## 输出目录规范

- 固定模式：`data-analysis-local/<主题>-<YYYYMMDD>/`
- 每次分析任务创建新目录，**不得复用旧目录**
- SQL 查询文件放在分析任务目录下，不放在工作区根目录

---

## 数据字典

SQL 数据字典位置（可按实际环境调整）：

```
~/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/
├── 合同系统数据字典/
├── 税务系统数据字典/
├── 财务共享数据字典/
└── 资金系统数据字典/
```

---

## Skills 参考

Skills 位于工作区根目录的 `skills/domain/` 下，使用相对路径引用：

| Skill | 路径 | 用途 |
|-------|------|------|
| `data-analysis` | `../skills/domain/data-analysis/` | 通用数据分析流程（清洗→EDA→建模→可视化→报告） |
| `financial-analysis` | `../skills/domain/financial-analysis/` | 成本分析、供应商分析、竞争情报等等 |
| `sql-generation` | `../skills/domain/sql-generation/` | SQL 查询生成（合同/税务/共享/资金） |
| `machine-learning` | `../skills/domain/machine-learning/` | 机器学习建模与预测 |

---

## 数据源策略

数据源由每次分析任务动态决定，不在工作区配置中硬编码固定文件路径。
每次任务的数据来源记录在各自的分析目录 `data-analysis-local/<主题>-<YYYYMMDD>/` 中。

### 本地 SQLite 数据库

主要数据库路径：`/Users/fox/DB/`

**数据库文件说明**：

| 文件 | 用途 |
|------|------|
| `analysis.db` | 个人上传分析数据和中间结果 |
| `analysis_temp.db` | 临时分析数据（237MB，含大量历史数据） |
| `external_data.db` | **外部数据**（航司及官方公开数据，覆盖11大类数据源） |

**external_data.db 数据范围**（详见 Obsidian：`外部数据源清单.md`）：

| 数据类别 | 来源示例 | 核心表 |
|---------|---------|-------|
| 国内政府及监管机构 | CAAC、NBS、MOT、SAFE、NDRC | `civil_aviation_stats`、`gov_public_data` |
| A股上市航司信披 | 国航/南航/东航/海航/春秋/吉祥/华夏 | `airline_annual_report` |
| 行业运营数据 | CAAC运输生产统计、机场吞吐量 | `airline_monthly_ops`、`airport_throughput_monthly` |
| 成本与燃油数据 | EIA航油价格、国家发改委 | `fuel_price_monthly`、`airline_cost_detail` |
| 汇率数据 | 国家外汇管理局 SAFE | `exchange_rate_daily` |
| 国际航司对标 | Delta/United/Southwest/Ryanair/Singapore | `competitor_benchmark` |
| 机场数据 | CAAC机场统计、ACI全球排名 | `airport_throughput_monthly` |
| 机队与交付数据 | Boeing、Airbus、COMAC | `aircraft_delivery_plan` |
| 国际航线数据 | CAAC国际航线、OAG | `china_intl_route_stats`、`route_capacity_weekly` |
| 行业对标指标 | CASK/RASK/客座率/运力 | `v_airline_core_metrics`、`v_industry_trend` |

**常用查询示例**：

```python
import sqlite3
import pandas as pd

# 连接外部数据库
conn = sqlite3.connect('/Users/fox/DB/external_data.db')

# 航司年报数据
df = pd.read_sql("""
    SELECT airline_name, report_year, revenue, net_profit, 
           passenger_load_factor, fleet_size
    FROM airline_annual_report
    WHERE airline_name IN ('吉祥航空', '春秋航空')
    ORDER BY airline_name, report_year
""", conn)

# 航油价格走势
fuel_df = pd.read_sql("SELECT * FROM fuel_price_monthly ORDER BY month DESC LIMIT 12", conn)

# 汇率数据
fx_df = pd.read_sql("SELECT * FROM exchange_rate_daily ORDER BY date DESC LIMIT 30", conn)

conn.close()
```

**约定**：
- `analysis.db` 用于**内部数据分析**（含春秋航空内部数据和用户上传数据），从中输出的数据受本地模型约束
- 外部数据**全部从 `/Users/fox/DB/external_data.db` 读取**，如果没有数据通过外网采集
- 所有从 `analysis.db` 流出的分析结果**必须使用本地大模型**，禁止发送到云端
- 使用 `with sqlite3.connect(db_path) as conn:` 上下文管理器自动关闭连接

### 其他数据源

| 来源类型 | 操作 |
|---------|------|
| 内部数据（Excel/CSV） | `pd.read_csv()` / `pd.read_excel()`，文件路径记录在分析目录或者用户指定路径 |
| 内部数据（结构化） | `/Users/fox/DB/analysis.db`，按本地模型约束处理 |
| 外部数据 | `/Users/fox/DB/external_data.db`（见上节），覆盖11大类数据源 |

---

## 注意事项

- 分析结果仅供决策参考，关键数字需标注数据来源
- 涉及春秋航空内部数据，不上传到公网
- 建模预测需标注置信区间，不作为直接操作依据
- 路径说明：本文件中使用 `~/` 代替绝对路径，`../` 表示工作区根目录（`Claude Code/`），
  可按实际环境调整
