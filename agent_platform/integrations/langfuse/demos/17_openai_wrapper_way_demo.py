"""
演示 17: Langfuse OpenAI 包装器方式。

如果你已经在使用 OpenAI Python SDK，只需将客户端导入替换为
langfuse.openai.OpenAI。Langfuse 将自动观测聊天补全请求，
并在存在活跃 trace/span 时将其嵌套其中。

实际调用所需依赖：
    pip install openai langfuse
    设置环境变量 OPENAI_API_KEY=...
"""

from __future__ import annotations

import os

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 如果未设置 OpenAI API Key，则跳过实际调用并记录原因
    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="openai-wrapper-demo-skipped",
            input={"reason": "OPENAI_API_KEY 未设置"},
            metadata={"integration": "langfuse.openai.OpenAI"},
        ) as span:
            span.update(
                output={
                    "next_step": "设置 OPENAI_API_KEY 以运行真正的 OpenAI 包装器调用。",
                    "example_import": "from langfuse.openai import OpenAI",
                }
            )
        flush_and_print(langfuse, "openai-wrapper-way-demo-skipped")
        return

    # 关键：使用 Langfuse 包装的 OpenAI 客户端
    from langfuse.openai import OpenAI

    client = OpenAI()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="openai-wrapper-parent",                # 父 span
        input={"question": "Langfuse 观测什么？"},
    ) as span:
        # 这个 chat.completions.create 调用会被 Langfuse 自动观测
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "请用一句话回答。"},
                {"role": "user", "content": "Langfuse 观测什么？"},
            ],
            temperature=0.2,
        )
        answer = response.choices[0].message.content
        span.update(output={"answer": answer})

    flush_and_print(langfuse, "openai-wrapper-way-demo")


if __name__ == "__main__":
    main()
