#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organizer.py - 向后兼容 shim（v5.0）
====================================
v5.0 将核心引擎重构为 `organizer/` 包。本文件保持向后兼容。

新代码请直接导入:
    from organizer import FileOrganizer              # organizer 包
    from organizer.rules import get_default_rules   # 规则函数
    from organizer.content_extractor import ContentExtractor

向后兼容导入（通过 __getattr__ 延迟加载）:
    from organizer import FileOrganizer, get_default_rules, load_rules
    from organizer import DEFAULT_RULES, ClassificationResult, ContentExtractor
    from organizer import DocumentOrganizer  # deprecated → FileOrganizer
"""

import sys
from pathlib import Path

# ---- 关键：确保 organizer/ 包在路径上 ----
_agent_dir = Path(__file__).parent
_pkg_dir = _agent_dir / "organizer"
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))


def __getattr__(name):
    """延迟导入，支持 from organizer import <name>"""
    if name in (
        "FileOrganizer", "ContentExtractor", "RollbackHandler",
        "get_default_rules", "load_rules", "DEFAULT_RULES",
    ):
        from organizer import (
            FileOrganizer, ContentExtractor, RollbackHandler,
            get_default_rules, load_rules, DEFAULT_RULES,
        )
        return locals()[name]
    if name == "DocumentOrganizer":
        from organizer import FileOrganizer
        return FileOrganizer
    if name == "ClassificationResult":
        from rules.classifier import ClassificationResult
        return ClassificationResult
    if name == "FilenameAnalyzer":
        # FilenameAnalyzer 不再存在，返回 None 避免完全崩溃
        return None
    raise AttributeError(f"module 'organizer' has no attribute {name!r}")


# ---- 模块级别名（for dir(organizer)）----
# 这些在第一次访问时通过 __getattr__ 解析

__all__ = [
    "FileOrganizer",
    "DocumentOrganizer",
    "ClassificationResult",
    "ContentExtractor",
    "RollbackHandler",
    "get_default_rules",
    "load_rules",
    "DEFAULT_RULES",
]