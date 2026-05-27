"""
Demo: retriever observation.

Use retriever observations for search/RAG retrieval steps. Store query,
filters, retrieved document IDs, scores, and small snippets that help debug
whether the right context was supplied to the model.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="retriever",
        name="policy-vector-search",
        input={"query": "refund window", "top_k": 3, "filters": {"locale": "en-US"}},
        metadata={"index": "help-center-vectors"},
    ) as retriever:
        retriever.update(
            output=[
                {"doc_id": "policy_refunds", "score": 0.94, "snippet": "Refunds are allowed within 30 days."},
                {"doc_id": "policy_exchanges", "score": 0.72, "snippet": "Exchanges follow the same window."},
            ]
        )

    flush_and_print(langfuse, "retriever-observation-demo")


if __name__ == "__main__":
    main()
