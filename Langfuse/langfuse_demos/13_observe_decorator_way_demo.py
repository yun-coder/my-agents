"""
演示 13: @observe 装饰器方式。

这是使用 SDK 让 Langfuse 观测普通 Python 函数的最快方式。
装饰器自动创建 observation、捕获函数输入/输出，
并将上下文传播到嵌套的被装饰调用。
"""

from __future__ import annotations

from langfuse import get_client, observe

from _common import flush_and_print, get_configured_langfuse


@observe(as_type="agent", name="decorated-support-agent")
def run_agent(question: str) -> str:
    # 父级 agent observation 由 @observe 自动创建
    draft = call_model(question)
    return f"最终答案: {draft}"


@observe(as_type="generation", name="decorated-model-call")
def call_model(prompt: str) -> str:
    # 对于 generation observation，用模型和用量详情丰富自动创建的 observation。
    # 生产环境中应在此处复制 provider 返回的用量信息。
    langfuse = get_client()
    result = "退款在 30 天内可用。"
    langfuse.update_current_generation(
        model="mock-gpt-4o-mini",
        input=prompt,
        output=result,
        usage_details={"input": 9, "output": 8, "total": 17},  # token 用量
    )
    return result


def main() -> None:
    langfuse = get_configured_langfuse()
    print(run_agent("退款窗口是多久？"))
    flush_and_print(langfuse, "observe-decorator-way-demo")


if __name__ == "__main__":
    main()
