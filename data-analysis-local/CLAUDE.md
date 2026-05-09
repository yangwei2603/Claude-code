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

分析内容**必须**由本地模型生成，人工仅负责审核和调整。

---

## 报告输出规范

### 输出格式

生成报告前，**必须先询问用户**选择输出格式：

| 格式 | 说明 |
|------|------|
| Markdown | 直接保存 `.md` 文件 |
| PDF | `pandoc -s --pdf-engine=xelatex report.md -o report.pdf` |
| Word | `pandoc -s report.md -o report.docx` |

### 报告头格式

每份报告必须包含以下信息：

```
作者：数字化办公室-AI
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

---

## 数据源策略

数据源由每次分析任务动态决定，不在工作区配置中硬编码固定文件路径。
每次任务的数据来源记录在各自的分析目录 `data-analysis-local/<主题>-<YYYYMMDD>/` 中。

### 本地 SQLite 数据库

用于存储清洗后的结构化数据、分析中间结果和查询缓存，避免重复读取大文件。

```python
import sqlite3
import pandas as pd

# 连接数据库（每个分析任务使用独立数据库文件）
db_path = "data-analysis-local/<主题>-<YYYYMMDD>/analysis.db"
conn = sqlite3.connect(db_path)

# 写入数据
df.to_sql("table_name", conn, if_exists="replace", index=False)

# 读取数据
df = pd.read_sql("SELECT * FROM table_name WHERE ...", conn)

# 用完后关闭
conn.close()
```

**约定**：
- 数据库文件放在分析任务目录下，命名 `<主题>.db`（如 `成本费用.db`）
- 不在工作区根目录放置数据库文件
- 大文件（>100MB）清洗后优先存入 SQLite，避免每次重新读取 CSV/Excel
- 使用 `if_exists="replace"` 覆盖同名表，`if_exists="append"` 追加数据
- 推荐使用 `with sqlite3.connect(db_path) as conn:` 上下文管理器自动关闭连接

### 其他数据源

| 来源类型 | 操作 |
|---------|------|
| 本地文件（CSV / Excel） | `pd.read_csv()` / `pd.read_excel()`，文件路径记录在分析目录 |
| 公司内部系统（YonBIP 等） | 导出数据后按本地文件处理；需要 SQL 查询时使用 `sql-generation` skill |
| 外部财务数据 | → 使用 `financial-analysis` skill |

---

## 注意事项

- 分析结果仅供决策参考，关键数字需标注数据来源
- 涉及春秋航空内部数据，不上传到公网
- 建模预测需标注置信区间，不作为直接操作依据
- 路径说明：本文件中使用 `~/` 代替绝对路径，`../` 表示工作区根目录（`Claude Code/`），
  可按实际环境调整
