"""统一 LLM 客户端：封装 OpenAI 兼容 API，支持流式输出和错误重试。"""

from __future__ import annotations

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from ..config import LLMSettings, load_config


class LLMClient:
    """OpenAI 兼容 LLM 客户端。

    自动从 dev.json 加载配置，支持：
    - 普通对话（chat）
    - 流式输出（chat_stream）
    - 工具调用（chat_with_tools）
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
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ):
        """流式生成器，每次 yield 一个文本片段。"""
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def chat_with_tools(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[dict],
        *,
        temperature: float = 0.0,
    ):
        """返回原始 completion 对象，由调用方处理 tool_calls。"""
        return self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            tools=tools,
        )


_client_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance
