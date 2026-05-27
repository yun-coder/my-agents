"""
Demo: scores.

Scores are evaluations attached to a trace or a specific observation. Langfuse
supports numeric, boolean, categorical, and text-like feedback patterns. Use
scores for user feedback, automated evals, quality gates, and regression tests.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="scored-generation",
        model="mock-gpt-4o-mini",
        input="What is the refund window?",
    ) as generation:
        generation.update(output="Refunds are available within 30 days.")

        # Score the current generation observation.
        langfuse.score_current_span(
            name="answer_relevance",
            value=0.97,
            data_type="NUMERIC",
            comment="Directly answered the user question.",
            metadata={"evaluator": "mock-rule"},
        )

        # Score the entire trace. A common use case is user feedback.
        langfuse.score_current_trace(
            name="user_feedback",
            value=1.0,
            data_type="BOOLEAN",
            comment="User clicked thumbs up in the UI.",
        )

    flush_and_print(langfuse, "score-demo")


if __name__ == "__main__":
    main()
