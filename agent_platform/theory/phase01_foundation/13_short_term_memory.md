# 13 短期记忆：对话上下文管理

## 一、概念概述

### 1.1 什么是 AI Agent 的短期记忆

短期记忆（Short-Term Memory）在 AI Agent 中指的是模型在当前会话中保持的历史对话信息。它让 Agent 能够理解对话的上下文、记住用户之前提到的信息、维持对话的连贯性。

与人类认知类似，AI 的短期记忆也有两个关键限制：
- **容量限制**：LLM 的上下文窗口有限（4K、8K、16K、32K、128K tokens 不等）
- **时效性**：较久远的信息可能被截断或压缩

### 1.2 短期记忆 vs 长期记忆

| 维度 | 短期记忆 | 长期记忆 |
|------|---------|---------|
| 存储位置 | LLM 上下文窗口 / 内存 | 向量数据库 / 关系数据库 |
| 持久性 | 会话结束即消失 | 跨会话持久保存 |
| 访问方式 | 直接作为上下文注入 | 通过检索获取 |
| 容量 | 有限（受上下文窗口限制） | 几乎无限 |
| 典型实现 | 滑动窗口、摘要压缩 | 向量存储 + RAG |
| 管理策略 | Token 预算、裁剪 | 索引、分片、归档 |

### 1.3 为什么需要短期记忆管理

- **Token 成本**：LLM 按 Token 计费，历史消息越多成本越高
- **上下文窗口溢出**：超出窗口限制会导致错误或截断
- **注意力稀释**：过长的上下文中，模型对重要信息的注意力下降（Lost-in-the-Middle 问题）
- **延迟增加**：输入越长，LLM 的推理延迟越高

---

## 二、核心原理

### 2.1 滑动窗口（Sliding Window）

滑动窗口是最简单、最常用的短期记忆策略：只保留最近 N 轮对话，丢弃较早的历史。

```python
# 滑动窗口实现
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ConversationTurn:
    """一轮对话。"""
    role: str  # "user" 或 "assistant"
    content: str
    tokens: int = 0  # 预估 token 数


class SlidingWindowMemory:
    """基于滑动窗口的短期记忆。"""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self._turns: deque[ConversationTurn] = deque()

    def add(self, role: str, content: str) -> None:
        """添加一轮对话。"""
        token_estimate = len(content) // 3  # 中文约 1.5 字/token
        self._turns.append(ConversationTurn(role, content, token_estimate))
        self._trim()

    def _trim(self) -> None:
        """根据 max_turns 裁剪历史。"""
        while len(self._turns) > self.max_turns:
            self._turns.popleft()

    def get_messages(self) -> List[Dict[str, str]]:
        """返回 OpenAI 格式的消息列表。"""
        return [
            {"role": t.role, "content": t.content}
            for t in self._turns
        ]

    def clear(self) -> None:
        self._turns.clear()
```

### 2.2 摘要压缩（Summary Compression）

当对话历史超出窗口时，将较早的对话生成摘要，保留最关键的信息。

```python
# 摘要压缩记忆
class SummaryCompressionMemory:
    """带摘要压缩的短期记忆。"""

    def __init__(self, max_turns: int = 20, max_tokens: int = 4000,
                 llm_client=None):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self._llm = llm_client
        self._turns: deque[ConversationTurn] = deque()
        self._summary: str = ""

    def add(self, role: str, content: str) -> None:
        token_estimate = len(content) // 3
        self._turns.append(ConversationTurn(role, content, token_estimate))
        self._trim()

    def _trim(self) -> None:
        # 按轮数裁剪
        while len(self._turns) > self.max_turns:
            removed = self._turns.popleft()
            self._summary = self._compress(removed)

        # 按 Token 数裁剪
        while self._total_tokens > self.max_tokens and len(self._turns) > 2:
            removed = self._turns.popleft()
            self._summary = self._compress(removed)

    @property
    def _total_tokens(self) -> int:
        return sum(t.tokens for t in self._turns)

    def _compress(self, turn: ConversationTurn) -> str:
        """压缩一轮对话为摘要。"""
        if self._llm:
            # 使用 LLM 生成摘要
            summary = self._llm.chat([
                {"role": "system",
                 "content": "用一句话概括以下对话的核心信息："},
                {"role": "user", "content": turn.content},
            ])
            return f"{self._summary}\n- {summary}" if self._summary else f"- {summary}"
        else:
            # 简单截取作为摘要
            if not self._summary:
                return f"前情提要：用户问了关于{turn.content[:30]}...的问题"
            return self._summary

    def get_messages(self) -> List[Dict[str, str]]:
        """返回带摘要的消息列表。"""
        messages = []
        if self._summary:
            messages.append({"role": "system", "content": self._summary})
        for turn in self._turns:
            messages.append({"role": turn.role, "content": turn.content})
        return messages
```

参考 `agent_platform/src/agent/memory.py` 中的 ConversationMemory 实现：

```python
# 平台实际使用的对话记忆
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    """一轮对话。"""
    role: str
    content: str
    tokens: int = 0


@dataclass
class ConversationMemory:
    """会话级别的对话记忆。

    用法:
        mem = ConversationMemory(max_turns=20, max_tokens=4000)
        mem.add("user", "什么是 RAG？")
        mem.add("assistant", "RAG 是检索增强生成...")
        messages = mem.get_messages()
    """

    max_turns: int = 20
    max_tokens: int = 4000
    _turns: deque[ConversationTurn] = field(default_factory=deque)
    _summary: str = ""

    def add(self, role: str, content: str) -> None:
        token_estimate = len(content) // 3
        self._turns.append(ConversationTurn(role, content, token_estimate))
        self._trim()

    def _trim(self) -> None:
        # 按轮数裁剪
        while len(self._turns) > self.max_turns:
            removed = self._turns.popleft()
            self._summary = self._update_summary(removed)

        # 按 Token 数裁剪
        while self._total_tokens > self.max_tokens and len(self._turns) > 2:
            removed = self._turns.popleft()
            self._summary = self._update_summary(removed)

    @property
    def _total_tokens(self) -> int:
        return sum(t.tokens for t in self._turns)

    def _update_summary(self, turn: ConversationTurn) -> str:
        if not self._summary:
            return f"前情提要：用户问了关于{turn.content[:30]}...的问题"
        return self._summary

    def get_messages(self) -> list[dict[str, str]]:
        messages = []
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
        lines = [
            f"--- 会话记忆 (turns={len(self._turns)}, "
            f"tokens={self._total_tokens}) ---"
        ]
        if self._summary:
            lines.append(f"[摘要] {self._summary}")
        for t in self._turns:
            content = t.content[:100]
            if len(t.content) > 100:
                content += "..."
            lines.append(f"[{t.role}] {content}")
        return "\n".join(lines)
```

### 2.3 Token 预算管理

Token 预算管理是确保上下文不溢出的核心技术。需要精确计算每个部分的 Token 消耗。

```python
# Token 预算管理器
class TokenBudgetManager:
    """Token 预算管理，防止上下文溢出。"""

    # 不同组件的预算分配比例
    BUDGET_RATIOS = {
        "system_prompt": 0.05,     # 系统提示词
        "conversation": 0.35,      # 对话历史
        "retrieval_results": 0.40, # 检索结果
        "query": 0.05,             # 当前查询
        "response": 0.10,          # 预留生成空间
        "buffer": 0.05,            # 缓冲余量
    }

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def get_budget(self, component: str) -> int:
        """获取指定组件的 Token 预算。"""
        ratio = self.BUDGET_RATIOS.get(component, 0.1)
        return int(self.max_tokens * ratio)

    def trim_conversation(self, messages: list, max_tokens: int) -> list:
        """裁剪对话历史以符合预算。"""
        tokens = 0
        trimmed = []
        for msg in reversed(messages):
            msg_tokens = len(msg["content"]) // 3
            if tokens + msg_tokens > max_tokens:
                break
            trimmed.insert(0, msg)
            tokens += msg_tokens
        return trimmed

    def estimate_tokens(self, text: str) -> int:
        """粗略估计文本的 Token 数。"""
        # 中文约 1.5 字符/token，英文约 4 字符/token
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        ascii_chars = len(text) - chinese_chars
        return chinese_chars // 2 + ascii_chars // 4
```

### 2.4 上下文溢出处理

当对话历史或检索结果不可避免地超出上下文窗口时，需要一套降级策略。

```python
# 上下文溢出处理器
class ContextOverflowHandler:
    """上下文溢出时的降级策略。"""

    def __init__(self, memory, llm_client=None):
        self._memory = memory
        self._llm = llm_client

    def handle_overflow(self, current_query: str,
                        retrieval_results: list) -> dict:
        """处理上下文溢出，返回处理后的结果。"""
        total_tokens = self._estimate_total_tokens(
            current_query, retrieval_results
        )
        max_tokens = 8000

        if total_tokens <= max_tokens:
            # 未溢出，正常处理
            return {"strategy": "normal", "query": current_query}

        if total_tokens > max_tokens * 1.5:
            # 严重溢出：强制压缩历史
            self._memory.clear()
            self._memory.add("system", "对话历史已被压缩以节省空间。")

            # 减少检索结果数量
            retrieval_results = retrieval_results[:3]

            return {
                "strategy": "aggressive_compress",
                "query": current_query,
                "retrieval_results": retrieval_results,
            }
        else:
            # 轻度溢出：裁剪最旧的历史
            while (self._estimate_total_tokens(
                    current_query, retrieval_results) > max_tokens
                   and len(self._memory._turns) > 2):
                self._memory._turns.popleft()

            return {"strategy": "trim", "query": current_query}

    def _estimate_total_tokens(self, query: str,
                                results: list) -> int:
        """估算总体 Token 消耗。"""
        tokens = len(query) // 3
        for msg in self._memory.get_messages():
            tokens += len(msg["content"]) // 3
        for r in results:
            tokens += len(r.get("text", "")) // 3
        return tokens
```

### 2.5 Lost-in-the-Middle 问题

研究表明，LLM 对长上下文中间部分的信息记忆最差，而对开头和结尾的信息记忆最好。这要求在构建上下文时，将最重要的信息放在开头或结尾。

```python
# 优化上下文排列
def optimize_context_order(retrieval_results: list,
                           top_k: int = 5) -> list:
    """优化检索结果的排列顺序：最重要的放在开头和结尾。"""
    if len(retrieval_results) <= 3:
        return retrieval_results

    # 将最相关的结果放在开头和结尾
    sorted_results = sorted(
        retrieval_results,
        key=lambda x: x.get("relevance_score", 0),
        reverse=True,
    )

    # 最重要的在开头，次重要的在结尾
    optimized = []
    optimized.append(sorted_results[0])  # 最重要的放到开头
    optimized.extend(sorted_results[1:top_k-1])  # 中间的
    if len(sorted_results) > top_k - 1:
        optimized.append(sorted_results[top_k-1])  # 次重要的放到结尾

    return optimized
```

---

## 三、实战指南

### 3.1 集成到 Agent 工作流

参考 `agent_platform/src/agent/graph.py` 中记忆与 Agent 的集成方式：

```python
# 将记忆集成到 LangGraph Agent 中
class MemoryAwareAgent:
    """带记忆管理的 Agent。"""

    def __init__(self, max_turns: int = 20, max_tokens: int = 4000):
        self.memory = ConversationMemory(
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        self.budget_manager = TokenBudgetManager()
        self.overflow_handler = ContextOverflowHandler(self.memory)

    def chat(self, query: str) -> str:
        # 1. 处理上下文溢出
        overflow_result = self.overflow_handler.handle_overflow(
            query, retrieval_results=[]
        )

        # 2. 获取记忆中的历史消息
        history = self.memory.get_messages()

        # 3. Token 预算裁剪
        budget = self.budget_manager.get_budget("conversation")
        history = self.budget_manager.trim_conversation(history, budget)

        # 4. 构建最终消息列表
        messages = history + [
            {"role": "user", "content": overflow_result["query"]}
        ]

        # 5. 调用 LLM
        response = self._llm.chat(messages)

        # 6. 保存到记忆
        self.memory.add("user", query)
        self.memory.add("assistant", response)

        return response
```

### 3.2 多会话管理

```python
# 会话管理器
class SessionManager:
    """管理多个会话的记忆。"""

    def __init__(self):
        self._sessions: dict[str, ConversationMemory] = {}

    def get_session(self, session_id: str) -> ConversationMemory:
        """获取或创建会话记忆。"""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory(
                max_turns=20,
                max_tokens=4000,
            )
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        """清除会话记忆。"""
        if session_id in self._sessions:
            self._sessions[session_id].clear()

    def cleanup_old_sessions(self, max_sessions: int = 100) -> None:
        """清理旧会话，防止内存泄漏。"""
        if len(self._sessions) > max_sessions:
            # 保留最新的 max_sessions 个会话
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: id(x[1]),  # 简化处理
            )
            self._sessions = dict(sorted_sessions[-max_sessions:])
```

### 3.3 对话日志与调试

```python
# 记忆状态可视化
def visualize_memory(memory: ConversationMemory) -> str:
    """将记忆状态可视化为易于阅读的格式。"""
    output = []
    output.append("=" * 50)
    output.append(f"对话记忆诊断")
    output.append(f"  总轮次: {len(memory._turns)}")
    output.append(f"  总 Token: {memory._total_tokens}")
    output.append(f"  最大轮次: {memory.max_turns}")
    output.append(f"  最大 Token: {memory.max_tokens}")
    output.append(f"  摘要: {memory._summary[:100] if memory._summary else '无'}")
    output.append("-" * 50)
    for i, turn in enumerate(memory._turns):
        content = turn.content[:80]
        if len(turn.content) > 80:
            content += "..."
        output.append(f"  [{i}] {turn.role} ({turn.tokens}tok): {content}")
    output.append("=" * 50)
    return "\n".join(output)

# 输出示例
mem = ConversationMemory(max_turns=5)
mem.add("user", "什么是 RAG？")
mem.add("assistant", "RAG 是检索增强生成...")
print(visualize_memory(mem))
```

---

## 四、最佳实践

### 4.1 记忆策略选择

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 简单问答 | 滑动窗口（10 轮） | 轻量级，无需摘要 |
| 复杂对话 | 滑动窗口 + 摘要压缩 | 保留关键上下文 |
| 长文档处理 | Token 预算管理 | 防止上下文溢出 |
| 多轮工具调用 | 滑动窗口（20 轮） | 保留工具调用记录 |
| 高并发服务 | 滑动窗口 + 超时清理 | 防止内存泄漏 |

### 4.2 Token 估算精度

```python
# 使用 tiktoken 精确计算 Token 数
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """使用 tiktoken 精确计算 Token 数。"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # 降级为粗略估计
        return len(text) // 3
```

### 4.3 记忆持久化

```python
import json
from pathlib import Path

class PersistentMemory(ConversationMemory):
    """可持久化的对话记忆。"""

    def save_to_file(self, filepath: str) -> None:
        data = {
            "max_turns": self.max_turns,
            "max_tokens": self.max_tokens,
            "summary": self._summary,
            "turns": [
                {"role": t.role, "content": t.content, "tokens": t.tokens}
                for t in self._turns
            ],
        }
        Path(filepath).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_from_file(cls, filepath: str) -> "PersistentMemory":
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        mem = cls(max_turns=data["max_turns"], max_tokens=data["max_tokens"])
        mem._summary = data["summary"]
        for t in data["turns"]:
            mem._turns.append(ConversationTurn(**t))
        return mem
```

---

## 五、常见陷阱

### 5.1 未设置 Token 上限

**陷阱**：对话轮数无限增长，最终超出上下文窗口或耗尽内存。

**解决**：始终设置 max_turns 和 max_tokens 上限。

### 5.2 摘要压缩丢失关键信息

**陷阱**：压缩后的摘要丢失了用户提到的关键信息（如名字、数字、偏好）。

**解决**：在压缩时保留关键信息，考虑使用 LLM 进行智能摘要而非简单截取。

### 5.3 多会话未隔离

**陷阱**：多个用户共享同一个记忆空间，导致历史混乱。

**解决**：使用 SessionManager 按 session_id 隔离。

### 5.4 记忆对象内存泄漏

**陷阱**：长期运行的服务器中，未清理的会话记忆对象堆积导致 OOM。

**解决**：定期清理过期会话，设置最大会话数限制。

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| 滑动窗口 | 否 | 纯内存操作 |
| 摘要压缩（截取） | 否 | 简单字符串截取 |
| 摘要压缩（LLM） | 是 | 使用 LLM 生成摘要 |
| Token 计数（tiktoken） | 否 | 本地计算 |
| Token 计数（粗略） | 否 | 纯数学计算 |
| 记忆持久化 | 否 | 文件 I/O 操作 |

---

## 七、技术关系

```text
用户查询
    |
    v
+----------------+
| 短期记忆管理    |
|                |
|  +----------+  |     +-------------+
|  | 滑动窗口  |  |     | Token 预算  |
|  | (轮数控制)|  |     | 管理        |
|  +----------+  |     +-------------+
|        |       |            |
|  +----------+  |     +-------------+
|  | 摘要压缩  |  |     | 溢出处理    |
|  +----------+  |     +-------------+
+----------------+
    |
    v
+----------------+     +----------------+
| LangGraph      |     | FastAPI        |
| Agent 工作流   |     | API 服务       |
| (graph.py)     |     | (routes.py)   |
+----------------+     +----------------+
    |                         |
    v                         v
+----------------+     +----------------+
| LLM 调用       |     | 记忆持久化     |
| (带上下文)     |     | (JSON / DB)   |
+----------------+     +----------------+
```

---

## 八、验收清单

- [ ] 理解短期记忆与长期记忆的区别
- [ ] 掌握滑动窗口策略的实现（轮数裁剪）
- [ ] 理解摘要压缩策略及其适用场景
- [ ] 掌握 Token 预算管理的分配策略
- [ ] 理解上下文溢出的处理方式（降级、强制压缩）
- [ ] 了解 Lost-in-the-Middle 问题及优化策略
- [ ] 能实现多会话隔离管理
- [ ] 理解记忆持久化的必要性
- [ ] 掌握对话日志和调试分析方法
- [ ] 能集成记忆管理到 Agent 工作流

---

## 九、学习资源

- **LLM 上下文窗口研究**: "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al., 2023)
- **LangChain 记忆模块**: https://python.langchain.com/docs/modules/memory/
- **OpenAI tiktoken**: https://github.com/openai/tiktoken
- **平台参考代码**: agent_platform/src/agent/memory.py (ConversationMemory 实现)
- **MemGPT / Letta**: https://github.com/letta-ai/letta (长期记忆管理框架)
