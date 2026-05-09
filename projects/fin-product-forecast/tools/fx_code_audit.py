#!/usr/bin/env python3
"""Scan repository artifacts for FX prediction related content and flag practical risks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = ("汇率", "USD/CNY", "exchange", "forex", "fx", "prediction", "预测")
SESSION_DIR = ROOT / "agents" / "main" / "sessions"
RUNS_FILE = ROOT / "subagents" / "runs.json"
REPORT_FILE = ROOT / "reports" / "fx_prediction_audit_report.md"


@dataclass
class Finding:
    title: str
    severity: str
    detail: str
    location: str
    suggestion: str


def contains_keyword(text: str) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in KEYWORDS)


def iter_session_texts() -> Iterable[tuple[str, str]]:
    if not SESSION_DIR.exists():
        return
    for path in sorted(SESSION_DIR.glob("*.jsonl*")):
        try:
            with path.open("r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = json.dumps(obj, ensure_ascii=False)
                    if contains_keyword(text):
                        yield f"{path.relative_to(ROOT)}:{i}", text
        except OSError:
            continue


def scan_sensitive_keys(text: str) -> list[str]:
    patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"apiKey\s*[:=]\s*\"[^\"]+\"",
        r"appSecret\s*[:=]\s*\"[^\"]+\"",
    ]
    hits = []
    for p in patterns:
        if re.search(p, text):
            hits.append(p)
    return hits


def build_findings() -> list[Finding]:
    findings: list[Finding] = []
    matches = list(iter_session_texts())

    if not matches:
        findings.append(
            Finding(
                title="仓库中未发现汇率预测源码",
                severity="high",
                detail="当前仓库主要为 OpenClaw 运行配置与日志，未定位到独立的汇率预测模型源码目录。",
                location="repo-scope",
                suggestion="请将汇率预测系统源码（数据处理/训练/推理）同步到当前仓库，或提供准确路径。",
            )
        )
        return findings

    findings.append(
        Finding(
            title="汇率预测信息主要存在于会话日志，不是可维护源码",
            severity="high",
            detail=f"共检测到 {len(matches)} 条与汇率/预测相关记录，均位于会话日志或运行记录中。",
            location="agents/main/sessions/*.jsonl*, subagents/runs.json",
            suggestion="将汇率预测逻辑沉淀为独立模块与测试，而不是仅保留在会话文本。",
        )
    )

    if RUNS_FILE.exists():
        raw = RUNS_FILE.read_text(encoding="utf-8", errors="ignore")
        if "15-25%" in raw:
            findings.append(
                Finding(
                    title="效果数字缺少可复现计算依据",
                    severity="medium",
                    detail="存在“预计降低运营成本15-25%”等结论型指标，但未绑定可复现公式/数据源。",
                    location="subagents/runs.json",
                    suggestion="在汇率预测系统中增加评估脚本，输出 MAE/MAPE 与成本影响的可追溯报表。",
                )
            )

    # Scan all tracked json files for possible sensitive keys.
    for path in ROOT.rglob("*.json"):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == ".git":
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        hits = scan_sensitive_keys(raw)
        if hits:
            findings.append(
                Finding(
                    title="发现明文凭据风险",
                    severity="critical",
                    detail="检测到疑似 API/应用密钥明文存储模式。",
                    location=str(rel),
                    suggestion="改用环境变量或密钥管理服务，并对历史提交执行密钥轮换。",
                )
            )
            break

    return findings


def render_report(findings: list[Finding]) -> str:
    lines = [
        "# 汇率预测系统代码排查报告",
        "",
        "## 结论摘要",
        "- 本次排查优先扫描与汇率预测相关的代码/记录，并给出可执行优化建议。",
        f"- 共输出 **{len(findings)}** 条问题，其中按严重级别排序。",
        "",
        "## 问题清单",
    ]

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for idx, f in enumerate(sorted(findings, key=lambda x: severity_rank.get(x.severity, 9)), start=1):
        lines.extend(
            [
                f"### {idx}. [{f.severity.upper()}] {f.title}",
                f"- 位置: `{f.location}`",
                f"- 现象: {f.detail}",
                f"- 建议: {f.suggestion}",
                "",
            ]
        )

    lines.extend(
        [
            "## 建议的下一步（面向汇率预测系统）",
            "1. 补齐源码：提交 `data_pipeline/`, `model/`, `inference/`, `evaluation/` 四类目录。",
            "2. 补齐基线：至少提供 Naive、ARIMA/Prophet、LSTM/XGBoost 三类基线对比。",
            "3. 补齐评估：固定时间切分，输出 MAE/MAPE/RMSE + 回测报告。",
            "4. 补齐运维：配置文件与密钥分离、模型版本与数据版本打标。",
            "5. 补齐可观测：上线后监控漂移、延迟、异常值比例与失败重试率。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    findings = build_findings()
    report = render_report(findings)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Wrote report to: {REPORT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
