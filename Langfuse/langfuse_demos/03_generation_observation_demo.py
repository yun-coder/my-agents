"""
Demo: generation observation.

Use generation observations for LLM calls. Langfuse can display model name,
model parameters, prompts/messages, completion output, token usage, and cost.
This demo mocks the provider response so it runs without an LLM API key.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    messages = [
        {"role": "system", "content": "Answer with one concise sentence."},
        {"role": "user", "content": "What does Langfuse trace?"},
    ]

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="mock-chat-completion",
        model="mock-gpt-4o-mini",
        model_parameters={"temperature": 0.2, "max_tokens": 64},
        input=messages,
    ) as generation:
        output = "Langfuse traces LLM application steps, model calls, metadata, and scores."

        # usage_details and cost_details are attached to generation
        # observations. In production, copy these from your provider response.
        generation.update(
            output=output,
            usage_details={"input": 24, "output": 15, "total": 39},
            cost_details={"input": 0.000012, "output": 0.000009, "total": 0.000021},
            metadata={"provider": "mock", "finish_reason": "stop"},
        )

    flush_and_print(langfuse, "generation-observation-demo")


if __name__ == "__main__":
    main()
