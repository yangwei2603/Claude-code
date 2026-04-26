"""
llm_client.py — MiniMax + DeepSeek 双 LLM 统一客户端

使用方式：
    from llm_client import llm

    # 简单对话
    resp = llm.chat("用 Python 写一个快速排序")
    print(resp)

    # 指定模型
    resp = llm.chat("解释 Kubernetes 架构", model="deepseek")

    # 多轮对话
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "什么是 CASK？"},
        {"role": "assistant", "content": "CASK 是单位可用座位公里的成本..."},
        {"role": "user", "content": "春秋的 CASK 有什么特点？"}
    ]
    resp = llm.chat(messages)

环境变量：
    MINIMAX_API_KEY — MiniMax API 密钥
    DEEPSEEK_API_KEY — DeepSeek API 密钥
"""

import os
import json
import requests
from typing import Union, List, Dict, Optional, Literal
from pathlib import Path


# ---------------------------------------------------------------------------
# 配置加载
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    """简单的 YAML 解析（仅支持顶层 key-value 和简单嵌套）。"""
    result = {}
    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val:
                    result[key] = val
                else:
                    result[key] = None
    return result


_cfg = {}
_settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
if _settings_path.exists():
    raw = _load_yaml(str(_settings_path))
    # 简化：扁平化读取 llm 配置
    _cfg["provider"] = raw.get("provider", "minimax")
    _cfg["minimax_model"] = raw.get("minimax_model", "MiniMax-Text-01")
    _cfg["minimax_base"] = raw.get("minimax_base", "https://api.minimax.chat/v1")
    _cfg["deepseek_model"] = raw.get("deepseek_model", "deepseek-chat")
    _cfg["deepseek_base"] = raw.get("deepseek_base", "https://api.deepseek.com/v1")

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


# ---------------------------------------------------------------------------
# 模型分级策略
# ---------------------------------------------------------------------------

def _auto_model(task: str) -> str:
    """
    根据任务类型自动选择模型。
    复杂推理/代码 → DeepSeek；结构化/模板化 → MiniMax。
    """
    heavy_keywords = ["解释", "分析", "推理", "设计", "架构", "为什么", "如何实现",
                      "compare", "analyze", "explain", "design", "architect",
                      "debug", "fix bug", "refactor", "优化性能"]
    light_keywords = ["生成", "列出", "总结", "翻译", "改写", "写一个", "create",
                      "list", "summarize", "translate", "write", "生成SQL"]

    for kw in heavy_keywords:
        if kw in task.lower():
            return "deepseek"
    for kw in light_keywords:
        if kw in task.lower():
            return "minimax"
    return "minimax"  # 默认 MiniMax


# ---------------------------------------------------------------------------
# 统一消息格式
# ---------------------------------------------------------------------------

Message = Union[str, Dict[str, str], List[Dict[str, str]]]


def _normalize(messages: Message) -> List[Dict[str, str]]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if isinstance(messages, dict):
        return [messages]
    if isinstance(messages, list):
        return messages
    raise ValueError(f"Unsupported message format: {type(messages)}")


# ---------------------------------------------------------------------------
# MiniMax 客户端
# ---------------------------------------------------------------------------

class MiniMaxClient:
    name = "minimax"
    model: str = _cfg.get("minimax_model", "MiniMax-Text-01")
    base_url: str = _cfg.get("minimax_base", "https://api.minimax.chat/v1")

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or MINIMAX_API_KEY
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY 环境变量未设置")

    def chat(self,
             messages: Message,
             model: str = "",
             temperature: float = 0.7,
             max_tokens: int = 8192) -> str:
        normalized = _normalize(messages)
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.model,
            "messages": normalized,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# DeepSeek 客户端
# ---------------------------------------------------------------------------

class DeepSeekClient:
    name = "deepseek"
    model: str = _cfg.get("deepseek_model", "deepseek-chat")
    base_url: str = _cfg.get("deepseek_base", "https://api.deepseek.com/v1")

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or DEEPSEEK_API_KEY
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")

    def chat(self,
             messages: Message,
             model: str = "",
             temperature: float = 0.7,
             max_tokens: int = 4096) -> str:
        normalized = _normalize(messages)
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.model,
            "messages": normalized,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------

class LLMClient:
    """
    统一 LLM 客户端，支持 MiniMax 和 DeepSeek，按 provider 或 auto 策略调用。
    """

    def __init__(self, provider: str = ""):
        self.provider = provider or _cfg.get("provider", "minimax")
        self._minimax = None
        self._deepseek = None

    def _get_client(self, model: str = "") -> Union[MiniMaxClient, DeepSeekClient]:
        if model == "deepseek":
            if self._deepseek is None:
                self._deepseek = DeepSeekClient()
            return self._deepseek
        if model == "minimax":
            if self._minimax is None:
                self._minimax = MiniMaxClient()
            return self._minimax
        # provider 级别
        if self.provider == "deepseek":
            if self._deepseek is None:
                self._deepseek = DeepSeekClient()
            return self._deepseek
        if self._minimax is None:
            self._minimax = MiniMaxClient()
        return self._minimax

    def chat(self,
             messages: Message,
             model: str = "",
             temperature: float = 0.7) -> str:
        """
        发送对话请求。

        参数：
            messages — str | dict | list[dict]，支持单轮/多轮对话
            model — "minimax" | "deepseek" | ""（使用 provider 设置或 auto 策略）
            temperature — 创造性参数，0.0~2.0
        """
        if not model:
            model = self.provider
        if model == "auto":
            # auto 策略：先尝试解析 task 内容
            if isinstance(messages, str):
                model = _auto_model(messages)
            elif isinstance(messages, list) and messages:
                last = messages[-1].get("content", "") if isinstance(messages[-1], dict) else ""
                model = _auto_model(str(last))
            else:
                model = "minimax"

        client = self._get_client(model)
        return client.chat(messages, temperature=temperature)

    def chat_stream(self,
                    messages: Message,
                    model: str = "",
                    temperature: float = 0.7):
        """
        流式对话（generator）。
        支持 MiniMax 和 DeepSeek 的流式响应。
        """
        if not model:
            model = self.provider
        client = self._get_client(model)
        normalized = _normalize(messages)
        url = f"{client.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {client.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or client.model,
            "messages": normalized,
            "temperature": temperature,
            "stream": True,
        }
        with requests.post(url, headers=headers, json=payload, timeout=120, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            delta = json.loads(data)["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------

# 使用示例：
#   from llm_client import llm
#   resp = llm.chat("你好", model="minimax")
llm = LLMClient()
