"""
PM Agent - 产品经理 Agent
负责需求分析、PRD 输出、模块拆分、优先级排序
"""

import json
from typing import Dict, List, Any


class PMAgent:
    def __init__(self):
        self.name = "PM Agent"
        self.role = "Product Manager"

    def analyze_requirement(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户需求，输出结构化 PRD

        Args:
            user_input: 用户原始需求

        Returns:
            PRD 文档结构
        """
        modules = self._extract_modules(user_input)
        priority = self._assess_priority(user_input)
        risk = self._assess_risk(user_input)

        prd = {
            "modules": modules,
            "priority": priority,
            "risk": risk,
            "requirements": user_input,
            "output_format": "PRD"
        }

        return prd

    def _extract_modules(self, user_input: str) -> List[str]:
        """提取业务模块"""
        # 简单的关键词提取，实际可结合 LLM
        keywords = ["登录", "权限", "报表", "用户", "订单", "支付", "库存", "财务"]
        modules = [kw for kw in keywords if kw in user_input]
        return modules if modules else ["基础模块"]

    def _assess_priority(self, user_input: str) -> str:
        """评估优先级"""
        urgent_keywords = ["紧急", "必须", "立即", "critical", "urgent"]
        if any(kw in user_input.lower() for kw in urgent_keywords):
            return "P0"
        return "P1"

    def _assess_risk(self, user_input: str) -> str:
        """评估风险"""
        complex_keywords = ["支付", "财务", "安全", "交易", "敏感"]
        if any(kw in user_input for kw in complex_keywords):
            return "高"
        return "中"

    def generate_prd(self, prd_data: Dict[str, Any]) -> str:
        """生成 PRD 文档"""
        prd_text = f"""# 产品需求文档

## 需求概述
{prd_data.get('requirements', '')}

## 优先级
{prd_data.get('priority', 'P1')}

## 风险等级
{prd_data.get('risk', '中')}

## 业务模块
{chr(10).join(f"- {m}" for m in prd_data.get('modules', []))}
"""
        return prd_text


if __name__ == "__main__":
    agent = PMAgent()
    result = agent.analyze_requirement("用户需要登录功能和权限管理模块")
    print(json.dumps(result, ensure_ascii=False, indent=2))