"""
Demo: @observe decorator instrumentation.

This is the quickest SDK-level way to let Langfuse observe normal Python
functions. The decorator creates observations, captures function input/output,
and propagates context to nested decorated calls.
"""

from __future__ import annotations

from langfuse import get_client, observe

from _common import flush_and_print, get_configured_langfuse


@observe(as_type="agent", name="decorated-support-agent")
def run_agent(question: str) -> str:
    # The parent agent observation is created automatically by @observe.
    draft = call_model(question)
    return f"Final answer: {draft}"


@observe(as_type="generation", name="decorated-model-call")
def call_model(prompt: str) -> str:
    # For generation observations, enrich the automatically created observation
    # with model and usage details. This is where you would copy provider usage.
    langfuse = get_client()
    result = "Refunds are available within 30 days."
    langfuse.update_current_generation(
        model="mock-gpt-4o-mini",
        input=prompt,
        output=result,
        usage_details={"input": 9, "output": 8, "total": 17},
    )
    return result


def main() -> None:
    langfuse = get_configured_langfuse()
    print(run_agent("What is the refund window?"))
    flush_and_print(langfuse, "observe-decorator-way-demo")


if __name__ == "__main__":
    main()
