#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分类模块 — 四级优先级分类决策逻辑
从 organizer.py 拆分出来：_classify、_classify_by_content、_match_infoproject_stage、_extract_project_name
"""

import re
from pathlib import Path
from typing import Optional

from rules import ClassificationResult


# 魔法数字
CONTENT_CONFIDENCE_DIVISOR = 10
CONTENT_MIN_CONFIDENCE = 0.5


def classify_file(
    filepath: Path,
    source_dir: Path,
    business_domain_rules: list,
    infoproject_stage_rules: list,
    keyword_rules: list,
    extension_rules: dict,
    content_extractor,  # ContentExtractor instance
    enable_content_analysis: bool,
    content_analysis_rules: dict,
) -> ClassificationResult:
    """
    四级优先级分类：
    1. 业务领域匹配（文件名关键词）
    2. 关键词规则匹配（文件名关键词）
    3. 文件内容智能分析
    4. 扩展名兜底

    纯函数，无状态副作用，便于单元测试。
    """
    filename = filepath.name
    name_no_ext = filepath.stem
    ext = filepath.suffix.lower()

    try:
        rel_parts = filepath.relative_to(source_dir).parts
    except ValueError:
        rel_parts = filepath.parts

    # ---- 优先级1：业务领域匹配 ----
    for rule in business_domain_rules:
        for kw in rule["keywords"]:
            hit = kw in filename
            if not hit:
                for part in rel_parts:
                    if kw in part:
                        hit = True
                        break
            if hit:
                base_target = rule["target"]
                if base_target == "02-信息化项目":
                    sub = _match_infoproject_stage(filename, infoproject_stage_rules)
                    proj_name = _extract_project_name(rel_parts)
                    if proj_name:
                        target = f"02-信息化项目/{proj_name}/{sub}" if sub else f"02-信息化项目/{proj_name}"
                    else:
                        target = f"02-信息化项目/{sub}" if sub else "02-信息化项目"
                else:
                    type_sub = extension_rules.get(ext, "")
                    target = f"{base_target}/{type_sub}" if type_sub else base_target
                return ClassificationResult(
                    target_path=target,
                    rule_name=f"业务领域[{kw}]",
                    priority=1,
                    confidence=0.9,
                    matched_keywords=[kw],
                    analysis_method="filename"
                )

    # ---- 优先级2：关键词规则 ----
    for rule in keyword_rules:
        for kw in rule["keywords"]:
            if kw in filename:
                return ClassificationResult(
                    target_path=rule["target"],
                    rule_name=f"关键词[{kw}]",
                    priority=2,
                    confidence=0.8,
                    matched_keywords=[kw],
                    analysis_method="filename"
                )

    # ---- 优先级3：文件内容智能分析 ----
    if enable_content_analysis and content_extractor.can_extract(filepath):
        content_result = _classify_by_content(
            filepath, content_extractor, content_analysis_rules
        )
        if content_result and content_result.confidence >= CONTENT_MIN_CONFIDENCE:
            return content_result

    # ---- 优先级4：扩展名兜底 ----
    if ext in extension_rules:
        return ClassificationResult(
            target_path=f"99-归档/01-临时文件/{extension_rules[ext]}",
            rule_name=f"扩展名[{ext}]",
            priority=4,
            confidence=0.3,
            matched_keywords=[ext],
            analysis_method="extension"
        )

    # 完全无匹配
    return ClassificationResult(
        target_path="99-归档/01-临时文件",
        rule_name="兜底规则",
        priority=0,
        confidence=0.0,
        analysis_method="fallback"
    )


def _classify_by_content(filepath: Path, content_extractor, content_analysis_rules: dict) -> Optional[ClassificationResult]:
    """基于文件内容进行智能分类"""
    content = content_extractor.extract(filepath)
    if not content:
        return None

    content_rules = content_analysis_rules.get("content_keywords", [])
    if not content_rules:
        return None

    best_match = None
    best_score = 0
    best_keywords = []

    content_lower = content.lower()

    for rule in content_rules:
        keywords = rule.get("keywords", [])
        target = rule.get("target", "")
        weight = rule.get("weight", 1)

        score = 0
        matched = []

        for kw in keywords:
            kw_lower = kw.lower()
            count = content_lower.count(kw_lower)
            if count > 0:
                score += count * weight
                matched.append(kw)

        if score > best_score:
            best_score = score
            best_match = target
            best_keywords = matched

    if best_score > 0:
        confidence = min(best_score / CONTENT_CONFIDENCE_DIVISOR, 1.0)
        return ClassificationResult(
            target_path=best_match,
            rule_name=f"内容分析[{', '.join(best_keywords[:3])}]",
            priority=3,
            confidence=confidence,
            matched_keywords=best_keywords,
            analysis_method="content"
        )

    return None


def _match_infoproject_stage(filename: str, infoproject_stage_rules: list) -> str:
    for rule in infoproject_stage_rules:
        for kw in rule["keywords"]:
            if kw in filename:
                return rule["sub"]
    return ""


def _extract_project_name(parts) -> str:
    """尝试从路径片段提取信息化项目名称"""
    for part in parts:
        if "信息化项目" in part or "项目" in part:
            continue
        if re.match(r"^\d{2}-", part):
            continue
        if part and part not in (".svn", ".git"):
            return part
    return ""
