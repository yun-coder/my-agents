"""
演示 16: 异步函数方式。

@observe 装饰器同样支持异步函数。上下文传播对异步应用
非常重要，因为子模型调用和工具调用需要保持在同一个 trace 内。
"""

from __future__ import annotations

import asyncio

from langfuse import get_client, observe

from _common import flush_and_print, get_configured_langfuse


@observe(as_type="chain", name="async-answer-chain")
async def async_answer(question: str) -> str:
    """异步链：调用异步模型并更新当前 observation"""
    model_answer = await async_model_call(question)
    get_client().update_current_span(output={"answer": model_answer})
    return model_answer


@observe(as_type="generation", name="async-model-call")
async def async_model_call(prompt: str) -> str:
    """异步 LLM 调用（模拟）"""
    await asyncio.sleep(0.01)                        # 模拟异步网络延迟
    answer = "退款在 30 天内可用。"
    get_client().update_current_generation(
        model="mock-async-model",
        input=prompt,
        output=answer,
        usage_details={"input": 8, "output": 8, "total": 16},
    )
    return answer


async def run() -> None:
    langfuse = get_configured_langfuse()
    print(await async_answer("退款窗口是多久？"))
    flush_and_print(langfuse, "async-observe-way-demo")


if __name__ == "__main__":
    asyncio.run(run())                                # 使用 asyncio.run 启动异步入口
