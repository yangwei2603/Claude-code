"""
规则分类器 - 基于规则的文档分类
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .rule_loader import RuleLoader

# 分类置信度常量
CONFIDENCE_KEYWORD_MATCH = 0.9        # P1: 关键词精确命中
CONFIDENCE_BUSINESS_RULE = 0.8        # 业务领域规则命中
CONFIDENCE_EXTENSION_FALLBACK = 0.3   # P4: 扩展名兜底

logger = logging.getLogger("rule_classifier")


@dataclass
class ClassificationResult:
    """分类结果"""
    target_path: str
    rule_name: str
    priority: int
    confidence: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    method: str = "rule"  # rule, extension, llm, fallback


class RuleBasedClassifier:
    """基于规则的分类器 - 优先使用规则，匹配失败返回 None"""

    def __init__(self, rule_loader: Optional[RuleLoader] = None):
        self.rule_loader = rule_loader or RuleLoader()

    def classify(self, filepath: Path, filename_only: bool = False) -> Optional[ClassificationResult]:
        """
        对文件进行分类（使用所有规则）

        Args:
            filepath: 文件路径
            filename_only: 是否只使用文件名（不读取内容）

        Returns:
            ClassificationResult 如果命中规则，None 如果未命中
        """
        filepath = Path(filepath)
        filename = filepath.name

        # 获取相对路径用于跨目录匹配
        try:
            rel_parts = filepath.parts
        except ValueError:
            rel_parts = filepath.parts

        # Step 1: 业务领域匹配（最高优先级）
        result = self._match_business_domain(filename, rel_parts)
        if result:
            return result

        # Step 2: 关键词规则匹配
        result = self._match_keyword_rules(filename)
        if result:
            return result

        # 未命中规则
        return None

    def classify_by_keyword_only(self, filepath: Path) -> Optional[ClassificationResult]:
        """
        只使用关键词规则分类（不含业务领域匹配）

        Args:
            filepath: 文件路径

        Returns:
            ClassificationResult 如果命中关键词规则，None 如果未命中
        """
        filename = Path(filepath).name

        # 只使用关键词规则匹配
        result = self._match_keyword_rules(filename)
        if result:
            return result

        return None

    def classify_by_extension(self, filepath: Path) -> ClassificationResult:
        """
        按扩展名分类（兜底）
        """
        ext = Path(filepath).suffix.lower()
        extension_target = self.rule_loader.extension_rules.get(ext, "99-归档/01-临时文件")

        return ClassificationResult(
            target_path=f"{extension_target}",
            rule_name=f"扩展名[{ext}]",
            priority=3,
            confidence=CONFIDENCE_EXTENSION_FALLBACK,
            matched_keywords=[ext],
            method="extension"
        )

    def _match_business_domain(self, filename: str, rel_parts: Tuple[str, ...]) -> Optional[ClassificationResult]:
        """匹配业务领域规则"""
        search_text = filename

        for rule in self.rule_loader.business_rules:
            for kw in rule["keywords"]:
                hit = kw in search_text
                if not hit:
                    # 也检查路径片段
                    for part in rel_parts:
                        if kw in part:
                            hit = True
                            break

                if hit:
                    base_target = rule["target"]

                    # 信息化项目特殊处理：检查子阶段
                    if base_target == "02-信息化项目":
                        sub = self._match_infoproject_stage(filename)
                        if sub:
                            base_target = f"02-信息化项目/{sub}"

                    # 添加文档类型子目录
                    type_sub = self._get_extension_subdir(Path(filename).suffix.lower())
                    if type_sub:
                        base_target = f"{base_target}/{type_sub}"

                    return ClassificationResult(
                        target_path=base_target,
                        rule_name=f"业务领域[{kw}]",
                        priority=1,
                        confidence=CONFIDENCE_KEYWORD_MATCH,
                        matched_keywords=[kw],
                        method="rule"
                    )

        return None

    def _match_keyword_rules(self, filename: str) -> Optional[ClassificationResult]:
        """匹配关键词规则"""
        for rule in self.rule_loader.keyword_rules:
            for kw in rule["keywords"]:
                if kw in filename:
                    return ClassificationResult(
                        target_path=rule["target"],
                        rule_name=f"关键词[{kw}]",
                        priority=2,
                        confidence=CONFIDENCE_BUSINESS_RULE,
                        matched_keywords=[kw],
                        method="rule"
                    )
        return None

    def _match_infoproject_stage(self, filename: str) -> str:
        """匹配信息化项目子阶段"""
        stage_keywords = {
            "00-项目立项": ["立项", "可行性", "投资估算"],
            "01-需求文档/BRD": ["BRD", "业务需求"],
            "01-需求文档/PRD": ["PRD", "产品需求", "功能需求"],
            "02-设计文档": ["概要设计", "详细设计", "数据库设计", "接口设计", "设计文档"],
            "03-运维文档/系统使用手册": ["使用手册", "操作手册", "用户手册", "操作指南"],
            "03-运维文档/运维手册": ["运维手册", "运维指南", "应急预案"],
            "04-测试文档": ["测试用例", "测试报告", "集成测试"],
        }

        for sub, keywords in stage_keywords.items():
            for kw in keywords:
                if kw in filename:
                    return sub

        return ""

    def _get_extension_subdir(self, ext: str) -> str:
        """根据扩展名获取子目录"""
        doc_exts = {".doc", ".docx", ".pdf", ".txt", ".md", ".rtf"}
        table_exts = {".xls", ".xlsx", ".csv", ".ods"}
        ppt_exts = {".ppt", ".pptx", ".odp"}
        code_exts = {".py", ".sql", ".js", ".java", ".go", ".rs", ".cpp", ".c", ".h", ".sh", ".ps1", ".bat"}
        config_exts = {".json", ".xml", ".yaml", ".yml", ".ini", ".conf", ".env"}

        if ext in doc_exts:
            return "文档"
        elif ext in table_exts:
            return "表格"
        elif ext in ppt_exts:
            return "演示"
        elif ext in code_exts:
            return "代码"
        elif ext in config_exts:
            return "配置"

        return ""

    def get_rule_stats(self) -> dict:
        """获取规则统计信息"""
        return {
            "business_rules_count": len(self.rule_loader.business_rules),
            "keyword_rules_count": len(self.rule_loader.keyword_rules),
            "extension_rules_count": len(self.rule_loader.extension_rules),
            "standard_dirs_count": len(self.rule_loader.standard_dirs),
        }

    def classify_cascade(
        self,
        filepath: Path,
        llm_classifier=None,
        content_extractor=None,
    ) -> ClassificationResult:
        """
        四级优先级分类级联

        P1: 关键词规则（不含业务领域）
        P2: LLM 智能分类（规则未命中时）
        P3: 内容分析（LLM 未命中或不可用时）
        P4: 扩展名兜底

        Args:
            filepath: 文件路径
            llm_classifier: LLM 分类器实例（可选）
            content_extractor: 内容提取器（可选）

        Returns:
            ClassificationResult 总是有返回（兜底保证）
        """
        filename = filepath.name

        # P1: 关键词规则（不含业务领域）
        result = self.classify_by_keyword_only(filepath)
        if result:
            return result

        # P2: LLM 智能分类
        if llm_classifier and llm_classifier.is_available():
            content = None
            if content_extractor and content_extractor.can_extract(filepath):
                content = content_extractor.extract(filepath)
            try:
                llm_result = llm_classifier.classify(
                    filename=filename,
                    content=content,
                    source_dir_hint=str(filepath.parent),
                )
                if llm_result:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM 分类失败（文件: {filename}）: {e}")

        # P3: 内容分析（文件内容关键词）
        result = self._classify_by_content(filepath)
        if result:
            return result

        # P4: 扩展名兜底
        return self.classify_by_extension(filepath)

    def _classify_by_content(self, filepath: Path) -> Optional[ClassificationResult]:
        """
        通过文件内容关键词分类（P3）

        读取文件内容，查找关键词匹配。
        目前仅为占位，后续由 content_analyzer 提供完整实现。
        """
        # 文件内容分析占位 - 实际由 organizer 调用 content_extractor 提取
        # 此处返回 None 继续级联
        return None
