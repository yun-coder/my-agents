"""
Demo: evaluator observation.

Use evaluator observations for LLM-as-a-judge, heuristic checks, or offline
evaluation steps. Pair the evaluator observation with scores when you want the
result to appear in Langfuse evaluation and analytics views.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="evaluator",
        name="answer-relevance-evaluator",
        input={
            "question": "What is the refund window?",
            "answer": "Refunds are available within 30 days.",
        },
        metadata={"evaluator": "heuristic-keyword-match"},
        version="evaluator-0.2.0",
    ) as evaluator:
        relevance = 0.98
        evaluator.update(output={"relevance": relevance, "reason": "Answer directly states the window."})

        # Scores can be attached from an observation object. This score belongs
        # to the evaluator observation and can be used for filtering/comparison.
        evaluator.score(
            name="answer_relevance",
            value=relevance,
            data_type="NUMERIC",
            comment="High relevance in mocked evaluator.",
        )

    flush_and_print(langfuse, "evaluator-observation-demo")


if __name__ == "__main__":
    main()
