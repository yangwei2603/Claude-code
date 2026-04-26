"""
Git Agent - Git Agent
负责自动 commit、push、PR
"""

import subprocess
import os
from typing import Dict, Any, Optional
from datetime import datetime


class GitAgent:
    def __init__(self, repo_path: str = "."):
        self.name = "Git Agent"
        self.role = "Git Manager"
        self.repo_path = repo_path

    def status(self) -> Dict[str, Any]:
        """查看 Git 状态"""
        result = self._run_command(["git", "status"])
        return result

    def add(self, files: Optional[list] = None) -> Dict[str, Any]:
        """
        添加文件到暂存区

        Args:
            files: 文件列表，None 表示所有文件

        Returns:
            执行结果
        """
        if files:
            result = self._run_command(["git", "add"] + files)
        else:
            result = self._run_command(["git", "add", "-A"])
        return result

    def commit(self, message: str) -> Dict[str, Any]:
        """
        提交更改

        Args:
            message: 提交信息

        Returns:
            执行结果
        """
        result = self._run_command(["git", "commit", "-m", message])
        return result

    def push(self, remote: str = "origin", branch: str = "HEAD") -> Dict[str, Any]:
        """
        推送更改

        Args:
            remote: 远程仓库名
            branch: 分支名

        Returns:
            执行结果
        """
        result = self._run_command(["git", "push", remote, branch])
        return result

    def create_branch(self, branch_name: str, from_branch: str = None) -> Dict[str, Any]:
        """
        创建分支

        Args:
            branch_name: 新分支名
            from_branch: 起始分支，None 表示从当前分支

        Returns:
            执行结果
        """
        if from_branch:
            result = self._run_command(["git", "checkout", "-b", branch_name, from_branch])
        else:
            result = self._run_command(["git", "checkout", "-b", branch_name])
        return result

    def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """切换分支"""
        return self._run_command(["git", "checkout", branch_name])

    def create_pr(self, title: str, body: str, head: str, base: str = "main") -> Dict[str, Any]:
        """
        创建 Pull Request

        Args:
            title: PR 标题
            body: PR 描述
            head: 源分支
            base: 目标分支

        Returns:
            执行结果
        """
        # 使用 gh CLI 创建 PR
        result = self._run_command([
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--head", head,
            "--base", base
        ])
        return result

    def get_current_branch(self) -> str:
        """获取当前分支名"""
        result = self._run_command(["git", "branch", "--show-current"])
        if result.get("success"):
            return result.get("stdout", "").strip()
        return ""

    def get_diff(self, files: Optional[list] = None) -> str:
        """获取差异"""
        if files:
            result = self._run_command(["git", "diff"] + files)
        else:
            result = self._run_command(["git", "diff"])
        return result.get("stdout", "")

    def log(self, limit: int = 10) -> Dict[str, Any]:
        """获取提交日志"""
        return self._run_command(["git", "log", f"-{limit}", "--oneline"])

    def auto_commit(self, message: str, files: Optional[list] = None) -> Dict[str, Any]:
        """
        自动提交（add + commit）

        Args:
            message: 提交信息
            files: 文件列表

        Returns:
            执行结果
        """
        add_result = self.add(files)
        if not add_result.get("success"):
            return add_result

        return self.commit(message)

    def _run_command(self, cmd: list) -> Dict[str, Any]:
        """执行命令"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {cmd[0]}"
            }


if __name__ == "__main__":
    agent = GitAgent("/Users/fox/Claude Code/GitHub/openclaw-home-pc")
    print(agent.status())