"""
llm_client.py — MiniMax + DeepSeek + 公司本地大模型 三 LLM 统一客户端

使用方式：
    from llm_client import llm

    # 简单对话
    resp = llm.chat("用 Python 写一个快速排序")
    print(resp)

    # 指定模型
    resp = llm.chat("解释 Kubernetes 架构", model="deepseek")

    # 使用本地大模型（涉密/内部数据）
    resp = llm.chat("分析公司内部财务数据", model="local")

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
    LOCAL_API_KEY — 公司本地大模型 API 密钥（OneAPI）
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
    """
    解析 YAML 配置，支持嵌套结构。
    嵌套的 key 用下划线连接，如：
        llm:
          minimax:
            model: "xxx"
    → {"llm_minimax_model": "xxx"}
    """
    import re

    def _flatten(obj, prefix=""):
        result = {}
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_key = f"{prefix}_{key}" if prefix else key
                if isinstance(val, dict):
                    result.update(_flatten(val, new_key))
                elif val is not None:
                    # 布尔/数字转字符串
                    result[new_key] = str(val) if not isinstance(val, str) else val
        return result

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # 简单 YAML 解析：处理注释、嵌套缩进、列表
    lines = content.splitlines()
    parsed = {}
    stack = [(0, "", parsed)]  # (indent_level, key, parent_dict)

    for line in lines:
        raw = line.rstrip()
        stripped = raw.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw) - len(stripped)
        # 检测缩进变化
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()

            current_dict = stack[-1][2] if stack else parsed

            if not val:  # 空值，可能是父节点
                current_dict[key] = {}
                stack.append((indent, key, current_dict[key]))
            else:
                # 去引号
                val = val.strip('"').strip("'")
                current_dict[key] = val

    # 展平为下划线连接格式
    def flatten(d, prefix=""):
        out = {}
        for k, v in d.items():
            new_key = f"{prefix}_{k}" if prefix else k
            if isinstance(v, dict):
                out.update(flatten(v, new_key))
            else:
                out[new_key] = v
        return out

    return flatten(parsed)


_cfg = {}
_settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
if _settings_path.exists():
    raw = _load_yaml(str(_settings_path))
    # 扁平化 key 格式：llm_provider, llm_minimax_model, llm_minimax_base_url, etc.
    _cfg["provider"] = raw.get("llm_provider", "minimax")
    _cfg["minimax_model"] = raw.get("llm_minimax_model", "MiniMax-Text-01")
    _cfg["minimax_base"] = raw.get("llm_minimax_base_url", "https://api.minimax.chat/v1")
    _cfg["minimax_max_tokens"] = int(raw.get("llm_minimax_max_tokens", 8192))
    _cfg["minimax_temperature"] = float(raw.get("llm_minimax_temperature", 0.7))
    _cfg["deepseek_model"] = raw.get("llm_deepseek_model", "deepseek-chat")
    _cfg["deepseek_base"] = raw.get("llm_deepseek_base_url", "https://api.deepseek.com/v1")
    _cfg["deepseek_max_tokens"] = int(raw.get("llm_deepseek_max_tokens", 4096))
    _cfg["deepseek_temperature"] = float(raw.get("llm_deepseek_temperature", 0.7))
    _cfg["local_model"] = raw.get("llm_local_model", "Qwen3-VL-235B-A22B-Instruct-AWQ")
    _cfg["local_base"] = raw.get("llm_local_base_url", "https://oneapi-test.springgroup.cn/v1")
    _cfg["local_max_tokens"] = int(raw.get("llm_local_max_tokens", 4096))
    _cfg["local_temperature"] = float(raw.get("llm_local_temperature", 0.7))

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
LOCAL_API_KEY = os.environ.get("LOCAL_API_KEY", "")


# ---------------------------------------------------------------------------
# 模型分级策略
# ---------------------------------------------------------------------------

def _auto_model(task: str) -> str:
    """
    根据任务类型自动选择模型。
    涉密/内部数据 → 本地模型；复杂推理/代码 → DeepSeek；结构化/模板化 → MiniMax。
    """
    # 本地模型触发词（涉密、内部数据）
    local_keywords = ["公司内部", "财务数据", "涉密", "内部文档", "薪酬", "合同",
                      "机密", "内部系统", "内网", "local", "private", "internal"]
    # 复杂推理触发词
    heavy_keywords = ["解释", "分析", "推理", "设计", "架构", "为什么", "如何实现",
                      "compare", "analyze", "explain", "design", "architect",
                      "debug", "fix bug", "refactor", "优化性能"]
    # 轻量任务触发词
    light_keywords = ["生成", "列出", "总结", "翻译", "改写", "写一个", "create",
                      "list", "summarize", "translate", "write", "生成SQL"]

    for kw in local_keywords:
        if kw in task.lower():
            return "local"
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
    max_tokens: int = _cfg.get("minimax_max_tokens", 8192)
    temperature: float = _cfg.get("minimax_temperature", 0.7)

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or MINIMAX_API_KEY
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY 环境变量未设置")

    def chat(self,
             messages: Message,
             model: str = "",
             temperature: float = None,
             max_tokens: int = None) -> str:
        normalized = _normalize(messages)
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.model,
            "messages": normalized,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
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
    max_tokens: int = _cfg.get("deepseek_max_tokens", 4096)
    temperature: float = _cfg.get("deepseek_temperature", 0.7)

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or DEEPSEEK_API_KEY
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")

    def chat(self,
             messages: Message,
             model: str = "",
             temperature: float = None,
             max_tokens: int = None) -> str:
        normalized = _normalize(messages)
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.model,
            "messages": normalized,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# 公司本地大模型客户端（OneAPI 代理）
# ---------------------------------------------------------------------------

class LocalClient:
    """
    公司本地大模型客户端，通过 OneAPI 统一接口调用。
    适用场景：涉密数据、内部文档、财务数据等不宜外传的请求。
    """
    name = "local"
    model: str = _cfg.get("local_model", "Qwen3-VL-235B-A22B-Instruct-AWQ")
    base_url: str = _cfg.get("local_base", "https://oneapi-test.springgroup.cn/v1")
    max_tokens: int = _cfg.get("local_max_tokens", 4096)
    temperature: float = _cfg.get("local_temperature", 0.7)

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or LOCAL_API_KEY or ""
        if not self.api_key:
            import warnings
            warnings.warn("LOCAL_API_KEY 环境变量未设置，将以无密钥模式调用（部分 API 可能不支持）")

    def chat(self,
             messages: Message,
             model: str = "",
             temperature: float = None,
             max_tokens: int = None) -> str:
        normalized = _normalize(messages)
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.model,
            "messages": normalized,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
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
    统一 LLM 客户端，支持 MiniMax、DeepSeek 和公司本地大模型，
    按 provider 或 auto 策略调用。
    """

    def __init__(self, provider: str = ""):
        self.provider = provider or _cfg.get("provider", "minimax")
        self._minimax = None
        self._deepseek = None
        self._local = None

    def _get_client(self, model: str = "") -> Union[MiniMaxClient, DeepSeekClient, LocalClient]:
        if model == "local":
            if self._local is None:
                self._local = LocalClient()
            return self._local
        if model == "deepseek":
            if self._deepseek is None:
                self._deepseek = DeepSeekClient()
            return self._deepseek
        if model == "minimax":
            if self._minimax is None:
                self._minimax = MiniMaxClient()
            return self._minimax
        # provider 级别
        if self.provider == "local":
            if self._local is None:
                self._local = LocalClient()
            return self._local
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
            model — "minimax" | "deepseek" | "local" | ""（使用 provider 设置或 auto 策略）
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
        支持 MiniMax、DeepSeek 和本地大模型的流式响应。
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
#   resp = llm.chat("分析公司财务数据", model="local")
llm = LLMClient()
