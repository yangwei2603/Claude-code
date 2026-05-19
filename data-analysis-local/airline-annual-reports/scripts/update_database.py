#!/usr/bin/env python3
"""
将提取的利用率数据更新到 external_data.db 的 airline_annual_report 表

用法: python3 update_database.py [年份]
"""
import os
import sys
import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PARSED_DIR = PROJECT_ROOT / "parsed"
DB_PATH = "/Users/fox/DB/external_data.db"

def load_parsed_data(year: int = None) -> dict:
    """加载已解析的数据"""
    parsed_file = PARSED_DIR / "utilization_data.json"
    if not parsed_file.exists():
        print(f"[错误] 解析结果文件不存在: {parsed_file}")
        print(f"请先运行: python3 parse_utilization.py")
        sys.exit(1)

    with open(parsed_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    if year:
        return {k: v for k, v in all_data.items() if str(v.get("year")) == str(year)}
    return all_data


def update_database(airline: str, year: int, data: dict, conn: sqlite3.Connection):
    """
    更新单条记录到 airline_annual_report 表
    """
    cur = conn.cursor()

    # 检查记录是否存在
    cur.execute("""
        SELECT id FROM airline_annual_report
        WHERE airline_name = ? AND report_year = ? AND report_type = 'annual'
    """, (airline, year))

    existing = cur.fetchone()

    plf = data.get("passenger_load_factor_pct")
    util = data.get("aircraft_utilization_hrs_per_day")
    avail = data.get("availability_pct")

    if existing:
        # UPDATE
        cur.execute("""
            UPDATE airline_annual_report
            SET passenger_load_factor = ?,
                data_source = ?
            WHERE id = ?
        """, (
            plf,
            f"年报PDF提取/{json.dumps(data, ensure_ascii=False)[:200]}",
            existing[0]
        ))
        print(f"  [更新] {airline} {year}: 客座率={plf}%")
    else:
        # INSERT（只更新我们有数据的字段）
        cur.execute("""
            INSERT INTO airline_annual_report
            (airline_name, report_year, report_type, passenger_load_factor, fleet_size, data_source)
            VALUES (?, ?, 'annual', ?, NULL, ?)
        """, (
            airline,
            year,
            plf,
            f"年报PDF提取/{json.dumps(data, ensure_ascii=False)[:200]}"
        ))
        print(f"  [新增] {airline} {year}: 客座率={plf}%")


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else None

    print(f"{'='*60}")
    print("更新数据库 - 利用率数据")
    print(f"数据库: {DB_PATH}")
    print(f"解析数据目录: {PARSED_DIR}")
    if year:
        print(f"目标年份: {year}")
    print(f"{'='*60}")

    # 加载数据
    all_parsed = load_parsed_data(year)

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    updated = 0
    for key, data in all_parsed.items():
        if data.get("status") != "success":
            continue
        airline = data.get("airline")
        yr = data.get("year")
        if not airline or not yr:
            continue

        try:
            update_database(airline, yr, data, conn)
            updated += 1
        except Exception as e:
            print(f"  [错误] {airline} {yr}: {e}")

    conn.commit()
    conn.close()

    print(f"\n完成，共更新 {updated} 条记录")

if __name__ == "__main__":
    main()
