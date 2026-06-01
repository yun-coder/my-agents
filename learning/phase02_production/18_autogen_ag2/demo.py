"""离线可运行：模拟多 Agent 消息协作与轮次限制。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    # source：发送消息的 Agent 名称。
    source: str
    # content：发送给下一个 Agent 的内容。
    content: str


def reviewer(message: Message) -> Message:
    return Message("reviewer", f"审查意见：请确认测试覆盖。原始内容：{message.content}")


def implementer(message: Message) -> Message:
    return Message("implementer", f"实现回复：已补充测试。收到：{message.content}")


def main() -> None:
    message = Message("user", "为订单查询接口增加缓存。")
    # max_rounds：防止多 Agent 在没有终止条件时无限互相回复。
    for round_index in range(2):
        message = reviewer(message) if round_index == 0 else implementer(message)
        print(message)


if __name__ == "__main__":
    main()
