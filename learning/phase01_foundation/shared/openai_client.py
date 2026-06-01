"""创建 OpenAI 兼容客户端。"""

from __future__ import annotations

from openai import OpenAI

from shared.config import OpenAISettings, get_openai_settings


def create_openai_client(settings: OpenAISettings | None = None) -> OpenAI:
    current = settings or get_openai_settings()
    # api_key 用于鉴权；base_url 允许课程复用 OpenAI 官方或兼容 API 根地址。
    return OpenAI(api_key=current.api_key, base_url=current.base_url)
