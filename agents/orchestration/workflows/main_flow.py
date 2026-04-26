"""
主工作流 - 串联所有 Agent
需求输入 → PM Agent → Task Agent → Dev Agent → Test Agent → Fix Agent → Review Agent → Git Agent → Deploy Agent
"""

import json
from typing import Dict, Any, List, Optional

from agents.pm_agent import PMAgent
from agents.task_agent import TaskAgent
from agents.dev_agent import DevAgent
from agents.test_agent import TestAgent
from agents.fix_agent import FixAgent
from agents.review_agent import ReviewAgent
from agents.git_agent import GitAgent
from agents.deploy_agent import DeployAgent
from agents.monitor_agent import MonitorAgent


class MainWorkflow:
    def __init__(self, repo_path: str = "."):
        self.agents = {
            "pm": PMAgent(),
            "task": TaskAgent(),
            "dev": DevAgent(),
            "test": TestAgent(),
            "fix": FixAgent(),
            "review": ReviewAgent(),
            "git": GitAgent(repo_path),
            "deploy": DeployAgent(),
            "monitor": MonitorAgent()
        }
        self.results = {}

    def run(self, user_requirement: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行完整工作流

        Args:
            user_requirement: 用户需求描述
            config: 配置选项

        Returns:
            工作流执行结果
        """
        config = config or {}
        workflow_result = {
            "status": "running",
            "requirement": user_requirement,
            "steps": []
        }

        # Step 1: PM Agent - 需求分析
        print("=" * 50)
        print("Step 1: PM Agent - 需求分析")
        print("=" * 50)
        prd_result = self.agents["pm"].analyze_requirement(user_requirement)
        workflow_result["steps"].append({
            "step": "pm_analysis",
            "agent": "PM Agent",
            "status": "completed",
            "output": prd_result
        })
        print(f"PRD Result: {json.dumps(prd_result, ensure_ascii=False, indent=2)}")
        print()

        # Step 2: Task Agent - 任务拆解
        print("=" * 50)
        print("Step 2: Task Agent - 任务拆解")
        print("=" * 50)
        tasks = self.agents["task"].decompose_task(prd_result)
        workflow_result["steps"].append({
            "step": "task_decomposition",
            "agent": "Task Agent",
            "status": "completed",
            "output": tasks
        })
        print(f"Tasks: {json.dumps(tasks, ensure_ascii=False, indent=2)}")
        print()

        # Step 3: Dev Agent - 开发
        print("=" * 50)
        print("Step 3: Dev Agent - 开发")
        print("=" * 50)
        dev_results = []
        for task in tasks:
            if task.get("owner") == "Dev Agent":
                code = self.agents["dev"].generate_code(task, {"language": "python"})
                dev_results.append({
                    "task": task["task"],
                    "code": code
                })
                print(f"Generated code for: {task['task']}")
        workflow_result["steps"].append({
            "step": "development",
            "agent": "Dev Agent",
            "status": "completed",
            "output": dev_results
        })
        print()

        # Step 4: Test Agent - 测试
        print("=" * 50)
        print("Step 4: Test Agent - 测试")
        print("=" * 50)
        test_results = []
        for task in tasks:
            if task.get("owner") == "Test Agent":
                test_code = self.agents["test"].generate_test(task, "")
                test_results.append({
                    "task": task["task"],
                    "test_code": test_code
                })
                print(f"Generated test for: {task['task']}")
        workflow_result["steps"].append({
            "step": "testing",
            "agent": "Test Agent",
            "status": "completed",
            "output": test_results
        })
        print()

        # Step 5: Fix Agent - 修复（如需要）
        # 这里可以添加错误处理逻辑

        # Step 6: Review Agent - 代码审查
        print("=" * 50)
        print("Step 6: Review Agent - 代码审查")
        print("=" * 50)
        review_results = []
        for result in dev_results:
            code = result.get("code", "")
            if code:
                review = self.agents["review"].review(code)
                review_results.append({
                    "task": result["task"],
                    "review": review
                })
                print(f"Review score for {result['task']}: {review.get('score', 0)}/100")
        workflow_result["steps"].append({
            "step": "review",
            "agent": "Review Agent",
            "status": "completed",
            "output": review_results
        })
        print()

        # Step 7: Git Agent - Git 操作
        print("=" * 50)
        print("Step 7: Git Agent - Git 操作")
        print("=" * 50)
        git_status = self.agents["git"].status()
        workflow_result["steps"].append({
            "step": "git_operations",
            "agent": "Git Agent",
            "status": "completed",
            "output": git_status.get("stdout", "")
        })
        print(f"Git status: {git_status.get('stdout', 'No output')[:200]}")
        print()

        # Step 8: Deploy Agent - 部署（可选）
        if config.get("auto_deploy", False):
            print("=" * 50)
            print("Step 8: Deploy Agent - 部署")
            print("=" * 50)
            deploy_result = self.agents["deploy"].deploy(
                version=config.get("version", "v1.0.0"),
                env=config.get("environment", "staging")
            )
            workflow_result["steps"].append({
                "step": "deployment",
                "agent": "Deploy Agent",
                "status": "completed" if deploy_result.get("success") else "failed",
                "output": deploy_result
            })
            print(f"Deploy result: {deploy_result}")
            print()

        workflow_result["status"] = "completed"
        return workflow_result

    def run_single_agent(self, agent_name: str, input_data: Any) -> Any:
        """
        单独运行某个 Agent

        Args:
            agent_name: Agent 名称
            input_data: 输入数据

        Returns:
            Agent 输出
        """
        if agent_name not in self.agents:
            return {"error": f"Unknown agent: {agent_name}"}

        agent = self.agents[agent_name]

        if agent_name == "pm":
            return agent.analyze_requirement(input_data)
        elif agent_name == "task":
            return agent.decompose_task(input_data)
        elif agent_name == "dev":
            return agent.generate_code(input_data, {})
        elif agent_name == "test":
            return agent.generate_test(input_data, "")
        elif agent_name == "fix":
            return agent.analyze_error(input_data)
        elif agent_name == "review":
            return agent.review(input_data)
        elif agent_name == "git":
            return agent.status()
        elif agent_name == "deploy":
            return agent.check_environment(input_data)
        elif agent_name == "monitor":
            return agent.check_system_health()

        return {"error": f"Agent {agent_name} not implemented"}


if __name__ == "__main__":
    workflow = MainWorkflow("/Users/fox/Claude Code/GitHub/openclaw-home-pc")

    # 运行完整工作流
    result = workflow.run(
        "用户需要一个登录系统，支持手机号和邮箱登录",
        {"auto_deploy": False}
    )

    print("\n" + "=" * 50)
    print("Workflow Result:")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))