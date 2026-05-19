#!/usr/bin/env python3
"""飞行员CI与高度双低分析 - 基于t_ads_sfuel_stat_dtl明细表

CI执行率定义：is_execute_ci = 1 的航班占比
高度执行率定义：actual_altitude >= plan_altitude - 500ft
排除 actual_altitude = 0 或 NULL 的异常记录
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "/Users/fox/DB/analysis.db"
OUTPUT_DIR = Path("/Users/fox/Claude Code/data-analysis-local/节油小站-飞行员CI与高度分析-20260512")

# 分析参数
MONTHS = [202603, 202604]
CI_THRESHOLD = 85
ALT_THRESHOLD = 15
MIN_FLIGHTS = 20

# 航班过滤条件
FLIGHT_TYPE_NORMAL = "(1, 2, 3, 4)"

def get_pilot_monthly_stats():
    """从明细表汇总飞行员月度统计"""
    conn = sqlite3.connect(DB_PATH)

    sql = """
    SELECT
        duty_captain_number,
        duty_captain_name,
        strftime('%Y%m', flight_date) as flight_month,
        COUNT(*) as flight_cnt,
        -- CI执行率：is_execute_ci = 1 的航班占比（分子分母都排除NULL）
        SUM(CASE WHEN is_execute_ci = 1 THEN 1 ELSE 0 END) * 100.0
            / NULLIF(SUM(CASE WHEN is_execute_ci IN (0, 1) THEN 1 ELSE 0 END), 0) as ci_rate,
        -- 高度执行率：actual_altitude >= plan_altitude - 500 的航班占比
        -- 排除 actual_altitude = 0 或 NULL 的异常记录
        SUM(CASE
            WHEN actual_altitude IS NOT NULL AND actual_altitude != 0
            AND (actual_altitude - plan_altitude) >= -500
            THEN 1 ELSE 0 END) * 100.0
            / NULLIF(SUM(CASE
            WHEN actual_altitude IS NOT NULL AND actual_altitude != 0
            THEN 1 ELSE 0 END), 0) as alt_rate
    FROM t_ads_sfuel_stat_dtl
    WHERE flight_date >= '2026-03-01' AND flight_date < '2026-05-01'
    AND is_valid = 0
    AND flight_status = 0
    AND flight_type IN {flight_type_normal}
    AND duty_captain_number IS NOT NULL
    AND duty_captain_number != ''
    GROUP BY duty_captain_number, duty_captain_name, strftime('%Y%m', flight_date)
    HAVING flight_cnt >= {min_flights}
    ORDER BY flight_month, alt_rate ASC
    """.format(flight_type_normal=FLIGHT_TYPE_NORMAL, min_flights=MIN_FLIGHTS)

    print("执行SQL查询...")
    pilots = []
    for row in conn.execute(sql):
        pilots.append({
            "pilot_code": row[0],
            "pilot_name": row[1],
            "flight_month": int(row[2]),
            "flight_cnt": row[3],
            "ci_rate": round(row[4], 1) if row[4] is not None else 0,
            "alt_rate": round(row[5], 1) if row[5] is not None else 0
        })

    conn.close()
    return pilots

def get_monthly_stats_dict(pilots):
    """按月份组织飞行员数据"""
    monthly_stats = {m: {} for m in MONTHS}
    for p in pilots:
        if p['flight_month'] in monthly_stats:
            monthly_stats[p['flight_month']][p['pilot_code']] = p
    return monthly_stats

def calculate_weighted_avg(pilot_code, monthly_stats):
    """计算飞行员工航班量加权平均CI和高度执行率"""
    total_flights = 0
    weighted_ci = 0
    weighted_alt = 0

    for month in MONTHS:
        if pilot_code in monthly_stats[month]:
            p = monthly_stats[month][pilot_code]
            flights = p['flight_cnt']
            weighted_ci += flights * p['ci_rate']
            weighted_alt += flights * p['alt_rate']
            total_flights += flights

    if total_flights == 0:
        return None, None, None

    return (
        round(weighted_ci / total_flights, 1),
        round(weighted_alt / total_flights, 1),
        total_flights
    )

def get_dual_low_pilots_aggregated(monthly_stats):
    """找出聚合双低的飞行员"""
    all_pilots = set()
    for month in MONTHS:
        all_pilots.update(monthly_stats[month].keys())

    dual_low = []
    for pilot_code in all_pilots:
        avg_ci, avg_alt, total_flights = calculate_weighted_avg(pilot_code, monthly_stats)
        if avg_ci is None:
            continue

        is_low_ci = avg_ci < CI_THRESHOLD
        is_low_alt = avg_alt < ALT_THRESHOLD

        if is_low_ci and is_low_alt:
            latest_name = None
            for month in reversed(MONTHS):
                if pilot_code in monthly_stats[month]:
                    latest_name = monthly_stats[month][pilot_code]['pilot_name']
                    break

            monthly_status = []
            for month in MONTHS:
                if pilot_code in monthly_stats[month]:
                    p = monthly_stats[month][pilot_code]
                    monthly_status.append({
                        "month": month,
                        "flight_amt": p['flight_cnt'],
                        "ci_rate": p['ci_rate'],
                        "alt_rate": p['alt_rate'],
                        "is_low_ci": p['ci_rate'] < CI_THRESHOLD,
                        "is_low_alt": p['alt_rate'] < ALT_THRESHOLD,
                        "is_dual_low": p['ci_rate'] < CI_THRESHOLD and p['alt_rate'] < ALT_THRESHOLD
                    })
                else:
                    monthly_status.append({
                        "month": month,
                        "flight_amt": 0,
                        "ci_rate": None,
                        "alt_rate": None,
                        "is_low_ci": False,
                        "is_low_alt": False,
                        "is_dual_low": False
                    })

            dual_low_count = sum(1 for s in monthly_status if s['is_dual_low'])
            persistent_dual_low = dual_low_count >= 2

            dual_low.append({
                "pilot_code": pilot_code,
                "pilot_name": latest_name,
                "total_flights": total_flights,
                "avg_ci_rate": avg_ci,
                "avg_alt_rate": avg_alt,
                "dual_low_months": dual_low_count,
                "persistent_dual_low": persistent_dual_low,
                "monthly_status": monthly_status
            })

    dual_low.sort(key=lambda x: x['avg_ci_rate'] + x['avg_alt_rate'])
    return dual_low

def get_pilot_routes(pilot_code):
    """获取飞行员常飞航线"""
    conn = sqlite3.connect(DB_PATH)

    sql = """
    SELECT
        dept_airport || '-' || arr_airport as route_code,
        dept_airport || '-' || arr_airport as route_name,
        COUNT(*) as cnt,
        SUM(CASE WHEN is_execute_ci = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as avg_ci,
        AVG(actual_altitude) as avg_alt,
        AVG(plan_altitude) as plan_alt
    FROM t_ads_sfuel_stat_dtl
    WHERE flight_date >= '2026-03-01' AND flight_date < '2026-05-01'
    AND is_valid = 0
    AND flight_status = 0
    AND flight_type IN (1, 2, 3, 4)
    AND duty_captain_number = ?
    GROUP BY dept_airport, arr_airport
    ORDER BY cnt DESC
    LIMIT 10
    """

    routes = []
    for row in conn.execute(sql, (pilot_code,)):
        routes.append({
            "route_cn": row[1],
            "route_code": row[0],
            "flight_cnt": row[2],
            "ci": round(row[3], 1) if row[3] else 0,
            "route_ci_avg": 0,
            "ci_gap": 0,
            "alt": round(row[4], 0) if row[4] else 0,
            "route_alt_avg": round(row[5], 0) if row[5] else 0,
            "alt_gap": 0
        })

    conn.close()
    return routes

def get_fleet_stats(monthly_stats):
    """计算机队整体统计"""
    all_pilots = []
    for month in MONTHS:
        all_pilots.extend(monthly_stats[month].values())

    ci_rates = [p['ci_rate'] for p in all_pilots if p['ci_rate'] > 0]
    alt_rates = [p['alt_rate'] for p in all_pilots if p['alt_rate'] > 0]

    return {
        "avg_ci_rate": round(sum(ci_rates) / len(ci_rates), 1) if ci_rates else 0,
        "avg_alt_rate": round(sum(alt_rates) / len(alt_rates), 1) if alt_rates else 0,
    }

if __name__ == "__main__":
    print("=" * 60)
    print("飞行员CI与高度双低分析 (基于t_ads_sfuel_stat_dtl)")
    print("分析月份: " + ",".join(str(m) for m in MONTHS))
    print("CI执行率: is_execute_ci = 1 的航班占比")
    print("高度执行率: actual_altitude >= plan_altitude - 500")
    print("=" * 60)

    print("\n从明细表汇总飞行员月度数据...")
    pilots = get_pilot_monthly_stats()
    print("汇总后飞行员记录数: " + str(len(pilots)))

    monthly_stats = get_monthly_stats_dict(pilots)

    for month in MONTHS:
        print("  " + str(month) + "月: " + str(len(monthly_stats[month])) + " 名飞行员")

    fleet_stats = get_fleet_stats(monthly_stats)
    print("\n机队平均: CI=" + str(fleet_stats['avg_ci_rate']) + "%, 高度执行率=" + str(fleet_stats['avg_alt_rate']) + "%")

    print("\n=== 各月双低统计 ===")
    for month in MONTHS:
        pilots_m = monthly_stats[month]
        low_ci = [p for p in pilots_m.values() if p['ci_rate'] < CI_THRESHOLD]
        low_alt = [p for p in pilots_m.values() if p['alt_rate'] < ALT_THRESHOLD]
        low_ci_codes = set(p['pilot_code'] for p in low_ci)
        dual_low = [p for p in low_alt if p['pilot_code'] in low_ci_codes]
        print("  " + str(month) + "月: 总" + str(len(pilots_m)) + "人, 低CI " + str(len(low_ci)) + "人, 低高度 " + str(len(low_alt)) + "人, 双低 " + str(len(dual_low)) + "人")

    print("\n=== 聚合双低分析 (CI<" + str(CI_THRESHOLD) + "% 且 高度执行率<" + str(ALT_THRESHOLD) + "%) ===")
    dual_low_agg = get_dual_low_pilots_aggregated(monthly_stats)
    print("聚合双低飞行员: " + str(len(dual_low_agg)) + " 人")

    persistent = [p for p in dual_low_agg if p['persistent_dual_low']]
    new = [p for p in dual_low_agg if not p['persistent_dual_low']]
    print("  持续双低(2个月+): " + str(len(persistent)) + " 人")
    print("  新增双低(1个月): " + str(len(new)) + " 人")

    print("\n=== 双低飞行员航线明细 ===")
    for p in dual_low_agg:
        routes = get_pilot_routes(p['pilot_code'])
        p['routes'] = routes

        status_str = "/".join([
            str(s['month']) + ("✓" if s['is_dual_low'] else "✗")
            for s in p['monthly_status']
        ])
        print("\n" + p['pilot_name'] + " (工号:" + p['pilot_code'] + ") [" + status_str + "]")
        print("  合计: " + str(p['total_flights']) + "班, CI=" + str(p['avg_ci_rate']) + "%, 高度=" + str(p['avg_alt_rate']) + "%")
        print("  常飞航线:")
        for r in routes[:5]:
            print("    " + r['route_cn'] + ": " + str(r['flight_cnt']) + "班, CI=" + str(r['ci']) + "%")

    result = {
        "months": MONTHS,
        "threshold_ci": CI_THRESHOLD,
        "threshold_alt": ALT_THRESHOLD,
        "fleet_stats": fleet_stats,
        "stats": {
            "total_months": len(MONTHS),
            "dual_low_count": len(dual_low_agg),
            "persistent_dual_low": len(persistent),
            "new_dual_low": len(new),
        },
        "dual_low_pilots": dual_low_agg
    }

    output_file = OUTPUT_DIR / "dual_low_pilots_3months.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n数据已保存: " + str(output_file))
    print("=" * 60)