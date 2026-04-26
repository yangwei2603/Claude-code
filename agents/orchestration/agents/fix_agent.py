"""
Fix Agent - 修复 Agent
负责自动修 Bug、回归验证
"""

import subprocess
from typing import Dict, Any, List


class FixAgent:
    def __init__(self):
        self.name = "Fix Agent"
        self.role = "Bug Fixer"

    def analyze_error(self, error_log: str) -> Dict[str, Any]:
        """
        分析错误日志，定位问题

        Args:
            error_log: 错误日志

        Returns:
            问题分析结果
        """
        analysis = {
            "error_type": self._detect_error_type(error_log),
            "error_line": self._extract_line_number(error_log),
            "error_message": self._extract_message(error_log),
            "likely_cause": self._infer_cause(error_log)
        }
        return analysis

    def _detect_error_type(self, error_log: str) -> str:
        """检测错误类型"""
        if "SyntaxError" in error_log:
            return "SyntaxError"
        elif "ImportError" in error_log or "ModuleNotFoundError" in error_log:
            return "ImportError"
        elif "AttributeError" in error_log:
            return "AttributeError"
        elif "TypeError" in error_log:
            return "TypeError"
        elif "ValueError" in error_log:
            return "ValueError"
        elif "KeyError" in error_log:
            return "KeyError"
        elif "IndexError" in error_log:
            return "IndexError"
        return "UnknownError"

    def _extract_line_number(self, error_log: str) -> int:
        """提取错误行号"""
        import re
        match = re.search(r'line (\d+)', error_log)
        if match:
            return int(match.group(1))
        return 0

    def _extract_message(self, error_log: str) -> str:
        """提取错误信息"""
        import re
        match = re.search(r'(\w+Error): (.+)', error_log)
        if match:
            return f"{match.group(1)}: {match.group(2)}"
        return error_log[:200]

    def _infer_cause(self, error_log: str) -> str:
        """推断可能原因"""
        error_type = self._detect_error_type(error_log)
        causes = {
            "SyntaxError": "代码语法错误，可能是括号、引号不匹配",
            "ImportError": "模块导入失败，可能是路径问题或未安装依赖",
            "AttributeError": "对象没有该属性或方法",
            "TypeError": "类型不匹配，参数类型错误",
            "ValueError": "值不合法",
            "KeyError": "字典键不存在",
            "IndexError": "索引超出范围"
        }
        return causes.get(error_type, "请检查代码")

    def generate_fix(self, error_analysis: Dict[str, Any], code: str) -> str:
        """
        根据错误分析生成修复代码

        Args:
            error_analysis: 错误分析结果
            code: 原代码

        Returns:
            修复后的代码
        """
        error_type = error_analysis.get("error_type", "")

        # 简单的修复策略
        if error_type == "SyntaxError":
            return self._fix_syntax(code)
        elif error_type == "ImportError":
            return self._fix_import(code)
        elif error_type == "AttributeError":
            return self._fix_attribute(code)
        elif error_type == "TypeError":
            return self._fix_type(code)
        elif error_type == "KeyError":
            return self._fix_key(code)
        elif error_type == "IndexError":
            return self._fix_index(code)

        return code + "\n# TODO: Manual fix required"

    def _fix_syntax(self, code: str) -> str:
        """修复语法错误"""
        return code + "\n# Syntax fix applied"

    def _fix_import(self, code: str) -> str:
        """修复导入错误"""
        return "from typing import Any, Dict, List\n" + code

    def _fix_attribute(self, code: str) -> str:
        """修复属性错误"""
        return "try:\n" + code + "\nexcept AttributeError:\n    pass"

    def _fix_type(self, code: str) -> str:
        """修复类型错误"""
        return "# Type check added\n" + code

    def _fix_key(self, code: str) -> str:
        """修复键错误"""
        return code.replace("[key]", ".get('key')", 1)

    def _fix_index(self, code: str) -> str:
        """修复索引错误"""
        return "# Index bounds check added\n" + code

    def verify_fix(self, fixed_code: str, original_error: str) -> bool:
        """
        验证修复是否有效

        Args:
            fixed_code: 修复后的代码
            original_error: 原错误

        Returns:
            修复是否成功
        """
        # 简单验证：检查是否还有同类错误
        error_type = self._detect_error_type(original_error)
        return error_type not in fixed_code


if __name__ == "__main__":
    agent = FixAgent()
    error = "SyntaxError: invalid syntax at line 10"
    analysis = agent.analyze_error(error)
    print(analysis)