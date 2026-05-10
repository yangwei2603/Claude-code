# SKILL.md — 机器学习与高级算法

> 覆盖机器学习、深度学习、神经网络、运筹优化建模分析。
> 适用于：预测、异常检测、分类、聚类、优化、调度、决策。
> **必须使用本地大模型进行数据分析**，本地模型不可达时终止任务。

---

## 技能定位

| 分析类型 | 推荐方法 | 场景 |
|---------|---------|------|
| 时间序列预测 | N-BEATS, PatchTST, DLinear, TiDE | 航班收益、客流、成本预测 |
| 异常检测 | OmniAnomaly, USD, AnomalyTransformer | 航班延误、费用异常、设备故障 |
| 多变量预测 | TFT (Temporal Fusion Transformer), DeepAR | 航班多指标联合预测 |
| 分类/回归 | XGBoost, LightGBM, CatBoost | 收益分类、成本预测 |
| 深度学习时序 | LSTM-ED, Temporal Convolutional Network | 航班延误预测 |
| 运筹优化 | OR-Tools, PuLP, Pyomo | 航班调度、排班、资源分配 |
| 强化学习 | RLlib, Stable-Baselines3 | 动态定价、航线优化 |
| 图神经网络 | PyTorch Geometric, DGL | 航线网络、枢纽分析 |

---

## SOTA 方法详解（个人整理，非官方文档）

### 1. 时间序列预测

| 方法 | 特点 | 适用场景 |
|------|------|---------|
| **N-BEATS** | 纯深度学习，无需特征工程，支持多周期分解 | 航班收入预测 |
| **PatchTST** | Transformer 变体，支持长序列，效率高 | 长期趋势预测 |
| **TiDE** | mlp 架构，速度快，精度接近 Transformer | 实时预测 |
| **DLinear** | 线性模型 + 趋势/季节分解，SOTA 轻量级 | 资源受限场景 |
| **DeepAR** | 自回归概率预测，支持不确定性量化 | 收益区间预测 |
| **TFT** | 多变量+可解释性+时序特征融合 | 航班多因素联合预测 |

**推荐 pipeline：**
```
1. 数据预处理 → 缺失值填补、异常平滑
2. 特征工程 → 滞后、滚动统计、节日/季节标记
3. 模型选择 → 按数据量/精度要求选 N-BEATS / PatchTST / TFT
4. 评估指标 → SMAPE, MASE, RMSE, 置信区间覆盖率
```

### 2. 异常检测

| 方法 | 特点 | 适用场景 |
|------|------|---------|
| **OmniAnomaly** | VAE + LSTM，抗噪声强，支持多维 | 航班延误异常 |
| **AnomalyTransformer** | Transformer + 关联异常建模 | 成本费用异常 |
| **USD (Unsupervised)** | 无监督，即插即用 | 未知模式异常 |
| **iForest, LOF** | 传统轻量快速 | 初步筛查 |

### 3. 运筹优化算法

| 方法 | 特点 | 适用场景 |
|------|------|---------|
| **OR-Tools (Google)** | 整数规划、约束求解器，支持 VRP、排班 | 航班编排、机组排班 |
| **PuLP** | Python LP/MILP，快速建模 | 资源分配、成本优化 |
| **Pyomo** | 优化建模，支持非线性 | 复杂约束优化 |
| **遗传算法 (DEAP)** | 启发式全局搜索 | NP-hard 调度问题 |
| **模拟退火** | 连续优化 | 航线网络优化 |

### 4. 强化学习

| 库 | 特点 | 适用场景 |
|---|------|---------|
| **RLlib** | 分布式 RL，支持 PPO/SAC | 动态定价 |
| **Stable-Baselines3** | 单机 RL，易用 | 策略优化 |
| **Gymnasium** | 环境接口，标准化 | 航班调度模拟 |

### 5. 图神经网络

| 库 | 特点 | 适用场景 |
|---|------|---------|
| **PyTorch Geometric** | GNN 标准库 | 航线网络分析 |
| **DGL** | 兼容多框架 | 枢纽节点重要性 |
| **GraphORM** | 图优化器 | 航班连接优化 |

---

## 建模工作流

### Phase 1: 数据理解
```
1. 探索性分析 (EDA) → 分布、趋势、季节性、缺失
2. 相关性分析 → 变量关系，特征选择
3. 异常检测 → 数据清洗
```

### Phase 2: 模型选择
```
数据量 < 10k      → 传统 ML (XGBoost/LightGBM)
数据量 10k-100k   → 轻量深度学习 (DLinear/N-BEATS)
数据量 > 100k     → Transformer 系列 (PatchTST/TFT)
序列长度 > 365    → PatchTST / TiDE
多变量+可解释需求 → TFT
```

### Phase 3: 训练与评估
```
评估指标：
- 回归：RMSE, MAE, SMAPE, MASE
- 概率预测：Coverage, CRPS
- 异常检测：Precision/Recall/F1, AUC-ROC
- 优化：目标函数值、求解时间
```

### Phase 4: 部署与监控
```
- 模型版本管理 (MLflow / DVC)
- 在线预测服务
- 漂移检测与重训练
```

---

## Python 工具链

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

---

## 规范约束

1. **必须使用本地大模型**生成分析报告，本地模型不可达时终止任务
2. **不手工编写分析结论**，所有结论由本地模型生成
3. **数据必须存储在本地**，`/Users/fox/DB/` 或 `data-analysis-local/` 目录下
4. **输出格式**：分析报告保存为 `.md`，模型文件存放在分析任务目录下

---

## 参考资源

- NeuralForecast / Darts — 时序预测开源库
- PyTorch Geometric — 图神经网络
- OR-Tools — Google 运筹优化
- RLlib — 分布式强化学习