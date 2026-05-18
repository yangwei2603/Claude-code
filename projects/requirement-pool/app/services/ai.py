"""
AI 质量分析服务（规则评分）
权重：描述完整性 40% + 效果清晰度 30% + 依赖识别 15% + 范围明确性 15%
"""
import re
from dataclasses import dataclass


@dataclass
class QualityScore:
    total: float
    desc_score: float
    obj_score: float
    dep_score: float
    scope_score: float
    suggestions: list[str]


VAGUE_WORDS = ["优化", "改进", "提升", "完善", "加强", "相关", "一些", "若干", "大概", "可能"]


def _desc_score(text: str | None) -> float:
    n = len(text or "")
    if n >= 50:
        return 100
    if n < 20:
        return 0
    return (n - 20) / 30 * 100


def _obj_score(text: str | None) -> float:
    n = len(text or "")
    if n >= 20:
        return 100
    if n < 10:
        return 0
    return (n - 10) / 10 * 100


def _dep_score(text: str | None) -> float:
    dep_keywords = ["依赖", "关联", "需要先", "前提", "等待", "前置", "对接", "调用", "基于"]
    t = text or ""
    return 100 if any(kw in t for kw in dep_keywords) else 0


def _scope_score(text: str | None) -> float:
    t = text or ""
    vague_count = sum(1 for w in VAGUE_WORDS if w in t)
    if vague_count == 0:
        return 100
    if vague_count <= 1:
        return 70
    if vague_count <= 2:
        return 40
    return 10


def _make_suggestions(r, ds, os, dps, ss) -> list[str]:
    sug = []
    if ds < 80:
        sug.append(f"【描述完整性】当前描述 {(len(r.demand_desc) if r.demand_desc else 0)} 字符，建议补充至 50 字符以上，说明需求的背景、当前痛点和具体场景")
    if os < 80:
        sug.append(f"【效果清晰度】当前效果描述 {(len(r.businessobjective) if r.businessobjective else 0)} 字符，建议补充至 20 字符以上，明确说明系统行为变化或业务指标改善")
    if dps == 0:
        sug.append("【依赖识别】需求描述中未提及依赖关系，建议补充上下游系统或前置条件")
    if ss < 80:
        sug.append("【范围明确性】需求范围不够具体，避免使用'优化'、'改进'等模糊词汇，建议明确具体改什么、怎么改")
    return sug


def score_requirement(r) -> QualityScore:
    ds = _desc_score(r.demand_desc)
    os = _obj_score(r.businessobjective)
    dps = _dep_score(r.demand_desc)
    ss = _scope_score(r.demand_desc)

    total = ds * 0.4 + os * 0.3 + dps * 0.15 + ss * 0.15

    suggestions = _make_suggestions(r, ds, os, dps, ss)

    return QualityScore(
        total=round(total, 1),
        desc_score=round(ds, 1),
        obj_score=round(os, 1),
        dep_score=round(dps, 1),
        scope_score=round(ss, 1),
        suggestions=suggestions,
    )