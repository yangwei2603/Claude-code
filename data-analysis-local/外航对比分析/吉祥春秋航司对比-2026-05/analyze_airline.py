# -*- coding: utf-8 -*-
"""
吉祥航空 vs 春秋航空 成本与收入对比分析
日期：2026-05-10
数据来源：/Users/fox/DB/external_data.db
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

OUTPUT_DIR = '/Users/fox/Claude Code/data-analysis-local/吉祥春秋航司对比-20260510/charts'
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# === 加载数据 ===
conn = sqlite3.connect('/Users/fox/DB/external_data.db')
df = pd.read_sql("""
    SELECT airline_name, stock_code, report_year, report_type,
           revenue, net_profit, gross_margin, net_margin, roe,
           passengers_million, passenger_load_factor, fleet_size,
           asset_liability_ratio, eps, operating_cash_flow
    FROM airline_annual_report
    WHERE airline_name IN ('吉祥航空', '春秋航空')
    AND report_type = 'annual'
    ORDER BY airline_name, report_year
""", conn)
conn.close()

df.columns