#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
航油成本分析脚本模板
使用方法: python scripts/analyze_*.py

数据库: /Users/fox/DB/analysis.db
表: t_ads_sfuel_stat_dtl (航班明细)
    t_ads_sfuel_stat_d (日表)
    t_ads_sfuel_stat_m (月表)
    t_ads_sfuel_stat_route_m (航线月表)
"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# 数据库路径
DB_PATH = '/Users/fox/DB/analysis.db'

# 输出目录
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/../charts'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def query_data(sql, params=None):
    """执行查询并返回DataFrame"""
    conn = get_connection()
    try:
        if params:
            return pd.read_sql(sql, conn, params=params)
        return pd.read_sql(sql, conn)
    finally:
        conn.close()


def save_chart(fig, filename):
    """保存图表"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"图表已保存: {filepath}")
    return filepath


# ============================================
# 分析函数模板
# ============================================

def analyze_monthly_fuel():
    """月度油耗汇总分析"""
    sql = """
    SELECT
        FLIGHT_MONTH,
        COUNT(*) AS FLIGHT_CNT,
        ROUND(SUM(CHOCK_FUEL) / 1000, 2) AS CHOCK_FUEL_TON,
        ROUND(SUM(CHOCK_FUEL) / (SUM(CHOCK_TIME) / 60), 2) AS CHOCK_FUEL_H,
        ROUND(AVG(CI_POINT_RATE), 4) AS CI_POINT_RATE_AVG
    FROM t_ads_sfuel_stat_dtl
    WHERE FLIGHT_TYPE IN (1,2,3,4)
      AND FLIGHT_STATUS = 0
      AND IS_VALID = 0
    GROUP BY FLIGHT_MONTH
    ORDER BY FLIGHT_MONTH
    """
    df = query_data(sql)
    print(df.head())
    return df


def analyze_route_fuel():
    """航线油耗排名分析"""
    sql = """
    SELECT
        DEPT_AIRPORT || '-' || ARR_AIRPORT AS ROUTE,
        COUNT(*) AS FLIGHT_CNT,
        ROUND(SUM(CHOCK_FUEL) / 1000, 2) AS CHOCK_FUEL_TON,
        ROUND(AVG(CHOCK_FUEL_H), 2) AS AVG_CHOCK_FUEL_H,
        ROUND(AVG(CI_POINT_RATE), 4) AS CI_POINT_RATE
    FROM t_ads_sfuel_stat_dtl
    WHERE FLIGHT_TYPE IN (1,2,3,4)
      AND FLIGHT_STATUS = 0
      AND IS_VALID = 0
    GROUP BY DEPT_AIRPORT, ARR_AIRPORT
    HAVING COUNT(*) >= 50
    ORDER BY CHOCK_FUEL_TON DESC
    LIMIT 20
    """
    df = query_data(sql)
    print(df.head())
    return df


def analyze_ci_execution():
    """CI执行率分析"""
    sql = """
    SELECT
        FLIGHT_MONTH,
        COUNT(*) AS FLIGHT_CNT,
        ROUND(AVG(CI_POINT_RATE), 4) AS CI_POINT_RATE_AVG,
        ROUND(SUM(CASE WHEN CI_POINT_RATE >= 0.6 THEN 1 ELSE 0 END) / COUNT(*), 4) AS CI_EXECUTE_RATE,
        ROUND(AVG(NO_CI_SLOW_RATE), 4) AS NO_CI_SLOW_RATE,
        ROUND(AVG(NO_CI_FAST_RATE), 4) AS NO_CI_FAST_RATE
    FROM t_ads_sfuel_stat_dtl
    WHERE FLIGHT_TYPE IN (1,2,3,4)
      AND FLIGHT_STATUS = 0
      AND CI_POINT_RATE IS NOT NULL
      AND IS_VALID = 0
    GROUP BY FLIGHT_MONTH
    ORDER BY FLIGHT_MONTH
    """
    df = query_data(sql)
    print(df.head())
    return df


def analyze_aircraft_efficiency():
    """机型效率对比"""
    sql = """
    SELECT
        AC_TYPE,
        COUNT(*) AS FLIGHT_CNT,
        ROUND(AVG(CHOCK_FUEL_H), 2) AS AVG_CHOCK_FUEL_H,
        ROUND(AVG(AIRBORNE_FUEL_H), 2) AS AVG_AIRBORNE_FUEL_H,
        ROUND(AVG(PASS_KILOMETRE_FUEL), 4) AS AVG_PASS_KM_FUEL,
        ROUND(AVG(RTK_FUEL), 4) AS AVG_RTK_FUEL
    FROM t_ads_sfuel_stat_dtl
    WHERE FLIGHT_TYPE IN (1,2,3,4)
      AND FLIGHT_STATUS = 0
      AND AC_TYPE IS NOT NULL
      AND IS_VALID = 0
    GROUP BY AC_TYPE
    HAVING COUNT(*) >= 100
    ORDER BY AVG_CHOCK_FUEL_H ASC
    """
    df = query_data(sql)
    print(df.head())
    return df


# ============================================
# 主函数
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("航油成本分析")
    print("=" * 60)

    # 示例：执行月度油耗分析
    print("\n--- 月度油耗汇总 ---")
    df_monthly = analyze_monthly_fuel()

    # 示例：执行航线油耗排名
    print("\n--- 航线油耗TOP20 ---")
    df_route = analyze_route_fuel()

    # 示例：执行CI执行率分析
    print("\n--- CI执行率分析 ---")
    df_ci = analyze_ci_execution()

    print("\n分析完成!")
