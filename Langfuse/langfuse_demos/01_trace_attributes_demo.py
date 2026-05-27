"""
Demo: trace-level attributes.

What Langfuse observes here:
- trace input and output
- user_id for user-level analytics
- session_id for multi-turn conversation grouping
- tags, metadata, and version for filtering and release comparison

Docs basis:
- Python SDK observe decorator
- propagate_attributes(...)
- update_current_trace(...)
"""

from __future__ import annotations

from langfuse import get_client, observe, propagate_attributes

from _common import flush_and_print, get_configured_langfuse


@observe(name="trace-attributes-demo")
def answer_customer_question(question: str) -> str:
    """Create one trace and enrich it with attributes used by Langfuse UI."""

    langfuse = get_client()

    # propagate_attributes applies these values to the current trace and to
    # child observations created inside this block.
    with propagate_attributes(
        user_id="user_123",
        session_id="support_session_2026_05_27",
        tags=["demo", "trace-attributes", "support"],
        metadata={
            "tenant": "acme",
            "channel": "web-chat",
            "experiment": "short-answer-v2",
        },
        version="2026.05.27",
    ):
        answer = "You can reset your password from Account > Security."

        # update_current_trace sets the trace-level input/output shown at the
        # top of the trace page. This is useful when the decorated function's
        # Python arguments are not the exact user-facing input.
        langfuse.update_current_trace(
            input={"question": question},
            output={"answer": answer},
        )
        return answer


def main() -> None:
    langfuse = get_configured_langfuse()
    print(answer_customer_question("How do I reset my password?"))
    flush_and_print(langfuse, "trace-attributes-demo")


if __name__ == "__main__":
    main()
