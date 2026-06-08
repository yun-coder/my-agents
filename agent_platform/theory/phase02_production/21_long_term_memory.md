# 第21章 长期记忆：让 Agent 记住用户

> 长期记忆是生产级 Agent 系统的关键能力。没有记忆的 Agent 每次对话都是"初次见面"，无法提供个性化的连续服务。本章深入分析 Mem0、Zep 等记忆存储方案，以及事实记忆、情景记忆的实现策略。

---

## 1. 概念概述

### 1.1 什么是长期记忆

在 AI Agent 系统中，记忆按时间跨度和抽象程度分为三层：

| 记忆类型 | 时间跨度 | 存储形式 | 用途 |
|----------|---------|---------|------|
| 短期记忆 | 当前对话 | 原始消息历史 | 维持上下文 |
| 长期记忆 | 跨会话 | 结构化摘要 + 向量 | 用户画像、偏好 |
| 事实记忆 | 永久 | 知识图谱 / Key-Value | 用户属性、配置 |

**短期记忆**在窗口过期后丢弃，**长期记忆**则持久化存储并在需要时检索。

### 1.2 为什么需要长期记忆

- **个性化**：记住用户偏好（语气偏好、关注领域）
- **连续性**：跨会话引用之前讨论过的内容
- **效率**：不需要每次重新收集用户信息
- **信任**：用户感觉 Agent "了解自己"

### 1.3 长期记忆的核心挑战

1. **相关提取**：从海量记忆中找出当前对话相关的片段
2. **记忆更新**：用户偏好可能变化，需要更新而非追加
3. **隐私保护**：用户需要控制哪些信息被记住
4. **存储效率**：无限增长的记忆需要压缩和过期策略

---

## 2. 核心原理

### 2.1 Mem0 记忆架构

Mem0 是一个专门为 AI Agent 设计的长期记忆层，提供类似人类记忆的"记忆-检索-遗忘"机制：

```python
from mem0 import Memory

# 初始化 Mem0（需要 API Key）
memory = Memory(
    config={
        "version": "v1.1",
        "openai": {
            "api_key": "sk-your-openai-key",
        },
        "embedder": {
            "provider": "openai",
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "url": "http://localhost:6333",
            },
        },
    }
)

# 添加记忆（自动提取关键信息）
result = memory.add(
    messages=[
        {"role": "user", "content": "我叫张三，是一名 Python 开发者"},
        {"role": "assistant", "content": "你好张三！有什么 Python 问题我可以帮你？"},
    ],
    user_id="user-123",
    agent_id="agent-main",
)

# 搜索相关记忆
related = memory.search(
    query="用户是什么职业？",
    user_id="user-123",
)
print(related)  # 返回：张三是一名 Python 开发者

# 获取所有记忆
all_memories = memory.get_all(user_id="user-123")

# 更新记忆
memory.update(memory_id="mem-456", data="张三现在是高级 Python 架构师")

# 删除记忆
memory.delete(memory_id="mem-456")
```

### 2.2 Mem0 的核心机制

Mem0 的工作原理分为四个阶段：

**阶段一：信息提取**
每次对话结束后，Mem0 分析消息对，提取可存储的事实：

```python
# Mem0 内部提取的逻辑（概念说明）
extracted_facts = [
    {
        "fact": "用户是 Python 开发者",
        "category": "职业信息",
        "confidence": 0.95,
        "source": "对话历史",
    },
    {
        "fact": "用户偏好简洁的回答风格",
        "category": "交流偏好",
        "confidence": 0.80,
        "source": "对话历史",
    },
]
```

**阶段二：冲突检测**
检查新事实是否与已有记忆冲突，如果冲突则更新而非追加。

**阶段三：向量化存储**
将事实通过 Embedding 模型转为向量，存入向量数据库。

**阶段四：相关性检索**
根据当前查询的 Embedding 相似度检索最相关的记忆片段。

### 2.3 Zep 记忆存储

Zep 是另一个流行的长期记忆解决方案，提供更丰富的记忆类型：

```python
from zep_cloud.client import Zep
from zep_cloud.types import MemoryMessage

# 初始化 Zep 客户端
zep = Zep(api_key="zep-api-key")

# 添加会话记忆
zep.memory.add(
    session_id="session-123",
    messages=[
        MemoryMessage(
            role="user",
            content="我叫李四，喜欢研究机器学习"
        ),
        MemoryMessage(
            role="assistant",
            content="你好李四！机器学习是一个很棒的领域。"
        ),
    ],
)

# 检索记忆（自动提取事实和摘要）
memory_result = zep.memory.get(
    session_id="session-123",
    min_score=0.7,  # 最小相关性分数
    limit=5,
)

# 获取用户摘要
summary = zep.memory.get_session_summary(session_id="session-123")
print(summary.overview)  # 自动生成的对话题摘要
```

### 2.4 事实记忆 vs 情景记忆

**事实记忆**存储确定的、可验证的信息：

```python
class FactMemory:
    """事实记忆：存储用户确定的属性信息。"""

    def __init__(self):
        self._facts: dict[str, list[dict]] = {}

    def remember(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> None:
        if user_id not in self._facts:
            self._facts[user_id] = []
        # 检查是否有冲突，有则更新
        for fact in self._facts[user_id]:
            if fact["key"] == key:
                fact["value"] = value
                fact["confidence"] = confidence
                fact["updated_at"] = __import__("datetime").datetime.now().isoformat()
                return
        self._facts[user_id].append({
            "key": key,
            "value": value,
            "confidence": confidence,
            "created_at": __import__("datetime").datetime.now().isoformat(),
        })

    def recall(self, user_id: str, key: str) -> str | None:
        facts = self._facts.get(user_id, [])
        for fact in facts:
            if fact["key"] == key:
                return fact["value"]
        return None

    def get_all(self, user_id: str) -> list[dict]:
        return self._facts.get(user_id, [])
```

**情景记忆**存储特定事件的记录，用于参考之前发生过的交互：

```python
class EpisodicMemory:
    """情景记忆：存储特定事件的记录。"""

    def __init__(self):
        self._episodes: dict[str, list[dict]] = {}

    def record(self, user_id: str, event_type: str, summary: str, details: dict | None = None) -> None:
        if user_id not in self._episodes:
            self._episodes[user_id] = []
        self._episodes[user_id].append({
            "type": event_type,
            "summary": summary,
            "details": details or {},
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })
        # 保留最近 100 条情景记忆
        if len(self._episodes[user_id]) > 100:
            self._episodes[user_id] = self._episodes[user_id][-100:]

    def query(self, user_id: str, event_type: str | None = None, limit: int = 10) -> list[dict]:
        episodes = self._facts.get(user_id, []) if hasattr(self, '_facts') else []
        episodes = self._episodes.get(user_id, [])
        if event_type:
            episodes = [e for e in episodes if e["type"] == event_type]
        return episodes[-limit:]
```

### 2.5 记忆检索与更新策略

```python
"""长期记忆管理系统：融合事实记忆、情景记忆和向量记忆。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryItem:
    """单条记忆记录。"""
    id: str
    content: str
    memory_type: str  # "fact" | "episodic" | "preference"
    confidence: float
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


class LongTermMemory:
    """长期记忆管理器：集成多种记忆类型。"""

    def __init__(self, storage_path: str = "./data/memory.json"):
        self._storage_path = storage_path
        self._memories: dict[str, list[MemoryItem]] = {}
        self._load()

    def _load(self) -> None:
        """从文件加载记忆。"""
        import os
        from pathlib import Path
        p = Path(self._storage_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                raw = json.load(f)
                for user_id, items in raw.items():
                    self._memories[user_id] = [MemoryItem(**item) for item in items]

    def _save(self) -> None:
        """保存记忆到文件。"""
        from pathlib import Path
        p = Path(self._storage_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        raw: dict[str, list[dict]] = {}
        for user_id, items in self._memories.items():
            raw[user_id] = [item.__dict__ for item in items]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)

    def add_fact(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> None:
        """添加或更新事实记忆。"""
        if user_id not in self._memories:
            self._memories[user_id] = []

        now = datetime.now().isoformat()
        for item in self._memories[user_id]:
            if item.metadata.get("key") == key and item.memory_type == "fact":
                item.content = value
                item.confidence = confidence
                item.updated_at = now
                self._save()
                return

        self._memories[user_id].append(MemoryItem(
            id=f"fact-{len(self._memories[user_id])}",
            content=value,
            memory_type="fact",
            confidence=confidence,
            created_at=now,
            updated_at=now,
            metadata={"key": key},
        ))
        self._save()

    def add_preference(self, user_id: str, preference: str, category: str = "general") -> None:
        """添加用户偏好。"""
        now = datetime.now().isoformat()
        if user_id not in self._memories:
            self._memories[user_id] = []

        for item in self._memories[user_id]:
            if item.content == preference and item.memory_type == "preference":
                item.updated_at = now
                self._save()
                return

        self._memories[user_id].append(MemoryItem(
            id=f"pref-{len(self._memories[user_id])}",
            content=preference,
            memory_type="preference",
            confidence=0.8,
            created_at=now,
            updated_at=now,
            metadata={"category": category},
        ))
        self._save()

    def query(self, user_id: str, memory_type: str | None = None, limit: int = 20) -> list[MemoryItem]:
        """查询用户的记忆。"""
        items = self._memories.get(user_id, [])
        if memory_type:
            items = [i for i in items if i.memory_type == memory_type]
        # 按更新时间降序
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items[:limit]

    def forget(self, user_id: str, memory_id: str) -> bool:
        """删除指定记忆。"""
        if user_id not in self._memories:
            return False
        before = len(self._memories[user_id])
        self._memories[user_id] = [m for m in self._memories[user_id] if m.id != memory_id]
        self._save()
        return len(self._memories[user_id]) < before

    def build_context(self, user_id: str) -> str:
        """构建记忆上下文，用于注入 System Prompt。"""
        items = self.query(user_id, limit=10)
        if not items:
            return ""
        parts = ["以下是关于用户我知道的信息："]
        for item in items:
            if item.memory_type == "fact":
                parts.append(f"- {item.metadata.get('key', '信息')}：{item.content}")
            elif item.memory_type == "preference":
                parts.append(f"- 偏好：{item.content}")
            else:
                parts.append(f"- 历史：{item.content}")
        return "\n".join(parts)
```

---

## 3. 实战指南

### 3.1 在 Agent 中集成长期记忆

以下代码展示如何将长期记忆集成到项目现有的 Agent 工作流中：

```python
"""在 Agent 工作流中集成长期记忆。"""

from __future__ import annotations

import logging
from typing import Any

from ...agent.graph import AgentWorkflow, AgentState
from ...llm.client import get_llm_client

logger = logging.getLogger(__name__)


class MemoryEnhancedAgent(AgentWorkflow):
    """带长期记忆增强的 Agent 工作流。"""

    def __init__(
        self,
        rag_generator=None,
        *,
        memory_store: LongTermMemory | None = None,
        enable_checkpoint: bool = False,
    ):
        super().__init__(rag_generator, enable_checkpoint=enable_checkpoint)
        self._long_term_memory = memory_store or LongTermMemory()

    def _inject_memory_context(self, state: AgentState) -> AgentState:
        """在 Agent 决策前注入记忆上下文。"""
        user_id = state.get("session_id", "default")
        memory_context = self._long_term_memory.build_context(user_id)
        if memory_context:
            # 在 messages 中插入记忆上下文
            messages = state.get("messages", [])
            messages.insert(0, {
                "role": "system",
                "content": f"## 用户记忆\n{memory_context}\n\n请利用以上信息提供个性化回复。",
            })
            state["messages"] = messages
        return state

    def _extract_memory(self, state: AgentState) -> None:
        """从对话中提取记忆。"""
        user_id = state.get("session_id", "default")
        messages = state.get("messages", [])
        query = state.get("query", "")
        answer = state.get("final_answer", "")

        if not query or not answer:
            return

        # 使用 LLM 提取可记忆的信息
        llm = get_llm_client()
        extraction_prompt = [
            {
                "role": "system",
                "content": """从以下对话中提取可以长期记忆的信息，包括：
1. 用户的事实信息（姓名、职业、地点等）
2. 用户偏好（风格偏好、兴趣领域等）
以 JSON 数组格式返回，每项包含 type 和 content。""",
            },
            {
                "role": "user",
                "content": f"用户问题：{query}\n助手回答：{answer}",
            },
        ]
        try:
            response = llm.chat(extraction_prompt, temperature=0.0)
            import json
            extracted = json.loads(response)
            for item in extracted:
                if item.get("type") == "fact":
                    key, value = item["content"].split("：", 1)
                    self._long_term_memory.add_fact(user_id, key, value)
                elif item.get("type") == "preference":
                    self._long_term_memory.add_preference(user_id, item["content"])
        except Exception as e:
            logger.warning("记忆提取失败：%s", e)

    def run(self, query: str, session_id: str = "default") -> AgentState:
        """执行带记忆增强的工作流。"""
        state = super().run(query, session_id)
        # 提取记忆
        self._extract_memory(state)
        return state
```

### 3.2 记忆注入 System Prompt

将长期记忆注入到 Agent 的 System Prompt 中，实现个性化对话：

```python
def build_personalized_prompt(user_id: str, memory: LongTermMemory) -> str:
    """构建个性化 System Prompt。"""
    facts = memory.query(user_id, memory_type="fact")
    preferences = memory.query(user_id, memory_type="preference")
    episodes = memory.query(user_id, memory_type="episodic", limit=3)

    prompt_parts = ["你是一个智能助手，以下是关于用户的信息："]

    if facts:
        prompt_parts.append("\n【用户信息】")
        for f in facts:
            prompt_parts.append(f"- {f.metadata.get('key', '')}：{f.content}")

    if preferences:
        prompt_parts.append("\n【用户偏好】")
        for p in preferences:
            prompt_parts.append(f"- {p.content}")

    if episodes:
        prompt_parts.append("\n【最近交互】")
        for e in episodes:
            prompt_parts.append(f"- {e.content}")

    prompt_parts.append("\n请基于以上信息提供个性化回复。")
    return "\n".join(prompt_parts)
```

---

## 4. 最佳实践

1. **分层记忆架构**：短期记忆（对话窗口）+ 长期记忆（向量数据库）+ 事实记忆（Key-Value 存储），三层配合使用。

2. **置信度评分**：每条记忆附带置信度，低置信度的记忆在上下文紧张时优先丢弃。

3. **定期更新**：用户信息会变化，设计记忆更新机制而非简单追加。

4. **隐私控制**：提供忘记接口（forget API），允许用户删除自己的记忆数据。

5. **记忆压缩**：定期将多条短记忆合并为一条摘要记忆，减少存储和提高检索效率。

6. **注入时机**：记忆上下文在用户提问后、LLM 回复前注入，避免干扰对话流程。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| 记忆污染 | 一次错误交互污染了长期记忆 | 加入人工审核机制，高置信度才存储 |
| 隐私泄露 | 记忆被未授权用户访问 | 严格按 user_id 隔离，加密存储 |
| 记忆过载 | 注入太多记忆导致 Token 超限 | 限制注入条数（建议不超过 10 条） |
| 陈旧记忆 | 用户偏好已改变但保留了旧记忆 | 每次使用时更新置信度，低于阈值则丢弃 |
| 幻觉增强 | Agent 基于错误记忆产生了幻觉 | 记忆注入时标注置信度，Agent 知道哪些信息不确定 |
| 存储爆炸 | 无限增长导致性能下降 | 设置最大记忆条数，使用 LRU 淘汰策略 |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| Mem0 Cloud | 是 | 云计算版需要 Mem0 API Key |
| Mem0 开源版 | 否 | 可本地部署，无需 Key |
| Zep Cloud | 是 | 需要 Zep API Key |
| Zep 开源版 | 否 | 可自托管，无需 Key |
| 自建 LongTermMemory | 否 | 本地文件存储，无需 Key |
| 记忆提取 LLM | 是 | 用于从对话中提取记忆片段的 LLM 调用 |

**注意**：Mem0 和 Zep 都有开源版本和云版本。开源版可本地部署，完全免费，但需要自行管理基础设施。

---

## 7. 技术关系

```
用户对话
    │
    ├──→ 短期记忆（当前对话消息）
    │
    ├──→ 记忆提取（LLM 分析对话 → 提取事实/偏好）
    │
    ├──→ 长期记忆存储
    │   ├── Mem0 / Zep（向量数据库）
    │   ├── 事实记忆（Key-Value）
    │   └── 情景记忆（事件日志）
    │
    └──→ 记忆检索（下次对话时注入 System Prompt）
         │
         ▼
    个性化 Agent 回复
```

---

## 8. 验收清单

- [ ] 理解短期记忆、长期记忆和事实记忆的区别
- [ ] 学会使用 Mem0 的 add / search / update / delete 基本操作
- [ ] 了解 Zep 的会话记忆和摘要功能
- [ ] 掌握从对话中自动提取记忆的方法
- [ ] 理解记忆的冲突检测和更新策略
- [ ] 能够将长期记忆注入 Agent 的 System Prompt
- [ ] 理解置信度评分的作用和应用
- [ ] 掌握隐私控制机制（forget API）
- [ ] 了解 Mem0 和 Zep 的开源与云版本差异
- [ ] 能够设计适合自身场景的分层记忆架构

---

## 9. 学习资源

- Mem0 官方文档：https://docs.mem0.ai/
- Mem0 开源仓库：https://github.com/mem0ai/mem0
- Zep 官方文档：https://help.getzep.com/
- Zep 开源仓库：https://github.com/getzep/zep
- 长期记忆模式：https://blog.langchain.dev/memory/
- 向量数据库对比：https://vdbs.superpulsar.ai/
- 项目源码参考：agent_platform/src/agent/memory.py
