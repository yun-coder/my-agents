# 12 LangGraph 入门：图结构 Agent 工作流

## 一、概念概述

### 1.1 什么是 LangGraph

LangGraph 是 LangChain 团队推出的 Agent 工作流编排框架（2024 年初开源）。与传统的 Chain 线性执行不同，LangGraph 使用**有向图**（Directed Graph）来定义 Agent 的执行流程，天然支持**循环**（Cycle）、**条件分支**（Conditional Edge）和**状态持久化**（State Persistence）。

LangGraph 的出现是为了解决 AgentExecutor 的核心缺陷：
- AgentExecutor 是黑盒：无法自定义内部的循环逻辑
- AgentExecutor 不支持图结构：难以实现复杂路由
- AgentExecutor 状态管理弱：难以持久化和恢复

### 1.2 核心特性

- **图结构编排**：将 Agent 工作流建模为 StateGraph
- **状态驱动**：所有节点共享一个 TypedDict 状态对象
- **条件路由**：根据当前状态动态选择下一个节点
- **循环支持**：Agent 可以多次调用工具后回到决策节点
- **Checkpoint 持久化**：在任意节点保存/恢复状态
- **流式执行**：支持逐节点和逐 Token 流式输出
- **人机协同**：支持 Human-in-the-Loop 中断和恢复

### 1.3 适用场景

- 需要多轮 Tool Calling 循环的 Agent
- 需要条件分支的复杂工作流
- 需要状态持久化和恢复的长流程任务
- 需要人机交互审批的流程
- 需要细粒度控制执行过程的场景

---

## 二、核心原理

### 2.1 StateGraph 概念模型

LangGraph 的核心概念只有五个：**State、Node、Edge、ConditionalEdge、Compile**。

```text
State (共享状态)
    v
Node A ----> Edge ----> Node B
  |                       |
  +-- ConditionalEdge ----+
          (条件路由)
                          v
                       Node C ----> END
```

#### 2.1.1 State（状态）

State 是一个 TypedDict 或 Pydantic BaseModel，定义了工作流的共享状态。所有节点都可以读写这个状态。

```python
from typing import TypedDict, List, Dict, Any

# 定义 Agent 的状态
class AgentState(TypedDict, total=False):
    messages: List[Dict[str, Any]]    # 对话消息
    query: str                         # 用户问题
    session_id: str                    # 会话 ID
    iteration_count: int               # 当前迭代次数
    final_answer: str                  # 最终回答
    tool_log: List[str]                # 工具调用日志
    error: str                         # 错误信息
```

参考 `agent_platform/src/agent/graph.py` 中的 AgentState 定义：

```python
# 平台实际使用的 AgentState
class AgentState(TypedDict, total=False):
    messages: list[dict[str, Any]]
    query: str
    session_id: str
    iteration_count: int
    final_answer: str
    tool_log: list[str]
    error: str
```

#### 2.1.2 Node（节点）

Node 是一个接受 State 并返回 State 更新的函数。每个节点完成一项具体工作。

```python
def agent_node(state: AgentState) -> Dict[str, Any]:
    """Agent 决策节点：决定下一步动作。"""
    query = state["query"]
    iteration = state.get("iteration_count", 0)

    # 调用 LLM 做决策（省略具体 LLM 调用）
    # ...

    # 返回状态更新（只返回要更新的字段）
    return {
        "messages": new_messages,
        "iteration_count": iteration + 1,
        "final_answer": answer if done else "",
    }

def tool_node(state: AgentState) -> Dict[str, Any]:
    """工具执行节点：执行工具调用。"""
    # 读取最后一条消息中的 tool_calls
    # 执行工具
    # 返回工具执行结果
    return {"messages": updated_messages, "tool_log": logs}
```

#### 2.1.3 Edge（边）

Edge 连接两个节点，定义了工作流的拓扑结构。

```python
# 添加节点间的顺序边
builder.add_edge("tools", "agent")    # 工具执行完后回到 agent
builder.add_edge("rag", "agent")      # RAG 检索完后回到 agent
```

#### 2.1.4 ConditionalEdge（条件边）

ConditionalEdge 根据当前状态动态决定下一个节点。

```python
# 条件路由函数
from typing import Literal

def router(state: AgentState) -> Literal["tools", "rag", "end"]:
    """根据状态路由到不同节点。"""
    if state.get("final_answer"):
        return "end"                     # 有答案了 -> 结束
    if state.get("error"):
        return "end"                     # 出错了 -> 结束

    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        if last.get("tool_calls"):
            return "tools"               # 需要调用工具
        if "需要搜索知识库" in str(last.get("content", "")):
            return "rag"                 # 需要 RAG 检索
    return "end"                         # 默认结束

# 添加条件边
builder.add_conditional_edges(
    "agent",                # 源节点
    router,                 # 路由函数
    {                       # 路由映射
        "tools": "tools",
        "rag": "rag",
        "end": END,          # END 是 LangGraph 内置的终止节点
    },
)
```

### 2.2 Compile（编译）

编译将 StateGraph 转换为可执行的 Runnable 对象。

```python
from langgraph.checkpoint.memory import MemorySaver

# 无持久化
graph = builder.compile()

# 带内存持久化
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

编译后的 Graph 是一个 Runnable 对象，支持 invoke、stream、astream。

### 2.3 Invoke vs Stream

```python
# invoke: 等待完整执行结束
result = graph.invoke(initial_state)
print(result["final_answer"])

# stream: 每一步输出事件
for event in graph.stream(initial_state):
    node_name = list(event.keys())[0]
    node_output = event[node_name]
    print(f"[{node_name}] 完成")
    if "final_answer" in node_output and node_output["final_answer"]:
        print(f"最终回答: {node_output['final_answer']}")

# stream_mode="updates": 只输出状态更新
for update in graph.stream(initial_state, stream_mode="updates"):
    for node_name, state_update in update.items():
        print(f"[{node_name}] -> {list(state_update.keys())}")
```

### 2.4 Checkpoint 基础

Checkpoint 是 LangGraph 的状态持久化机制，允许在任意节点保存状态，并在后续恢复。

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# Memory Saver（内存级别，重启丢失）
memory_checkpointer = MemorySaver()

# SQLite Saver（持久化到文件）
sqlite_checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# 编译时传入 checkpointer
graph = builder.compile(checkpointer=sqlite_checkpointer)

# 通过 thread_id 区分不同会话
config = {"configurable": {"thread_id": "user_session_001"}}

# 首次执行
result = graph.invoke(initial_state, config=config)

# 线程恢复：在同一个 thread_id 上继续
result2 = graph.invoke({"query": "继续刚才的问题"}, config=config)
```

### 2.5 Thread ID 与会话隔离

Thread ID 是 LangGraph 中的会话标识，用于隔离不同用户的会话状态。

```python
# 用户 A 的会话
config_a = {"configurable": {"thread_id": "user_a"}}

# 用户 B 的会话
config_b = {"configurable": {"thread_id": "user_b"}}

# 两者状态完全隔离
graph.invoke({"query": "我的名字是小明"}, config=config_a)
graph.invoke({"query": "我的名字是小红"}, config=config_b)

# 用户 A 的状态（知道名字是小明）
state_a = graph.get_state(config_a)
print(state_a.values["messages"][-1]["content"])
```

---

## 三、实战指南

### 3.1 构建完整 Agent 工作流

参考 `agent_platform/src/agent/graph.py` 中的完整实现：

```python
import json
import logging
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5


class AgentState(TypedDict, total=False):
    """Agent 工作流共享状态。"""
    messages: list[dict[str, Any]]
    query: str
    session_id: str
    iteration_count: int
    final_answer: str
    tool_log: list[str]
    error: str


class AgentWorkflow:
    """基于 LangGraph 的 Agent 工作流。"""

    def __init__(self, rag_generator=None, memory=None,
                 enable_checkpoint=False):
        self._llm = get_llm_client()
        self._rag = rag_generator
        self._memory = memory or ConversationMemory()

        # 构建图
        builder = StateGraph(AgentState)

        # 添加节点
        builder.add_node("agent", self._agent_node)
        builder.add_node("tools", self._tool_node)
        builder.add_node("rag", self._rag_node)

        # 设置入口点
        builder.set_entry_point("agent")

        # 条件边：agent 决定下一步
        builder.add_conditional_edges(
            "agent",
            self._router,
            {"tools": "tools", "rag": "rag", "end": END},
        )

        # 固定边
        builder.add_edge("tools", "agent")
        builder.add_edge("rag", "agent")

        # 编译
        if enable_checkpoint:
            self._checkpointer = MemorySaver()
            self._graph = builder.compile(checkpointer=self._checkpointer)
        else:
            self._graph = builder.compile()

    def run(self, query: str, session_id: str = "default") -> AgentState:
        """执行 Agent 工作流。"""
        initial_state = {
            "messages": self._memory.get_messages(),
            "query": query,
            "session_id": session_id,
            "iteration_count": 0,
            "final_answer": "",
            "tool_log": [],
            "error": "",
        }
        result = self._graph.invoke(initial_state)
        if result.get("final_answer"):
            self._memory.add("user", query)
            self._memory.add("assistant", result["final_answer"])
        return result

    def stream(self, query: str, session_id: str = "default"):
        """流式执行。"""
        initial_state = {
            "messages": [],
            "query": query,
            "session_id": session_id,
            "iteration_count": 0,
            "final_answer": "",
            "tool_log": [],
            "error": "",
        }
        for event in self._graph.stream(initial_state):
            yield event

    def _agent_node(self, state: AgentState) -> dict:
        """Agent 决策节点。"""
        iteration = state.get("iteration_count", 0)
        if iteration >= MAX_TOOL_ITERATIONS:
            return {"final_answer": "已达到最大工具调用次数，请简化你的问题。"}

        response = self._llm.chat_with_tools(messages, TOOL_DEFINITIONS)
        choice = response.choices[0]

        if choice.message.tool_calls:
            return {"messages": messages + [choice.message.model_dump()],
                    "iteration_count": iteration + 1}
        elif choice.message.content:
            if "需要搜索知识库" in choice.message.content:
                return {"iteration_count": iteration + 1}
            return {"final_answer": choice.message.content}
        return {"final_answer": "无法理解你的问题。"}

    def _tool_node(self, state: AgentState) -> dict:
        """工具执行节点。"""
        messages = state.get("messages", [])
        last_message = messages[-1]
        tool_calls = last_message.get("tool_calls", [])

        tool_results = []
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            func_args = json.loads(tc["function"]["arguments"])
            executor = TOOL_EXECUTORS.get(func_name)
            if executor:
                result = executor(**func_args)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result),
                })
        return {"messages": messages + tool_results}

    def _rag_node(self, state: AgentState) -> dict:
        """RAG 检索节点。"""
        if self._rag:
            answer = self._rag.generate(state["query"])
            return {"messages": [{"role": "system",
                    "content": f"知识库检索结果: {answer.answer}"}]}
        return {}

    def _router(self, state: AgentState) -> Literal["tools", "rag", "end"]:
        """条件路由逻辑。"""
        if state.get("final_answer") or state.get("error"):
            return "end"
        messages = state.get("messages", [])
        if messages:
            last = messages[-1]
            if last.get("tool_calls"):
                return "tools"
            content = str(last.get("content", ""))
            if "需要搜索知识库" in content:
                return "rag"
        return "end"
```

### 3.2 人机交互（中断与恢复）

```python
# 添加中断点
graph = builder.compile(
    interrupt_before=["tools"],    # 调用工具前中断
    interrupt_after=["agent"],     # Agent 决策后中断
)

# 执行（会暂停在中断点）
result = graph.invoke(initial_state, config=config)

# 检查中断位置
print(result["__interrupt__"])  # 显示中断信息

# 继续执行（带用户输入）
graph.invoke(
    {"human_input": "确认执行"},
    config=config,
)
```

### 3.3 子图（Subgraph）

复杂工作流可以嵌套子图，实现模块化。

```python
# 定义子图
def create_rag_subgraph():
    builder = StateGraph(RAGState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("rerank", rerank_node)
    builder.add_node("generate", generate_node)
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "generate")
    builder.set_entry_point("retrieve")
    builder.set_finish_point("generate")
    return builder.compile()

# 将子图作为节点添加到主图
main_builder = StateGraph(AgentState)
main_builder.add_node("agent", agent_node)
main_builder.add_node("rag_subgraph", create_rag_subgraph())
main_builder.add_node("tools", tool_node)
```

---

## 四、最佳实践

### 4.1 节点设计原则

- **单一职责**：每个节点只做一件事（决策、执行工具、检索）
- **幂等性**：节点的执行结果只依赖 state，不应有副作用
- **轻量级**：节点应快速执行，避免长时间计算阻塞

### 4.2 状态管理

- **最小化状态**：State 中只放必要的字段，避免传递大量数据
- **不可变更新**：返回新的状态字典而非修改原状态
- **字段命名规范**：用清晰的名称（final_answer, tool_log），避免歧义

### 4.3 路由设计

- **明确的终止条件**：确保图不会陷入无限循环
- **最大迭代限制**：设置 MAX_TOOL_ITERATIONS 防止死循环
- **兜底路由**：在条件路由中始终包含 end 兜底路径

### 4.4 错误处理

```python
def safe_node(state: AgentState) -> dict:
    """健壮的节点实现。"""
    try:
        result = do_something(state)
        return result
    except Exception as e:
        logger.error("节点执行失败: %s", e)
        return {"error": str(e), "final_answer": f"执行出错: {e}"}
```

---

## 五、常见陷阱

### 5.1 状态共享陷阱

**陷阱**：多个节点同时修改状态的同一个字段，导致竞态问题。

**解决**：每个节点只更新自己负责的字段，避免修改其他节点的输出。

### 5.2 无限循环

**陷阱**：没有设置最大迭代次数或终止条件不当，导致图陷入死循环。

**解决**：
```python
if state.get("iteration_count", 0) >= MAX_ITERATIONS:
    return {"final_answer": "达到最大迭代次数，结束。"}
```

### 5.3 Checkpoint 序列化失败

**陷阱**：State 中包含无法序列化的对象（如数据库连接、文件句柄）。

**解决**：State 中只放 JSON 可序列化的基本类型（str, int, list, dict）。

### 5.4 条件边配置错误

**陷阱**：路由函数返回了映射中不存在的值。

**解决**：使用 Literal 类型标注约束返回值，确保映射覆盖所有可能性。

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| LangGraph 库本身 | 否 | 开源框架，本地运行 |
| LLM 调用（Agent 决策） | 是 | 需要 LLM 的 API Key |
| RAG 相关（检索+生成） | 取决于具体实现 | 见 RAG 章节的 API Key 表 |
| Checkpoint (MemorySaver) | 否 | 纯内存存储 |
| Checkpoint (SqliteSaver) | 否 | 本地 SQLite 文件 |

---

## 七、技术关系

```text
LangGraph 与相关技术的关系:

LangChain (组件库)
    |
    +-- 提供 Prompt Template, Tool, OutputParser 等组件
    +-- LangGraph 将这些组件组织为图工作流
            |
            v
LangGraph (工作流编排)
    |
    +-- StateGraph ----> 有状态图
    +-- Node       ----> 计算节点
    +-- Edge       ----> 固定连接
    +-- ConditionalEdge -> 条件路由
    +-- Checkpointer ---> 状态持久化
            |
            v
LangFuse / LangSmith (可观测性)
    +-- 追踪 Graph 的执行链路和 Token 消耗
```

LangGraph 正在逐步替代 LangChain 原有的 AgentExecutor，成为 LangChain 生态中 Agent 编排的标准方案。

---

## 八、验收清单

- [ ] 理解 StateGraph 的五个核心概念：State、Node、Edge、ConditionalEdge、Compile
- [ ] 能编写 TypedDict 类型的状态定义
- [ ] 掌握 add_node / add_edge / add_conditional_edges 的用法
- [ ] 理解条件路由函数的签名和返回值
- [ ] 区分 invoke 和 stream 的执行方式
- [ ] 理解 Checkpoint 和 thread_id 的作用
- [ ] 能设置 max_iterations 防止无限循环
- [ ] 理解人机交互（Human-in-the-Loop）的实现方式
- [ ] 掌握图的编译和运行流程
- [ ] 理解 LangGraph 相对于 AgentExecutor 的优势

---

## 九、学习资源

- **LangGraph 官方文档**: https://langchain-ai.github.io/langgraph/
- **LangGraph 教程**: https://langchain-ai.github.io/langgraph/tutorials/
- **LangGraph 概念指南**: https://langchain-ai.github.io/langgraph/concepts/
- **平台参考代码**: agent_platform/src/agent/graph.py (AgentWorkflow 实现)
- **LangGraph GitHub**: https://github.com/langchain-ai/langgraph
