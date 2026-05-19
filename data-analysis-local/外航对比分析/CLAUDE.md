# CLAUDE.md — 外航对比分析

> 上市航司对标分析工作目录，用于春秋航空与吉祥航空、国航、东航、南航、海航、华夏航空的年报数据对比分析。
> 数据来源于巨潮资讯公开披露的上市公司年报。

---

## 数据源

| 数据源 | 路径 | 说明 |
|--------|------|------|
| 年报 PDF | `raw/` 或 `上市航司年报解析-2026-05/downloads/` | 巨潮资讯下载的 PDF 文件 |
| 解析结果 | `上市航司年报解析-2026-05/parsed/` | 提取的指标 JSON |
| 外部数据库 | `/Users/fox/DB/external_data.db` | 航司运营数据、行业对标指标 |

---

## 目录结构

```
外航对比分析/
├── CLAUDE.md                         # 本文件
├── metadata/                         # 数据字典
├── raw/                              # 原始数据文件
├── scripts/                          # 通用脚本模板
└── <分析主题>-<YYYY-MM>/             # 每次分析任务子目录
    ├── README.md                     # 指标口径文档
    ├── analyze_*.py                  # 分析脚本
    ├── data.json                     # 分析数据
    ├── index.html                    # HTML报告
    └── charts/                       # 图表输出
```

**命名规范**：`外航对比分析/<分析主题>-<YYYY-MM>/`

---

## 分析子项目

### 吉祥春秋航司对比-2026-05（吉祥春秋航司对比分析）

| 文件 | 说明 |
|------|------|
| `analyze.py` | 航司对比分析脚本 |
| `analyze_airline.py` | 单航司分析脚本 |
| `charts/` | 对比图表输出 |
| `report_analysis_20260510.html` | HTML报告 |

### 上市航司年报解析-2026-05（上市航司年报解析）

| 文件 | 说明 |
|------|------|
| `scripts/fetch_cninfo*.py` | 巨潮资讯 PDF 下载脚本 |
| `scripts/parse_all_pdfs_v2.py` | 年报 PDF 解析脚本 |
| `scripts/parse_utilization_v2.py` | 利用率数据提取脚本 |
| `parsed/all_metrics_extracted.json` | 提取的年报指标 |
| `parsed/all_pdf_parsed_results_v2.json` | PDF 解析结果 |

**工具依赖**：playwright + Chrome、pdfplumber

---

## 核心指标

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| 客座率 | RPK/ASK，航班客座利用水平 | 年报经营数据 |
| 飞机日利用率 | 每日每架飞机飞行小时数 | 年报运营数据 |
| 可用率 | 可用飞机架数/总飞机架数 | 年报机队数据 |
| CASK | 单位可用座公里成本 | 年报财务数据 |
| RASK | 单位可用座公里收入 | 年报财务数据 |

---

## 分析流程

1. **下载年报 PDF** — 运行 `scripts/fetch_cninfo_browser.py`
2. **解析提取数据** — 运行 `scripts/parse_utilization_v2.py`
3. **更新数据库** — 运行 `scripts/update_database.py`
4. **执行对比分析** — 在本次任务目录下创建分析脚本
5. **生成报告** — 输出 HTML 报告

---

## 相关文档

- 数据字典：`metadata/`
- 外部数据：`/Users/fox/DB/external_data.db`
