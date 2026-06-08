"""
演示 21: LiteLLM 回调集成方式。

LiteLLM 可以通过回调将模型调用日志发送到 Langfuse。Langfuse 文档
描述了三种 LiteLLM 集成路径：代理日志记录、LiteLLM Python SDK 回调、
或使用 Langfuse 已经插桩的 OpenAI/LangChain 兼容路径。

实际 SDK 调用所需依赖：
    pip install litellm langfuse
    设置 OPENAI_API_KEY=... 或配置其他 LiteLLM provider
"""

from __future__ import annotations

import os

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 未设置 API Key 时跳过实际调用
    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="litellm-callback-demo-skipped",
            input={"reason": "OPENAI_API_KEY 未设置"},
            metadata={"integration": "litellm.success_callback = ['langfuse']"},
        ) as span:
            span.update(
                output={
                    "sdk_route": "在 completion() 调用前设置 litellm.success_callback = ['langfuse']。",
                    "proxy_route": "在 LiteLLM Proxy 配置/UI 中将 Langfuse 设为回调。",
                }
            )
        flush_and_print(langfuse, "litellm-callback-way-demo-skipped")
        return

    import litellm

    # 设置 LiteLLM 的成功和失败回调为 Langfuse
    litellm.success_callback = ["langfuse"]           # 成功时回调 Langfuse
    litellm.failure_callback = ["langfuse"]           # 失败时也回调 Langfuse

    # LiteLLM 自动将调用信息发送到 Langfuse
    response = litellm.completion(
        model="openai/gpt-4o-mini",                  # LiteLLM 格式的模型名
        messages=[{"role": "user", "content": "简要回答: Langfuse 观测什么？"}],
        metadata={
            "generation_name": "litellm-demo-generation",
            "trace_user_id": "user_litellm_001",
            "session_id": "session_litellm_001",
            "tags": ["demo", "litellm"],
        },
    )
    print(response["choices"][0]["message"]["content"])

    flush_and_print(langfuse, "litellm-callback-way-demo")


if __name__ == "__main__":
    main()
