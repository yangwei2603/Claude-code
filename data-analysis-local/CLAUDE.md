# CLAUDE.md — data-analysis-local 工作区导航

> 本文件是 Claude Code 在此工作区的最高优先级导航文档。
> 所有分析任务优先参考本文件路由到对应 Skill。

---

## 目录结构

```
data-analysis-local/               ← 工作区根目录
│
├── v_clm_contract_dw.sql          ← ✅ 已验证：合同数据宽表视图
│
├── <主题>-<YYYYMMDD>/              ← 分析任务目录（每次任务新建，见下方模板）
│   ├── raw/                        # 原始数据（只读）
│   ├── cleaned_<主题>.csv          # 清洗后数据
│   ├── charts/                     # 可视化图表（PNG，dpi=150）
│   ├── analysis.py                 # 分析脚本
│   └── report_<YYYYMMDD>.md        # 分析报告
│
└── README.md                       ← 工作区说明
```

---

## Skill 路由图

```
用户需求
│
├─► 「查一下 XX 供应商的合同金额」      → sql-generation skill
│                                        → v_clm_contract_dw + 供应商统计
│
├─► 「分析 XX 月成本费用趋势」         → financial-analysis skill
│                                        → analysis.py 模板 + 图表
│
├─► 「六大航司 CASK 对比」            → airline-analysis skill（全局）
│                                        → neodata-financial-search
│
├─► 「航司财务数据查询」              → neodata-financial-search
│                                        → 自然语言金融数据
│
├─► 「生成 PPT 报告」                → pptx skill
│
└─► 「处理 Excel 数据」               → xlsx skill
```

---

## Skill 能力对照表

| Skill | 触发词 | 核心功能 | 状态 |
|-------|--------|----------|------|
| `financial-analysis` | 成本分析、供应商分析、竞争情报、报表发布 | 多维成本钻取、供应商评估、竞争环境关联、MCP规范 | ✅ 已创建 |
| `sql-generation` | SQL查询、数据字典、指标取数 | 合同/税务/共享/资金四域SQL模板 | ✅ 已创建 |
| `airline-analysis` | 航司年报、CASK分解、六大航司对比 | 16页航司分析PPT | ✅ 已有 |
| `neodata-financial-search` | 财务数据查询、行情、宏观经济 | 自然语言金融数据查询 | ✅ 插件 |
| `pptx` | PPT、演示文稿、幻灯片 | 分析报告→PPT | ✅ 插件 |
| `xlsx` | Excel、CSV、数据处理 | 原始数据处理 | ✅ 插件 |

---

## SQL 数据字典（已验证）

| 视图/表 | 数据库 | 用途 | 状态 |
|---------|--------|------|------|
| `v_clm_contract_dw` | `yonbip_clm_contract` | 合同全量字段 | ✅ 已验证 |
| `v_tax_transaction_dw` | `yonbip_tax` | 税务交易 | 🔜 待实现 |
| `v_fss_dw` | `yonbip_fss` | 财务共享作业 | 🔜 待实现 |
| `v_cms_cashflow_dw` | `yonbip_cms` | 资金流水 | 🔜 待实现 |

---

## Quick Reference

| 需求 | 快速路径 |
|------|----------|
| 写 SQL 查供应商 | `sql-generation` → 合同域模板 → 改 vendor_name 条件 |
| 多维成本分析 | `financial-analysis` → analysis.py 模板 → 加分组聚合 |
| 供应商执行率 | `sql-generation` → 合同执行全景查询 |
| 欠票预警 | `sql-generation` → 欠票预警 SQL |
| 生成分析报告 | `financial-analysis` → 报告模板 |
| 竞对情报 | `airline-analysis` + `neodata-financial-search` |

---

## 数据存储规范

- **原始数据**: `<任务目录>/raw/`
- **图表输出**: `<任务目录>/charts/`（PNG，dpi=150）
- **报告同步**: 复制 `report_*.md` 到 Obsidian Vault `05-数据资产/02-业务分析/`
- **SQL脚本**: 统一放入 `05-数据资产/01-数据治理/数据字典/`

---

## 新分析任务创建模板

一键生成 `<主题>-<YYYYMMDD>` 目录结构：

```bash
# 在 data-analysis-local/ 下执行
mkdir -p "<主题>-<YYYYMMDD>"/{raw,charts}
touch "<主题>-<YYYYMMDD>/{cleaned_data.csv,analysis.py,report_<YYYYMMDD>.md}"
```

### 目录结构规范

```
<主题>-<YYYYMMDD>/
├── raw/                    # 原始数据（只读，永不修改）
│   └── *.csv / *.sql / *.xlsx
├── cleaned_<主题>.csv      # 清洗后数据（去重、格式化、补全）
├── charts/                 # 可视化输出（PNG，dpi=150）
│   └── *.png
├── analysis.py             # 分析脚本（含 EDA + 建模 + 可视化）
└── report_<YYYYMMDD>.md     # 分析报告（结论 + 建议 + 附录）
```

### 创建检查清单

- [ ] 目录命名：`<主题>-<YYYYMMDD>`（如 `成本费用多维分析-20260507`）
- [ ] `raw/` 放入原始数据文件
- [ ] `analysis.py` 使用 `skills/domain/data-analysis/SKILL.md` 模板
- [ ] `report_<YYYYMMDD>.md` 包含：背景、方法、发现、建议、附录
- [ ] 图表输出到 `charts/`，分辨率 150dpi
- [ ] 完成后同步报告到 Obsidian `05-数据资产/02-业务分析/`

---

## Obsidian Vault 协同路径

```
Obsidian Vault: /Users/fox/Documents/Obsidian Vault/
│
├── 05-数据资产/
│   ├── 01-数据治理/
│   │   └── 数据字典/              ← SQL 脚本存放
│   └── 02-业务分析/
│       └── <分析主题>/            ← 分析报告同步
│
└── 自动笔记/04-创新应用/          ← 自动化任务记录
```
