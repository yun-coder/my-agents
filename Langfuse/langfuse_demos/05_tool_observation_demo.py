"""
Demo: tool observation.

Use tool observations for functions or external systems called by an agent:
- search APIs
- calculators
- database lookups
- CRM or ticketing operations
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="tool",
        name="lookup-invoice-tool",
        input={"customer_id": "cust_123", "invoice_month": "2026-05"},
        metadata={"system": "billing-api"},
    ) as tool:
        # The tool output should include enough structure to debug failures.
        # Avoid storing secrets, raw credentials, or unnecessary PII.
        tool.update(
            output={
                "invoice_id": "inv_2026_05_123",
                "status": "ready",
                "amount": 199.0,
            }
        )

    flush_and_print(langfuse, "tool-observation-demo")


if __name__ == "__main__":
    main()
