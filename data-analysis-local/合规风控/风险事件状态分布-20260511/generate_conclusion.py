import sys
sys.path.append('/Users/fox/Claude Code')

import pandas as pd
from agents.orchestration.llm_client import llm

# ============================================================
# 准备分析数据
# ============================================================
df = pd.read_excel('/Users/fox/Downloads/自定义模板.xlsx')
active = df[df['任务状态'].isin(['处理中', '审批中'])].copy()
active['计划完成日期'] = pd.to_datetime(active['计划完成日期'], errors='coerce')
today = pd.Timestamp('2026-05-11')
active['是否超期'] = active['计划完成日期'] < today
overdue = active[active['是否超期']]

# 状态分布
status_dist = df['任务状态'].value_counts().to_dict()
active_dist = active['任务状态'].value_counts().to_dict()
overdue_dist = overdue['处理人上级部门.名称'].value_counts().to_dict()
active_dept = active['处理人上级部门.名称'].value_counts().to_dict()

# 处理措施关键词
from collections import Counter
kw_counter = Counter()
for m in active['处理措施'].dropna().tolist():
    m = str(m)
    if '派单' in m or '分配' in m: kw_counter['派单/分配问题'] += 1
    if '付款' in m or '支付' in m or '结算' in m: kw_counter['付款/结算问题'] += 1
    if 'IT' in m or '系统' in m or '架构' in m: kw_counter['IT系统问题'] += 1
    if '单据' in m or '流程' in m or '审批' in m: kw_counter['流程/单据问题'] += 1
    if '供应商' in m or '客户' in m: kw_counter['供应商/客户问题'] += 1

# 未分类
unclassified = len(active[active['处理措施'].isna() | (active['处理措施'] == '')])

# 风险原因完成情况
cause_dist = df['完成情况说明'].apply(lambda x: '未分类' if pd.isna(x) or str(x).strip() == '' else '已填写').value_counts().to_dict()

# ============================================================
# 组装 prompt
# ============================================================
prompt = f"""你是一位资深风险管理顾问，专注于企业内部控制和财务风险管理。请基于以下风险事件处理数据，为春秋集团财务部（CFO）撰写一份分析报告的【核心发现】【风险评估】【处理建议】三个章节。

## 数据概况
- 风险事件总记录数：1,849 条
- 全部状态分布：已关闭=1,564(84.6%)，处理中=138，审批中=78，已完成=65，已拒绝=3，待提交=1
- 活跃事件（处理中+审批中）合计：216 条
- 超期事件：161 条（占活跃事件74.5%）
- 超期事件涉及20个部门

## 活跃事件部门分布（Top10）
财务部：79条（超期48条）
上海行付通支付有限公司：21条（超期17条）
春秋航空：16条（超期14条）
市场管理部：15条（超期12条）
航材工装处：13条（超期13条）
人力资源部：11条（超期11条）
资源中心：11条（超期11条）
投融资管理部：9条（超期8条）
维修航线中心：7条（超期0条）
航站管理处：6条（超期5条）

## 活跃事件处理措施关键词分类
IT系统问题：51条（23.6%）
流程/单据问题：32条（14.8%）
付款/结算问题：22条（10.2%）
派单/分配问题：16条（7.4%）
供应商/客户问题：9条（4.2%）
未分类（说明为空）：约125条

## 全部事件风险原因分类（基于完成情况说明）
付款/结算异常：258条（含多类组合）
IT系统问题：98条
流程/单据问题：75条
派单/分配问题：27条
未分类（说明为空）：806条

## 超期事件部门明细（Top8）
财务部：48条（占全部超期29.8%）
上海行付通支付有限公司：17条
春秋航空：14条
航材工装处：13条
市场管理部：12条
人力资源部：11条
资源中心：11条
投融资管理部：8条

## 典型风险事件示例（处理措施原文）
1. "请确认是否符合共享系统派单条件，并说明未派单原因" — IT资产类付款，信管架构处初始派单规则缺失
2. "IT资产类付款-信管架构处，不在派单组内，重新确认补充"
3. "上海程****公司未提交预存申请，已提醒对方后手工申请完成上账"
4. "无异常，单据CH-GY2604200311预计支付时间超期需手工匹配，已处理"
5. "1.在最近一次结算中完成退货扣减；2.每月定期拉取供应商退货清单核对"

请以专业财务顾问视角，撰写以下三个章节，要求简洁、数据驱动、可操作，每章不超过300字：

### 一、核心发现
（总结关键数据发现，识别主要风险点）

### 二、风险评估
（评估当前风险态势，识别高风险部门和风险成因）

### 三、处理建议
（提出5条具体可落地的处理建议，标明优先级）

输出格式：纯文本，直接输出三个章节内容，不要额外解释。"""

print("正在调用本地大模型（OneAPI）生成分析结论...")
print("模型: Qwen3-VL-235B-A22B-Instruct-AWQ")
print("API: https://oneapi-test.springgroup.cn/v1")
print("-" * 60)

response = llm.chat(prompt, model="local", temperature=0.3)

print(response)

# 保存结论
with open('/Users/fox/Claude Code/data-analysis-local/风险事件状态分布-20260511/llm分析结论.txt', 'w', encoding='utf-8') as f:
    f.write(response)

print("-" * 60)
print("结论已保存: llm分析结论.txt")
