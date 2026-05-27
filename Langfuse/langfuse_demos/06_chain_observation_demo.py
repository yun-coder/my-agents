"""
Demo: chain observation.

Use chain observations for deterministic or semi-deterministic pipelines that
combine multiple steps, such as prompt building -> retrieval -> generation.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="chain",
        name="rag-answer-chain",
        input={"question": "What is the refund window?"},
        metadata={"chain": "simple-rag"},
        version="rag-chain-0.1.0",
    ) as chain:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="format-prompt",
            input={"template": "policy-answer-v1"},
        ) as span:
            span.update(output={"prompt_chars": 312})

        chain.update(output={"answer": "Refunds are available within 30 days."})

    flush_and_print(langfuse, "chain-observation-demo")


if __name__ == "__main__":
    main()
