#!/usr/bin/env python3
"""生成飞行员CI与高度双低分析HTML报告 - 支持单月和多月聚合"""

import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/Users/fox/Claude Code/data-analysis-local/节油小站-飞行员CI与高度分析-20260512")
DATA_FILE_3MONTHS = OUTPUT_DIR / "dual_low_pilots_3months.json"
OUTPUT_HTML = OUTPUT_DIR / "report_dual_low_analysis_3months.html"

def generate_monthly_badge(status):
    """生成月度状态徽章"""
    badges = []
    for s in status:
        month_str = str(s['month'])[-2:]
        if s['is_dual_low']:
            badges.append(f"<span class='month-badge danger'>{month_str}月双低</span>")
        elif s['is_low_ci']:
            badges.append(f"<span class='month-badge warning'>{month_str}月低CI</span>")
        elif s['is_low_alt']:
            badges.append(f"<span class='month-badge info'>{month_str}月低高度</span>")
        else:
            badges.append(f"<span class='month-badge'>{month_str}月正常</span>")
    return "\n".join(badges)

def generate_pilot_rows(pilots):
    pilot_rows = ""
    for p in pilots:
        routes_html = ""
        for r in p["routes"]:
            ci_class = "negative" if r["ci_gap"] < -10 else "positive" if r["ci_gap"] > 10 else ""
            alt_class = "negative" if r["alt_gap"] < -1000 else "positive" if r["alt_gap"] > 1000 else ""
            routes_html += f"""
                <tr>
                    <td>{r['route_cn']}</td>
                    <td><code>{r['route_code']}</code></td>
                    <td>{r['flight_cnt']}</td>
                    <td class="{ci_class}">{r['ci']:.1f}%</td>
                    <td>{r['route_ci_avg']:.1f}%</td>
                    <td class="{ci_class}">{r['ci_gap']:+.1f}%</td>
                    <td class="{alt_class}">{r['alt']:,.0f}</td>
                    <td>{r['route_alt_avg']:,.0f}</td>
                    <td class="{alt_class}">{r['alt_gap']:+,.0f}</td>
                </tr>
            """

        persistent_tag = "🔴持续双低" if p["persistent_dual_low"] else "🟡新增双低"
        status_badges = generate_monthly_badge(p["monthly_status"])

        pilot_rows += f"""
        <div class="pilot-card">
            <div class="pilot-header">
                <div class="pilot-name">{p['pilot_name']} <span class="tag {('tag-danger' if p['persistent_dual_low'] else 'tag-warning')}">{persistent_tag}</span></div>
                <div class="pilot-meta">工号: {p['pilot_code']} | 3月合计: {p['total_flights']}班</div>
                <div class="pilot-scores">
                    <span class="score-badge danger">CI执行率: {p['avg_ci_rate']:.1f}%</span>
                    <span class="score-badge danger">高度执行率: {p['avg_alt_rate']:.1f}%</span>
                </div>
                <div class="monthly-status">{status_badges}</div>
            </div>
            <div class="routes-section">
                <h4>航线明细（3月合计）</h4>
                <table class="route-table">
                    <thead>
                        <tr>
                            <th>航线</th>
                            <th>航码</th>
                            <th>班次</th>
                            <th>CI</th>
                            <th>航线均</th>
                            <th>CI差</th>
                            <th>实际高度</th>
                            <th>航线均</th>
                            <th>高度差(ft)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {routes_html}
                    </tbody>
                </table>
            </div>
        </div>
        """
    return pilot_rows

def generate_html(data):
    pilots = data["dual_low_pilots"]
    stats = data["stats"]
    months_str = "/".join(str(m)[-2:] + "月" for m in data["months"])

    pilot_rows = generate_pilot_rows(pilots)

    # 持续双低 vs 新增双低分类
    persistent = [p for p in pilots if p['persistent_dual_low']]
    new = [p for p in pilots if not p['persistent_dual_low']]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>飞行员CI与高度双低分析报告（{months_str}聚合）</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
        header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .subtitle {{ opacity: 0.9; font-size: 14px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .kpi-card {{ background: white; padding: 18px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; }}
        .kpi-value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
        .kpi-label {{ color: #7f8c8d; font-size: 13px; margin-top: 5px; }}
        .kpi-card.danger .kpi-value {{ color: #e74c3c; }}
        .kpi-card.warning .kpi-value {{ color: #f39c12; }}
        .section-title {{ font-size: 20px; color: #2c3e50; margin: 30px 0 15px; padding-left: 15px; border-left: 4px solid #e74c3c; }}
        .section-sub {{ font-size: 14px; color: #7f8c8d; margin: 20px 0 10px; }}
        .pilot-card {{ background: white; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden; }}
        .pilot-header {{ background: #f8f9fa; padding: 20px 25px; border-bottom: 1px solid #eee; }}
        .pilot-name {{ font-size: 20px; font-weight: bold; color: #2c3e50; display: flex; align-items: center; gap: 10px; }}
        .pilot-meta {{ color: #7f8c8d; font-size: 13px; margin: 5px 0 10px; }}
        .pilot-scores {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }}
        .score-badge {{ padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500; }}
        .score-badge.danger {{ background: #fde8e8; color: #c0392b; }}
        .score-badge {{ background: #e8f4f8; color: #2980b9; }}
        .monthly-status {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
        .month-badge {{ padding: 4px 10px; border-radius: 12px; font-size: 12px; }}
        .month-badge.danger {{ background: #fde8e8; color: #c0392b; }}
        .month-badge.warning {{ background: #fff3cd; color: #856404; }}
        .month-badge.info {{ background: #e8f4f8; color: #2980b9; }}
        .month-badge {{ background: #e8f8e8; color: #27ae60; }}
        .tag {{ padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: normal; }}
        .tag-danger {{ background: #fde8e8; color: #c0392b; }}
        .tag-warning {{ background: #fff3cd; color: #856404; }}
        .routes-section {{ padding: 20px 25px; }}
        .routes-section h4 {{ font-size: 14px; color: #7f8c8d; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }}
        .route-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .route-table th {{ background: #f8f9fa; padding: 12px 10px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #e0e0e0; position: sticky; top: 0; }}
        .route-table td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
        .route-table tr:hover {{ background: #fafafa; }}
        .route-table code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
        .negative {{ color: #e74c3c; font-weight: 500; }}
        .positive {{ color: #27ae60; font-weight: 500; }}
        footer {{ text-align: center; padding: 30px; color: #95a5a6; font-size: 12px; }}
        .info-box {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px 20px; margin-bottom: 20px; }}
        .info-box strong {{ color: #856404; }}
        .summary-box {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .summary-box h3 {{ margin-bottom: 15px; color: #2c3e50; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .summary-item {{ padding: 15px; border-radius: 8px; }}
        .summary-item.danger {{ background: #fde8e8; border-left: 4px solid #e74c3c; }}
        .summary-item.warning {{ background: #fff3cd; border-left: 4px solid #f39c12; }}
        .summary-item h4 {{ margin-bottom: 10px; }}
        .summary-item.danger h4 {{ color: #c0392b; }}
        .summary-item.warning h4 {{ color: #856404; }}
        .summary-item ul {{ margin-left: 20px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>飞行员CI与高度双低分析报告</h1>
            <div class="subtitle">数据期间: {months_str} | CI阈值: &lt;{data['threshold_ci']}% | 高度执行率阈值: &lt;{data['threshold_alt']}% | 3月航班量加权聚合</div>
        </header>

        <div class="info-box">
            <strong>定义说明：</strong>
            CI执行率 = 执行CI的航班占比（is_execute_ci=1）；高度执行率 = 实际高度≥计划高度-500ft的航班占比。
            双低 = CI执行率和高度执行率均低于阈值。持续双低 = 2个月均双低。
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value">{data['stats']['total_months']}</div>
                <div class="kpi-label">分析月数</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{data['fleet_stats']['avg_ci_rate']:.1f}%</div>
                <div class="kpi-label">机队平均CI</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{data['fleet_stats']['avg_alt_rate']:.1f}%</div>
                <div class="kpi-label">机队平均高度执行率</div>
            </div>
            <div class="kpi-card danger">
                <div class="kpi-value">{stats['dual_low_count']}</div>
                <div class="kpi-label">聚合双低飞行员</div>
            </div>
            <div class="kpi-card danger">
                <div class="kpi-value">{stats['persistent_dual_low']}</div>
                <div class="kpi-label">持续双低(2个月+)</div>
            </div>
            <div class="kpi-card warning">
                <div class="kpi-value">{stats['new_dual_low']}</div>
                <div class="kpi-label">新增双低(1个月)</div>
            </div>
        </div>

        <div class="summary-box">
            <h3>分类汇总</h3>
            <div class="summary-grid">
                <div class="summary-item danger">
                    <h4>🔴 持续双低（需重点干预）</h4>
                    <ul>
"""
    for p in persistent:
        html += f"<li>{p['pilot_name']}（工号{p['pilot_code']}）：{p['total_flights']}班，CI={p['avg_ci_rate']}%，高度={p['avg_alt_rate']}%</li>\n"

    html += f"""                    </ul>
                </div>
                <div class="summary-item warning">
                    <h4>🟡 新增双低（需关注）</h4>
                    <ul>
"""
    for p in new:
        html += f"<li>{p['pilot_name']}（工号{p['pilot_code']}）：{p['total_flights']}班，CI={p['avg_ci_rate']}%，高度={p['avg_alt_rate']}%</li>\n"

    html += f"""                    </ul>
                </div>
            </ul>
        </div>
    </div>

        <h2 class="section-title">双低飞行员清单（共{len(pilots)}人）</h2>
        <h3 class="section-sub">按3月综合评分（CI+高度执行率）排序</h3>

        {pilot_rows}

        <footer>
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d')} | 数据来源: pilot_person_monthly_stats / pilot_route_monthly_stats</p>
        </footer>
    </div>
</body>
</html>"""

    return html

if __name__ == "__main__":
    with open(DATA_FILE_3MONTHS, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = generate_html(data)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"报告已生成: {OUTPUT_HTML}")
