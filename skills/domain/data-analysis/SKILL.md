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
- **输出格式**：交互友好可下钻HTML报告（默认）、Markdown 报告、PPT 汇报材料

## 标准分析流程

### Step 1：明确分析目标

在开始前，确认以下三点：

1. **问题定义**：这次分析要回答什么业务问题？
2. **数据范围**：涉及哪些时间段、维度、粒度？
3. **输出格式**：默认交互式 HTML 报告（可下钻）/ Markdown 报告 / PPT 汇报 / 数据表格

### Step 2：数据获取

根据数据来源选择入口：

| 来源 | 操作 |
|------|------|
| 本地数据库 / 公司数据库 | → 使用 `sql-generation` skill 生成查询 SQL |
| 导出的 CSV / Excel 文件 | pandas 读取，标注文件路径 |
| 外部财务数据（航司） | → 本 skill 内置财务分析模块（供应商、成本、竞争情报） |
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

根据分析类型选择合适的建模方法：

#### 6.1 建模方法选择

| 分析类型 | 推荐方法 | 典型场景 |
|---------|---------|---------|
| 时间序列预测 | N-BEATS, PatchTST, DLinear, TiDE | 航班收益、客流、成本预测 |
| 异常检测 | OmniAnomaly, USD, iForest, LOF | 航班延误、费用异常、设备故障 |
| 多变量预测 | TFT (Temporal Fusion Transformer), DeepAR | 航班多指标联合预测 |
| 分类/回归 | XGBoost, LightGBM, CatBoost | 收益分类、成本预测 |
| 深度学习时序 | LSTM-ED, Temporal Convolutional Network | 航班延误预测 |
| 运筹优化 | OR-Tools, PuLP, Pyomo | 航班调度、排班、资源分配 |
| 强化学习 | RLlib, Stable-Baselines3 | 动态定价、航线优化 |
| 图神经网络 | PyTorch Geometric, DGL | 航线网络、枢纽分析 |

#### 6.2 模型选择指南（按数据规模）

```
数据量 < 10k      → 传统 ML (XGBoost/LightGBM)
数据量 10k-100k   → 轻量深度学习 (DLinear/N-BEATS)
数据量 > 100k     → Transformer 系列 (PatchTST/TFT)
序列长度 > 365    → PatchTST / TiDE
多变量+可解释需求 → TFT
```

#### 6.3 评估指标

| 任务类型 | 指标 |
|---------|------|
| 回归 | RMSE, MAE, SMAPE, MASE |
| 概率预测 | Coverage, CRPS |
| 异常检测 | Precision/Recall/F1, AUC-ROC |
| 优化 | 目标函数值、求解时间 |

#### 6.4 Python 工具链

| 任务 | 库 |
|------|---|
| 数据处理 | pandas, polars, numpy |
| 时序 ML | statsmodels, prophet, neuralforecast, darts |
| 深度学习 | PyTorch, PyTorch Lightning |
| AutoML | AutoGluon, FLAML, H2O |
| 图学习 | PyTorch Geometric, DGL |
| 强化学习 | RLlib, SB3, Gymnasium |
| 优化 | OR-Tools, PuLP, Pyomo, scipy.optimize |
| 可视化 | matplotlib, seaborn, plotly |
| 实验管理 | MLflow, Weights & Biases, DVC |

#### 6.5 建模工作流

```
Phase 1: 数据理解
  - 探索性分析 (EDA) → 分布、趋势、季节性、缺失
  - 相关性分析 → 变量关系，特征选择
  - 异常检测 → 数据清洗

Phase 2: 模型选择
  - 按数据量/精度要求选模型

Phase 3: 训练与评估
  - 评估指标验证

Phase 4: 部署与监控
  - 模型版本管理 (MLflow / DVC)
  - 在线预测服务
  - 漂移检测与重训练
```

### Step 7：报告输出

输出到：`data-analysis-local/<主题>-<YYYYMMDD>/`

**报告格式（按优先级）**：
1. **HTML（默认）** — 交互式可下钻，分析完成后立即生成
2. Markdown — 用户要求时生成
3. PDF/Word — 用户要求时生成

**无特殊要求时，默认生成交互式 HTML 报告**。

---

## 输出目录规范

```
data-analysis-local/
└── <主题>-<YYYYMMDD>/
    ├── CLAUDE.md            # 项目说明（必填）
    ├── analyze_*.py        # 分析脚本（必须）
    ├── data.json           # 分析数据
    ├── index.html          # HTML 报告（必须）
    ├── charts/             # 静态图表
    │   └── *.png
    └── raw/                # 原始数据副本
        └── *
```

**目录命名规则**：
- `<主题>`：简短英文或拼音（与分析内容相关）
- `<YYYYMMDD>`：任务开始日期（8位数字）
- 示例：`fuel-cost-20260519/`、`supplier-analysis-20260520/`

**必填文件**：CLAUDE.md（项目说明）、analyze_*.py（分析脚本）、index.html（HTML报告）

---

## 与其他 Skill 的衔接

```
数据分析任务
  │
  ├── 需要 SQL 查询？──────────────→ sql-generation (domain)
  ├── 航司财务专项？──────────────→ data-analysis (domain) 内置
  ├── 需要 PPT 汇报？─────────────→ [WorkBuddy pptx skill]
  └── 需要文档归档/ADR？──────────→ documentation-and-adrs (engineering)
```

---

## 注意事项

- 分析结果仅供决策参考，关键数字需标注数据来源
- 涉及春秋航空内部数据，不上传到公网
- 建模预测需标注置信区间，不作为直接操作依据
