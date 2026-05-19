#!/usr/bin/env python3
"""从 zentao zt_demand_pool 导出 CSV，供需求池平台导入"""
import sqlite3
import csv

ZANTAO_DB = '/Users/fox/DB/analysis.db'
OUTPUT_CSV = '/Users/fox/Claude Code/projects/requirement-pool-hermes/data/zt_demand_pool_export.csv'

# 字段映射：(zt原始字段, 需求池平台header字段名)
FIELDS = [
    ('demand_id',          'demand_id'),
    ('demand_name',        'demand_name'),
    ('demand_status',      'demand_status'),
    ('demand_desc',        'demand_desc'),
    ('businessobjective', 'businessobjective'),
    ('businessdesc',       'businessdesc'),
    ('business_id',        'business_id'),
    ('business_name',      'business_name'),
    ('business_status',    'business_status'),
    ('business_review_status', 'business_review_status'),
    ('proj_approval_id',   'proj_approval_id'),
    ('approval_status',    'approval_status'),
    ('approval_name',      'approval_name'),
    ('business_pm_name',   'business_pm_name'),
    ('responsible_dept_name', 'responsible_dept_name'),
    ('deadline',           'deadline'),
    ('business_created_date', 'business_created_date'),
    ('business_edited_date',  'last_modified'),
    ('pri',                'importance'),
    ('reason_type',        'reason_type'),
    ('dept',               'department'),
    ('begin_time',         'begin_time'),
    ('end_time',           'end_time'),
    ('type',               'type'),
    ('model',              'model'),
]

conn = sqlite3.connect(ZANTAO_DB)
cur = conn.cursor()

cols = [f[0] for f in FIELDS]
cur.execute(f'SELECT {", ".join(cols)} FROM zt_demand_pool ORDER BY demand_id')
rows = cur.fetchall()
conn.close()

with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([f[1] for f in FIELDS])
    writer.writerows(rows)

print(f'导出成功: {len(rows)} 条 → {OUTPUT_CSV}')