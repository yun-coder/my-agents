"""
Demo: embedding observation.

Use embedding observations for calls that convert text/images into vectors.
Track model, input count, dimensions, token usage, and any batching metadata.
Do not store huge raw vectors unless you truly need them for debugging.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    documents = [
        "Refunds are available within 30 days.",
        "Invoices can be downloaded from the billing page.",
    ]

    with langfuse.start_as_current_observation(
        as_type="embedding",
        name="embed-help-center-documents",
        model="mock-text-embedding-3-small",
        input=documents,
        metadata={"batch_size": len(documents), "dimensions": 1536},
    ) as embedding:
        embedding.update(
            output={"vector_count": len(documents), "stored_vector_preview": "[omitted]"},
            usage_details={"input": 21, "total": 21},
        )

    flush_and_print(langfuse, "embedding-observation-demo")


if __name__ == "__main__":
    main()
