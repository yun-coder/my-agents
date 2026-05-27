"""
Demo: guardrail observation.

Use guardrail observations for safety, compliance, policy, or schema checks.
They are useful both before an LLM call and before returning an answer to a
user.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="guardrail",
        name="pii-output-check",
        input={"answer": "Your invoice is ready in the billing portal."},
        metadata={"policy": "no-sensitive-identifiers"},
        version="guardrail-1.0.0",
    ) as guardrail:
        passed = True
        guardrail.update(
            output={"passed": passed, "violations": []},
            level="DEFAULT" if passed else "WARNING",
        )

    flush_and_print(langfuse, "guardrail-observation-demo")


if __name__ == "__main__":
    main()
