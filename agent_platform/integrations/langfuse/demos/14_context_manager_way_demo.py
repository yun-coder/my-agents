"""
演示 14: 上下文管理器方式。

当你需要对 observation 边界进行显式控制，同时利用
OpenTelemetry 活跃上下文实现自动嵌套时，使用
start_as_current_observation(...) 上下文管理器。
"""

from __future__ import annotations

from langfuse import propagate_attributes

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="context-manager-root",                 # 根 observation
        input={"request_id": "req_ctx_001"},
    ) as root_span:
        # propagate_attributes 将用户/会话/标签等属性注入到活跃上下文中
        with propagate_attributes(
            user_id="user_ctx_001",
            session_id="session_ctx_001",
            tags=["demo", "context-manager"],
            metadata={"source": "14_context_manager_way_demo.py"},
        ):
            # 嵌套的子 observation，自动继承父级上下文
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="nested-generation",            # 嵌套的 generation
                model="mock-model",
                input="写一段简短的政策回答。",
            ) as generation:
                generation.update(output="退款在 30 天内可用。")

            root_span.update(output={"status": "ok"})

    flush_and_print(langfuse, "context-manager-way-demo")


if __name__ == "__main__":
    main()
