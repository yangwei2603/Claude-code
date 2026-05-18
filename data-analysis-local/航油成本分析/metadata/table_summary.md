# 航油成本分析 - 数据表清单

> 更新日期：2026-05-18
> 数据来源：归档.zip + 节油.7z

---

## 数据库信息

- **数据库路径**：`/Users/fox/DB/analysis.db`
- **元数据表**：`table_metadata`

---

## 表清单

| 序号 | 表名 | 中文名 | 记录数 | 字段数 | 时间范围 | 说明 |
|------|------|--------|--------|--------|----------|------|
| 1 | t_ads_sfuel_stat_dtl | 航油成本统计明细表 | 1,355,057 | 91 | 2017-01-01 ~ 2026-05-17 | 航班级别燃油与飞行数据（粒度最细） |
| 2 | t_ads_sfuel_stat_d | 节油指标表-日表 | 3,424 | 114 | 2017-01-01 ~ 2026-05-17 | 日维度汇总 |
| 3 | t_ads_sfuel_stat_m | 节油指标表-月表 | 113 | 145 | 201701 ~ 202605 | 月维度汇总 |
| 4 | t_ads_sfuel_stat_route_m | 节油小站-航线统计信息月表 | 84,799 | 83 | 2017-01 ~ 2026-05 | 航线×月维度 |
| 5 | v_dws_flt_opt_stat_d | 航班运行统计日视图 | 3,424 | 40 | 2017-01-01 ~ 2026-05-17 | 航班正常率、延误、返航备降 |

---

## 表关系

```
t_ads_sfuel_stat_dtl (航班明细, 135万条)
        │
        ├── 聚合 ──→ t_ads_sfuel_stat_d (日表, 3424条)
        │                    │
        │                    └── 聚合 ──→ t_ads_sfuel_stat_m (月表, 113条)
        │                                           │
        │                                           └── 航线维度 ──→ t_ads_sfuel_stat_route_m (航线月表, 84799条)
        │
        └── v_dws_flt_opt_stat_d (航班运行视图, 3424条)
```

---

## 粒度说明

| 表 | 粒度 | 主键 |
|----|------|------|
| t_ads_sfuel_stat_dtl | 航班ID (LEG_ID) | LEG_ID |
| t_ads_sfuel_stat_d | 日期 (FLIGHT_DATE) | STATISTIC_DATE |
| t_ads_sfuel_stat_m | 月份 (FLIGHT_MONTH) | STATISTIC_DATE |
| t_ads_sfuel_stat_route_m | 航线×月份 | ROUTE_CODE4 + FLIGHT_MONTH |
| v_dws_flt_opt_stat_d | 日期 (CAL_DAY) | CAL_DAY |

---

## 字段统计

### t_ads_sfuel_stat_dtl (91字段)

| 类别 | 字段数 | 主要字段 |
|------|--------|----------|
| 航班信息 | 15 | LEG_ID, FLIGHT_NO, AC_NO, FLIGHT_DATE, DEPT_AIRPORT, ARR_AIRPORT |
| 油耗数据 | 20 | CHOCK_FUEL, AIRBORNE_FUEL, TAXI_FUEL, APU_FUEL, EXTRA_FUEL |
| 时间数据 | 12 | CHOCK_TIME, AIRBORNE_TIME, TAXI_TIME, TAXI_IN/OUT_TIME |
| 计划数据 | 15 | PLAN_CHOCK_FUEL, PLAN_AIRBORNE_FUEL, PLAN_TAXI_FUEL |
| 效率指标 | 10 | CHOCK_FUEL_H, AIRBORNE_FUEL_H, RTK_FUEL, ATK_FUEL |
| CI执行率 | 4 | CI_POINT_RATE, NO_CI_SLOW_RATE, NO_CI_FAST_RATE |
| 运行标志 | 8 | IS_DIRECT, IS_ORBIT, IS_SINGLE_TAXI, FLIGHT_STATUS |
| 高度数据 | 6 | PLAN_ALTITUDE, ACTUAL_ALTITUDE, ABOVE/BELOW_PLAN_ALTITUDE |
| 业载数据 | 4 | PAYLOAD, LANDING_FUEL |
| 其他 | 10 | CREATOR, CREATE_TIME, UPDATE_TIME, IS_VALID |

### t_ads_sfuel_stat_m (145字段)

月表包含更丰富的汇总指标，包括：
- APU使用指标（apu_time_sum, apu_cycle_sum, apu_ct_rate 等）
- 机型细分（neo, sharklets, wingtip, a321）
- 单发滑行率分机场（zlxy, zggg, zspd, zuck, zlll, zugy）
- 临时航路使用率（x11, x33, v50）

---

## 数据质量规则

### 有效记录过滤条件

```sql
WHERE FLIGHT_TYPE NOT IN (5, 6, 7, 8)  -- 剔除调机、试飞、训练、本场训练
  AND FLIGHT_STATUS = 0                  -- 正常航班
  AND ALTERNATE_REGULAR = 0            -- 非备降后的正班
  AND IS_VALID = 0                     -- 有效标志
```

### 异常值检查

```sql
-- 耗油异常
CHOCK_FUEL_H > 10000  -- 超过10000kg/h视为异常

-- 高度异常
ACTUAL_ALTITUDE < 0 OR ACTUAL_ALTITUDE > 50000  -- ft

-- 落地剩油
ACTUAL_LANDING_FUEL < 0  -- 不应为负值
```

---

## 航班类型说明

| FLIGHT_TYPE | 说明 |
|-------------|------|
| 1 | 正班 |
| 2 | 补班 |
| 3 | 加班 |
| 4 | 包机 |
| 5 | 调机（剔除） |
| 6 | 试飞（剔除） |
| 7 | 训练（剔除） |
| 8 | 本场训练（剔除） |

---

## 航班状态说明

| FLIGHT_STATUS | 说明 |
|---------------|------|
| 0 | 正常 |
| 1 | 返航 |
| 2 | 备降 |
| 3 | 取消 |
| 9 | 删除 |

---

## 相关文件

- 数据字典：`/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/`
- 数据口径手册：`/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/航油成本数据口径手册.md`
- SQL查询样例：`/Users/fox/Documents/Obsidian Vault/自动笔记/03-数据资产/01-数据治理/航油成本数据字典/航油成本数据逻辑代码样例.md`
