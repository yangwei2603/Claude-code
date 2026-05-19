# 航空年报利用率数据提取项目

## 目标
从巨潮资讯官网下载上市航空公司年报 PDF，提取其中的利用率（客座率、飞机利用率、可用率）数据，存入 `external_data.db`。

## 目标航司
春秋航空(601021)、吉祥航空(603885)、中国国航(601111)、中国东航(600115)、中国南航(600029)、海航控股(600221)、华夏航空(002928)

## 目标年份
2023、2024、2025

## 目录结构
```
airline-annual-reports/
├── downloads/          # 下载的 PDF 文件
├── parsed/            # 解析结果 JSON
├── scripts/
│   ├── fetch_cninfo.py         # curl 版下载（需 API）
│   ├── fetch_cninfo_browser.py  # playwright 浏览器版下载
│   ├── parse_utilization.py    # PDF 解析提取数据
│   ├── update_database.py      # 写入 external_data.db
│   └── test_playwright.py      # playwright 测试
└── CLAUDE.md
```

## 工具依赖
- playwright (已安装) + Chrome（系统已安装）
- pdfplumber 0.11.8（已安装）
- curl（系统自带）
- sqlite3（系统自带）

## 使用流程

### 第一步：下载 PDF
```bash
cd /Users/fox/Claude Code/data-analysis-local/airline-annual-reports/scripts
python3 fetch_cninfo_browser.py 2024        # 下载2024年年报
python3 fetch_cninfo_browser.py 2023 2024 2025  # 一次性下载多年
```

### 第二步：解析 PDF 提取利用率数据
```bash
python3 parse_utilization.py
```
输出: `parsed/utilization_data.json`

### 第三步：更新数据库
```bash
python3 update_database.py 2024
```

## 数据说明
年报中利用率相关指标（通常在"经营数据"或"运营数据"章节）：
- **客座率** (Passenger Load Factor): RPK/ASK，反映航班客座利用水平
- **飞机日利用率**: 每日每架飞机飞行小时数，反映飞机使用强度
- **可用率**: 可用飞机架数/总飞机架数，反映机队健康度

## 关键文件
- 巨潮资讯（证监会指定信披平台）: https://www.cninfo.com.cn
- 上海证券交易所: https://www.sse.com.cn

## 注意事项
- PDF 下载需要浏览器环境（playwright + Chrome）
- 巨潮资讯有时需要处理反爬，浏览器方式更稳定
- PDF 解析依赖 pdfplumber，部分扫描版 PDF 无法解析
- 数据写入数据库前会先检查记录是否存在（upsert）
