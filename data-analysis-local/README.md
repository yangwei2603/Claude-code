# 数据分析-local 工作区说明

本目录为 Claude Code 数据分析任务的本地工作区，用于存放分析脚本、数据文件和报告输出。

---

## 命名规范

每次分析任务创建独立子目录：

```
<主题>-<YYYYMMDD>/
```

示例：
- `成本费用多维分析-20260507/`
- `财务部报表发布清单分析-20260507/`
- `航司CASK对比分析-20260601/`

---

## 标准目录结构

```
<主题>-<YYYYMMDD>/
├── raw/                        # 原始数据（CSV、SQL导出等）
├── cleaned_*.csv               # 清洗后数据（不修改原始文件）
├── charts/                     # 可视化图表（PNG，dpi=150）
├── analysis.py                 # 分析脚本
└── report_analysis_<YYYYMMDD>.md  # 最终分析报告
```

---

## SQL 查询文件

SQL 文件直接放在根目录，按系统命名：

| 文件 | 说明 |
|------|------|
| `v_clm_contract_dw.sql` | 用友 YonBIP 合同系统视图查询 |

---

## 与 Obsidian Vault 的协同

分析报告可同步到 Obsidian：

- **目标路径**：`05-数据资产/<主题>/`
- **同步方式**：复制 `report_analysis_*.md` 到 Vault 对应目录
- **图表引用**：将 `charts/` 中的图片也复制，更新 Markdown 内的图片路径

---

## 触发技能

使用 Claude Code 进行数据分析时，优先参考：

- `skills/domain/financial-analysis/SKILL.md` — 通用财务分析（含供应商/竞争情报/MCP规范）
- `skills/domain/sql-generation/SKILL.md` — SQL 生成（含合同/税务/共享/资金四域）
- `airline-analysis`（全局 Skill）— 航司专项年报分析

> 新 Skill 均存放于 `data-analysis-local/skills/domain/`，由本目录的 `CLAUDE.md` 统一路由。
> 详细路由图见 `CLAUDE.md`。
