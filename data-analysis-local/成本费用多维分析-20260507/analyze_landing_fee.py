#!/usr/bin/env python3
"""
机场起降费下钻分析脚本
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


def load_data(excel_path: str) -> dict:
    """加载所需数据"""
    xl = pd.ExcelFile(excel_path)
    return {
        'detail': pd.read_excel(xl, sheet_name='细分科目对比（全部绝对值总成本）'),
        'subject': pd.read_excel(xl, sheet_name='科目对比（全部绝对值总成本）_点击科目可以联动下方细分科目'),
        'monthly': pd.read_excel(xl, sheet_name=0),
    }


def extract_landing_fee_analysis(data: dict) -> tuple:
    """提取起降费相关数据"""
    df_subject = data['subject']
    df_detail = data['detail']

    # 总成本 - 年月='合计'的行
    total = df_subject[df_subject['年月'] == '合计'].iloc[0]['本期']

    # 起降费(科目级)
    landing_subject = df_subject[df_subject['科目'] == '起降费'].iloc[0]

    # 机场起降费
    landing_detail = df_detail[df_detail['细分科目'] == '机场起降费'].iloc[0]

    # 机场相关全部细分
    df_related = df_detail[df_detail['细分科目'].astype(str).str.contains(
        '机场|起降|港|导航|民航|离港|货运|过夜'
    )][['细分科目', '本期', '春秋年累计', '同比增长率', '环比增长率']]

    return total, landing_subject, landing_detail, df_related


def build_prompt(total, landing_subject, landing_detail, df_related) -> str:
    """构建分析 prompt"""
    return f"""请对起降费进行下钻分析。

## 核心数据

### 起降费两层数据对比（单位：亿元）
| 层级 | 本期(4月) | 春秋年累计 | 同比 | 环比 |
|------|----------|-----------|------|------|
| 起降费(科目级) | {landing_subject['本期']:.3f} | {landing_subject['春秋年累计']:.3f} | +{landing_subject['同比增长率']*100:.1f}% | +{landing_subject['环比增长率']*100:.1f}% |
| 机场起降费(细分) | {landing_detail['本期']:.3f} | {landing_detail['春秋年累计']:.3f} | +{landing_detail['同比增长率']*100:.1f}% | +{landing_detail['环比增长率']*100:.1f}% |

**差额（其他起降费）**: 本期 {landing_subject['本期']-landing_detail['本期']:.3f}亿元

### 机场/起降相关细分科目（亿元）
{df_related.to_string()}

### 关键占比
- 机场起降费占起降费汇总：{landing_detail['本期']/landing_subject['本期']*100:.1f}%
- 起降费占总成本：{landing_subject['本期']/total*100:.1f}%
- 机场起降费占总成本：{landing_detail['本期']/total*100:.1f}%

## 分析维度

1. **结构拆解**：起降费 = 机场起降费(72.9%) + 其他起降费(27.1%)，"其他"可能包含什么？
2. **增长驱动**：起降费同比+7.3%，而机场起降费同比仅+4.1%，说明其他分项增长更快
3. **配比关系**：机场起降费:导航费:民航基金 ≈ 2.38:0.33:0.19，反映什么业务特征
4. **风险**：起降费占比{landing_subject['本期']/total*100:.1f}%总成本，环比+3.0%意味着什么
5. **建议**：精细化管控建议

请输出结构化分析报告，中文。"""


def save_report(content: str, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"报告已保存: {output_path}")


def main():
    excel_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXCEL

    if not os.path.exists(excel_path):
        print(f"文件不存在: {excel_path}")
        sys.exit(1)

    print(f"正在分析: {excel_path}")

    data = load_data(excel_path)
    total, landing_subject, landing_detail, df_related = extract_landing_fee_analysis(data)

    print(f"总成本: {total:.3f}亿")
    print(f"起降费(科目级): {landing_subject['本期']:.3f}亿")
    print(f"机场起降费(细分): {landing_detail['本期']:.3f}亿")

    prompt = build_prompt(total, landing_subject, landing_detail, df_related)

    print("正在调用本地大模型分析...")
    analysis = llm.chat(prompt, model='local')
    print(analysis)

    # 构建报告
    report = f"""## 机场起降费下钻分析

**分析时间**: {datetime.now().strftime('%Y-%m-%d')}
**数据来源**: 成本数字看板_成本费用多维分析

### 数据结构

#### 起降费两层数据对比（单位：亿元）
| 层级 | 本期(4月) | 春秋年累计 | 同比增长率 | 环比增长率 |
|------|----------|-----------|-----------|-----------|
| **起降费(科目级)** | {landing_subject['本期']:.3f} | {landing_subject['春秋年累计']:.3f} | +{landing_subject['同比增长率']*100:.1f}% | +{landing_subject['环比增长率']*100:.1f}% |
| 机场起降费(细分) | {landing_detail['本期']:.3f} | {landing_detail['春秋年累计']:.3f} | +{landing_detail['同比增长率']*100:.1f}% | +{landing_detail['环比增长率']*100:.1f}% |

**差额（其他起降费）**: 本期 {landing_subject['本期']-landing_detail['本期']:.3f}亿元，占比 {100-landing_detail['本期']/landing_subject['本期']*100:.1f}%

### 机场/起降相关细分科目

{df_related.to_string()}

### 占比分析

| 指标 | 数值 |
|------|------|
| 机场起降费占起降费汇总 | {landing_detail['本期']/landing_subject['本期']*100:.1f}% |
| 其他起降费占起降费汇总 | {100-landing_detail['本期']/landing_subject['本期']*100:.1f}% |
| 起降费占总成本 | {landing_subject['本期']/total*100:.1f}% |
| 机场起降费占总成本 | {landing_detail['本期']/total*100:.1f}% |

---

## AI 分析结果

{analysis}
"""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_str = datetime.now().strftime('%Y%m%d')
    report_name = f"report_landing_fee_{date_str}.md"
    output_path = os.path.join(script_dir, report_name)

    save_report(report, output_path)


if __name__ == "__main__":
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
    main()
