"""
Demo: agent observation.

Use agent observations to represent an autonomous decision-making unit. Child
observations usually include LLM generations, tool calls, retrieval steps, and
guardrails performed while the agent works on one task.
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="agent",
        name="support-triage-agent",
        input={"ticket": "Customer asks for invoice copy."},
        metadata={"agent_strategy": "classify-then-act"},
    ) as agent:
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="agent-planning-generation",
            model="mock-planner",
            input="Classify ticket and choose next action.",
        ) as generation:
            generation.update(output="Intent: billing. Action: fetch_invoice_tool.")

        agent.update(
            output={
                "intent": "billing",
                "selected_action": "fetch_invoice_tool",
                "confidence": 0.91,
            }
        )

    flush_and_print(langfuse, "agent-observation-demo")


if __name__ == "__main__":
    main()
