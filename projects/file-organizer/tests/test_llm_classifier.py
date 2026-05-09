"""
测试 LLM 分类器（缓存 + 批量请求）
"""

import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from llm.llm_classifier import (
    LLMClassifier, LLMConfig, LLMCache,
    LLMClassificationResult, MiniMaxClient, DeepSeekClient
)


class TestLLMCache:
    """测试 LRU 缓存"""

    def test_cache_set_get(self):
        cache = LLMCache(max_size=10)
        cache.set("test.txt", '{"target_path":"01-知识库"}')
        result = cache.get("test.txt")
        assert result is not None
        assert "target_path" in result

    def test_cache_miss(self):
        cache = LLMCache(max_size=10)
        result = cache.get("not_exist.txt")
        assert result is None

    def test_cache_eviction(self):
        cache = LLMCache(max_size=3)
        for i in range(5):
            cache.set(f"file{i}.txt", f'{{"n":{i}}}')
        # 超过 max_size，最老的被清除
        stats = cache.stats()
        assert stats["size"] == 3

    def test_cache_clear(self):
        cache = LLMCache(max_size=10)
        cache.set("a.txt", '{"a":1}')
        cache.clear()
        assert cache.get("a.txt") is None

    def test_cache_stats(self):
        cache = LLMCache(max_size=100)
        cache.set("a.txt", '{"a":1}')
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 100


class TestLLMConfig:
    """测试 LLM 配置"""

    def test_from_json(self):
        data = {
            "provider": "deepseek",
            "api_key": "sk-test123",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "min_confidence": 0.7,
            "max_tokens": 300,
        }
        cfg = LLMConfig.from_json(data)
        assert cfg.provider == "deepseek"
        assert cfg.api_key == "sk-test123"
        assert cfg.min_confidence == 0.7
        assert cfg.max_tokens == 300

    def test_to_dict(self):
        cfg = LLMConfig(provider="minimax", api_key="sk-test")
        d = cfg.to_dict()
        assert d["provider"] == "minimax"
        assert "api_key" not in d  # to_dict 不含 api_key

    def test_default_values(self):
        cfg = LLMConfig()
        assert cfg.provider == "deepseek"
        assert cfg.min_confidence == 0.6
        assert cfg.max_tokens == 500
        assert cfg.enable_cache is True


class TestLLMClassificationResult:
    """测试 LLM 分类结果转换"""

    def test_to_classification_result(self):
        llm_res = LLMClassificationResult(
            target_path="01-知识库管理\\02-培训学习",
            confidence=0.8,
            rule_name="DeepSeek LLM分类",
            provider="deepseek",
        )
        cr = llm_res.to_classification_result()
        assert cr.target_path == "01-知识库管理\\02-培训学习"
        assert cr.priority == 2
        assert cr.confidence == 0.8
        assert cr.method == "llm"


class TestLLMClassifierDisabled:
    """测试 LLM 分类器禁用状态"""

    def test_no_api_key(self):
        """无 API key 时禁用"""
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        assert classifier.enabled is False

    def test_is_available_false_when_disabled(self):
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        assert classifier.is_available() is False

    def test_get_cache_stats_empty(self):
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        stats = classifier.get_cache_stats()
        assert stats["size"] == 0

    def test_clear_cache_when_disabled(self):
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        classifier.clear_cache()  # 不应报错

    def test_classify_returns_none_when_disabled(self, tmp_path):
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        result = classifier.classify(filename="test.txt")
        assert result is None


class TestLLMClassifierPromptBuilding:
    """测试 Prompt 构建"""

    def test_build_prompt_with_content(self):
        cfg = LLMConfig(provider="deepseek", api_key="test")
        classifier = LLMClassifier(config=cfg)
        prompt = classifier._build_prompt(
            filename="report.docx",
            content="这是项目报告的内容",
            category_tree=["00-战略\\00-数字化战略"],
            source_dir_hint="/path/to/files",
        )
        assert "report.docx" in prompt
        assert "这是项目报告的内容" in prompt
        assert "00-战略" in prompt

    def test_build_prompt_without_content(self):
        cfg = LLMConfig(provider="deepseek", api_key="test")
        classifier = LLMClassifier(config=cfg)
        prompt = classifier._build_prompt(
            filename="data.csv",
            content=None,
            category_tree=["01-表格\\CSV数据"],
            source_dir_hint=None,
        )
        assert "data.csv" in prompt
        assert "文件内容预览" not in prompt

    def test_parse_response_valid(self):
        cfg = LLMConfig(provider="deepseek", api_key="test")
        classifier = LLMClassifier(config=cfg)
        result = classifier._parse_response("01-知识库管理\\02-培训学习", "培训资料.docx")
        assert result is not None
        assert result.target_path == "01-知识库管理\\02-培训学习"
        assert result.confidence > 0

    def test_parse_response_invalid(self):
        cfg = LLMConfig(provider="deepseek", api_key="test")
        classifier = LLMClassifier(config=cfg)
        result = classifier._parse_response("invalid response", "test.txt")
        assert result is None

    def test_parse_response_short(self):
        cfg = LLMConfig(provider="deepseek", api_key="test")
        classifier = LLMClassifier(config=cfg)
        result = classifier._parse_response("a", "test.txt")
        assert result is None


class TestLLMBatchClassify:
    """测试批量分类"""

    def test_classify_batch_disabled(self):
        """禁用时返回全 None"""
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        items = [
            {"filename": "a.txt"},
            {"filename": "b.txt"},
        ]
        results = classifier.classify_batch(items)
        assert results == [None, None]

    def test_classify_batch_structure(self):
        """检查返回结构"""
        cfg = LLMConfig(provider="deepseek", api_key="")
        classifier = LLMClassifier(config=cfg)
        items = [{"filename": f"file{i}.txt"} for i in range(3)]
        results = classifier.classify_batch(items)
        assert len(results) == 3
        assert all(r is None for r in results)