"""
Task Agent - 任务拆解 Agent
负责将 PRD 拆解为标准化任务颗粒，分配执行对象
"""

import json
from typing import Dict, List, Any


class TaskAgent:
    def __init__(self):
        self.name = "Task Agent"
        self.role = "Task Planner"

    def decompose_task(self, prd: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        将 PRD 拆解为子任务

        Args:
            prd: PM Agent 输出的 PRD 数据

        Returns:
            任务列表，每项包含 task 描述和 owner
        """
        tasks = []
        modules = prd.get("modules", [])

        task_mapping = {
            "登录": ["创建用户表", "实现登录接口", "会话管理"],
            "权限": ["权限表设计", "权限校验中间件", "角色管理接口"],
            "报表": ["报表数据模型", "报表查询接口", "导出功能"],
            "用户": ["用户 CRUD", "用户搜索", "用户状态管理"],
            "订单": ["订单表设计", "下单流程", "订单状态机"],
            "支付": ["支付接口", "回调处理", "对账功能"],
            "库存": ["库存表设计", "库存扣减", "库存预警"],
            "财务": ["财务报表", "财务对账", "发票管理"],
        }

        for module in modules:
            module_tasks = task_mapping.get(module, ["基础功能开发"])
            for task in module_tasks:
                tasks.append({
                    "task": task,
                    "owner": self._get_owner(task),
                    "module": module
                })

        return tasks

    def _get_owner(self, task: str) -> str:
        """根据任务类型分配执行 Agent"""
        if any(kw in task for kw in ["表", "设计", "模型"]):
            return "Dev Agent"
        elif any(kw in task for kw in ["接口", "功能", "流程"]):
            return "Dev Agent"
        elif any(kw in task for kw in ["测试", "用例"]):
            return "Test Agent"
        elif any(kw in task for kw in ["部署", "发布", "上线"]):
            return "Deploy Agent"
        return "Dev Agent"

    def standardize_output(self, tasks: List[Dict[str, str]]) -> str:
        """输出标准化任务列表"""
        output = "```json\n"
        output += json.dumps(tasks, ensure_ascii=False, indent=2)
        output += "\n```"
        return output


if __name__ == "__main__":
    agent = TaskAgent()
    prd = {
        "modules": ["登录", "权限"],
        "priority": "P1",
        "risk": "中"
    }
    tasks = agent.decompose_task(prd)
    print(agent.standardize_output(tasks))