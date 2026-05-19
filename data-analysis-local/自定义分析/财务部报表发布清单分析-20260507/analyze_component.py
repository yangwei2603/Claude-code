#!/usr/bin/env python3
"""
组件分析脚本
使用本地私有化大模型 (Qwen3-VL-235B-A22B-Instruct-AWQ)
"""

import sys
import os
import warnings
from datetime import datetime

import pandas as pd

sys.path.insert(0, "/Users/fox/Claude Code/agents/orchestration")
from llm_client import llm

DEFAULT_EXCEL = "/Users/fox/Downloads/组件.xlsx"


def load_data(excel_path: str) -> pd.DataFrame:
    df = pd.read_excel(excel_path)
    return df


def basic_stats(df: pd.DataFrame, subject: str) -> str:
    stats = []
    stats.append(f"## 财务部报表数据分析（{subject}）")
    stats.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d')}")
    stats.append(f"\n### 基本信息")
    stats.append(f"- 总报表数：{len(df)} 个")
    stats.append(f"- 科室数：{df['归属科室'].nunique()} 个")
    stats.append(f"- 主题数：{df['主题'].nunique()} 个")

    stats.append(f"\n### 当月热度分布")
    for k, v in df['当月热度'].value_counts().items():
        stats.append(f"- {k}: {v} 个 ({v/len(df)*100:.1f}%)")

    stats.append(f"\n### 保障等级分布")
    for k, v in df['保障等级'].value_counts().items():
        stats.append(f"- {k}: {v} 个 ({v/len(df)*100:.1f}%)")

    stats.append(f"\n### 归属科室分布 (TOP10)")
    for k, v in df['归属科室'].value_counts().head(10).items():
        stats.append(f"- {k}: {v} 个")

    stats.append(f"\n### 主题分布")
    for k, v in df['主题'].value_counts().items():
        stats.append(f"- {k}: {v} 个 ({v/len(df)*100:.1f}%)")

    stats.append(f"\n### 数据更新频率分布")
    for k, v in df['数据更新频率'].value_counts().items():
        stats.append(f"- {k}: {v} 个")

    stats.append(f"\n### TOP15 高访问量报表")
    top = df.nlargest(15, '当月访问量')[['报表名称', '归属科室', '当月访问量', '累计访问量', '当月热度', '保障等级']]
    for _, row in top.iterrows():
        stats.append(f"| {row['报表名称']} | {row['当月访问量']} | {row['累计访问量']} | {row['当月热度']} | {row['保障等级']} |")

    return "\n".join(stats)


def analyze_with_llm(stats: str) -> str:
    prompt = f"""请分析以下财务部报表数据，提取关键 insights：

{stats}

请从以下维度分析：
1. 报表热度情况（热度上升/下降的分布）
2. 科室分布情况
3. 主题分布（哪些主题报表最多）
4. 保障等级与访问量的关系
5. 潜在问题与建议

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

    filename = os.path.basename(excel_path)
    subject = filename.replace('.xlsx', '')

    print(f"正在分析: {excel_path}")

    df = load_data(excel_path)
    stats = basic_stats(df, subject)

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