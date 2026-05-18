# CLAUDE.md — 航油成本分析

> 航油成本数据分析工作目录，用于春秋航空航油成本、节油效率、CI执行率等分析。
> 数据来源于 ADS 系统导出的航班粒度数据。

---

## 数据源

| 数据源 | 路径 | 说明 |
|--------|------|------|
| 航班明细表 | `/Users/fox/DB/analysis.db` → `t_ads_sfuel_stat_dtl` | 航班粒度原始数据，135万+条 |
| 日表 | `/Users/fox/DB/analysis.db` → `t_ads_sfuel_stat_d` | 日维度汇总 |
| 月表 | `/Users/fox/DB/analysis.db` → `t_ads_sfuel_stat_m` | 月维度汇总 |
| 航线月表 | `/Users/fox/DB/analysis.db` → `t_ads_sfuel_stat_route_m` | 航线×月维度 |
| 航班运行视图 | `/Users/fox/DB/analysis.db` → `v_dws_flt_opt_stat_d` | 航班正常率、延误等 |

**元数据表**：`/Users/fox/DB/analysis.db` → `table_metadata`

---

## 数据字典

完整数据字典位于：
- `/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/`

包含：
- `t_ads_sfuel_stat_dtl_数据字典.md` — 航班明细表（91字段）
- `节油相关表数据字典.md` — 日/月/航线汇总表
- `航油成本数据口径手册.md` — 指标口径体系
- `航油成本数据逻辑代码样例.md` — SQL查询样例

---

## 分析类型

| 分析类型 | 使用表 | 说明 |
|----------|--------|------|
| 航班粒度分析 | t_ads_sfuel_stat_dtl | 单航班油耗、CI执行率分析 |
| 日度汇总分析 | t_ads_sfuel_stat_d | 按日汇总的节油指标 |
| 月度汇总分析 | t_ads_sfuel_stat_m | 按月汇总的节油指标 |
| 航线分析 | t_ads_sfuel_stat_route_m | 按航线维度的油耗排名 |
| 航班运行分析 | v_dws_flt_opt_stat_d | 正常率、延误、返航备降等 |
| 同比/环比分析 | t_ads_sfuel_stat_m | 月度趋势对比 |

---

## 核心指标

| 指标 | 说明 | 计算公式 |
|------|------|----------|
| CI点执行率 | CI推荐速度与实际速度偏差≤7节的比例 | COUNT(偏差≤7) / COUNT(总点数) |
| CI航班执行率 | CI点执行率≥60%的航班占比 | COUNT(CI点执行率≥0.6) / COUNT(总航班) |
| 轮挡小时耗油 | 轮挡时间内每小时耗油量 | 轮挡耗油 / 轮挡时间 |
| 空中小时耗油 | 空中飞行每小时耗油量 | 空中耗油 / 空中时间 |
| 直飞率 | 直飞航班占比 | 直飞航班数 / 计划直飞航班数 |
| 绕飞率 | 绕飞航班占比 | 绕飞航班数 / 总航班数 |
| 返航备降率 | 返航+备降航班占比 | (返航+备降) / 总航班 |

---

## 目录结构

```
航油成本分析/                          # 航油成本分析项目根目录
├── CLAUDE.md                         # 本文件
├── metadata/                         # 数据字典和元数据
│   ├── table_summary.md              # 表清单和字段信息
│   └── 指标说明.md                   # 核心指标定义
├── raw/                              # 原始数据文件（Excel/CSV）
├── scripts/                          # 分析脚本模板
│   └── *.py                         # Python分析脚本
├── charts/                           # 输出图表（模板）
└── <YYYYMMDD>/                      # 每次分析任务子目录
    ├── analyze_*.py                  # 分析脚本
    ├── data.json                     # 分析数据
    ├── index.html                    # HTML报告
    └── charts/                       # 图表输出
```

**命名规范**：每次分析任务在 `航油成本分析/` 下创建独立子目录，格式 `<YYYYMMDD>`（8位日期），不得在其他位置创建。

---

## 分析流程

1. **数据确认** — 检查 `/Users/fox/DB/analysis.db` 中数据完整性
2. **创建任务目录** — 在 `航油成本分析/<YYYYMMDD>/` 下创建本次分析目录
3. **编写脚本** — 在本次任务目录下创建分析脚本
4. **执行分析** — `python3 <YYYYMMDD>/analyze_*.py`
5. **生成报告** — 输出 HTML 报告到 `航油成本分析/<YYYYMMDD>/`

---

## 相关文档

- 数据字典：`/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/`
- 数据口径手册：`/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/航油成本数据口径手册.md`
- SQL样例：`/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/航油成本数据逻辑代码样例.md`
