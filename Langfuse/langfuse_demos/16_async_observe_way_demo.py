"""
Demo: async function instrumentation.

The @observe decorator also works with async functions. Context propagation is
important for async apps because child model calls and tool calls should remain
attached to the same trace.
"""

from __future__ import annotations

import asyncio

from langfuse import get_client, observe

from _common import flush_and_print, get_configured_langfuse


@observe(as_type="chain", name="async-answer-chain")
async def async_answer(question: str) -> str:
    model_answer = await async_model_call(question)
    get_client().update_current_observation(output={"answer": model_answer})
    return model_answer


@observe(as_type="generation", name="async-model-call")
async def async_model_call(prompt: str) -> str:
    await asyncio.sleep(0.01)
    answer = "Refunds are available within 30 days."
    get_client().update_current_generation(
        model="mock-async-model",
        input=prompt,
        output=answer,
        usage_details={"input": 8, "output": 8, "total": 16},
    )
    return answer


async def run() -> None:
    langfuse = get_configured_langfuse()
    print(await async_answer("What is the refund window?"))
    flush_and_print(langfuse, "async-observe-way-demo")


if __name__ == "__main__":
    asyncio.run(run())
