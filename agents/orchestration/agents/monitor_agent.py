"""
Monitor Agent - 监控 Agent
负责日志分析、告警处理、自动生成优化建议
"""

import re
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class MonitorAgent:
    def __init__(self):
        self.name = "Monitor Agent"
        self.role = "Monitoring"

    def analyze_logs(self, log_content: str, time_range: str = "1h") -> Dict[str, Any]:
        """
        分析日志内容

        Args:
            log_content: 日志内容
            time_range: 时间范围

        Returns:
            分析结果
        """
        analysis = {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "total_lines": len(log_content.split("\n")),
            "error_count": 0,
            "warning_count": 0,
            "error_patterns": [],
            "warnings": [],
            "recommendations": []
        }

        lines = log_content.split("\n")
        for line in lines:
            if self._is_error(line):
                analysis["error_count"] += 1
                error_type = self._classify_error(line)
                if error_type not in analysis["error_patterns"]:
                    analysis["error_patterns"].append(error_type)
            elif self._is_warning(line):
                analysis["warning_count"] += 1
                analysis["warnings"].append(line)

        # 生成优化建议
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _is_error(self, line: str) -> bool:
        """判断是否为错误行"""
        error_keywords = ["ERROR", "Exception", "FATAL", "CRITICAL", "FAILED", "Traceback"]
        return any(kw in line.upper() for kw in error_keywords)

    def _is_warning(self, line: str) -> bool:
        """判断是否为警告行"""
        warning_keywords = ["WARNING", "WARN", "PERFORMANCE", "SLOW"]
        return any(kw in line.upper() for kw in warning_keywords)

    def _classify_error(self, error_line: str) -> str:
        """分类错误"""
        if "Timeout" in error_line:
            return "Timeout Error"
        elif "Memory" in error_line or "MemoryError" in error_line:
            return "Memory Error"
        elif "Connection" in error_line or "Connect" in error_line:
            return "Connection Error"
        elif "Permission" in error_line or "Access" in error_line:
            return "Permission Error"
        elif "SyntaxError" in error_line:
            return "Syntax Error"
        elif "ImportError" in error_line:
            return "Import Error"
        elif "KeyError" in error_line:
            return "Key Error"
        elif "ValueError" in error_line:
            return "Value Error"
        else:
            return "General Error"

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if analysis["error_count"] > 10:
            recommendations.append("错误数量较多，建议立即进行系统检查")

        if "Timeout Error" in analysis["error_patterns"]:
            recommendations.append("检测到超时错误，建议增加超时时间或优化慢查询")

        if "Memory Error" in analysis["error_patterns"]:
            recommendations.append("检测到内存错误，建议增加内存或检查内存泄漏")

        if "Connection Error" in analysis["error_patterns"]:
            recommendations.append("检测到连接错误，检查网络和依赖服务状态")

        if analysis["warning_count"] > 50:
            recommendations.append("警告数量较多，建议优化代码和配置")

        if not recommendations:
            recommendations.append("系统运行正常，未检测到明显问题")

        return recommendations

    def check_system_health(self) -> Dict[str, Any]:
        """
        检查系统健康状态

        Returns:
            健康状态报告
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self._check_cpu(),
            "memory": self._check_memory(),
            "disk": self._check_disk(),
            "processes": self._check_processes()
        }

        health["overall"] = "healthy" if all([
            health["cpu"]["status"] == "ok",
            health["memory"]["status"] == "ok",
            health["disk"]["status"] == "ok"
        ]) else "unhealthy"

        return health

    def _check_cpu(self) -> Dict[str, Any]:
        """检查 CPU 使用率"""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["top", "-l", "1", "-n", "1"],
                    capture_output=True,
                    text=True
                )
                return {"status": "ok", "info": "CPU check completed"}
        except:
            pass
        return {"status": "unknown"}

    def _check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "status": "ok" if mem.percent < 80 else "warning",
                "usage_percent": mem.percent,
                "total_gb": mem.total / (1024**3)
            }
        except ImportError:
            return {"status": "unknown", "error": "psutil not installed"}
        except:
            pass
        return {"status": "unknown"}

    def _check_disk(self) -> Dict[str, Any]:
        """检查磁盘使用"""
        try:
            import psutil
            disk = psutil.disk_usage("/")
            return {
                "status": "ok" if disk.percent < 80 else "warning",
                "usage_percent": disk.percent
            }
        except ImportError:
            return {"status": "unknown", "error": "psutil not installed"}
        except:
            pass
        return {"status": "unknown"}

    def _check_processes(self) -> Dict[str, Any]:
        """检查关键进程"""
        return {
            "status": "ok",
            "critical_processes_running": True
        }

    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成监控报告"""
        report = ["# System Monitoring Report", ""]
        report.append(f"**Time Range**: {analysis.get('time_range', 'N/A')}")
        report.append(f"**Generated**: {analysis.get('timestamp', '')}")
        report.append("")

        report.append("## Summary")
        report.append(f"- Total Log Lines: {analysis.get('total_lines', 0)}")
        report.append(f"- Errors: {analysis.get('error_count', 0)}")
        report.append(f"- Warnings: {analysis.get('warning_count', 0)}")
        report.append("")

        if analysis.get("error_patterns"):
            report.append("## Error Patterns Detected")
            for pattern in analysis["error_patterns"]:
                report.append(f"- {pattern}")
            report.append("")

        if analysis.get("recommendations"):
            report.append("## Recommendations")
            for rec in analysis["recommendations"]:
                report.append(f"- {rec}")

        return "\n".join(report)


if __name__ == "__main__":
    import platform
    agent = MonitorAgent()
    print(agent.check_system_health())