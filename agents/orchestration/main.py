#!/usr/bin/env python3
"""
Agent Skill System - 主入口
企业级多 Agent 工作流系统

Usage:
    python main.py --requirement "用户需求描述"
    python main.py --agent pm --input "需求"
    python main.py --workflow
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from workflows.main_flow import MainWorkflow


def main():
    parser = argparse.ArgumentParser(description="Agent Skill System")
    parser.add_argument("--requirement", "-r", type=str, help="用户需求描述")
    parser.add_argument("--agent", "-a", type=str, help="单独运行某个 Agent")
    parser.add_argument("--input", "-i", type=str, help="Agent 输入数据")
    parser.add_argument("--config", "-c", type=str, help="配置文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出文件路径")
    parser.add_argument("--deploy", action="store_true", help="启用自动部署")
    parser.add_argument("--environment", "-e", type=str, default="staging", help="部署环境")
    parser.add_argument("--version", "-v", type=str, default="v1.0.0", help="版本号")
    parser.add_argument("--repo-path", type=str, default=None, help="Git 仓库路径（默认为当前目录）")

    args = parser.parse_args()

    # 初始化工作流
    repo_path = args.repo_path or os.environ.get("AGENT_REPO_PATH", str(Path(__file__).parent))
    workflow = MainWorkflow(repo_path)

    if args.agent:
        # 单独运行某个 Agent
        print(f"Running agent: {args.agent}")
        result = workflow.run_single_agent(args.agent, args.input)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.requirement:
        # 运行完整工作流
        print(f"Requirement: {args.requirement}")
        print(f"Environment: {args.environment}")
        print(f"Version: {args.version}")
        print()

        config = {
            "auto_deploy": args.deploy,
            "environment": args.environment,
            "version": args.version
        }

        result = workflow.run(args.requirement, config)
        print("\n" + "=" * 50)
        print("Final Result:")
        print("=" * 50)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 保存结果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nResult saved to: {args.output}")

    else:
        # 交互模式
        print("Agent Skill System - Interactive Mode")
        print("=" * 50)
        print("Available agents:")
        print("  - pm      : Product Manager Agent")
        print("  - task    : Task Decomposition Agent")
        print("  - dev     : Development Agent")
        print("  - test    : Test Agent")
        print("  - fix     : Bug Fix Agent")
        print("  - review  : Code Review Agent")
        print("  - git     : Git Agent")
        print("  - deploy  : Deploy Agent")
        print("  - monitor : Monitor Agent")
        print()
        print("Usage: python main.py --agent <agent_name> --input <input_data>")
        print("       python main.py --requirement <your_requirement>")


if __name__ == "__main__":
    main()