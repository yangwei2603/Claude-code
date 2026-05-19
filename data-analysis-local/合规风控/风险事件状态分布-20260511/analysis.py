import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# 1. 读取数据
df = pd.read_excel('/Users/fox/Downloads/自定义模板.xlsx')
print(f"总记录数: {len(df)}")
print(f"字段列表: {list(df.columns)}")
print()

# 2. 状态分布统计
status_col = '任务状态'
print(f"任务状态唯一值: {df[status_col].unique()}")
print()

status_counts = df[status_col].value_counts()
status_pct = df[status_col].value_counts(normalize=True) * 100

print("=== 任务状态分布 ===")
stats_df = pd.DataFrame({
    '数量': status_counts,
    '占比(%)': status_pct.round(2)
})
print(stats_df)
print()

# 3. 可视化
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 饼图
colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9']
axes[0].pie(status_counts, labels=status_counts.index, autopct='%1.1f%%',
            colors=colors[:len(status_counts)], startangle=90)
axes[0].set_title('风险事件任务状态分布（饼图）', fontsize=14)

# 条形图
bars = axes[1].bar(status_counts.index, status_counts.values, color=colors[:len(status_counts)])
axes[1].set_title('风险事件任务状态分布（条形图）', fontsize=14)
axes[1].set_xlabel('任务状态')
axes[1].set_ylabel('事件数量')
for bar, val in zip(bars, status_counts.values):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                 str(val), ha='center', va='bottom', fontsize=11)

plt.tight_layout()
output_path = '/Users/fox/Claude Code/data-analysis-local/风险事件状态分布-20260511/任务状态分布.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"图表已保存: {output_path}")

# 4. 保存统计结果
stats_df.to_csv('/Users/fox/Claude Code/data-analysis-local/风险事件状态分布-20260511/统计结果.csv', encoding='utf-8-sig')
print("统计结果已保存: 统计结果.csv")
