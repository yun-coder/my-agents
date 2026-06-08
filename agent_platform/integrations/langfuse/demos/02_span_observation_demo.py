"""
演示 02: span（跨度）类型 observation。

span 用于表示不一定是 LLM 调用的通用计时工作单元：
- 请求验证
- 路由分发
- 数据库调用
- 业务逻辑
- 外部 API 调用
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # start_as_current_observation 创建一个计时的 observation，
    # 并将其设置为当前活跃上下文。任何嵌套的 Langfuse observation
    # 都会自动成为它的子节点。
    with langfuse.start_as_current_observation(
        as_type="span",                             # observation 类型：span
        name="validate-and-route-request",           # 名称：验证并路由请求
        input={"query": "refund policy", "locale": "en-US"},  # 输入
        metadata={"component": "router"},            # 元数据：所属组件
        version="router-1.3.0",                      # 版本号
    ) as span:
        route = {"intent": "policy_question", "target_chain": "refund_policy_chain"}

        # update 可以在执行过程中多次调用，也可以在结束时调用一次。
        # output 是在 Langfuse 中为此 observation 展示的最终值。
        span.update(output=route)

    flush_and_print(langfuse, "span-observation-demo")


if __name__ == "__main__":
    main()
