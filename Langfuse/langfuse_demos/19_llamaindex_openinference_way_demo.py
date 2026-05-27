"""
Demo: LlamaIndex via OpenInference instrumentation.

Langfuse can receive OpenTelemetry spans emitted by OpenInference
instrumentation. For LlamaIndex, the instrumentor captures LlamaIndex LLM,
retrieval, and query-engine operations and sends them to Langfuse.

Required for a real call:
    pip install openinference-instrumentation-llama-index llama-index llama-index-llms-openai langfuse
    set OPENAI_API_KEY=...
"""

from __future__ import annotations

import os

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="llamaindex-openinference-demo-skipped",
            input={"reason": "OPENAI_API_KEY is not set"},
            metadata={"integration": "openinference.instrumentation.llama_index"},
        ) as span:
            span.update(output={"next_step": "Install LlamaIndex packages and set OPENAI_API_KEY."})
        flush_and_print(langfuse, "llamaindex-openinference-way-demo-skipped")
        return

    from llama_index.llms.openai import OpenAI
    from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

    LlamaIndexInstrumentor().instrument()
    llm = OpenAI(model="gpt-4o-mini")

    with langfuse.start_as_current_observation(
        as_type="span",
        name="llamaindex-openinference-parent",
        input={"prompt": "Say hello from LlamaIndex."},
    ) as span:
        response = llm.complete("Say hello from LlamaIndex in one sentence.")
        span.update(output=str(response))
        print(response)

    flush_and_print(langfuse, "llamaindex-openinference-way-demo")


if __name__ == "__main__":
    main()
