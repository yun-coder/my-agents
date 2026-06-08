"""
演示 11: event（事件）类型 observation。

event 是零耗时的 observation。用于记录时间点事实：
- 缓存命中/未命中
- 重试尝试
- 回退方案被选中
- 用户点击了"赞"
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="event-parent-pipeline",                # 父管道作为事件容器
        input={"request_id": "req_123"},
    ) as span:
        # create_event 创建一个零耗时的瞬时事件
        langfuse.create_event(
            name="cache-miss",                        # 事件：缓存未命中
            input={"cache_key": "policy:refund-window"},
            output={"hit": False},
            metadata={"cache": "redis"},              # 缓存类型
            level="DEFAULT",
        )

        langfuse.create_event(
            name="retry-attempt",                     # 事件：重试尝试
            input={"attempt": 2, "reason": "transient timeout"},  # 第2次尝试，原因：瞬时超时
            metadata={"max_attempts": 3},             # 最大重试次数
            level="WARNING",                           # 警告级别
        )

        span.update(output={"status": "completed_after_retry"})  # 状态：重试后完成

    flush_and_print(langfuse, "event-observation-demo")


if __name__ == "__main__":
    main()
