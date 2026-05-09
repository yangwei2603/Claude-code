# FX 预测系统（前端 + 后端 + SQLite + 无监督学习）

## 架构
- 前端：`fx_system/frontend/index.html`
- 后端：`fx_system/backend/server.py`（Python 原生 HTTP 服务）
- 数据库：`fx_system/fx_data.sqlite3`（SQLite）
- 数据采集：`fx_system/backend/data_sources.py`
- 建模：`fx_system/backend/modeling.py`

## 官方数据源（可直接在线拉取）
1. **FRED（Federal Reserve Bank of St. Louis）**：`DEXCHUS`（USDCNY）
2. **ECB（European Central Bank）**：`eurofxref-hist.xml`（推导 USDCNY）
3. **Bank of Canada**：Valet API（USDCAD）

> 注意：不同官方数据源口径/更新时间可能不同，训练前建议按来源和时间对齐。

## 模型能力
- 监督学习：线性回归趋势预测（未来 `horizon` 天）
- 无监督学习：KMeans(2) 对收益-波动特征做市场状态聚类（regime detection）

## 启动
```bash
cd fx_system/backend
python3 server.py
```
访问：<http://127.0.0.1:8010>

## API
- `POST /api/ingest`：拉取官网数据并入库
- `POST /api/train`：训练模型并输出预测 + 无监督聚类结果
- `POST /api/import-csv`：离线导入本地 CSV（网络受限场景）
- `GET /api/rates?pair=USDCNY&limit=20`：查看行情
- `GET /api/model/latest?pair=USDCNY`：查看最新模型参数

## 实盘建议
该版本已可用于**日常研究与半自动决策支持**，但仍建议：
1. 增加多模型集成（ARIMA/XGBoost/LSTM）与 walk-forward 回测
2. 接入实盘交易前做模拟盘与滑点/交易成本压力测试
3. 加入交易风控（仓位上限、回撤熔断、事件日降杠杆）

## 网络受限说明
当运行环境无法直连外网（例如代理返回 403）时，`/api/ingest` 会返回 `errors` 字段并保持服务可用；可先导入本地 CSV 再训练。
