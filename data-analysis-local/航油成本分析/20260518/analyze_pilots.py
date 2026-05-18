#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞行员高度执行率和CI执行率分析
分析最近3个月执行率低的飞行员，用于宣贯谈话
"""

import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, timedelta

DB_PATH = '/Users/fox/DB/analysis.db'
OUTPUT_DIR = '/Users/fox/Claude Code/data-analysis-local/航油成本分析-20260518'

def get_connection():
    return sqlite3.connect(DB_PATH)

def query_data(sql, params=None):
    conn = get_connection()
    try:
        if params:
            return pd.read_sql(sql, conn, params=params)
        return pd.read_sql(sql, conn)
    finally:
        conn.close()

# 最近3个月数据
end_date = '2026-05-17'
start_date = '2026-02-01'

print("=" * 60)
print("飞行员高度执行率与CI执行率分析")
print("=" * 60)
print(f"\n分析周期: {start_date} ~ {end_date}")

# 1. 查询每位飞行员的汇总数据（使用CAST处理TEXT类型数值字段）
sql = f"""
SELECT
    duty_captain_number AS pilot_no,
    duty_captain_name AS pilot_name,
    COUNT(*) AS flight_count,
    ROUND(AVG(CAST(REPLACE(ci_point_rate, ',', '') AS REAL)), 4) AS avg_ci_rate,
    ROUND(SUM(CASE WHEN CAST(REPLACE(ci_point_rate, ',', '') AS REAL) >= 0.6 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS ci_execute_rate,
    ROUND(AVG(CAST(REPLACE(above_plan_altitude, ',', '') AS REAL)), 2) AS avg_above_alt,
    ROUND(AVG(CAST(REPLACE(below_plan_altitude, ',', '') AS REAL)), 2) AS avg_below_alt,
    ROUND(AVG(CAST(REPLACE(actual_altitude, ',', '') AS REAL)), 2) AS avg_actual_alt,
    ROUND(AVG(CAST(REPLACE(plan_altitude, ',', '') AS REAL)), 2) AS avg_plan_alt,
    ROUND(AVG(CASE WHEN CAST(REPLACE(plan_altitude, ',', '') AS REAL) > 0
        THEN (CAST(REPLACE(actual_altitude, ',', '') AS REAL) - CAST(REPLACE(plan_altitude, ',', '') AS REAL)) / CAST(REPLACE(plan_altitude, ',', '') AS REAL) * 100
        ELSE 0 END), 2) AS altitude_deviation_pct
FROM t_ads_sfuel_stat_dtl
WHERE flight_date >= '{start_date}'
  AND flight_date <= '{end_date}'
  AND flight_type IN (1,2,3,4)
  AND flight_status = 0
  AND is_valid = 0
  AND ci_point_rate IS NOT NULL
  AND duty_captain_number IS NOT NULL
  AND duty_captain_number != ''
GROUP BY duty_captain_number, duty_captain_name
HAVING COUNT(*) >= 20
ORDER BY avg_ci_rate ASC, altitude_deviation_pct ASC
LIMIT 50
"""

df_pilots = query_data(sql)
print(f"\n分析飞行员数量: {len(df_pilots)}")
print("\nCI执行率最低的10位飞行员:")
print(df_pilots.head(10).to_string(index=False))

# 2. 计算整体统计
sql_all = f"""
SELECT
    COUNT(DISTINCT duty_captain_number) AS total_pilots,
    ROUND(AVG(CAST(REPLACE(ci_point_rate, ',', '') AS REAL)), 4) AS overall_ci_rate,
    ROUND(SUM(CASE WHEN CAST(REPLACE(ci_point_rate, ',', '') AS REAL) >= 0.6 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS overall_ci_execute_rate,
    ROUND(AVG(CAST(REPLACE(above_plan_altitude, ',', '') AS REAL)), 2) AS overall_avg_above,
    ROUND(AVG(CAST(REPLACE(below_plan_altitude, ',', '') AS REAL)), 2) AS overall_avg_below
FROM t_ads_sfuel_stat_dtl
WHERE flight_date >= '{start_date}'
  AND flight_date <= '{end_date}'
  AND flight_type IN (1,2,3,4)
  AND flight_status = 0
  AND is_valid = 0
  AND ci_point_rate IS NOT NULL
"""

df_overall = query_data(sql_all)
overall_stats = df_overall.iloc[0].to_dict()
print("\n整体统计:")
print(f"  飞行员总数: {overall_stats['total_pilots']}")
print(f"  平均CI点执行率: {overall_stats['overall_ci_rate']}")
print(f"  平均CI航班执行率: {overall_stats['overall_ci_execute_rate']}")

# 3. 按CI执行率分组
df_pilots['ci_level'] = pd.cut(df_pilots['avg_ci_rate'],
                               bins=[0, 0.4, 0.5, 0.6, 0.7, 1.0],
                               labels=['差(<0.4)', '较差(0.4-0.5)', '一般(0.5-0.6)', '良好(0.6-0.7)', '优秀(>0.7)'])

# 4. 按月份统计趋势
sql_monthly = f"""
SELECT
    strftime('%Y-%m', flight_date) AS month,
    COUNT(DISTINCT duty_captain_number) AS pilot_count,
    ROUND(AVG(CAST(REPLACE(ci_point_rate, ',', '') AS REAL)), 4) AS avg_ci_rate,
    ROUND(SUM(CASE WHEN CAST(REPLACE(ci_point_rate, ',', '') AS REAL) >= 0.6 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS ci_execute_rate
FROM t_ads_sfuel_stat_dtl
WHERE flight_date >= '{start_date}'
  AND flight_date <= '{end_date}'
  AND flight_type IN (1,2,3,4)
  AND flight_status = 0
  AND is_valid = 0
  AND ci_point_rate IS NOT NULL
GROUP BY strftime('%Y-%m', flight_date)
ORDER BY month
"""

df_monthly = query_data(sql_monthly)
print("\n月度趋势:")
print(df_monthly.to_string(index=False))

# 5. 需要重点关注的飞行员（CI执行率<0.82 或 高度偏离大于5%）
df_concern = df_pilots[
    (df_pilots['avg_ci_rate'] < 0.82) |
    (df_pilots['altitude_deviation_pct'] > 5) |
    (df_pilots['altitude_deviation_pct'] < -5)
].copy()
df_concern = df_concern.sort_values('avg_ci_rate')

print(f"\n需要关注的飞行员数量: {len(df_concern)}")
print("\n重点关注名单:")
print(df_concern[['pilot_no', 'pilot_name', 'flight_count', 'avg_ci_rate', 'ci_execute_rate', 'altitude_deviation_pct']].to_string(index=False))

# 6. 生成统计数据
stats = {
    'total_pilots': int(overall_stats['total_pilots']),
    'analyzed_pilots': len(df_pilots),
    'concern_pilots': len(df_concern),
    'overall_ci_rate': float(overall_stats['overall_ci_rate']),
    'overall_ci_execute_rate': float(overall_stats['overall_ci_execute_rate']),
    'overall_avg_above_alt': float(overall_stats['overall_avg_above']),
    'overall_avg_below_alt': float(overall_stats['overall_avg_below']),
    'period': f"{start_date} ~ {end_date}"
}

# 转换为可序列化格式
records = df_pilots.fillna(0).to_dict('records')
for r in records:
    for k, v in r.items():
        if pd.isna(v):
            r[k] = 0

concern_records = df_concern.fillna(0).to_dict('records')
for r in concern_records:
    for k, v in r.items():
        if pd.isna(v):
            r[k] = 0

monthly_records = df_monthly.fillna(0).to_dict('records')

# 7. 保存JSON数据
data = {
    'stats': stats,
    'pilots': records,
    'concern_pilots': concern_records,
    'monthly': monthly_records
}

data_path = os.path.join(OUTPUT_DIR, 'data.json')
with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n数据已保存: {data_path}")

print("\n分析完成!")