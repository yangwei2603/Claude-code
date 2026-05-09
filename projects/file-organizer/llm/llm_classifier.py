"""
LLM 智能分类器 - 支持 MiniMax / DeepSeek，Prompt 缓存 + 批量请求
"""

import os
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from rules.classifier import ClassificationResult


logger = logging.getLogger("llm_classifier")

# LLM 默认常量
DEFAULT_MIN_CONFIDENCE = 0.6
DEFAULT_MAX_TOKENS = 500
DEFAULT_TIMEOUT = 30
DEFAULT_BATCH_SIZE = 10
DEFAULT_CACHE_SIZE = 1000
DEFAULT_TEMPERATURE = 0.1
DEFAULT_LLM_CONFIDENCE = 0.7
DEFAULT_LLM_HIGH_CONFIDENCE = 0.8

# ============ 配置 ============

@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "deepseek"  # "minimax" | "deepseek"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout_seconds: int = DEFAULT_TIMEOUT
    max_batch_size: int = DEFAULT_BATCH_SIZE
    enable_cache: bool = True
    cache_max_size: int = DEFAULT_CACHE_SIZE

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量加载配置"""
        # 优先级：MINIMAX_API_KEY > DEEPSEEK_API_KEY
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        provider = "minimax"
        base_url = ""

        if not api_key:
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
            provider = "deepseek"
            base_url = os.environ.get("DEEPSEEK_BASE_URL", "")

        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            provider = "claude"
            base_url = os.environ.get("ANTHROPIC_BASE_URL", "")

        # Provider 默认值
        defaults = {
            "minimax": {
                "base_url": "https://api.minimax.chat/v1",
                "model": "MiniMax-01",
            },
            "deepseek": {
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
            },
            "claude": {
                "base_url": "https://api.anthropic.com",
                "model": "claude-opus-4-7",
            },
        }

        d = defaults.get(provider, defaults["deepseek"])
        if not base_url:
            base_url = d["base_url"]
        model = os.environ.get(f"{provider.upper()}_MODEL", "") or d["model"]

        return cls(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            min_confidence=float(os.environ.get("LLM_MIN_CONFIDENCE", str(DEFAULT_MIN_CONFIDENCE))),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))),
            timeout_seconds=int(os.environ.get("LLM_TIMEOUT", str(DEFAULT_TIMEOUT))),
            max_batch_size=int(os.environ.get("LLM_BATCH_SIZE", str(DEFAULT_BATCH_SIZE))),
            enable_cache=os.environ.get("LLM_CACHE", "1") != "0",
            cache_max_size=int(os.environ.get("LLM_CACHE_SIZE", str(DEFAULT_CACHE_SIZE))),
        )

    @classmethod
    def from_json(cls, data: dict) -> "LLMConfig":
        """从 JSON 加载配置"""
        return cls(
            provider=data.get("provider", "deepseek"),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            model=data.get("model", ""),
            min_confidence=float(data.get("min_confidence", DEFAULT_MIN_CONFIDENCE)),
            max_tokens=int(data.get("max_tokens", DEFAULT_MAX_TOKENS)),
            timeout_seconds=int(data.get("timeout_seconds", DEFAULT_TIMEOUT)),
            max_batch_size=int(data.get("max_batch_size", DEFAULT_BATCH_SIZE)),
            enable_cache=bool(data.get("enable_cache", True)),
            cache_max_size=int(data.get("cache_max_size", DEFAULT_CACHE_SIZE)),
        )

    def to_dict(self) -> dict:
        """序列化为 dict（不含 api_key）"""
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "min_confidence": self.min_confidence,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "max_batch_size": self.max_batch_size,
            "enable_cache": self.enable_cache,
            "cache_max_size": self.cache_max_size,
        }


# ============ 缓存 ============

class LLMCache:
    """LRU Prompt 缓存"""

    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE):
        self.max_size = max_size
        self._cache: Dict[str, Tuple[str, float]] = {}  # key -> (result, timestamp)
        self._lock = threading.Lock()

    def _make_key(self, filename: str, content_hash: Optional[str] = None) -> str:
        """生成缓存 key"""
        data = filename if content_hash is None else f"{filename}:{content_hash}"
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, filename: str, content_hash: Optional[str] = None) -> Optional[str]:
        """获取缓存的分类结果"""
        if not self._cache:
            return None
        key = self._make_key(filename, content_hash)
        with self._lock:
            if key in self._cache:
                result, ts = self._cache.pop(key)
                self._cache[key] = (result, ts)  # 移到末尾（最新）
                return result
        return None

    def set(self, filename: str, result: str, content_hash: Optional[str] = None):
        """设置缓存"""
        key = self._make_key(filename, content_hash)
        with self._lock:
            if key in self._cache:
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # 删除最老的
                oldest = next(iter(self._cache))
                self._cache.pop(oldest)
            self._cache[key] = (result, time.time())

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict:
        """获取缓存统计"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
            }


# ============ API 客户端 ============

class MiniMaxClient:
    """MiniMax API 客户端"""

    def __init__(self, api_key: str, base_url: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, messages: List[dict], model: str, max_tokens: int) -> dict:
        """调用 MiniMax Chat API"""
        import requests
        url = f"{self.base_url}/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": DEFAULT_TEMPERATURE,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # MiniMax v2 返回格式
        return {"content": data["choices"][0]["messages"][0]["text"]}


class DeepSeekClient:
    """DeepSeek API 客户端（OpenAI 兼容）"""

    def __init__(self, api_key: str, base_url: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, messages: List[dict], model: str, max_tokens: int) -> dict:
        """调用 DeepSeek Chat API"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=DEFAULT_TEMPERATURE,
        )
        return {"content": response.choices[0].message.content}


# ============ LLM 分类器 ============

@dataclass
class LLMClassificationResult:
    """LLM 分类结果（带置信度）"""
    target_path: str
    confidence: float
    rule_name: str = ""
    provider: str = ""
    method: str = "llm"

    def to_classification_result(self) -> ClassificationResult:
        """转换为标准的 ClassificationResult"""
        return ClassificationResult(
            target_path=self.target_path,
            rule_name=self.rule_name or f"{self.provider.upper()} LLM分类",
            priority=2,
            confidence=self.confidence,
            matched_keywords=[],
            method=self.method,
        )


class LLMClassifier:
    """
    LLM 智能分类器
    - 支持 MiniMax / DeepSeek 多模型
    - Prompt 缓存（LRU）
    - 批量请求（ThreadPoolExecutor）
    - 置信度阈值过滤
    """

    PROVIDERS = {
        "minimax": {"name": "MiniMax", "client_class": MiniMaxClient},
        "deepseek": {"name": "DeepSeek", "client_class": DeepSeekClient},
    }

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self.enabled = bool(self.config.api_key)
        self._client: Optional[Any] = None
        self._client_lock = threading.Lock()

        # 缓存
        self._cache = LLMCache(self.config.cache_max_size) if self.config.enable_cache else None

        # 批量请求线程池
        self._executor: Optional[ThreadPoolExecutor] = None

        if not self.enabled:
            logger.warning(f"LLM API key 未设置，智能分类将被禁用")
            logger.warning("请设置 MINIMAX_API_KEY 或 DEEPSEEK_API_KEY 环境变量")

    def _get_client(self) -> Any:
        """懒加载客户端（线程安全）"""
        if self._client is not None:
            return self._client
        with self._client_lock:
            if self._client is None and self.enabled:
                provider_info = self.PROVIDERS.get(self.config.provider, {})
                client_class = provider_info.get("client_class")
                if client_class:
                    try:
                        self._client = client_class(
                            api_key=self.config.api_key,
                            base_url=self.config.base_url,
                            timeout=self.config.timeout_seconds,
                        )
                    except Exception as e:
                        logger.error(f"初始化 {self.config.provider} 客户端失败: {e}")
                        self.enabled = False
        return self._client

    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return self.enabled and self._get_client() is not None

    def classify(
        self,
        filename: str,
        content: Optional[str] = None,
        content_hash: Optional[str] = None,
        category_tree: Optional[List[str]] = None,
        source_dir_hint: Optional[str] = None,
    ) -> Optional[ClassificationResult]:
        """
        对单个文件进行 LLM 分类

        Args:
            filename: 文件名
            content: 文件内容（可选）
            content_hash: 内容哈希（用于缓存）
            category_tree: 分类目录树
            source_dir_hint: 源目录提示

        Returns:
            ClassificationResult 或 None（未命中或置信度不足）
        """
        if not self.is_available():
            return None

        # 检查缓存
        if self._cache:
            cached = self._cache.get(filename, content_hash)
            if cached:
                try:
                    data = json.loads(cached)
                    # 缓存的是 dict，需重建为 ClassificationResult
                    return ClassificationResult(
                        target_path=data["target_path"],
                        rule_name=data.get("rule_name", ""),
                        priority=2,
                        confidence=data["confidence"],
                        matched_keywords=[],
                        analysis_method="llm",
                    )
                except (json.JSONDecodeError, KeyError):
                    pass

        # 构建请求
        prompt = self._build_prompt(filename, content, category_tree, source_dir_hint)

        try:
            client = self._get_client()
            resp = client.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self.config.model,
                max_tokens=self.config.max_tokens,
            )
            result_text = resp.get("content", "").strip()
            llm_result = self._parse_response(result_text, filename)

            if llm_result:
                # 检查置信度阈值
                if llm_result.confidence >= self.config.min_confidence:
                    # 存入缓存
                    if self._cache:
                        self._cache.set(filename, json.dumps({
                            "target_path": llm_result.target_path,
                            "confidence": llm_result.confidence,
                            "rule_name": llm_result.rule_name,
                        }), content_hash)
                    return llm_result.to_classification_result()
        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")

        return None

    def classify_batch(
        self,
        items: List[dict],
        category_tree: Optional[List[str]] = None,
        callback=None,
    ) -> List[Optional[ClassificationResult]]:
        """
        批量分类文件

        Args:
            items: [{"filename": str, "content": str, "content_hash": str, "source_dir_hint": str}, ...]
            category_tree: 分类目录树
            callback: 完成回调 (index, result)

        Returns:
            结果列表（顺序与输入对应）
        """
        if not self.is_available():
            return [None] * len(items)

        results = [None] * len(items)

        def classify_one(idx: int, item: dict) -> Tuple[int, Optional[ClassificationResult]]:
            result = self.classify(
                filename=item["filename"],
                content=item.get("content"),
                content_hash=item.get("content_hash"),
                category_tree=category_tree,
                source_dir_hint=item.get("source_dir_hint"),
            )
            if callback:
                callback(idx, result)
            return idx, result

        # 使用线程池并发
        with ThreadPoolExecutor(max_workers=self.config.max_batch_size) as executor:
            futures = [
                executor.submit(classify_one, i, item)
                for i, item in enumerate(items)
            ]
            for future in as_completed(futures):
                try:
                    idx, result = future.result()
                    results[idx] = result
                except Exception as e:
                    logger.error(f"批量任务失败: {e}")

        return results

    def _build_prompt(
        self,
        filename: str,
        content: Optional[str],
        category_tree: Optional[List[str]],
        source_dir_hint: Optional[str],
    ) -> str:
        """构建分类提示词"""
        if not category_tree:
            category_tree = self._get_default_category_tree()

        categories_str = "\n".join(f"- {cat}" for cat in category_tree)

        content_hint = ""
        if content:
            preview = content[:2000].replace("\\", "/")
            content_hint = f"\n\n文件内容预览（前2000字符）:\n{preview}"

        hint = ""
        if source_dir_hint:
            hint = f"\n源目录提示: {source_dir_hint}"

        return f"""你是一个文件分类助手。根据文件名和文件内容，将文件分类到最合适的目录。

文件名: {filename}{content_hint}{hint}

可用的分类目录:
{categories_str}

请选择一个最合适的目录，格式要求：
1. 目录必须在上述列表中
2. 如果是代码文件，选择对应的代码目录
3. 如果是文档，选择对应的文档目录

直接输出目录路径，格式为 "目录1\\目录2"，不要输出其他内容。

如果不确定，选择最可能的目录。"""

    def _parse_response(self, response_text: str, filename: str) -> Optional[LLMClassificationResult]:
        """解析 LLM 响应"""
        target_path = response_text.strip().strip('"\'')

        if not target_path or len(target_path) < 2:
            return None

        # 简单验证：包含路径分隔符
        if "\\" not in target_path and "/" not in target_path:
            return None

        # 估算置信度（路径越具体越可信）
        # 注意：当前为启发式估算，未使用 LLM 返回的真实置信度
        confidence = DEFAULT_LLM_CONFIDENCE
        if len(target_path) > 15:
            confidence = DEFAULT_LLM_HIGH_CONFIDENCE
        if any(kw in target_path for kw in ["BRD", "PRD", "设计", "测试", "运维"]):
            confidence = 0.85

        return LLMClassificationResult(
            target_path=target_path,
            confidence=confidence,
            rule_name=f"{self.config.provider.upper()} LLM分类",
            provider=self.config.provider,
        )

    def _get_default_category_tree(self) -> List[str]:
        """获取默认分类目录树"""
        return [
            "00-战略与架构\\00-数字化战略",
            "00-战略与架构\\01-业务架构",
            "01-知识库管理\\00-知识体系",
            "01-知识库管理\\01-最佳实践",
            "01-知识库管理\\02-培训学习",
            "01-知识库管理\\03-规章制度",
            "01-知识库管理\\04-问答知识库",
            "02-信息化项目\\00-项目立项",
            "02-信息化项目\\01-需求文档\\BRD",
            "02-信息化项目\\01-需求文档\\PRD",
            "02-信息化项目\\02-设计文档",
            "02-信息化项目\\03-运维文档",
            "02-信息化项目\\04-测试文档",
            "03-数字化项目\\00-客舱数字化",
            "03-数字化项目\\01-飞行数字化",
            "03-数字化项目\\02-维修数字化",
            "03-数字化项目\\03-司库管理数字化",
            "03-数字化项目\\04-共享数字化",
            "03-数字化项目\\05-核算与报告数字化",
            "03-数字化项目\\06-机供品数字化",
            "03-数字化项目\\07-起降数字化",
            "03-数字化项目\\08-数据分析报告\\00-经营分析",
            "03-数字化项目\\08-数据分析报告\\01-专题分析",
            "03-数字化项目\\08-数据分析报告\\02-数据报表",
            "04-创新应用\\00-Agent智能体",
            "04-创新应用\\01-流程自动化",
            "04-创新应用\\02-智能分析",
            "05-数据资产\\00-数据标准",
            "05-数据资产\\01-数据治理",
            "05-数据资产\\02-数据开发",
            "05-数据资产\\03-数据集成",
            "05-数据资产\\04-数据安全",
            "06-团队与运营\\00-团队建设",
            "06-团队与运营\\01-沟通协作\\周报月报",
            "06-团队与运营\\01-沟通协作\\会议纪要",
            "06-团队与运营\\02-资源库",
            "06-团队与运营\\03-通知公告",
            "06-团队与运营\\04-调研访谈",
            "00-文档\\Word文档",
            "00-文档\\PDF文档",
            "00-文档\\文本文件",
            "01-表格\\Excel表格",
            "01-表格\\CSV数据",
            "02-演示\\PPT演示",
            "03-代码\\Python",
            "03-代码\\SQL脚本",
            "03-代码\\Web前端",
            "03-代码\\Java",
            "04-配置\\配置文件",
            "06-媒体\\图片",
            "06-媒体\\视频",
            "06-媒体\\音频",
            "99-归档\\00-历史项目",
            "99-归档\\01-临时文件\\备份文件",
            "99-归档\\01-临时文件\\大文件待处理",
        ]

    def clear_cache(self):
        """清空缓存"""
        if self._cache:
            self._cache.clear()

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        if self._cache:
            return self._cache.stats()
        return {"size": 0, "max_size": 0}

    def get_provider_name(self) -> str:
        """获取当前 Provider 名称"""
        return self.PROVIDERS.get(self.config.provider, {}).get("name", "Unknown")


# 向后兼容别名
ClaudeClassifier = LLMClassifier