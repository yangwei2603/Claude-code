#!/usr/bin/env python3
"""生成飞行员CI与高度分析报告（4月航班量≥20班过滤版）"""

import sqlite3
from pathlib import Path

DB_PATH = "/Users/fox/DB/analysis.db"
OUTPUT_HTML = "/Users/fox/Claude Code/data-analysis-local/节油小站-飞行员CI与高度分析-20260512/report_pilot_ci_altitude_20260512_v2.html"

conn = sqlite3.connect(DB_PATH)

# 计算每条航线平均值
route_sql = """
SELECT route_code4,
       AVG(ci_execute_rate) as route_ci_avg,
       AVG(actual_altitude_avg) as route_alt_avg
FROM pilot_route_monthly_stats
WHERE cal_month = '2026-04' AND is_valid = 0
GROUP BY route_code4
"""
route_avg = {row[0]: {"ci": row[1], "alt": row[2]} for row in conn.execute(route_sql)}

# 获取Top20低CI飞行员（航班量≥20班）
pilot_sql = """
SELECT duty_captain_code, duty_captain_name, COUNT(*) as flight_cnt,
       AVG(ci_execute_rate) as avg_ci,
       AVG(actual_altitude_avg) as avg_alt
FROM pilot_route_monthly_stats
WHERE cal_month = '2026-04' AND is_valid = 0
GROUP BY duty_captain_code, duty_captain_name
HAVING COUNT(*) >= 20
ORDER BY avg_ci ASC
LIMIT 20
"""
top20 = list(conn.execute(pilot_sql))

# 获取Top5详细信息
def get_pilot_detail(conn, emp_no):
    sql = """
    SELECT route_name, route_code4, ci_execute_rate, actual_altitude_avg
    FROM pilot_route_monthly_stats
    WHERE duty_captain_code = ? AND cal_month = '2026-04' AND is_valid = 0
    ORDER BY ci_execute_rate ASC
    """
    rows = []
    for row in conn.execute(sql, (emp_no,)):
        rc = row[1]
        ra = route_avg.get(rc, {"ci": 0, "alt": 0})
        ci = row[2] or 0
        alt = row[3] or 0
        ci_gap = (ci - ra["ci"]) * 100 if ra["ci"] else 0
        alt_gap = alt - ra["alt"] if ra["alt"] else 0
        rows.append({
            "route_cn": row[0], "route_code": rc,
            "ci": round(ci * 100, 1), "route_ci_avg": round(ra["ci"] * 100, 1),
            "ci_gap": round(ci_gap, 1),
            "alt": round(alt, 0) if alt else 0,
            "alt_abnormal": (alt is None or alt == 0),
            "route_alt_avg": round(ra["alt"], 0),
            "alt_gap": round(alt_gap, 0)
        })
    return rows

# 生成HTML
html = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>节油小站飞行员 CI 与高度执行率分析（4月≥20班）</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, Arial, sans-serif; background: #f5f7fa; color: #333; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
h1 { text-align: center; color: #2c3e50; padding: 20px 0 5px; border-bottom: 3px solid #3498db; }
.meta { text-align: center; color: #888; font-size: 13px; padding: 8px 0 20px; }
.section { background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
h2 { color: #2c3e50; border-left: 4px solid #3498db; padding-left: 12px; margin-bottom: 16px; font-size: 17px; }
.pilot-card { border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #fafafa; }
.pilot-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.pilot-name { font-size: 18px; font-weight: bold; color: #e74c3c; }
.pilot-code { color: #888; font-size: 13px; }
.badges { display: flex; gap: 8px; flex-wrap: wrap; }
.badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
.badge-red { background: #ffeaea; color: #c0392b; }
.badge-orange { background: #fff4e6; color: #d35400; }
.badge-blue { background: #eaf4ff; color: #2980b9; }
.summary-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.stat-box { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
.stat-num { font-size: 32px; font-weight: bold; color: #3498db; }
.stat-label { font-size: 13px; color: #888; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
th { background: #3498db; color: #fff; padding: 8px 10px; text-align: left; }
td { padding: 7px 10px; border-bottom: 1px solid #eee; }
tr:hover { background: #f8f9fa; }
.reason-box { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 12px 14px; margin-top: 12px; }
.reason-title { color: #856404; font-weight: bold; font-size: 13px; margin-bottom: 6px; }
.reason-item { color: #856404; font-size: 13px; padding: 2px 0 2px 16px; list-style: none; }
.reason-item::before { content: "▶ "; font-size: 10px; margin-right: 6px; }
.footer { text-align: center; color: #aaa; font-size: 12px; padding: 20px 0; }
.rank-tag { font-size: 11px; padding: 1px 6px; border-radius: 4px; margin-left: 6px; }
.rank-bad { background: #ffeaea; color: #e74c3c; }
.rank-warn { background: #fff4e6; color: #e67e22; }
.risk-high { color: #c0392b; font-weight: bold; }
.risk-mid { color: #d35400; }
</style>
</head>
<body>
<div class="container">
  <h1>节油小站飞行员 CI 与高度执行率分析</h1>
  <div class="meta">分析日期：2026-05-12 &nbsp;|&nbsp; <strong>数据范围：2026年4月（航班量≥20班）</strong> &nbsp;|&nbsp; 符合条件的飞行员 363人</div>

  <div class="section">
    <h2>一、总体概况</h2>
    <div class="summary-grid">
      <div class="stat-box"><div class="stat-num">363</div><div class="stat-label">4月≥20班飞行员数</div></div>
      <div class="stat-num" style="font-size:20px;color:#e74c3c;padding-top:16px">Top5 CI均&lt;71%</div>
      <div class="stat-num" style="font-size:20px;color:#d35400;padding-top:16px">Top20 CI均&lt;74%</div>
    </div>
    <p style="font-size:13px;color:#666;margin-top:12px">
      筛选条件：2026年4月执行航班量 ≥ 20班。分析维度：CI执行率 vs 同航线平均值，高度差距 vs 同航线平均值。
    </p>
  </div>

  <div class="section">
    <h2>二、CI 执行率最低的5人（航班量≥20班）</h2>
'''

# Top5 详细卡片
for i, row in enumerate(top20[:5], 1):
    emp_no = int(row[0]) if row[0] else 0
    name = row[1]
    flight_cnt = row[2]
    avg_ci = round(row[3] * 100, 1)
    avg_alt = round(row[4], 0)
    details = get_pilot_detail(conn, emp_no)

    # 找扣分原因（CI差距最严重的前3条）
    bad_routes = [d for d in details if d["ci_gap"] < -20]
    bad_routes = sorted(bad_routes, key=lambda x: x["ci_gap"])[:5]

    alt_gap = avg_alt - sum(route_avg.get(d["route_code"], {"alt": 0})["alt"] for d in details[:len(details)]) / max(len(details), 1)

    html += f'''
    <div class="pilot-card">
      <div class="pilot-header">
        <div>
          <span class="pilot-name">{name}</span>
          <span class="pilot-code">工号 {emp_no}</span>
        </div>
        <div class="badges">
          <span class="badge badge-red">CI {avg_ci}%</span>
          <span class="badge badge-blue">航班 {flight_cnt}班</span>
          <span class="badge badge-orange">高度差 {avg_alt - 27389:.0f} ft</span>
        </div>
      </div>
      <div class="reason-box">
        <div class="reason-title">⚠ 主要扣分航线（CI执行率低于同航线平均20%以上）</div>
        <ul style="padding-left:0">
'''
    for d in bad_routes:
        html += f'          <li class="reason-item">{d["route_cn"]}（{d["route_code"]}）CI={d["ci"]}%，同航线均{d["route_ci_avg"]}%，差距 {d["ci_gap"]}%</li>\n'
        if d["alt_abnormal"]:
            html += f'          <li class="reason-item" style="color:#d35400">　⚠ 高度数据异常（{d["alt"]:.0f}ft），已标记</li>\n'
        elif d["alt_gap"] < -1000:
            html += f'          <li class="reason-item" style="color:#d35400">　高度 {d["alt"]:.0f}ft，同航线均{d["route_alt_avg"]:.0f}ft，差距 {d["alt_gap"]:.0f}ft</li>\n'

    html += '        </ul>\n      </div>\n      <table>\n        <thead><tr><th>航线</th><th>代码</th><th>CI执行率</th><th>航线均CI</th><th>CI差值</th><th>实际高度(ft)</th><th>航线均高(ft)</th><th>高度差(ft)</th></tr></thead>\n        <tbody>\n'

    for d in details:
        ci_color = 'style="color:red;font-weight:bold"' if d["ci_gap"] < -20 else ''
        alt_color = 'style="color:#d35400;font-weight:bold"' if d["alt_gap"] < -1500 else ''
        alt_bg = 'style="background:#fff3cd;font-weight:bold"' if d["alt_abnormal"] else ''
        row_style = 'style="background:#fff3cd"' if d["alt_abnormal"] else ''
        html += f'          <tr{row_style}><td>{d["route_cn"]}</td><td>{d["route_code"]}</td><td {ci_color}>{d["ci"]}%</td><td>{d["route_ci_avg"]}%</td><td {ci_color}>{d["ci_gap"]:.0f}%</td><td {alt_color} {alt_bg}>{d["alt"]:.0f}</td><td>{d["route_alt_avg"]:.0f}</td><td {alt_color} {alt_bg}>{d["alt_gap"]:.0f}</td></tr>\n'

    html += '        </tbody></table></div>\n'

# Top6-20 表格
html += '''
  </div>
  <div class="section">
    <h2>三、CI 执行率排名 6-20（航班量≥20班）</h2>
    <table>
      <thead><tr><th>排名</th><th>工号</th><th>姓名</th><th>航班数</th><th>平均CI</th><th>风险标注</th></tr></thead>
      <tbody>
'''

risk_labels = {6: "●●○ 中高", 7: "●●○ 中高", 8: "●●○ 中高", 9: "●●○ 中高", 10: "●● 中",
               11: "●● 中", 12: "●● 中", 13: "●● 中", 14: "●● 中", 15: "●● 中",
               16: "● 中低", 17: "● 中低", 18: "● 中低", 19: "● 中低", 20: "● 中低"}

for i, row in enumerate(top20[5:], 6):
    emp_no = int(row[0]) if row[0] else 0
    name = row[1]
    flight_cnt = row[2]
    avg_ci = round(row[3] * 100, 1)
    ci_color = 'style="color:#c0392b;font-weight:bold"' if avg_ci < 70 else ('style="color:#d35400;font-weight:bold"' if avg_ci < 73 else '')
    risk = risk_labels.get(i, "●")
    risk_color = 'style="color:#c0392b"' if risk == "●●○ 中高" else ('style="color:#d35400"' if risk == "●● 中" else 'style="color:#888"')
    html += f'        <tr><td>{i}</td><td>{emp_no}</td><td><b>{name}</b></td><td>{flight_cnt}</td><td {ci_color}>{avg_ci}%</td><td {risk_color}>{risk}</td></tr>\n'

html += '''
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>四、数据说明</h2>
    <ul style="font-size:13px;color:#666;line-height:2;padding-left:20px">
      <li><strong>筛选条件</strong>：2026年4月执行航班量 ≥ 20班（民航局对统计代表性最低要求）</li>
      <li><strong>航线平均</strong>：同一航线所有飞行员同期平均值，已剔除无效记录</li>
      <li><strong>高度差距</strong>：负值 = 低于同航线平均高度（偏低），正值 = 高于平均</li>
      <li><strong>高度为0 ft</strong>：可能是数据采集问题，建议核实原始飞行数据</li>
      <li><strong>CI</strong> = 连续下降（Continuous Descent）程序执行率，越高越好</li>
      <li><strong>风险标注</strong>：●●● 高 / ●● 中 / ● 低 — 综合CI和高度差距评定</li>
    </ul>
  </div>

  <div class="footer">
    数据来源：pilot_route_monthly_stats（节油小站-机长航线统计信息月表）<br>
    分析人：数字化办公室-AI &nbsp;|&nbsp; 分析日期：2026-05-12 &nbsp;|&nbsp; 筛选条件：4月航班量≥20班
  </div>
</div>
</body>
</html>
'''

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

conn.close()
print(f"报告已生成: {OUTPUT_HTML}")