"""
Demo: manual start/end lifecycle.

Use start_observation(...) when an observation cannot be expressed as a simple
with-block, for example background jobs, callbacks, queues, or code that starts
in one function and finishes in another. You must call end() yourself.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    job = langfuse.start_observation(
        as_type="span",
        name="manual-background-job",
        input={"job_id": "job_123", "kind": "daily-eval"},
    )

    try:
        result = {"processed_rows": 1500, "failed_rows": 0}
        job.update(output=result, level="DEFAULT")
    except Exception as exc:
        # Mark the observation as an error before re-raising. This makes failed
        # jobs visible in Langfuse even when the exception is handled upstream.
        job.update(level="ERROR", status_message=str(exc))
        raise
    finally:
        job.end()

    flush_and_print(langfuse, "manual-lifecycle-way-demo")


if __name__ == "__main__":
    main()
