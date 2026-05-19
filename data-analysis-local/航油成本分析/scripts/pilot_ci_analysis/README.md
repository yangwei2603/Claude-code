# 飞行员CI与高度执行率双低分析

## 分析方法

采用 **Z分数法** 识别双低飞行员：
- 综合Z分数 = (CI_Z分数 + 高度执行率_Z分数) / 2
- 分数越负，说明该飞行员在两项指标上同时差于机队平均水平越多

## 指标口径

### CI执行率
- **定义**：执行CI的航班占比（is_execute_ci=1）
- **计算公式**：SUM(is_execute_ci=1) / SUM(is_execute_ci IN (0,1))
- **说明**：分子分母同时排除NULL/无效值

### 高度执行率
- **定义**：实际高度 ≥ 计划高度 - 500ft 的航班占比
- **计算公式**：实际高度达标的航班数 / 有效航班数（排除actual_altitude=0或NULL）
- **说明**：仅检查高度差值是否在-500ft以内，无平飞阶段限制

### 双低判定
- CI执行率 < 85%
- 高度执行率 < 15%
- **两项同时满足**才判定为双低

### 过滤条件
- is_valid = 0
- flight_status = 0
- flight_type IN (1,2,3,4)
- duty_captain_number 不为空
- 航班量 ≥ 20班（最小样本量）

## 文件说明

| 文件 | 说明 |
|------|------|
| `analyze_dual_low_pilots.py` | 数据提取脚本 |
| `generate_dual_low_report.py` | 报告生成脚本 |
| `scientific_dual_low_top10.json` | 分析数据（JSON） |
| `report_scientific_dual_low_20260519.html` | 分析报告（HTML，可展开航班明细） |

## 分析周期
- 2026年3-4月聚合

## 机队基准
- CI执行率均值：91.8%（标准差5.2%）
- 高度执行率均值：82.9%（标准差7.4%）