import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from collections import Counter
import re
import os

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = '/Users/fox/Claude Code/data-analysis-local/风险事件状态分布-20260511'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. 读取数据
df = pd.read_excel('/Users/fox/Downloads/自定义模板.xlsx')
print(f"总记录数: {len(df)}")

# ============================
# Part 1: 风险态势分析
# ============================
print("\n" + "="*60)
print("【风险态势分析】")
print("="*60)

# 活跃事件（处理中 + 审批中）
active_df = df[df['任务状态'].isin(['处理中', '审批中'])]
print(f"\n活跃事件总数: {len(active_df)}")

# 1.1 活跃事件按状态分布
active_by_status = active_df['任务状态'].value_counts()
print("\n活跃事件状态分布:")
print(active_by_status)

# 1.2 活跃事件按部门分布（上级部门）
active_by_dept = active_df['处理人上级部门.名称'].value_counts()
print(f"\n活跃事件部门分布（前15）:")
print(active_by_dept.head(15))

# 1.3 超期分析（计划完成日期 < 2026-05-11）
active_df = active_df.copy()
active_df['计划完成日期'] = pd.to_datetime(active_df['计划完成日期'], errors='coerce')
today = pd.Timestamp('2026-05-11')
active_df['是否超期'] = active_df['计划完成日期'] < today
overdue = active_df[active_df['是否超期']]
print(f"\n活跃事件中超期数量: {len(overdue)} / {len(active_df)}")
if len(overdue) > 0:
    overdue_by_dept = overdue['处理人上级部门.名称'].value_counts()
    print("超期事件部门分布:")
    print(overdue_by_dept)

# ============================
# Part 2: 风险原因分类
# ============================
print("\n" + "="*60)
print("【风险原因分类】")
print("="*60)

# 使用完成情况说明 + 处理措施 进行关键词提取
# 定义风险原因关键词分类
risk_keywords = {
    '派单/分配问题': ['派单', '派单规则', '不在派单组', '分配', '归属'],
    '付款/结算异常': ['付款', '支付', '结算', '对账', '挂账', '账期', '应收账款', '应付账款', '退货扣减', '退款'],
    '流程/单据问题': ['单据', '流程', '审批', '提交', '申请', '附件', '材料'],
    'IT系统问题': ['IT', '系统', '架构', '信管', '接口', '数据', '推送'],
    '供应商/客户问题': ['供应商', '客户', '对方', '第三方', '合作伙伴'],
    '数据/文档问题': ['数据', '文档', '报表', '清单', '台账', '核对'],
}

def classify_risk(text):
    if pd.isna(text):
        return '未分类'
    text = str(text)
    matched = []
    for category, keywords in risk_keywords.items():
        for kw in keywords:
            if kw in text:
                matched.append(category)
                break
    return ' | '.join(matched) if matched else '未分类'

# 对完成情况说明进行分类
df['风险原因分类'] = df['完成情况说明'].apply(classify_risk)

# 统计各分类数量
cause_counts = df['风险原因分类'].value_counts()
print("\n风险原因分类（基于完成情况说明）:")
print(cause_counts)

# 对活跃事件的处理措施进行分类
active_df['处理措施分类'] = active_df['处理措施'].apply(classify_risk)
active_cause_counts = active_df['处理措施分类'].value_counts()
print("\n活跃事件处理措施分类（前20）:")
print(active_cause_counts.head(20))

# ============================
# 可视化
# ============================
fig, axes = plt.subplots(2, 2, figsize=(16, 14))

# 1. 活跃事件状态分布
colors1 = ['#ff6b6b', '#4ecdc4']
axes[0,0].pie(active_by_status, labels=active_by_status.index, autopct='%1.1f%%',
              colors=colors1, startangle=90)
axes[0,0].set_title('活跃事件状态分布', fontsize=13)

# 2. 活跃事件部门分布（Top 10）
top10_dept = active_by_dept.head(10)
bars = axes[0,1].barh(range(len(top10_dept)), top10_dept.values, color=plt.cm.Blues(np.linspace(0.3, 0.9, len(top10_dept))))
axes[0,1].set_yticks(range(len(top10_dept)))
axes[0,1].set_yticklabels(top10_dept.index)
axes[0,1].set_title('活跃事件部门分布（Top 10）', fontsize=13)
axes[0,1].set_xlabel('事件数量')
for i, (bar, val) in enumerate(zip(bars, top10_dept.values)):
    axes[0,1].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   str(val), va='center', fontsize=10)
axes[0,1].invert_yaxis()

# 3. 风险原因分类
cause_for_plot = cause_counts.head(10)
colors3 = plt.cm.Oranges(np.linspace(0.3, 0.9, len(cause_for_plot)))
bars3 = axes[1,0].barh(range(len(cause_for_plot)), cause_for_plot.values, color=colors3)
axes[1,0].set_yticks(range(len(cause_for_plot)))
axes[1,0].set_yticklabels(cause_for_plot.index)
axes[1,0].set_title('风险原因分类（全部事件 Top 10）', fontsize=13)
axes[1,0].set_xlabel('事件数量')
for bar, val in zip(bars3, cause_for_plot.values):
    axes[1,0].text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                   str(val), va='center', fontsize=10)
axes[1,0].invert_yaxis()

# 4. 活跃事件处理措施分类
active_cause_for_plot = active_cause_counts.head(10)
colors4 = plt.cm.Reds(np.linspace(0.3, 0.9, len(active_cause_for_plot)))
bars4 = axes[1,1].barh(range(len(active_cause_for_plot)), active_cause_for_plot.values, color=colors4)
axes[1,1].set_yticks(range(len(active_cause_for_plot)))
axes[1,1].set_yticklabels(active_cause_for_plot.index)
axes[1,1].set_title('活跃事件处理措施分类（Top 10）', fontsize=13)
axes[1,1].set_xlabel('事件数量')
for bar, val in zip(bars4, active_cause_for_plot.values):
    axes[1,1].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   str(val), va='center', fontsize=10)
axes[1,1].invert_yaxis()

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/风险态势与原因分析.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n图表已保存: {OUTPUT_DIR}/风险态势与原因分析.png")

# 保存活跃事件明细
active_export = active_df[['事件编号', '处理措施', '处理人.姓名', '处理人上级部门.名称',
                            '计划完成日期', '任务状态', '完成情况说明', '处理措施分类']]
active_export.to_csv(f'{OUTPUT_DIR}/活跃事件明细.csv', index=False, encoding='utf-8-sig')
print(f"活跃事件明细已保存: {OUTPUT_DIR}/活跃事件明细.csv")

# 保存超期事件明细
if len(overdue) > 0:
    overdue_export = overdue[['事件编号', '处理措施', '处理人.姓名', '处理人上级部门.名称',
                              '计划完成日期', '任务状态', '完成情况说明']]
    overdue_export.to_csv(f'{OUTPUT_DIR}/超期事件明细.csv', index=False, encoding='utf-8-sig')
    print(f"超期事件明细已保存: {OUTPUT_DIR}/超期事件明细.csv")
