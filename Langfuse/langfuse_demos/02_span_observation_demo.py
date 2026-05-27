"""
Demo: span observation.

Use spans for generic timed work that is not necessarily an LLM call:
- request validation
- routing
- database calls
- business logic
- external API calls
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # start_as_current_observation creates a timed observation and sets it as
    # the active context. Any nested Langfuse observations become its children.
    with langfuse.start_as_current_observation(
        as_type="span",
        name="validate-and-route-request",
        input={"query": "refund policy", "locale": "en-US"},
        metadata={"component": "router"},
        version="router-1.3.0",
    ) as span:
        route = {"intent": "policy_question", "target_chain": "refund_policy_chain"}

        # update can be called at the end or multiple times during execution.
        # output is the final value shown for this observation in Langfuse.
        span.update(output=route)

    flush_and_print(langfuse, "span-observation-demo")


if __name__ == "__main__":
    main()
