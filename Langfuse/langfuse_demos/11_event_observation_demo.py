"""
Demo: event observation.

Events are zero-duration observations. Use them for point-in-time facts:
- cache hit/miss
- retry attempt
- fallback selected
- user clicked thumbs-up
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="event-parent-pipeline",
        input={"request_id": "req_123"},
    ) as span:
        langfuse.create_event(
            name="cache-miss",
            input={"cache_key": "policy:refund-window"},
            output={"hit": False},
            metadata={"cache": "redis"},
            level="DEFAULT",
        )

        langfuse.create_event(
            name="retry-attempt",
            input={"attempt": 2, "reason": "transient timeout"},
            metadata={"max_attempts": 3},
            level="WARNING",
        )

        span.update(output={"status": "completed_after_retry"})

    flush_and_print(langfuse, "event-observation-demo")


if __name__ == "__main__":
    main()
