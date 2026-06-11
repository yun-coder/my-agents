"""统一 LLM 客户端：封装 OpenAI 兼容 API，支持流式输出和错误重试。

所有 chat / chat_stream / chat_with_tools 调用都会被 `traced_operation`
自动追踪到 LangFuse（as_type="generation"，含 model + usage）。
"""

from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from ..config import LLMSettings, load_config
from ..observability import init_tracing, traced_operation

logger = logging.getLogger(__name__)


def _extract_usage(response: Any) -> dict[str, int] | None:
    """从 OpenAI response 里抽取 token 用量。"""
    u = getattr(response, "usage", None)
    if not u:
        return None
    return {
        "input": getattr(u, "prompt_tokens", 0),
        "output": getattr(u, "completion_tokens", 0),
        "total": getattr(u, "total_tokens", 0),
    }


class LLMClient:
    """OpenAI 兼容 LLM 客户端。

    自动从 dev.json 加载配置，支持：
    - 普通对话（chat）
    - 流式输出（chat_stream）
    - 工具调用（chat_with_tools）

    所有调用通过 LangFuse `traced_operation` 自动追踪。
    """

    def __init__(self, settings: LLMSettings | None = None) -> None:
        cfg = settings or load_config().llm
        self._client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        self._model = cfg.model

    @property
    def model(self) -> str:
        return self._model

    def chat(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        with traced_operation(
            "llm.chat",
            input=messages,
            model=self._model,
            as_type="generation",
            metadata={"temperature": temperature, "max_tokens": max_tokens},
        ) as op:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            op.update(output=content, usage=_extract_usage(response))
            return content

    def chat_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ):
        """流式生成器，每次 yield 一个文本片段。"""
        with traced_operation(
            "llm.chat_stream",
            input=messages,
            model=self._model,
            as_type="generation",
            metadata={"temperature": temperature, "max_tokens": max_tokens},
        ) as op:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            chunks: list[str] = []
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    chunks.append(delta.content)
                    yield delta.content
            op.update(output="".join(chunks))

    def chat_with_tools(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[dict],
        *,
        temperature: float = 0.0,
    ):
        """返回原始 completion 对象，由调用方处理 tool_calls。"""
        with traced_operation(
            "llm.chat_with_tools",
            input=messages,
            model=self._model,
            as_type="generation",
            metadata={
                "temperature": temperature,
                "tools": [t.get("function", {}).get("name", "?") for t in tools],
            },
        ) as op:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                tools=tools,
            )
            op.update(
                output=response.choices[0].message.model_dump(),
                usage=_extract_usage(response),
            )
            return response


_client_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取全局 LLMClient 单例。

    第一次调用时**自动 init_tracing**（幂等）—— 这是 LangFuse 追踪的总开关，
    所有 LLM 调用都会经过 `get_llm_client`，所以这里接入点最稳。
    """
    global _client_instance
    if _client_instance is None:
        init_tracing()               # 幂等；失败走降级
        _client_instance = LLMClient()
    return _client_instance
