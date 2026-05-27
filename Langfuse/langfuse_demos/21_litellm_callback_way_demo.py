"""
Demo: LiteLLM callback integration.

LiteLLM can send model call logs to Langfuse through callbacks. Langfuse docs
describe three LiteLLM routes: proxy logging, LiteLLM Python SDK callbacks, or
using an OpenAI/LangChain-compatible path that Langfuse already instruments.

Required for a real SDK call:
    pip install litellm langfuse
    set OPENAI_API_KEY=... or configure another LiteLLM provider
"""

from __future__ import annotations

import os

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="litellm-callback-demo-skipped",
            input={"reason": "OPENAI_API_KEY is not set"},
            metadata={"integration": "litellm.success_callback = ['langfuse']"},
        ) as span:
            span.update(
                output={
                    "sdk_route": "Set litellm.success_callback = ['langfuse'] before completion().",
                    "proxy_route": "Set Langfuse as a callback in LiteLLM Proxy config/UI.",
                }
            )
        flush_and_print(langfuse, "litellm-callback-way-demo-skipped")
        return

    import litellm

    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

    response = litellm.completion(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Answer briefly: what does Langfuse observe?"}],
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
