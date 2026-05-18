#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 t_ads_sfuel_stat_dtl 表中数值类 TEXT 字段转换为 REAL 类型
简化版：直接执行，无需交互
"""

import sqlite3, sys

DB_PATH = '/Users/fox/DB/analysis.db'

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

def clean(val):
    if val is None or val == '':
        return None
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = str(val).replace(',', '').strip()
    if cleaned in ('', 'NULL', 'NaN'):
        return None
    try:
        return float(cleaned)
    except:
        return None

print("Step 1: Connect", flush=True)
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
cur = conn.cursor()

print("Step 2: Get field list", flush=True)
cur.execute('SELECT name, type FROM pragma_table_info("t_ads_sfuel_stat_dtl") ORDER BY cid')
field_order = [r[0] for r in cur.fetchall()]
schema_dict = {row[0]: row[1] for row in cur.fetchall()}
print(f"  Total fields: {len(field_order)}", flush=True)

print("Step 3: Count rows", flush=True)
cur.execute("SELECT COUNT(*) FROM t_ads_sfuel_stat_dtl")
total = cur.fetchone()[0]
print(f"  Total rows: {total}", flush=True)

# 构建 CREATE TABLE SQL
print("Step 4: Generate CREATE SQL", flush=True)
type_map = {'INTEGER': 'INTEGER', 'REAL': 'REAL', 'TEXT': 'TEXT'}
lines = ["CREATE TABLE t_ads_sfuel_stat_dtl_new ("]
for fname in field_order:
    orig_type = schema_dict.get(fname, 'TEXT')
    new_type = 'REAL' if fname in TEXT_TO_REAL_FIELDS else orig_type
    lines.append(f'    "{fname}" {new_type},')
lines[-1] = lines[-1].rstrip(',')
lines.append(")")
create_sql = '\n'.join(lines)

print("Step 5: Create new table", flush=True)
cur.execute("DROP TABLE IF EXISTS t_ads_sfuel_stat_dtl_new")
cur.execute(create_sql)
conn.commit()
print("  Done creating", flush=True)

print("Step 6: Read and transform data", flush=True)
cur.execute("SELECT * FROM t_ads_sfuel_stat_dtl")
cols = [desc[0] for desc in cur.description]
col_idx = {c: i for i, c in enumerate(cols)}
num_cols = TEXT_TO_REAL_FIELDS.intersection(set(cols))

batch_size = 20000
migrated = 0

while True:
    rows = cur.fetchmany(batch_size)
    if not rows:
        break
    new_rows = []
    for row in rows:
        nr = list(row)
        for c in num_cols:
            nr[col_idx[c]] = clean(row[col_idx[c]])
        new_rows.append(nr)
    ph = ','.join(['?' for _ in cols])
    cur.executemany(f"INSERT INTO t_ads_sfuel_stat_dtl_new VALUES ({ph})", new_rows)
    migrated += len(new_rows)
    print(f"  Migrated {migrated}/{total}", flush=True)

conn.commit()
print("Step 7: Verify", flush=True)
cur.execute("SELECT COUNT(*) FROM t_ads_sfuel_stat_dtl_new")
new_count = cur.fetchone()[0]
cur.execute("SELECT AVG(chock_fuel) FROM t_ads_sfuel_stat_dtl_new WHERE chock_fuel IS NOT NULL")
new_avg = cur.fetchone()[0]
cur.execute("SELECT AVG(CAST(chock_fuel AS REAL)) FROM t_ads_sfuel_stat_dtl WHERE chock_fuel IS NOT NULL")
old_avg = cur.fetchone()[0]
print(f"  New count: {new_count}, Old: {total}")
print(f"  chock_fuel avg: new={new_avg:.2f}, old(CAST)={old_avg:.2f}")

print("Step 8: Replace tables", flush=True)
cur.execute("DROP TABLE IF EXISTS t_ads_sfuel_stat_dtl_backup")
cur.execute("ALTER TABLE t_ads_sfuel_stat_dtl RENAME TO t_ads_sfuel_stat_dtl_backup")
cur.execute("ALTER TABLE t_ads_sfuel_stat_dtl_new RENAME TO t_ads_sfuel_stat_dtl")
conn.commit()

cur.execute("SELECT name, type FROM pragma_table_info('t_ads_sfuel_stat_dtl') WHERE name IN ('chock_fuel','actual_altitude','plan_altitude')")
print("Final schema check:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("DONE!", flush=True)