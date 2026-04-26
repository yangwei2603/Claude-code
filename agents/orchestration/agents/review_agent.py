"""
Review Agent - 审查 Agent
负责安全检查、性能检查、SQL 风险、权限问题、代码规范
"""

from typing import Dict, List, Any, Tuple


class ReviewAgent:
    def __init__(self):
        self.name = "Review Agent"
        self.role = "Code Reviewer"

    def review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        全面审查代码

        Args:
            code: 待审查代码
            language: 编程语言

        Returns:
            审查结果
        """
        results = {
            "security": self.check_security(code),
            "performance": self.check_performance(code),
            "sql_risk": self.check_sql_risk(code),
            "permission": self.check_permission(code),
            "code_style": self.check_code_style(code, language)
        }

        # 计算总分
        issues_count = sum([
            len(results["security"].get("issues", [])),
            len(results["performance"].get("issues", [])),
            len(results["sql_risk"].get("issues", [])),
            len(results["permission"].get("issues", [])),
            len(results["code_style"].get("issues", []))
        ])

        results["score"] = max(0, 100 - issues_count * 10)
        results["passed"] = issues_count == 0

        return results

    def check_security(self, code: str) -> Dict[str, Any]:
        """安全检查"""
        issues = []

        # 检查硬编码密码
        if any(kw in code.lower() for kw in ["password", "pwd", "secret"]) and "=" in code:
            if not any(x in code for x in ["os.environ", "getenv", "env", "config"]):
                issues.append("⚠️ 可能存在硬编码密码或密钥")

        # 检查 SQL 注入风险
        if "execute(" in code and "+" in code and "SELECT" in code.upper():
            issues.append("⚠️ 可能存在 SQL 注入风险，请使用参数化查询")

        # 检查命令注入风险
        if "os.system" in code or "subprocess.call" in code:
            if "+" in code or "input" in code:
                issues.append("⚠️ 可能存在命令注入风险")

        # 检查 eval 使用
        if "eval(" in code:
            issues.append("⚠️ 使用 eval() 存在安全风险")

        # 检查不安全的加密
        if "md5(" in code.lower() or "sha1(" in code.lower():
            issues.append("⚠️ MD5/SHA1 已不安全，建议使用 bcrypt 或 argon2")

        return {
            "category": "Security",
            "issues": issues,
            "passed": len(issues) == 0
        }

    def check_performance(self, code: str) -> Dict[str, Any]:
        """性能检查"""
        issues = []

        # 检查循环内查询
        if "for " in code and (".query(" in code or ".find(" in code):
            issues.append("⚠️ 检测到循环内数据库查询，可能导致 N+1 问题")

        # 检查全表扫描
        if ".all()" in code and "filter" not in code:
            issues.append("⚠️ 可能存在全表扫描，建议添加分页")

        # 检查重复查询
        if code.count(".query(") > 5 or code.count(".find(") > 5:
            issues.append("⚠️ 检测到大量数据库查询，考虑缓存")

        # 检查大文件读取
        if "open(" in code and "rb" in code and "read()" in code:
            if "with" not in code:
                issues.append("⚠️ 文件未使用 with 语句，可能导致资源泄漏")

        return {
            "category": "Performance",
            "issues": issues,
            "passed": len(issues) == 0
        }

    def check_sql_risk(self, code: str) -> Dict[str, Any]:
        """SQL 风险检查"""
        issues = []

        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE"]
        code_upper = code.upper()

        for keyword in sql_keywords:
            if keyword in code_upper and "+" in code and "?" not in code and "%" not in code:
                issues.append(f"⚠️ {keyword} 语句可能存在注入风险")
                break

        if "cursor.execute" in code and '"%s"' in code:
            issues.append("⚠️ 使用 % 格式化字符串有 SQL 注入风险，请使用 parameterized queries")

        return {
            "category": "SQL Risk",
            "issues": issues,
            "passed": len(issues) == 0
        }

    def check_permission(self, code: str) -> Dict[str, Any]:
        """权限检查"""
        issues = []

        # 检查文件权限
        if ".chmod(" in code or "0o777" in code:
            issues.append("⚠️ 设置 777 权限存在安全风险")

        # 检查敏感文件访问
        if any(f in code for f in ["/etc/passwd", ".ssh/", ".env"]):
            issues.append("⚠️ 访问敏感文件请确保有适当权限控制")

        # 检查注释中的敏感信息
        if "TODO" in code and any(kw in code.upper() for kw in ["PASSWORD", "SECRET", "KEY"]):
            issues.append("⚠️ 注释中可能包含敏感信息")

        return {
            "category": "Permission",
            "issues": issues,
            "passed": len(issues) == 0
        }

    def check_code_style(self, code: str, language: str) -> Dict[str, Any]:
        """代码规范检查"""
        issues = []

        if language == "python":
            # 检查 PEP8 基本规范
            if "\t" in code:
                issues.append("⚠️ 使用了 Tab 缩进，建议使用 4 空格")

            if len(code.split("\n")) > 100 and "class " in code:
                issues.append("⚠️ 类代码过长，考虑拆分")

            if "except:" in code:
                issues.append("⚠️ 使用裸 except 请添加具体异常类型")

        return {
            "category": "Code Style",
            "issues": issues,
            "passed": len(issues) == 0
        }

    def generate_report(self, review_results: Dict[str, Any]) -> str:
        """生成审查报告"""
        report = ["# Code Review Report", ""]
        report.append(f"**Score**: {review_results.get('score', 0)}/100")
        report.append(f"**Status**: {'✅ PASSED' if review_results.get('passed') else '❌ FAILED'}")
        report.append("")

        for category in ["security", "performance", "sql_risk", "permission", "code_style"]:
            data = review_results.get(category, {})
            report.append(f"## {data.get('category', category)}")
            if data.get("issues"):
                for issue in data["issues"]:
                    report.append(f"- {issue}")
            else:
                report.append("- ✅ No issues found")
            report.append("")

        return "\n".join(report)


if __name__ == "__main__":
    agent = ReviewAgent()
    code = '''
password = "123456"  # hardcoded
result = db.execute("SELECT * FROM users WHERE id=" + user_id)
'''
    results = agent.review(code)
    print(agent.generate_report(results))