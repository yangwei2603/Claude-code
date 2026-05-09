# 快速入门指南

## 环境要求

- Python 3.8+
- 无需额外框架依赖（使用 Python 原生 HTTP 服务）

## 安装依赖

```bash
# 安装可选依赖（用于数据处理和建模）
pip install numpy pandas scikit-learn requests
```

## Step 1：启动预测服务

```bash
cd fx_system/backend
python3 server.py
# 输出：Starting server on http://127.0.0.1:8010
```

## Step 2：拉取数据

```bash
curl -X POST http://127.0.0.1:8010/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"pairs": ["USDCNY"], "source": "FRED"}'
```

## Step 3：训练模型

```bash
curl -X POST http://127.0.0.1:8010/api/train \
  -H "Content-Type: application/json" \
  -d '{"pair": "USDCNY", "horizon": 5, "lookback": 60}'
```

## Step 4：查看预测结果

```bash
curl "http://127.0.0.1:8010/api/model/latest?pair=USDCNY"
```

## Step 5：打开前端可视化

浏览器访问：`http://127.0.0.1:8010`

## 离线模式（网络受限）

当无法拉取官方数据时：

1. 准备 CSV 文件（字段：`timestamp, close`）
2. 导入数据：

```bash
curl -X POST http://127.0.0.1:8010/api/import-csv \
  -H "Content-Type: application/json" \
  -d '{"pair": "USDCNY", "csv_path": "/path/to/data.csv"}'
```

3. 正常调用 `/api/train` 建模

## 量化回测

```bash
python3 tools/fx_quant_strategy.py \
  --csv reports/sample_usdcny.csv \
  --out reports/output.csv \
  --lookback 20 \
  --vol-window 30 \
  --target-vol 0.10 \
  --max-leverage 2.0 \
  --stop-loss 0.02
```

## 配置飞书预警

编辑 `fin-product-forecast.json` 中的 `channels.feishu` 配置：

```json
{
  "feishu": {
    "enabled": true,
    "appId": "your_app_id",
    "appSecret": "your_app_secret"
  }
}
```

## 项目结构速查

```
fin-product-forecast/
├── fx_system/          汇率预测核心系统
│   ├── backend/        HTTP 服务
│   ├── frontend/       可视化前端
│   └── README.md       模块说明
├── tools/              量化工具集
│   ├── fx_quant_strategy.py   量化回测
│   └── fx_code_audit.py        代码审计
├── docs/               项目文档
│   ├── PROJECT.md      项目整体说明
│   ├── ARCHITECTURE.md 系统架构
│   ├── API.md          接口文档
│   ├── QUANT_STRATEGY.md 量化策略说明
│   └── GUIDE.md        快速入门（本文）
└── fin-product-forecast.json  配置文件
```
