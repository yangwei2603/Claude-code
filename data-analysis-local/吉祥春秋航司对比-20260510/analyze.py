# -*- coding: utf-8 -*-
"""
吉祥航空 vs 春秋航空 对比分析
日期：2026-05-10
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = '/Users/fox/Claude Code/data-analysis-local/吉祥春秋航司对比-20260510'
CHARTS_DIR = os.path.join(OUTPUT_DIR, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# === 直接从数据库读取 ===
conn = sqlite3.connect('/Users/fox/DB/external_data.db')
df = pd.read_sql("""
    SELECT airline_name, report_year, report_type,
           revenue, net_profit, gross_margin,
           passengers_million, passenger_load_factor, fleet_size
    FROM airline_annual_report
    WHERE airline_name IN ('吉祥航空', '春秋航空')
    AND report_type = 'annual'
    ORDER BY airline_name, report_year
""", conn)
conn.close()

# === 数据清洗 ===
df['report_year'] = df['report_year'].astype(int)
df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')
df['net_profit'] = pd.to_numeric(df['net_profit'], errors='coerce')
df['gross_margin'] = pd.to_numeric(df['gross_margin'], errors='coerce')
df['passengers_million'] = pd.to_numeric(df['passengers_million'], errors='coerce')
df['passenger_load_factor'] = pd.to_numeric(df['passenger_load_factor'], errors='coerce')
df['fleet_size'] = pd.to_numeric(df['fleet_size'], errors='coerce')

# 计算净利率
df['net_margin'] = (df['net_profit'] / df['revenue'] * 100).round(2)
df['单机营收'] = (df['revenue'] / df['fleet_size']).round(2)

# 分离两家公司
juneyao = df[df['airline_name'] == '吉祥航空'].sort_values('report_year')
spring = df[df['airline_name'] == '春秋航空'].sort_values('report_year')

print("=== 吉祥航空 ===")
print(juneyao[['report_year','revenue','net_profit','gross_margin','net_margin','passengers_million','passenger_load_factor','fleet_size']].to_string(index=False))
print("\n=== 春秋航空 ===")
print(spring[['report_year','revenue','net_profit','gross_margin','net_margin','passengers_million','passenger_load_factor','fleet_size']].to_string(index=False))

years = juneyao['report_year'].values

# === 图表1：营收与净利润 ===
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1.1 营收趋势
ax1 = axes[0, 0]
ax1.plot(years, juneyao['revenue'].values, 'b-o', label='吉祥航空', linewidth=2, markersize=8)
ax1.plot(years, spring['revenue'].values, 'r-s', label='春秋航空', linewidth=2, markersize=8)
ax1.set_title('营业收入对比（亿元）', fontsize=12, fontweight='bold')
ax1.set_xlabel('年份')
ax1.set_ylabel('营收（亿元）')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xticks(years)

# 1.2 净利润趋势
ax2 = axes[0, 1]
ax2.plot(years, juneyao['net_profit'].values, 'b-o', label='吉祥航空', linewidth=2, markersize=8)
ax2.plot(years, spring['net_profit'].values, 'r-s', label='春秋航空', linewidth=2, markersize=8)
ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax2.set_title('净利润对比（亿元）', fontsize=12, fontweight='bold')
ax2.set_xlabel('年份')
ax2.set_ylabel('净利润（亿元）')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xticks(years)

# 1.3 旅客运输量
ax3 = axes[1, 0]
w = 0.35
ax3.bar(years - w, juneyao['passengers_million'].values, width=w*0.9, label='吉祥航空', color='steelblue')
ax3.bar(years + w, spring['passengers_million'].values, width=w*0.9, label='春秋航空', color='coral')
ax3.set_title('旅客运输量对比（百万人次）', fontsize=12, fontweight='bold')
ax3.set_xlabel('年份')
ax3.set_ylabel('旅客（百万人）')
ax3.legend()
ax3.set_xticks(years)

# 1.4 客座率
ax4 = axes[1, 1]
ax4.plot(years, juneyao['passenger_load_factor'].values, 'b-o', label='吉祥航空', linewidth=2, markersize=8)
ax4.plot(years, spring['passenger_load_factor'].values, 'r-s', label='春秋航空', linewidth=2, markersize=8)
ax4.set_title('客座率对比（%）', fontsize=12, fontweight='bold')
ax4.set_xlabel('年份')
ax4.set_ylabel('客座率（%）')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_xticks(years)
ax4.set_ylim(60, 100)

plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, 'airline_comparison_1.png'), dpi=150, bbox_inches='tight')
plt.close()
print("\n图表1已保存")

# === 图表2：盈利能力 ===
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 2.1 毛利率
ax1 = axes[0]
x = years
w = 0.35
gm_j = juneyao['gross_margin'].fillna(0).values
gm_s = spring['gross_margin'].fillna(0).values
ax1.bar(x - w/2, gm_j, w, label='吉祥航空', color='steelblue')
ax1.bar(x + w/2, gm_s, w, label='春秋航空', color='coral')
ax1.set_title('毛利率对比（%）', fontsize=12, fontweight='bold')
ax1.set_xlabel('年份')
ax1.set_ylabel('毛利率（%）')
ax1.legend()
ax1.set_xticks(x)
ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

# 2.2 净利率
ax2 = axes[1]
nm_j = juneyao['net_margin'].fillna(0).values
nm_s = spring['net_margin'].fillna(0).values
ax2.bar(x - w/2, nm_j, w, label='吉祥航空', color='steelblue')
ax2.bar(x + w/2, nm_s, w, label='春秋航空', color='coral')
ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax2.set_title('净利率对比（%）', fontsize=12, fontweight='bold')
ax2.set_xlabel('年份')
ax2.set_ylabel('净利率（%）')
ax2.legend()
ax2.set_xticks(x)

plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, 'airline_comparison_2.png'), dpi=150, bbox_inches='tight')
plt.close()
print("图表2已保存")

# === 图表3：机队效率 ===
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 3.1 机队规模
ax1 = axes[0]
ax1.plot(years, juneyao['fleet_size'].values, 'b-o', label='吉祥航空', linewidth=2, markersize=8)
ax1.plot(years, spring['fleet_size'].values, 'r-s', label='春秋航空', linewidth=2, markersize=8)
ax1.set_title('机队规模对比（架）', fontsize=12, fontweight='bold')
ax1.set_xlabel('年份')
ax1.set_ylabel('机队（架）')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xticks(years)
for i, (j, s) in enumerate(zip(juneyao['fleet_size'].values, spring['fleet_size'].values)):
    ax1.annotate(f'{int(j)}', (years[i], j), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9)
    ax1.annotate(f'{int(s)}', (years[i], s), textcoords="offset points", xytext=(0,-12), ha='center', fontsize=9)

# 3.2 单机营收效率
ax2 = axes[1]
rpj = juneyao['单机营收'].values
rps = spring['单机营收'].values
ax2.bar(x - w/2, rpj, w, label='吉祥航空', color='steelblue')
ax2.bar(x + w/2, rps, w, label='春秋航空', color='coral')
ax2.set_title('单机营收效率（亿元/架）', fontsize=12, fontweight='bold')
ax2.set_xlabel('年份')
ax2.set_ylabel('单机营收（亿元/架）')
ax2.legend()
ax2.set_xticks(x)

plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, 'airline_comparison_3.png'), dpi=150, bbox_inches='tight')
plt.close()
print("图表3已保存")

# === 关键对比数据 ===
print("\n" + "="*80)
print("关键指标对比（2023-2025）")
print("="*80)
for yr in [2023, 2024, 2025]:
    j = juneyao[juneyao['report_year']==yr].iloc[0]
    s = spring[spring['report_year']==yr].iloc[0]
    print(f"\n{yr}年:")
    print(f"  营收: 吉祥={j['revenue']:.1f}亿, 春秋={s['revenue']:.1f}亿, 差异={s['revenue']-j['revenue']:.1f}亿")
    if not pd.isna(j['net_profit']) and not pd.isna(s['net_profit']):
        print(f"  净利润: 吉祥={j['net_profit']:.1f}亿, 春秋={s['net_profit']:.1f}亿")
        print(f"  净利率: 吉祥={j['net_margin']:.1f}%, 春秋={s['net_margin']:.1f}%")
    if not pd.isna(j['passengers_million']) and not pd.isna(s['passengers_million']):
        print(f"  旅客: 吉祥={j['passengers_million']:.0f}万, 春秋={s['passengers_million']:.0f}万")
    if not pd.isna(j['passenger_load_factor']) and not pd.isna(s['passenger_load_factor']):
        print(f"  客座率: 吉祥={j['passenger_load_factor']:.1f}%, 春秋={s['passenger_load_factor']:.1f}%")

print("\n所有图表已保存到:", CHARTS_DIR)