"""
演示 19: LlamaIndex 通过 OpenInference 插桩方式。

Langfuse 可以接收 OpenInference 插桩发出的 OpenTelemetry span。
对于 LlamaIndex，instrumentor 自动捕获 LlamaIndex 的 LLM、
检索和查询引擎操作，并将其发送到 Langfuse。

实际调用所需依赖：
    pip install openinference-instrumentation-llama-index llama-index llama-index-llms-openai langfuse
    设置环境变量 OPENAI_API_KEY=...
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
            name="llamaindex-openinference-demo-skipped",
            input={"reason": "OPENAI_API_KEY 未设置"},
            metadata={"integration": "openinference.instrumentation.llama_index"},
        ) as span:
            span.update(output={"next_step": "安装 LlamaIndex 相关包并设置 OPENAI_API_KEY。"})
        flush_and_print(langfuse, "llamaindex-openinference-way-demo-skipped")
        return

    from llama_index.llms.openai import OpenAI
    from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

    # 启动 OpenInference LlamaIndex 插桩器，自动采集 span
    LlamaIndexInstrumentor().instrument()
    llm = OpenAI(model="gpt-4o-mini")

    with langfuse.start_as_current_observation(
        as_type="span",
        name="llamaindex-openinference-parent",      # 父 span
        input={"prompt": "用 LlamaIndex 打个招呼。"},
    ) as span:
        response = llm.complete("用一句话从 LlamaIndex 说你好。")
        span.update(output=str(response))
        print(response)

    flush_and_print(langfuse, "llamaindex-openinference-way-demo")


if __name__ == "__main__":
    main()
