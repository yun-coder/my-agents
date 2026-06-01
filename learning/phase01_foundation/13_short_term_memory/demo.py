"""离线可运行：按字符预算裁剪旧消息的最小示例。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    # role：消息作者角色，例如 user 或 assistant。
    role: str
    # content：消息正文。本章不处理多模态内容块。
    content: str


class SlidingWindowMemory:
    def __init__(self, max_chars: int = 80) -> None:
        # max_chars 是教学用近似预算。生产系统应改用模型对应 tokenizer 统计 token。
        self.max_chars = max_chars
        self.messages: deque[Message] = deque()

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role, content))
        while sum(len(message.content) for message in self.messages) > self.max_chars:
            self.messages.popleft()

    def snapshot(self) -> list[dict[str, str]]:
        return [
            {"role": message.role, "content": message.content}
            for message in self.messages
        ]


def main() -> None:
    memory = SlidingWindowMemory(max_chars=45)
    memory.add("user", "我叫小明，正在学习 Agent。")
    memory.add("assistant", "你好，小明。")
    memory.add("user", "请解释什么是短期记忆。")
    memory.add("assistant", "短期记忆用于保留当前会话需要的上下文。")
    for message in memory.snapshot():
        print(message)


if __name__ == "__main__":
    main()
