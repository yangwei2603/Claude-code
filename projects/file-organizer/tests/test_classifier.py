"""
测试规则分类器的 4 级级联分类
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rules.classifier import RuleBasedClassifier, ClassificationResult


class TestClassifyCascade:
    """测试 classify_cascade 4级优先级"""

    def setup_method(self):
        self.classifier = RuleBasedClassifier()

    def test_p1_keyword_match(self, tmp_path):
        """P1: 关键词命中，直接返回"""
        # 创建文件（关键词：合同）
        test_file = tmp_path / "合同协议.docx"
        test_file.write_text("test")

        result = self.classifier.classify_cascade(test_file)

        assert result is not None
        assert result.method == "rule"
        assert result.priority == 2
        assert "合同" in result.target_path or result.rule_name

    def test_p4_extension_fallback(self, tmp_path):
        """P4: 扩展名兜底（无关键词命中）"""
        test_file = tmp_path / "random_file.unknown"
        test_file.write_text("test")

        result = self.classifier.classify_cascade(test_file)

        assert result is not None
        assert result.method == "extension"
        assert result.priority == 3

    def test_p1_no_llm_when_no_key(self, tmp_path):
        """P1未命中时调用LLM（如果可用）"""
        test_file = tmp_path / "测试文档.docx"
        test_file.write_text("test")

        # 不带 LLM 分类器
        result = self.classifier.classify_cascade(test_file, llm_classifier=None)
        # 应该落到 P4 扩展名兜底
        assert result is not None
        assert result.method == "extension"

    def test_extension_py(self, tmp_path):
        """Python 文件按扩展名分类"""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        result = self.classifier.classify_cascade(test_file)

        assert result is not None
        assert result.method == "extension"
        assert ".py" in result.matched_keywords

    def test_extension_xlsx(self, tmp_path):
        """Excel 文件按扩展名分类"""
        test_file = tmp_path / "report.xlsx"
        test_file.write_text("data")

        result = self.classifier.classify_cascade(test_file)

        assert result is not None
        assert result.method == "extension"
        assert ".xlsx" in result.matched_keywords

    def test_keyword_priority_beats_extension(self, tmp_path):
        """关键词匹配优先于扩展名兜底"""
        # 文件名含有关键词"周报"
        test_file = tmp_path / "项目周报.docx"
        test_file.write_text("test")

        result = self.classifier.classify_cascade(test_file)

        assert result is not None
        # 周报匹配关键词，优先级为2（关键词）
        assert result.priority == 2
        assert result.method == "rule"