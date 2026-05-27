"""
Demo: context manager instrumentation.

Use start_as_current_observation(...) when you want explicit control over
observation boundaries while still getting automatic nesting from the active
OpenTelemetry context.
"""

from __future__ import annotations

from langfuse import propagate_attributes

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="context-manager-root",
        input={"request_id": "req_ctx_001"},
    ) as root_span:
        with propagate_attributes(
            user_id="user_ctx_001",
            session_id="session_ctx_001",
            tags=["demo", "context-manager"],
            metadata={"source": "14_context_manager_way_demo.py"},
        ):
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="nested-generation",
                model="mock-model",
                input="Write a short policy answer.",
            ) as generation:
                generation.update(output="Refunds are available within 30 days.")

            root_span.update(output={"status": "ok"})

    flush_and_print(langfuse, "context-manager-way-demo")


if __name__ == "__main__":
    main()
