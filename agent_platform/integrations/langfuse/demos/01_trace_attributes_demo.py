"""
演示 01: trace（追踪）级别属性。

本演示展示 Langfuse 在 trace 层面可以观测的维度：
- trace 的输入（input）和输出（output）
- user_id —— 用于用户维度的分析
- session_id —— 用于多轮对话分组
- tags、metadata 和 version —— 用于筛选和版本对比

文档基础：
- Python SDK 的 @observe 装饰器
- propagate_attributes(...) 属性传播
- @observe 自动捕获函数参数作为输入、返回值作为输出
"""

from __future__ import annotations

from langfuse import observe, propagate_attributes

from _common import flush_and_print, get_configured_langfuse


@observe(name="trace-attributes-demo")
def answer_customer_question(question: str) -> str:
    """创建一个 trace 并使用 Langfuse UI 中呈现的各种属性对其丰富。"""

    # propagate_attributes 将以下属性值应用到当前 trace 及
    # 此代码块内创建的所有子 observation。
    with propagate_attributes(
        user_id="user_123",                                     # 用户标识
        session_id="support_session_2026_05_27",                # 会话标识，用于多轮对话分组
        tags=["demo", "trace-attributes", "support"],           # 标签，用于分类筛选
        metadata={
            "tenant": "acme",                                    # 租户信息
            "channel": "web-chat",                               # 交互渠道
            "experiment": "short-answer-v2",                     # 实验标识
        },
        version="2026.05.27",                                    # 版本号，用于版本对比
    ):
        answer = "您可以在 账户 > 安全 中重置密码。"

        # @observe 装饰器会自动捕获函数参数作为输入、返回值作为输出，
        # 因此无需再手动调用已弃用的 set_current_trace_io()。
        return answer


def main() -> None:
    langfuse = get_configured_langfuse()
    print(answer_customer_question("如何重置密码？"))
    flush_and_print(langfuse, "trace-attributes-demo")


if __name__ == "__main__":
    main()
