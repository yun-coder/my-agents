"""对话记忆管理：滑动窗口 + 摘要压缩 + Token 预算。

短期记忆策略：
1. 保留最近 N 轮完整对话（滑动窗口）
2. 超出窗口的早期对话生成摘要
3. Token 预算控制，防止上下文溢出
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    """一轮对话。"""

    role: str  # "user" 或 "assistant"
    content: str
    tokens: int = 0  # 预估 token 数


@dataclass
class ConversationMemory:
    """会话级别的对话记忆。

    用法:
        mem = ConversationMemory(max_turns=20, max_tokens=4000)
        mem.add("user", "什么是 RAG？")
        mem.add("assistant", "RAG 是检索增强生成...")
        messages = mem.get_messages()  # 返回 OpenAI 格式的消息列表
    """

    max_turns: int = 20
    max_tokens: int = 4000
    _turns: deque[ConversationTurn] = field(default_factory=deque)
    _summary: str = ""

    def add(self, role: str, content: str) -> None:
        token_estimate = len(content) // 3  # 粗略估计：中文约 1.5 字/token
        self._turns.append(ConversationTurn(role, content, token_estimate))
        self._trim()

    def _trim(self) -> None:
        """根据 max_turns 和 max_tokens 裁剪历史。"""
        while len(self._turns) > self.max_turns:
            removed = self._turns.popleft()
            self._summary = self._update_summary(removed)

        while self._total_tokens > self.max_tokens and len(self._turns) > 2:
            removed = self._turns.popleft()
            self._summary = self._update_summary(removed)

    @property
    def _total_tokens(self) -> int:
        return sum(t.tokens for t in self._turns)

    def _update_summary(self, turn: ConversationTurn) -> str:
        """简单的累积摘要策略。"""
        if not self._summary:
            return f"前情提要：用户问了关于{turn.content[:30]}...的问题"
        return self._summary

    def get_messages(self) -> list[dict[str, str]]:
        """返回 OpenAI 格式的消息列表。"""
        messages: list[dict[str, str]] = []
        if self._summary:
            messages.append({"role": "system", "content": self._summary})
        for turn in self._turns:
            messages.append({"role": turn.role, "content": turn.content})
        return messages

    def clear(self) -> None:
        self._turns.clear()
        self._summary = ""

    def to_log(self) -> str:
        """输出对话日志，方便调试。"""
        lines = [f"--- 会话记忆 (turns={len(self._turns)}, tokens={self._total_tokens}) ---"]
        if self._summary:
            lines.append(f"[摘要] {self._summary}")
        for t in self._turns:
            lines.append(f"[{t.role}] {t.content[:100]}{'...' if len(t.content) > 100 else ''}")
        return "\n".join(lines)
