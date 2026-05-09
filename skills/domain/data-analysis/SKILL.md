---
name: data-analysis
description: 通用数据分析技能，标准化从数据获取到报告输出的完整流程。触发词：数据分析、数据清洗、EDA、探索性分析、数据建模、数据可视化、分析报告、报表分析、成本分析、财务数据、多维分析、同比环比。
---

# 数据分析 Skill（通用）

## 能力范围

- **数据获取**：SQL 查询、CSV 导入、API 拉取、手工录入
- **数据清洗**：空值处理、格式标准化、异常值识别
- **探索性分析 (EDA)**：描述统计、分布分析、相关性分析
- **数据建模**：趋势预测、聚类分析、回归分析
- **可视化**：时序趋势图、多维对比图、热力图
- **报告输出**：结构化 Markdown 报告、PPT 汇报材料

## 标准分析流程

### Step 1：明确分析目标

在开始前，确认以下三点：

1. **问题定义**：这次分析要回答什么业务问题？
2. **数据范围**：涉及哪些时间段、维度、粒度？
3. **输出格式**：Markdown 报告 / PPT 汇报 / 数据表格？

### Step 2：数据获取

根据数据来源选择入口：

| 来源 | 操作 |
|------|------|
| 本地数据库 / 公司数据库 | → 使用 `sql-generation` skill 生成查询 SQL |
| 导出的 CSV / Excel 文件 | pandas 读取，标注文件路径 |
| 外部财务数据（航司） | → 使用 `financial-analysis` skill |
| 飞书多维表格 / 在线表格 | 下载后以 CSV 处理 |

### Step 3：数据清洗（Pandas 标准流程）

```python
import pandas as pd

df = pd.read_csv("data.csv")

# 1. 基本探查
print(df.shape, df.dtypes, df.isnull().sum())

# 2. 空值处理（按列决策：删除 or 填充）
df.dropna(subset=["关键字段"])
df["数值字段"].fillna(0, inplace=True)

# 3. 格式标准化
df["日期"] = pd.to_datetime(df["日期"])
df["金额"] = df["金额"].astype(float)

# 4. 去重
df.drop_duplicates(inplace=True)
```

**约束**：清洗操作必须可追溯，不直接修改原始文件，输出清洗后版本到 `cleaned_*.csv`。

### Step 4：探索性分析 (EDA)

```python
# 描述统计
print(df.describe())

# 时序趋势（按月/季度）
monthly = df.groupby(df["日期"].dt.to_period("M"))["金额"].sum()

# 同比环比
df["同比"] = df["金额"] / df["金额"].shift(12) - 1
df["环比"] = df["金额"] / df["金额"].shift(1) - 1

# 多维分解（示例：按部门 × 费用类型）
pivot = df.pivot_table(values="金额", index="部门", columns="费用类型", aggfunc="sum")
```

### Step 5：可视化

```python
import matplotlib.pyplot as plt
import matplotlib

# 中文字体支持（macOS）
matplotlib.rcParams["font.family"] = "PingFang SC"
matplotlib.rcParams["axes.unicode_minus"] = False

# 趋势图
plt.figure(figsize=(12, 5))
plt.plot(monthly.index.astype(str), monthly.values)
plt.title("月度趋势")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("charts/trend.png", dpi=150)
```

**图表规范**：
- 涨/增 → 红色（#E84040）；跌/减 → 绿色（#00B06F）
- 所有图表保存到分析目录的 `charts/` 子目录
- 文件名格式：`<图表类型>_<维度>_<日期>.png`

### Step 6：建模（按需）

| 分析类型 | 工具 | 典型场景 |
|---------|------|---------|
| 趋势预测 | sklearn LinearRegression | 成本趋势预测 |
| 聚类分析 | sklearn KMeans | 供应商/航线市场分类 |
| 异常检测 | IsolationForest | 费用异常识别 |

### Step 7：报告输出

输出到：`数据分析-local/<主题>-<YYYYMMDD>/report_analysis_<YYYYMMDD>.md`

**报告格式选择**：生成报告前，必须询问用户选择输出格式（Markdown / PDF / Word）。

报告结构模板：

```markdown
# <分析主题> 分析报告

**分析日期**：YYYY-MM-DD
**数据来源**：<原始数据文件名>
**分析人**：数字化办公室-AI

## 执行摘要

（3-5句话，核心结论 + 关键数字）

## 数据概况

| 维度 | 数值 | 同比 |
|------|------|------|

## 深度分析

### <维度1>
### <维度2>

## 异常与风险

## 建议

---

**报告信息**
- 数据来源：<原始数据文件名>
- 分析模型：Qwen3-VL-235B-A22B-Instruct-AWQ（本地私有化部署）
- 分析人：数字化办公室-AI
- 分析日期：YYYY-MM-DD
```

---

## 输出目录规范

```
数据分析-local/
└── <主题>-<YYYYMMDD>/
    ├── raw/                # 原始数据文件
    ├── cleaned_*.csv       # 清洗后数据
    ├── charts/             # 图表文件
    ├── analysis.py         # 分析脚本
    └── report_analysis_<YYYYMMDD>.md  # 最终报告
```

---

## 与其他 Skill 的衔接

```
数据分析任务
  │
  ├── 需要 SQL 查询？──────────────→ sql-generation (domain)
  ├── 航司财务专项？──────────────→ financial-analysis (domain)
  ├── 需要 PPT 汇报？─────────────→ [WorkBuddy pptx skill]
  └── 需要文档归档/ADR？──────────→ documentation-and-adrs (engineering)
```

---

## 注意事项

- 分析结果仅供决策参考，关键数字需标注数据来源
- 涉及春秋航空内部数据，不上传到公网
- 建模预测需标注置信区间，不作为直接操作依据
