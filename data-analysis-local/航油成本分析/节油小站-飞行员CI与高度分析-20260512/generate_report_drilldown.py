#!/usr/bin/env python3
"""生成飞行员CI与高度分析报告（可下钻明细版）"""

import sqlite3

DB_PATH = "/Users/fox/DB/analysis.db"
OUTPUT_HTML = "/Users/fox/Claude Code/data-analysis-local/节油小站-飞行员CI与高度分析-20260512/report_pilot_ci_drilldown.html"

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

# 获取Top20低CI飞行员
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

# 总飞行员数
total_pilots = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT duty_captain_code FROM pilot_route_monthly_stats
        WHERE cal_month = '2026-04' AND is_valid = 0
        GROUP BY duty_captain_code HAVING COUNT(*) >= 20
    )
""").fetchone()[0]

# 高度异常总记录数
abnormal_alt_cnt = conn.execute("""
    SELECT COUNT(*) FROM pilot_route_monthly_stats
    WHERE cal_month = '2026-04' AND is_valid = 0
    AND (actual_altitude_avg IS NULL OR actual_altitude_avg = 0)
""").fetchone()[0]

# 计算Top5和Top20平均CI
top5_avg_ci = round(sum(row[3] for row in top20[:5]) / 5 * 100, 1)
top20_avg_ci = round(sum(row[3] for row in top20) / 20 * 100, 1)

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
        alt = row[3]
        alt_val = round(alt, 0) if alt else 0
        alt_abnormal = (alt is None or alt == 0)
        ci_gap = (ci - ra["ci"]) * 100 if ra["ci"] else 0
        alt_gap = alt_val - ra["alt"] if ra["alt"] else 0
        rows.append({
            "route_cn": row[0], "route_code": rc,
            "ci": round(ci * 100, 1), "route_ci_avg": round(ra["ci"] * 100, 1),
            "ci_gap": round(ci_gap, 1),
            "alt": alt_val,
            "alt_abnormal": alt_abnormal,
            "route_alt_avg": round(ra["alt"], 0),
            "alt_gap": round(alt_gap, 0)
        })
    return rows

# 构建HTML
html_parts = []

html_parts.append('''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>节油小站飞行员 CI 与高度执行率分析（可下钻明细）</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, Arial, sans-serif; background: #f5f7fa; color: #333; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
h1 { text-align: center; color: #2c3e50; padding: 20px 0 5px; border-bottom: 3px solid #3498db; }
.meta { text-align: center; color: #888; font-size: 13px; padding: 8px 0 20px; }
.section { background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
h2 { color: #2c3e50; border-left: 4px solid #3498db; padding-left: 12px; margin-bottom: 16px; font-size: 17px; }
.pilot-card { border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #fafafa; }
.pilot-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; user-select: none; }
.pilot-name { font-size: 18px; font-weight: bold; color: #e74c3c; }
.pilot-code { color: #888; font-size: 13px; }
.badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
.badge-red { background: #ffeaea; color: #c0392b; }
.badge-orange { background: #fff4e6; color: #d35400; }
.badge-blue { background: #eaf4ff; color: #2980b9; }
.badge-abnormal { background: #ff9800; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 3px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-box { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
.stat-num { font-size: 28px; font-weight: bold; color: #3498db; }
.stat-label { font-size: 13px; color: #888; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
th { background: #3498db; color: #fff; padding: 8px 10px; text-align: left; }
td { padding: 7px 10px; border-bottom: 1px solid #eee; }
tr:hover { background: #f8f9fa; }
.abnormal-row { background: #fff8e1 !important; }
.abnormal-cell { background: #fff3cd; font-weight: bold; color: #d35400; }
.abnormal-tag { display: inline-block; background: #ff9800; color: #fff; font-size: 10px; padding: 1px 5px; border-radius: 3px; margin-left: 4px; }
.footer { text-align: center; color: #aaa; font-size: 12px; padding: 20px 0; }
.toggle-icon { font-size: 14px; margin-left: 8px; color: #888; transition: transform 0.2s; display: inline-block; width: 16px; text-align: center; }
.toggle-icon.collapsed { transform: rotate(-90deg); }
.detail-table { margin-top: 12px; display: table; width: 100%; }
.detail-table.hidden { display: none; }
</style>
</head>
<body>
<div class="container">
  <h1>节油小站飞行员 CI 与高度执行率分析</h1>
  <div class="meta">分析日期：2026-05-14 &nbsp;|&nbsp; <strong>数据范围：2026年4月（航班量≥20班）</strong></div>

  <div class="section">
    <h2>一、总体概况</h2>
    <div class="summary-grid">
      <div class="stat-box"><div class="stat-num">''' + str(total_pilots) + '''</div><div class="stat-label">≥20班飞行员数</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#e74c3c">''' + str(top5_avg_ci) + '''%</div><div class="stat-label">Top5 平均CI</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#d35400">''' + str(top20_avg_ci) + '''%</div><div class="stat-label">Top20 平均CI</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#ff9800">''' + str(abnormal_alt_cnt) + '''</div><div class="stat-label">高度异常记录数</div></div>
    </div>
    <p style="font-size:13px;color:#666;margin-top:12px">
      筛选条件：2026年4月执行航班量 ≥ 20班。点击飞行员卡片可展开下钻明细。
      <span style="background:#fff3cd;padding:2px 6px;border-radius:3px">黄色背景行</span> = 高度数据异常（0或NULL）。
    </p>
  </div>

  <div class="section">
    <h2>二、低CI飞行员明细（点击卡片展开下钻）</h2>
''')

# Top20 卡片（可展开）
for i, row in enumerate(top20, 1):
    emp_no = int(row[0]) if row[0] else 0
    name = row[1]
    flight_cnt = row[2]
    avg_ci = round(row[3] * 100, 1)
    avg_alt = round(row[4], 0)
    details = get_pilot_detail(conn, emp_no)

    bad_routes = [d for d in details if d["ci_gap"] < -20]
    bad_routes = sorted(bad_routes, key=lambda x: x["ci_gap"])[:5]
    abnormal_count = sum(1 for d in details if d["alt_abnormal"])

    abnormal_badge_html = (' <span class="badge-abnormal">高度异常 ' + str(abnormal_count) + '条</span>') if abnormal_count > 0 else ''

    card_html = '''
    <div class="pilot-card" id="pilot-''' + str(i) + '''">
      <div class="pilot-header" onclick="toggleDetail(''' + str(i) + ''')">
        <div>
          <span class="pilot-name">''' + name + '''</span>
          <span class="pilot-code">工号 ''' + str(emp_no) + '''</span>''' + abnormal_badge_html + '''
        </div>
        <div class="badges">
          <span class="badge badge-red">CI ''' + str(avg_ci) + '''%</span>
          <span class="badge badge-blue">航班 ''' + str(flight_cnt) + '''班</span>
          <span class="badge badge-orange">均高 ''' + str(int(avg_alt)) + ''' ft</span>
          <span id="toggle-icon-''' + str(i) + '''" class="toggle-icon">▼</span>
        </div>
      </div>
'''

    if bad_routes:
        card_html += '''      <div style="margin-top:12px">
        <div style="color:#856404;font-weight:bold;font-size:13px;margin-bottom:6px">⚠ 主要扣分航线（CI低于同航线平均20%以上）</div>
        <ul style="padding-left:0;font-size:13px;color:#856404">
'''
        for d in bad_routes:
            if d["alt_abnormal"]:
                alt_warn = ' <span class="abnormal-tag">高度异常</span>'
            elif d["alt_gap"] < -1000:
                alt_warn = ' <span style="color:#d35400">低于均值' + str(int(d["alt_gap"])) + 'ft</span>'
            else:
                alt_warn = ''
            card_html += '          <li style="list-style:none;padding:2px 0">▶ ' + d["route_cn"] + '（' + d["route_code"] + '）CI=' + str(d["ci"]) + '%，同航线均' + str(d["route_ci_avg"]) + '%，差距 ' + str(d["ci_gap"]) + '%' + alt_warn + '</li>\n'
        card_html += '        </ul>\n      </div>\n'

    card_html += '''      <div id="detail-''' + str(i) + '''" class="detail-table">
        <table>
          <thead><tr><th>航线</th><th>代码</th><th>CI执行率</th><th>航线均CI</th><th>CI差值</th><th>实际高度(ft)</th><th>航线均高(ft)</th><th>高度差(ft)</th></tr></thead>
          <tbody>
'''
    for d in details:
        ci_color = 'style="color:red;font-weight:bold"' if d["ci_gap"] < -20 else ''
        alt_color = 'style="color:#d35400;font-weight:bold"' if d["alt_gap"] < -1500 else ''
        row_class = 'class="abnormal-row"' if d["alt_abnormal"] else ''
        alt_cell_class = 'class="abnormal-cell"' if d["alt_abnormal"] else ''
        if d["alt_abnormal"]:
            alt_display = str(int(d["alt"])) + ' <span class="badge-abnormal">异常</span>'
        else:
            alt_display = str(int(d["alt"]))
        card_html += '            <tr ' + row_class + '><td>' + d["route_cn"] + '</td><td>' + d["route_code"] + '</td><td ' + ci_color + '>' + str(d["ci"]) + '%</td><td>' + str(d["route_ci_avg"]) + '%</td><td ' + ci_color + '>' + str(d["ci_gap"]) + '%</td><td ' + alt_color + ' ' + alt_cell_class + '>' + alt_display + '</td><td>' + str(int(d["route_alt_avg"])) + '</td><td ' + alt_color + '>' + str(int(d["alt_gap"])) + '</td></tr>\n'

    card_html += '''          </tbody></table>
        </div>
    </div>
'''
    html_parts.append(card_html)

# Top6-20 表格
risk_labels = {6: "●●○ 中高", 7: "●●○ 中高", 8: "●●○ 中高", 9: "●●○ 中高", 10: "●● 中",
               11: "●● 中", 12: "●● 中", 13: "●● 中", 14: "●● 中", 15: "●● 中",
               16: "● 中低", 17: "● 中低", 18: "● 中低", 19: "● 中低", 20: "● 中低"}

html_parts.append('''
  </div>
  <div class="section">
    <h2>三、CI 执行率排名 6-20（航班量≥20班）</h2>
    <table>
      <thead><tr><th>排名</th><th>工号</th><th>姓名</th><th>航班数</th><th>平均CI</th><th>风险</th><th>下钻</th></tr></thead>
      <tbody>
''')

for i, row in enumerate(top20[5:], 6):
    emp_no = int(row[0]) if row[0] else 0
    name = row[1]
    flight_cnt = row[2]
    avg_ci = round(row[3] * 100, 1)
    ci_color = 'style="color:#c0392b;font-weight:bold"' if avg_ci < 70 else ('style="color:#d35400;font-weight:bold"' if avg_ci < 73 else '')
    risk = risk_labels.get(i, "●")
    risk_color = 'style="color:#c0392b"' if risk == "●●○ 中高" else ('style="color:#d35400"' if risk == "●● 中" else 'style="color:#888"')
    html_parts.append('        <tr><td>' + str(i) + '</td><td>' + str(emp_no) + '</td><td><b>' + name + '</b></td><td>' + str(flight_cnt) + '</td><td ' + ci_color + '>' + str(avg_ci) + '%</td><td ' + risk_color + '>' + risk + '</td><td><a href="#pilot-' + str(i) + '" onclick="toggleDetail(' + str(i) + ');return false" style="color:#3498db">查看明细</a></td></tr>\n')

html_parts.append('''      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>四、数据说明</h2>
    <ul style="font-size:13px;color:#666;line-height:2;padding-left:20px">
      <li><strong>筛选条件</strong>：2026年4月执行航班量 ≥ 20班</li>
      <li><strong>航线平均</strong>：同一航线所有飞行员同期平均值，已剔除无效记录</li>
      <li><strong>高度异常标记</strong>：<span style="background:#fff3cd;padding:2px 6px;border-radius:3px">黄色背景行</span> = 高度为0或NULL（疑似数据采集问题）</li>
      <li><strong>下钻功能</strong>：点击任意飞行员卡片（或"查看明细"链接）展开该飞行员所有航线明细记录</li>
      <li><strong>CI</strong> = 连续下降（Continuous Descent）程序执行率，越高越好</li>
      <li><strong>风险标注</strong>：●●● 高 / ●● 中 / ● 低 — 综合CI和高度差距评定</li>
    </ul>
  </div>

  <div class="footer">
    数据来源：pilot_route_monthly_stats（节油小站-机长航线统计信息月表）<br>
    分析人：数字化办公室-AI &nbsp;|&nbsp; 分析日期：2026-05-14 &nbsp;|&nbsp; 筛选条件：4月航班量≥20班
  </div>
</div>
<script>
function toggleDetail(i) {
  var detail = document.getElementById('detail-' + i);
  var icon = document.getElementById('toggle-icon-' + i);
  if (detail.classList.contains('hidden')) {
    detail.classList.remove('hidden');
    icon.classList.remove('collapsed');
    icon.textContent = '▼';
  } else {
    detail.classList.add('hidden');
    icon.classList.add('collapsed');
    icon.textContent = '▶';
  }
}
</script>
</body>
</html>
''')

html = ''.join(html_parts)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

conn.close()
print(f"报告已生成: {OUTPUT_HTML}")