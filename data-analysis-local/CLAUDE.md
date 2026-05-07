# CLAUDE.md

This file provides guidance to Claude Code when working in the `data-analysis-local/` workspace.

---

## Workspace Purpose

Local data analysis workspace for Spring Airlines finance team. Stores analysis scripts, data files, and reports for cost analysis, supplier contracts, and financial reporting.

---

## Directory Structure

```
data-analysis-local/
├── <主题>-<YYYYMMDD>/                 # Per-task analysis folder
│   ├── analyze_*.py                  # Analysis scripts
│   ├── report_*.md                   # Analysis reports
│   └── charts/                       # Visualizations (PNG, dpi=150)
├── CLAUDE.md                         # This file
└── README.md                         # Workspace overview
```


---

## Report Generation

**重要**：生成报告前，必须先询问用户选择输出格式：
- **Markdown (md)**：直接保存 `.md` 文件
- **PDF**：使用 `pandoc -s --pdf-engine=xelatex report.md -o report.pdf` 转换
- **Word**：使用 `pandoc -s report.md -o report.docx` 转换

报告必须包含以下信息：
- **作者**：`数字化办公室-AI`
- **日期**：具体年月日（如 `2026-05-07`）
- **数据来源**：原始数据文件名
- **模型信息**：报告底部注明使用的本地模型名称

---

## Skills Reference

Skills are located in the parent workspace at `/Users/fox/Claude Code/skills/`:

| Skill | Use Case |
|-------|----------|
| `skills/domain/financial-analysis/` | Cost analysis, supplier analysis, competitive intelligence |
| `skills/domain/sql-generation/` | SQL queries for YonBIP (contract/tax/treasury) |
| `skills/domain/data-analysis/` | General data analysis workflow |

---

## Data Dictionary

**SQL 数据字典位置**（优先参考）：
```
/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/
├── 合同系统数据字典/
├── 税务系统数据字典/
├── 财务共享数据字典/
└── 资金系统数据字典/
```

**SQL 查询文件直接放在分析任务目录下**，不放在工作区根目录。

---

## Obsidian Sync

Reports sync to: `/Users/fox/Documents/Obsidian Vault/自动笔记/04-创新应用/02-智能分析/<主题>/`

---

## Data Sources

| Source | Path | Description |
|--------|------|-------------|
| Cost Excel | `~/Downloads/成本数字看板_成本费用多维分析-3.0.xlsx` | Monthly cost breakdown |
| Component Excel | `~/Downloads/组件.xlsx` | Report inventory |

---

## SQLite Database

DBeaver connection: `/Users/fox/DB/analysis.db`
