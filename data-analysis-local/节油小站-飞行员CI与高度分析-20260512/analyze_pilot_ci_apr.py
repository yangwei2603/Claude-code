#!/usr/bin/env python3
"""节油小站飞行员CI与高度分析 - 4月航班量≥20班过滤版"""

import sys
import sqlite3
import json
from pathlib import Path

DB_PATH = "/Users/fox/DB/analysis.db"
OUTPUT_DIR = Path("/Users/fox/Claude Code/data-analysis-local/节油小站-飞行员CI与高度分析-20260512")

def get_pilot_stats():
    """获取4月份航班量≥20班的飞行员统计"""
    conn = sqlite3.connect(DB_PATH)

    # 计算每条航线平均
    route_sql = """
    SELECT "航线四字码",
           AVG(CI执行率) as route_ci_avg,
           AVG("实际高度_AVG(英尺）") as route_alt_avg
    FROM pilot_route_monthly_stats
    WHERE "日历月" = '2026-04' AND "是否有效：0-是，1-否\" = 0
    GROUP BY "航线四字码\"
    """
    route_avg = {row[0]: {"ci": row[1], "alt": row[2]} for row in conn.execute(route_sql)}

    # 飞行员汇总
    pilot_sql = """
    SELECT "责任机长工号", "责任机长姓名", COUNT(*) as flight_cnt,
           AVG(CI执行率) as avg_ci,
           AVG("实际高度_AVG(英尺）") as avg_alt
    FROM pilot_route_monthly_stats
    WHERE "日历月" = '2026-04' AND "是否有效：0-是，1-否\" = 0
    GROUP BY "责任机长工号", "责任机长姓名"
    HAVING COUNT(*) >= 20
    ORDER BY avg_ci ASC
    """

    pilots = []
    for row in conn.execute(pilot_sql):
        emp_no = row[0]
        name = row[1]
        flight_cnt = row[2]
        avg_ci = row[3]
        avg_alt = row[4]

        # 计算对标航线平均
        pilot_routes_sql = """
        SELECT DISTINCT \"航线四字码\"
        FROM pilot_route_monthly_stats
        WHERE \"责任机长工号\" = ? AND \"日历月\" = '2026-04' AND \"是否有效：0-是，1-否\" = 0
        """
        route_codes = [r[0] for r in conn.execute(pilot_routes_sql, (emp_no,))]

        route_ci_list = [route_avg[rc]["ci"] for rc in route_codes if rc in route_avg]
        route_alt_list = [route_avg[rc]["alt"] for rc in route_codes if rc in route_avg]

        avg_route_ci = sum(route_ci_list) / len(route_ci_list) if route_ci_list else 0
        avg_route_alt = sum(route_alt_list) / len(route_alt_list) if route_alt_list else 0
        alt_gap = avg_alt - avg_route_alt

        pilots.append({
            "emp_no": int(emp_no) if emp_no else 0,
            "name": name,
            "flight_cnt": flight_cnt,
            "avg_ci": round(avg_ci * 100, 1),
            "avg_alt": round(avg_alt, 0),
            "avg_route_alt": round(avg_route_alt, 0),
            "alt_gap": round(alt_gap, 0),
            "ci_gap": round((avg_ci - avg_route_ci) * 100, 1) if avg_route_ci > 0 else 0
        })

    conn.close()
    return pilots

def get_route_details(emp_no):
    """获取飞行员的航线明细"""
    conn = sqlite3.connect(DB_PATH)

    # 先算航线平均
    route_sql = """
    SELECT "航线四字码",
           AVG(CI执行率) as route_ci_avg,
           AVG("实际高度_AVG(英尺）") as route_alt_avg
    FROM pilot_route_monthly_stats
    WHERE "日历月" = '2026-04' AND "是否有效：0-是，1-否\" = 0
    GROUP BY "航线四字码\"
    """
    route_avg = {row[0]: {"ci": row[1], "alt": row[2]} for row in conn.execute(route_sql)}

    sql = """
    SELECT "航线中文", "航线四字码", "CI执行率", "实际高度_AVG(英尺）"
    FROM pilot_route_monthly_stats
    WHERE "责任机长工号\" = ? AND "日历月\" = '2026-04' AND "是否有效：0-是，1-否\" = 0
    ORDER BY "CI执行率\" ASC
    """

    routes = []
    for row in conn.execute(sql, (emp_no,)):
        route_code = row[1]
        ra = route_avg.get(route_code, {"ci": 0, "alt": 0})
        routes.append({
            "route_cn": row[0],
            "route_code": route_code,
            "ci": round(row[2] * 100, 1) if row[2] else 0,
            "alt": round(row[3], 0) if row[3] else 0,
            "route_ci_avg": round(ra["ci"] * 100, 1),
            "route_alt_avg": round(ra["alt"], 0),
            "ci_gap": round((row[2] - ra["ci"]) * 100, 1) if row[2] and ra["ci"] else 0,
            "alt_gap": round(row[3] - ra["alt"], 0) if row[3] and ra["alt"] else 0
        })

    conn.close()
    return routes

if __name__ == "__main__":
    pilots = get_pilot_stats()

    # 输出JSON供本地模型分析
    result = {
        "month": "2026-04",
        "min_flights": 20,
        "total_pilots": len(pilots),
        "pilots": pilots[:50]  # 前50名最差
    }

    output_file = OUTPUT_DIR / "pilot_analysis_apr2026.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已生成: {output_file}")
    print(f"4月份航班量≥20班的飞行员共: {len(pilots)} 人")
    print(f"CI最低5人: {[p['name'] for p in pilots[:5]]}")

    # 输出Top10低CI飞行员详细信息
    for p in pilots[:5]:
        print(f"\n{p['name']} (工号:{p['emp_no']}) - 航班{p['flight_cnt']}班, CI {p['avg_ci']}%, 高度差 {p['alt_gap']}ft")