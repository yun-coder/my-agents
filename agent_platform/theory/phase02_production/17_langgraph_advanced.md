# 第17章 LangGraph 深入：生产级 Agent 编排

> LangGraph 是 LangChain 生态中用于构建有状态、多步骤 Agent 工作流的图编排框架。本章深入探讨生产环境中 LangGraph 的高级特性，包括持久化检查点、人机交互模式、子图并行与错误恢复。

---

## 1. 概念概述

### 1.1 什么是 LangGraph

LangGraph 是一个基于状态图（StateGraph）的 Agent 编排框架，允许开发者将 Agent 行为建模为有向图。每个节点代表一个计算步骤（如 LLM 调用、工具执行），边代表状态转移逻辑。与简单的链式调用不同，LangGraph 支持循环（tool-calling 循环）、条件分支和并行执行。

### 1.2 与普通 LangChain Chain 的区别

| 维度 | LangChain Chain | LangGraph |
|------|----------------|-----------|
| 流程结构 | 线性 DAG，无环 | 有向图，支持循环 |
| 状态管理 | 隐式传递 | 显式的 State 对象 |
| 持久化 | 无内置支持 | 原生 Checkpoint 接口 |
| 人机交互 | 不支持 | interrupt/resume 机制 |
| 并行 | 需手动实现 | Send API 内置支持 |

### 1.3 核心概念速览

- **StateGraph**：定义状态类型和图结构的基类
- **Node**：图中每个处理步骤，接收并返回 State
- **Edge**：节点之间的连接，可以是条件边或普通边
- **Checkpointer**：负责在每一步保存 State 快照
- **Interrupt**：在指定断点暂停执行，等待外部输入恢复
- **Command**：用于中断恢复时传递外部数据

---

## 2. 核心原理

### 2.1 Checkpoint 持久化机制

LangGraph 的检查点机制是生产部署的核心。每次节点执行完毕后，Checkpointer 将当前 State 序列化保存到后端存储。支持三种后端：

```python
# 内存检查点（开发/测试用，进程重启后丢失）
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# SQLite 检查点（单机部署推荐）
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# PostgreSQL 检查点（生产多实例推荐）
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/langgraph"
)
```

检查点保存的内容包括：
- 完整的 State 字典（messages, iteration_count, tool_log 等）
- 节点执行上下文（当前正在执行的节点）
- 父图/子图嵌套关系（用于子图场景）
- 元数据（时间戳、图版本号）

### 2.2 interrupt() 与 Command 机制

interrupt() 是 LangGraph 实现人机交互的核心 API。当 Agent 执行到需要人类确认或补充信息的节点时，可以调用 interrupt() 暂停整个图，等待外部通过 Command(resume=...) 恢复。

```python
from langgraph.types import interrupt, Command

def human_review_node(state: AgentState) -> AgentState:
    """人类审核节点：暂停等待人工确认。"""
    approval = interrupt({
        "question": "是否执行以下工具调用？",
        "tool_calls": state.get("pending_tool_calls", []),
    })
    if approval == "approve":
        state["human_approved"] = True
    else:
        state["human_approved"] = False
        state["feedback"] = approval
    return state
```

调用方通过以下方式恢复：

```python
thread = {"configurable": {"thread_id": "session-123"}}
graph.invoke(
    Command(resume="approve"),
    config=thread,
)
```

### 2.3 Human-in-the-Loop 模式

LangGraph 支持三种人机交互模式：

**模式一：提前审批（Before Execution）**
在工具调用节点前插入审批节点，人类批准后才执行工具。

**模式二：执行后审核（After Execution）**
工具执行完成后，结果需要人工审核再决定是否继续。

**模式三：动态断点（Dynamic Breakpoint）**
根据运行时条件动态设置断点位置。

```python
# 编译图时设置静态断点
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["tools"],
    interrupt_after=["agent"],
)
```

### 2.4 子图（Subgraph）

子图允许将复杂工作流拆分为可复用的子模块。子图拥有自己的 State 定义，可以从父图接收输入并向上返回结果。

```python
from langgraph.graph import StateGraph

subgraph_builder = StateGraph(AgentState)
subgraph_builder.add_node("tool_agent", tool_agent_node)
subgraph_builder.add_node("executor", tool_executor_node)
subgraph_builder.add_edge("tool_agent", "executor")
subgraph_builder.add_edge("executor", END)
subgraph = subgraph_builder.compile()

main_builder = StateGraph(AgentState)
main_builder.add_node("router", router_node)
main_builder.add_node("tool_subgraph", subgraph)
```

### 2.5 Send API 并行执行

Send API 允许将多个任务分发到同一个节点的不同实例，实现真正的并行执行：

```python
from langgraph.types import Send

def continue_to_tools(state: AgentState):
    tool_calls = state.get("tool_calls", [])
    return [
        Send("execute_tool", {"tool_call": tc, "session_id": state["session_id"]})
        for tc in tool_calls
    ]

builder.add_conditional_edges(
    "route_tools",
    continue_to_tools,
    path_map=[("execute_tool", "execute_tool") for _ in range(10)],
)
builder.add_edge("execute_tool", "aggregate")
```

---

## 3. 实战指南

### 3.1 生产级 Checkpoint 配置

以下代码基于项目中 graph.py 的模式，增加了完整的持久化支持：

```python
"""生产级 LangGraph 工作流：支持 PostgreSQL 持久化 + 中断恢复。"""
from __future__ import annotations
import json
import logging
from typing import Any, Literal, TypedDict
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt, Command
from ...llm.client import get_llm_client
from ...rag.generator import RAGGenerator
from ...agent.tools import TOOL_DEFINITIONS, TOOL_EXECUTORS
from ...agent.memory import ConversationMemory

logger = logging.getLogger(__name__)
MAX_TOOL_ITERATIONS = 5


class ProductionAgentState(TypedDict, total=False):
    messages: list[dict[str, Any]]
    query: str
    session_id: str
    iteration_count: int
    final_answer: str
    tool_log: list[str]
    error: str
    pending_tool_calls: list[dict]
    human_approved: bool | None
    human_feedback: str


class ProductionAgentWorkflow:
    """生产级工作流：支持中断、恢复和持久化。"""

    def __init__(
        self,
        rag_generator: RAGGenerator | None = None,
        *,
        pg_conn_string: str = "",
    ):
        self._llm = get_llm_client()
        self._rag = rag_generator
        builder = StateGraph(ProductionAgentState)
        builder.add_node("agent", self._agent_node)
        builder.add_node("human_review", self._human_review_node)
        builder.add_node("tools", self._tool_node)
        builder.add_node("rag", self._rag_node)
        builder.set_entry_point("agent")
        builder.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {"human_review": "human_review", "tools": "tools", "rag": "rag", "end": END},
        )
        builder.add_conditional_edges(
            "human_review",
            self._route_after_review,
            {"tools": "tools", "agent": "agent"},
        )
        builder.add_edge("tools", "agent")
        builder.add_edge("rag", "agent")
        self._checkpointer = PostgresSaver.from_conn_string(pg_conn_string)
        self._graph = builder.compile(
            checkpointer=self._checkpointer,
            interrupt_before=["human_review"],
        )

    def run(
        self, query: str, session_id: str = "default", *, resume: str | None = None
    ) -> dict[str, Any]:
        config = {"configurable": {"thread_id": session_id}}
        if resume:
            return self._graph.invoke(Command(resume=resume), config=config)
        initial_state: ProductionAgentState = {
            "messages": [],
            "query": query,
            "session_id": session_id,
            "iteration_count": 0,
            "final_answer": "",
            "tool_log": [],
            "error": "",
            "pending_tool_calls": [],
            "human_approved": None,
            "human_feedback": "",
        }
        return self._graph.invoke(initial_state, config=config)

    def get_state(self, session_id: str) -> dict:
        config = {"configurable": {"thread_id": session_id}}
        return self._graph.get_state(config)

    def _agent_node(self, state: ProductionAgentState) -> ProductionAgentState:
        if state.get("iteration_count", 0) >= MAX_TOOL_ITERATIONS:
            state["final_answer"] = "已达到最大迭代次数。"
            return state
        messages = [{"role": "system", "content": "你是一个智能助手。"}]
        history = state.get("messages", [])
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": state["query"]})
        try:
            response = self._llm.chat_with_tools(messages, TOOL_DEFINITIONS)
            choice = response.choices[0]
            if choice.message.tool_calls:
                state["messages"] = messages + [choice.message.model_dump()]
                state["iteration_count"] = state.get("iteration_count", 0) + 1
                state["pending_tool_calls"] = [
                    tc.model_dump() for tc in choice.message.tool_calls
                ]
            elif choice.message.content:
                content = choice.message.content
                if "需要搜索知识库" in content:
                    state["iteration_count"] = state.get("iteration_count", 0) + 1
                else:
                    state["final_answer"] = content
        except Exception as e:
            logger.error("Agent 错误：%s", e)
            state["error"] = str(e)
        return state

    def _human_review_node(self, state: ProductionAgentState) -> ProductionAgentState:
        if state.get("human_approved") is not None:
            return state
        result = interrupt({
            "pending_calls": state.get("pending_tool_calls", []),
            "iteration": state.get("iteration_count", 0),
        })
        if isinstance(result, dict):
            state["human_approved"] = result.get("approved", False)
            state["human_feedback"] = result.get("feedback", "")
        else:
            state["human_approved"] = result == "approve"
        return state

    def _tool_node(self, state: ProductionAgentState) -> ProductionAgentState:
        messages = state.get("messages", [])
        if not messages:
            return state
        last_message = messages[-1]
        tool_calls = last_message.get("tool_calls", [])
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            func_args = json.loads(tc["function"]["arguments"])
            executor = TOOL_EXECUTORS.get(func_name)
            if executor:
                args_list = list(func_args.values())
                result = executor(*args_list) if args_list else executor()
                state.setdefault("tool_log", []).append(
                    f"[{func_name}] -> {str(result)[:100]}"
                )
        state["pending_tool_calls"] = []
        return state

    def _rag_node(self, state: ProductionAgentState) -> ProductionAgentState:
        query = state.get("query", "")
        if self._rag:
            answer = self._rag.generate(query)
            state["messages"] = state.get("messages", []) + [
                {"role": "system", "content": f"知识库结果：{', '.join(answer.sources)}"}
            ]
        return state

    def _route_after_agent(
        self, state: ProductionAgentState
    ) -> Literal["human_review", "tools", "rag", "end"]:
        if state.get("final_answer") or state.get("error"):
            return "end"
        if state.get("pending_tool_calls"):
            return "human_review"
        messages = state.get("messages", [])
        if messages and messages[-1].get("tool_calls"):
            return "tools"
        return "end"

    def _route_after_review(
        self, state: ProductionAgentState
    ) -> Literal["tools", "agent"]:
        if state.get("human_approved"):
            return "tools"
        state["pending_tool_calls"] = []
        return "agent"
```

### 3.2 客户端调用示例

```python
wf = ProductionAgentWorkflow(pg_conn_string="postgresql://localhost:5432/langgraph")
result = wf.run("帮我搜索并计算一些数据", session_id="session-001")

state = wf.get_state("session-001")
if state.next:
    print("待批准的调用：", state.values.get("pending_tool_calls"))

result = wf.run(
    "帮我搜索并计算一些数据",
    session_id="session-001",
    resume="approve",
)
```

### 3.3 动态断点示例

```python
def check_for_breakpoint(state: AgentState) -> None:
    tool_calls = state.get("tool_calls", [])
    for tc in tool_calls:
        if tc["function"]["name"] == "delete_file":
            interrupt({
                "type": "safety_check",
                "message": f"即将删除文件，请确认操作",
                "tool_call": tc,
            })
```

---

## 4. 最佳实践

1. **选择合适的 Checkpoint 后端**：单机开发用 SQLite，多实例生产用 PostgreSQL。MemorySaver 仅用于单元测试。

2. **线程安全设计**：多实例部署时，PostgresSaver 通过数据库事务保证状态一致性。每个会话使用唯一 thread_id。

3. **中断粒度控制**：不是每个工具调用都需要人工审核。只在高风险操作（删除、写文件、支付）或 Agent 置信度低时设置断点。

4. **子图复用**：将通用功能（如工具执行、RAG 检索）封装为子图，在不同工作流中复用。

5. **状态最小化**：State 中只保存需要跨节点共享的数据，临时计算结果用完即清理，减少 checkpoint 存储开销。

6. **超时与重试**：为每个节点设置超时时间，避免 LLM 调用卡死整个工作流。

7. **日志结构化**：在 tool_log 中记录每次工具调用的输入输出，便于审计和调试。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| State 突变问题 | 在节点中直接修改 state 嵌套字段导致不一致 | 始终返回新的 state 对象而非原地修改 |
| Checkpoint 序列化失败 | state 中包含不可序列化的对象（如数据库连接） | State 中只保存 JSON 可序列化的基础类型 |
| 中断后重复执行 | 恢复时未正确处理已完成节点的幂等性 | 在节点开头检查是否已执行过 |
| Send API 风扇过大 | 并行发起的子任务过多导致资源耗尽 | 限制并行数（建议不超过 10） |
| 子图状态泄漏 | 子图修改了父图的 state 引用 | 子图使用独立的 State 类型 |
| thread_id 冲突 | 多实例使用相同的 thread_id 导致状态混淆 | 使用 UUID 或 user_id + timestamp 生成唯一 ID |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| LangGraph 核心库 | 否 | 开源框架，无需 Key |
| LLM 客户端（graph.py） | 是 | 需要 OpenAI 兼容 API Key |
| PostgreSQL Checkpoint | 否 | 数据库连接信息通过 conn_string 配置 |
| Sqlite Checkpoint | 否 | 本地文件存储 |
| LangSmith（可选） | 是 | 用于追踪调试，需要 LangSmith API Key |

---

## 7. 技术关系

```
用户查询
    │
    ▼
┌─────────────────────┐
│  Agent Node (LLM)   │ ←── LLM Client (llm/client.py)
│  决策调用工具/回答   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Human Review Node  │ ←── interrupt() 暂停，等待外部 Command
│  人工审核工具调用    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Tool Node          │ ←── TOOL_EXECUTORS (tools.py)
│  执行工具函数        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  RAG Node (可选)     │ ←── RAGGenerator (rag/generator.py)
│  知识库检索          │
└──────┬──────────────┘
       │
       ▼
  Checkpoint 保存 ─────→ PostgreSQL / SQLite
```

---

## 8. 验收清单

- [ ] 理解 StateGraph 的构建流程：定义状态 -> 添加节点 -> 添加边 -> 编译
- [ ] 掌握三种 Checkpoint 后端的配置方法和适用场景
- [ ] 学会使用 interrupt() 在任意节点暂停工作流
- [ ] 学会使用 Command(resume=...) 恢复中断的工作流
- [ ] 理解子图的独立状态管理和与父图的通信方式
- [ ] 掌握 Send API 的多任务并行分发机制
- [ ] 能在项目中实现 Human-in-the-Loop 审核流程
- [ ] 理解动态断点和静态断点的区别
- [ ] 能够排查 State 序列化引起的常见错误
- [ ] 理解 thread_id 在多实例部署中的重要性

---

## 9. 学习资源

- LangGraph 官方文档：https://langchain-ai.github.io/langgraph/
- LangGraph Checkpoint 指南：https://langchain-ai.github.io/langgraph/concepts/persistence/
- Human-in-the-Loop 教程：https://langchain-ai.github.io/langgraph/tutorials/human_in_the_loop/
- LangGraph GitHub 仓库：https://github.com/langchain-ai/langgraph
- 项目源码参考：agent_platform/src/agent/graph.py
- LangGraph 子图示例：https://langchain-ai.github.io/langgraph/how-tos/subgraph/
- LangGraph Send API：https://langchain-ai.github.io/langgraph/how-tos/map-reduce/
