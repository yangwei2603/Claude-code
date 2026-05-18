#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 CSV 重新加载 t_ads_sfuel_stat_dtl 表数据
CSV 文件来自归档.zip解压
"""

import sqlite3
import csv
import os

DB_PATH = '/Users/fox/DB/analysis.db'
CSV_DIR = '/tmp/archive_extract'

TEXT_TO_REAL_FIELDS = {
    'chock_fuel', 'plan_chock_fuel', 'chock_fuel_h', 'plan_chock_fuel_h',
    'airborne_time', 'plan_airborne_time', 'plan_chock_time',
    'airborne_fuel', 'plan_airborne_fuel', 'airborne_fuel_h', 'plan_airborne_fuel_h',
    'plan_airborne_fuel_extra_h',
    'taxi_in_time', 'taxi_in_fuel', 'taxi_out_time', 'taxi_out_fuel',
    'taxi_time', 'taxi_fuel', 'plan_taxi_time', 'plan_taxi_fuel',
    'actual_route_mile', 'plan_route_mile', 'actual_cruise_dis', 'plan_cruise_dis',
    'apu_fuel', 'direct_reduce_mile', 'orbit_add_mile',
    'actual_altitude', 'plan_altitude', 'above_plan_altitude', 'below_plan_altitude',
    'actual_landing_fuel', 'plan_landing_fuel',
    'actual_payload', 'plan_payload',
    'extra_fuel', 'plan_extra_fuel', 'plan_cxtra_fuel', 'plan_dxtra_fuel',
    'plan_alt_distance', 'pass_kilometre_fuel', 'seat_kilometre_fuel',
    'rtk_fuel', 'atk_fuel',
    'touch_down_fuel', 'acars_taxi_in_time', 'acars_taxi_in_fuel',
    'acars_taxi_out_time', 'acars_taxi_out_fuel',
    'foc_chock_fuel', 'foc_chock_time', 'foc_chock_fuel_h',
    'takeoff_weight', 'plan_takeoff_weight',
    'apu_time', 'transit_time', 'route_length',
    'apu_fuel_rep607', 'chock_apu_fuel', 'airline_distance',
}


def clean_numeric(val, is_numeric):
    """将文本数值转为 REAL，处理千分位逗号和空值"""
    if val is None or val == '':
        return None
    if isinstance(val, (int, float)):
        return float(val) if is_numeric else val
    if not is_numeric:
        return val
    cleaned = str(val).replace(',', '').strip()
    if cleaned in ('', 'NULL', 'NaN'):
        return None
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def create_table(cur, field_order):
    """创建正确类型的表"""
    # 完整的字段类型映射
    field_types = {
        'statistic_date': 'INTEGER',
        'leg_id': 'TEXT',
        'flight_no': 'TEXT',
        'flight_date': 'TEXT',
        'ac_no': 'TEXT',
        'carrier': 'TEXT',
        'dori': 'INTEGER',
        'flight_type': 'INTEGER',
        'flight_status': 'INTEGER',
        'is_delay': 'REAL',
        'dept_airport': 'TEXT',
        'arr_airport': 'TEXT',
        'ci_point_rate': 'REAL',
        'no_ci_slow_rate': 'REAL',
        'no_ci_fast_rate': 'REAL',
        'chock_time': 'REAL',
        'chock_fuel': 'REAL',
        'plan_chock_time': 'REAL',
        'plan_chock_fuel': 'REAL',
        'chock_fuel_h': 'REAL',
        'plan_chock_fuel_h': 'REAL',
        'airborne_time': 'REAL',
        'plan_airborne_time': 'REAL',
        'airborne_fuel': 'REAL',
        'plan_airborne_fuel': 'REAL',
        'airborne_fuel_h': 'REAL',
        'plan_airborne_fuel_h': 'REAL',
        'plan_airborne_fuel_extra_h': 'REAL',
        'taxi_in_time': 'REAL',
        'taxi_in_fuel': 'REAL',
        'taxi_out_time': 'REAL',
        'taxi_out_fuel': 'REAL',
        'taxi_time': 'REAL',
        'taxi_fuel': 'REAL',
        'plan_taxi_time': 'REAL',
        'plan_taxi_fuel': 'REAL',
        'actual_route_mile': 'REAL',
        'plan_route_mile': 'REAL',
        'actual_cruise_dis': 'REAL',
        'plan_cruise_dis': 'REAL',
        'apu_fuel': 'REAL',
        'is_direct': 'INTEGER',
        'is_orbit': 'INTEGER',
        'direct_reduce_mile': 'REAL',
        'orbit_add_mile': 'REAL',
        'actual_altitude': 'REAL',
        'plan_altitude': 'REAL',
        'above_plan_altitude': 'REAL',
        'below_plan_altitude': 'REAL',
        'actual_landing_fuel': 'REAL',
        'plan_landing_fuel': 'REAL',
        'actual_payload': 'REAL',
        'plan_payload': 'REAL',
        'extra_fuel': 'REAL',
        'plan_extra_fuel': 'REAL',
        'plan_cxtra_fuel': 'REAL',
        'plan_dxtra_fuel': 'REAL',
        'plan_alt_distance': 'REAL',
        'pass_kilometre_fuel': 'REAL',
        'seat_kilometre_fuel': 'REAL',
        'rtk_fuel': 'REAL',
        'atk_fuel': 'REAL',
        'alternate_regular': 'INTEGER',
        'creation_time': 'TEXT',
        'creator': 'TEXT',
        'update_time': 'TEXT',
        'updater': 'TEXT',
        'is_valid': 'INTEGER',
        'touch_down_fuel': 'REAL',
        'acars_taxi_in_time': 'REAL',
        'acars_taxi_in_fuel': 'REAL',
        'acars_taxi_out_time': 'REAL',
        'acars_taxi_out_fuel': 'REAL',
        'foc_chock_time': 'REAL',
        'foc_chock_fuel': 'REAL',
        'foc_chock_fuel_h': 'REAL',
        'plan_takeoff_weight': 'REAL',
        'takeoff_weight': 'REAL',
        'transit_time': 'REAL',
        'apu_time': 'REAL',
        'is_srce_acars': 'INTEGER',
        'is_single_taxi': 'INTEGER',
        'duty_captain_number': 'TEXT',
        'duty_captain_name': 'TEXT',
        'ac_type': 'TEXT',
        'route_length': 'REAL',
        'layout': 'INTEGER',
        'chock_apu_fuel': 'REAL',
        'apu_fuel_rep607': 'REAL',
        'airline_distance': 'REAL',
        'is_execute_ci': 'INTEGER',
    }

    lines = ["CREATE TABLE t_ads_sfuel_stat_dtl ("]
    for fname in field_order:
        ftype = field_types.get(fname, 'TEXT')
        lines.append(f'    "{fname}" {ftype},')
    lines[-1] = lines[-1].rstrip(',')
    lines.append(")")
    cur.execute('\n'.join(lines))


def load_csv(filepath, cur, conn, batch_size=10000):
    """加载单个 CSV 文件"""
    print(f"  Loading: {os.path.basename(filepath)}", flush=True)

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头
        cols = header
        col_idx = {c: i for i, c in enumerate(cols)}
        num_cols = TEXT_TO_REAL_FIELDS.intersection(set(cols))

        total_rows = 0
        while True:
            rows = []
            for _ in range(batch_size):
                try:
                    row = next(reader)
                    rows.append(row)
                except StopIteration:
                    break

            if not rows:
                break

            # 转换数值字段
            new_rows = []
            for row in rows:
                nr = []
                for i, (c, v) in enumerate(zip(cols, row)):
                    if c in num_cols:
                        nr.append(clean_numeric(v, True))
                    else:
                        nr.append(v if v else None)
                new_rows.append(nr)

            placeholders = ','.join(['?' for _ in cols])
            cur.executemany(f"INSERT INTO t_ads_sfuel_stat_dtl VALUES ({placeholders})", new_rows)
            total_rows += len(new_rows)
            print(f"    {total_rows}", flush=True)

            if total_rows % 50000 == 0:
                conn.commit()

    conn.commit()
    return total_rows


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # 1. 删除现有表和新表
    print("Step 1: Cleaning up tables...", flush=True)
    cur.execute("DROP TABLE IF EXISTS t_ads_sfuel_stat_dtl")
    cur.execute("DROP TABLE IF EXISTS t_ads_sfuel_stat_dtl_new")
    cur.execute("DROP TABLE IF EXISTS t_ads_sfuel_stat_dtl_backup")

    # 2. 从 CSV 获取字段顺序（使用第一个文件）
    csv_path_1 = os.path.join(CSV_DIR, "t_ads_sfuel_stat_dtl-2023之后.csv")
    with open(csv_path_1, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        field_order = next(reader)
    print(f"Step 2: Field order from CSV: {len(field_order)} fields", flush=True)

    # 3. 创建表
    print("Step 3: Creating table...", flush=True)
    create_table(cur, field_order)
    conn.commit()

    # 4. 加载两个 CSV 文件
    print("Step 4: Loading CSV data...", flush=True)
    csv_path_1 = os.path.join(CSV_DIR, "t_ads_sfuel_stat_dtl-2023之后.csv")
    csv_path_2 = os.path.join(CSV_DIR, "t_ads_sfuel_stat_dtl2023以前.csv")

    rows1 = load_csv(csv_path_1, cur, conn)
    print(f"  Loaded {rows1} rows from 2023之后", flush=True)

    rows2 = load_csv(csv_path_2, cur, conn)
    print(f"  Loaded {rows2} rows from 2023以前", flush=True)

    # 5. 验证
    print("Step 5: Verifying...", flush=True)
    cur.execute("SELECT COUNT(*) FROM t_ads_sfuel_stat_dtl")
    total = cur.fetchone()[0]
    print(f"  Total rows: {total}", flush=True)

    cur.execute("SELECT AVG(chock_fuel) FROM t_ads_sfuel_stat_dtl WHERE chock_fuel IS NOT NULL")
    avg = cur.fetchone()[0]
    print(f"  chock_fuel avg: {avg:.2f}", flush=True)

    cur.execute("SELECT name, type FROM pragma_table_info('t_ads_sfuel_stat_dtl') WHERE name IN ('chock_fuel', 'actual_altitude', 'plan_altitude')")
    print("  Schema check:")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]}", flush=True)

    conn.close()
    print("\nDONE! Data loaded successfully.", flush=True)


if __name__ == '__main__':
    main()