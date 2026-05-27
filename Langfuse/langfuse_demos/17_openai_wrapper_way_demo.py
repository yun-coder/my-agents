"""
Demo: Langfuse OpenAI wrapper.

If you already use the OpenAI Python SDK, replace the client import with
langfuse.openai.OpenAI. Langfuse will observe chat completions automatically
and nest them under the active trace/span when one exists.

Required for a real call:
    pip install openai langfuse
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
            name="openai-wrapper-demo-skipped",
            input={"reason": "OPENAI_API_KEY is not set"},
            metadata={"integration": "langfuse.openai.OpenAI"},
        ) as span:
            span.update(
                output={
                    "next_step": "Set OPENAI_API_KEY to run the real OpenAI wrapper call.",
                    "example_import": "from langfuse.openai import OpenAI",
                }
            )
        flush_and_print(langfuse, "openai-wrapper-way-demo-skipped")
        return

    from langfuse.openai import OpenAI

    client = OpenAI()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="openai-wrapper-parent",
        input={"question": "What does Langfuse observe?"},
    ) as span:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Answer in one sentence."},
                {"role": "user", "content": "What does Langfuse observe?"},
            ],
            temperature=0.2,
        )
        answer = response.choices[0].message.content
        span.update(output={"answer": answer})

    flush_and_print(langfuse, "openai-wrapper-way-demo")


if __name__ == "__main__":
    main()
