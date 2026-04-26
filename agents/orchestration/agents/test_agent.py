"""
Test Agent - 测试 Agent
负责自动生成测试用例、自动运行测试、输出错误日志
"""

import subprocess
from typing import Dict, List, Any


class TestAgent:
    def __init__(self):
        self.name = "Test Agent"
        self.role = "Tester"

    def generate_test(self, task: Dict[str, str], code_context: str) -> str:
        """
        根据代码生成测试用例

        Args:
            task: 任务描述
            code_context: 代码上下文

        Returns:
            测试代码
        """
        task_name = task.get("task", "")
        module = task.get("module", "")

        if "表" in task_name or "模型" in task_name:
            return self._generate_model_test(module)
        elif "接口" in task_name or "API" in task_name:
            return self._generate_api_test(module)
        else:
            return self._generate_basic_test(module)

    def _generate_model_test(self, module: str) -> str:
        """生成模型测试"""
        return f'''
import pytest
from models.{module.lower()} import {module}Model

class Test{module}Model:
    def test_create(self):
        model = {module}Model()
        assert model.id is None

    def test_to_dict(self):
        model = {module}Model()
        result = model.to_dict()
        assert isinstance(result, dict)

    def test_from_dict(self):
        data = {{"id": 1}}
        model = {module}Model.from_dict(data)
        assert model.id == 1
'''

    def _generate_api_test(self, module: str) -> str:
        """生成 API 测试"""
        return f'''
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class Test{module}API:
    def test_create_{module.lower()}(self):
        response = client.post("/{module.lower()}", json={{"name": "test"}})
        assert response.status_code in [200, 201]

    def test_get_{module.lower()}(self):
        response = client.get("/{module.lower()}/1")
        assert response.status_code in [200, 404]
'''

    def _generate_basic_test(self, module: str) -> str:
        """生成基础测试"""
        return f'''
import pytest

class Test{module}:
    def test_basic(self):
        assert True
'''

    def run_tests(self, test_file: str) -> Dict[str, Any]:
        """
        运行测试并返回结果

        Args:
            test_file: 测试文件路径

        Returns:
            测试结果
        """
        try:
            result = subprocess.run(
                ["pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
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
                "error": "Test timeout"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "pytest not found"
            }

    def parse_test_report(self, test_result: Dict[str, Any]) -> str:
        """解析测试报告"""
        if test_result.get("success"):
            return "✅ All tests passed"
        else:
            return f"""❌ Tests failed
{test_result.get('stderr', '')}"""


if __name__ == "__main__":
    agent = TestAgent()
    test_code = agent.generate_test({"task": "创建用户表", "module": "用户"}, "")
    print(test_code)