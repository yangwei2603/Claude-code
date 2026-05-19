#!/usr/bin/env python3
"""
成本费用多维分析脚本
使用本地私有化大模型 (Qwen3-VL-235B-A22B-Instruct-AWQ)

文件夹/报告命名：从 Excel 内容主题提炼，如 sheet 名、报表类型
"""

import sys
import os
import warnings
from datetime import datetime

import pandas as pd

sys.path.insert(0, "/Users/fox/Claude Code/agents/orchestration")
from llm_client import llm

DEFAULT_EXCEL = "/Users/fox/Downloads/成本数字看板_成本费用多维分析-3.0.xlsx"


def load_all_sheets(excel_path: str) -> dict:
    """加载所有 sheet 数据"""
    xl = pd.ExcelFile(excel_path)
    sheets = {}
    for sheet in xl.sheet_names:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        if not df.empty:
            sheets[sheet.strip()] = df
    return sheets


def basic_stats(sheets: dict) -> str:
    """生成基础统计信息"""
    stats = []
    stats.append(f"## 成本费用多维分析")
    stats.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d')}")
    stats.append(f"\n### Sheet 列表")
    for name, df in sheets.items():
        stats.append(f"- {name}: {df.shape[0]} 行 x {df.shape[1]} 列")

    # 月度趋势
    if '月-趋势（绝对值总成本）' in sheets:
        df = sheets['月-趋势（绝对值总成本）']
        stats.append(f"\n### 月度趋势（2025-2026）")
        stats.append(df.to_string())

    # 季度累计
    if '季-成本季度累计-自然年' in sheets:
        df = sheets['季-成本季度累计-自然年']
        stats.append(f"\n### 季度累计（自然年）")
        stats.append(df.to_string())

    # 年度趋势
    if '春秋年-成本年累计趋势-春秋年' in sheets:
        df = sheets['春秋年-成本年累计趋势-春秋年']
        stats.append(f"\n### 年度累计趋势（春秋年）")
        stats.append(df.to_string())

    # 科目对比
    for key in sheets:
        if '科目对比' in key and '细分' not in key:
            df = sheets[key]
            stats.append(f"\n### 科目对比（全部绝对值总成本）")
            stats.append(df.head(20).to_string())
            break

    # 细分科目 TOP15
    for key in sheets:
        if '细分科目对比' in key:
            df = sheets[key]
            top = df.nlargest(15, '本期')[['细分科目', '本期', '春秋年累计', '同比增长率', '环比增长率']]
            stats.append(f"\n### 细分科目 TOP15（按本期金额排序）")
            stats.append(top.to_string())
            break

    return "\n".join(stats)


def analyze_with_llm(stats: str) -> str:
    """使用本地大模型分析统计数据"""
    prompt = f"""请分析以下成本费用数据，提取关键 insights：

{stats}

请从以下维度分析：
1. 成本变化趋势（月度、季度、年度）
2. 主要成本科目占比与变化（航油费、人力成本、维修成本等）
3. 同比/环比增长率分析
4. 潜在风险与建议

请用中文简洁输出分析报告。"""

    resp = llm.chat(prompt, model='local')
    return resp


def save_report(content: str, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"报告已保存: {output_path}")


def main():
    excel_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXCEL

    if not os.path.exists(excel_path):
        print(f"文件不存在: {excel_path}")
        sys.exit(1)

    # 提炼主题：从 sheet 名或数据内容中提取
    subject = "成本费用多维分析"

    print(f"正在分析: {excel_path}")

    sheets = load_all_sheets(excel_path)
    print(f"已加载 {len(sheets)} 个 sheet")

    stats = basic_stats(sheets)

    print("正在调用本地大模型分析...")
    analysis = analyze_with_llm(stats)

    report = f"{stats}\n\n---\n\n## AI 分析结果\n\n{analysis}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_str = datetime.now().strftime('%Y%m%d')
    report_name = f"report_analysis_{date_str}.md"
    output_path = os.path.join(script_dir, report_name)

    save_report(report, output_path)

    print("\n" + "=" * 50)
    print(analysis)


if __name__ == "__main__":
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
    main()