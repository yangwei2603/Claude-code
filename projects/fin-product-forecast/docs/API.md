# fx_system API 接口文档

## 基础信息

- **端口**：8010
- **启动**：`cd fx_system/backend && python3 server.py`
- **访问**：`http://127.0.0.1:8010`

---

## API 列表

### `POST /api/ingest`

拉取官方数据源并入库。

**请求体**（可选）：

```json
{
  "pairs": ["USDCNY", "EURUSD"],
  "source": "FRED"
}
```

**响应**：

```json
{
  "status": "ok",
  "ingested": 1250,
  "errors": []
}
```

> 当网络受限（如代理 403）时返回 `errors` 字段但 `status` 仍为 `ok`，可改用 `/api/import-csv` 导入离线数据。

---

### `POST /api/train`

训练模型并输出预测结果与聚类标签。

**请求体**（可选）：

```json
{
  "pair": "USDCNY",
  "horizon": 5,
  "lookback": 60
}
```

**响应**：

```json
{
  "status": "ok",
  "pair": "USDCNY",
  "model": "linear_regression",
  "coefficients": {
    "intercept": 7.24,
    "slope": 0.001
  },
  "train_r2": 0.73,
  "forecast": [7.251, 7.253, 7.255, 7.257, 7.259],
  "regimes": ["low_vol", "high_vol", "high_vol"]
}
```

---

### `POST /api/import-csv`

离线 CSV 导入（网络受限场景）。

**请求体**：

```json
{
  "pair": "USDCNY",
  "csv_path": "/path/to/data.csv"
}
```

CSV 格式：

```csv
timestamp,close
2025-01-01,7.2456
2025-01-02,7.2489
```

---

### `GET /api/rates`

查询行情数据。

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `pair` | string | `USDCNY` | 货币对 |
| `limit` | int | `20` | 返回条数 |

**响应**：

```json
{
  "pair": "USDCNY",
  "rates": [
    {"timestamp": "2025-04-25", "close": 7.2512},
    ...
  ]
}
```

---

### `GET /api/model/latest`

查看最新模型参数。

**参数**：

| 参数 | 类型 | 默认值 |
|------|------|--------|
| `pair` | string | `USDCNY` |

**响应**：

```json
{
  "pair": "USDCNY",
  "model": "linear_regression",
  "coefficients": {"intercept": 7.24, "slope": 0.001},
  "trained_at": "2025-04-25T10:30:00"
}
```

---

## 数据源配置

### FRED（Federal Reserve Bank of St. Louis）

- **货币对**：USDCNY（DEXCHUS）
- **地址**：https://fred.stlouisfed.org/

### ECB（European Central Bank）

- **接口**：`eurofxref-hist.xml`
- **说明**：通过 EUR/USD 推导 USDCNY

### Bank of Canada

- **接口**：Valet API
- **货币对**：USDCAD

---

## 网络受限处理

当运行环境无法直连外网时：

1. 使用 `/api/import-csv` 导入本地 CSV 数据
2. CSV 格式：`timestamp,close`，时间格式 `YYYY-MM-DD`
3. 导入后正常调用 `/api/train` 进行建模
