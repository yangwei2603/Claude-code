# -*- coding: utf-8 -*-
"""Markdown转HTML"""
import markdown
import os

md_path = '/Users/fox/Claude Code/data-analysis-local/吉祥春秋航司对比-20260510/report_analysis_20260510.md'
html_path = '/Users/fox/Claude Code/data-analysis-local/吉祥春秋航司对比-20260510/report_analysis_20260510.html'

with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# 完整HTML模板
full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>吉祥航空 vs 春秋航空 对比分析报告</title>
<style>
    body {{ font-family: "Arial Unicode MS", "Microsoft YaHei", sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.8; color: #333; }}
    h1 {{ color: #1a1a1a; border-bottom: 3px solid #c0392b; padding-bottom: 10px; }}
    h2 {{ color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }}
    h3 {{ color: #34495e; }}
    table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
    th {{ background: #2c3e50; color: white; padding: 10px; text-align: left; }}
    td {{ border: 1px solid #ddd; padding: 8px; }}
    tr:nth-child(even) {{ background: #f9f9f9; }}
    code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
    img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; }}
    blockquote {{ border-left: 4px solid #c0392b; margin: 15px 0; padding: 10px 15px; background: #f9f9f9; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 30px 0; }}
    .highlight {{ background: #e8f4f8; padding: 15px; border-radius: 5px; }}
</style>
</head>
<body>
{html_content}
</body>
</html>'''

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"HTML已生成: {html_path}")