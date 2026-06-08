# LangGraph 入门指南

## 什么是 LangGraph

LangGraph 是 LangChain 团队开发的一个基于图结构的状态管理框架，专门用于构建复杂的 Agent 工作流。它使用有向图（StateGraph）来定义 Agent 的执行流程。

## 核心概念

### State（状态）
State 是 Agent 工作流中共享的数据结构，在图的节点之间传递。通常使用 TypedDict 或 Pydantic 模型定义。

### Node（节点）
Node 是图中的执行单元。每个节点接收 State 并返回更新后的 State。

### Edge（边）
Edge 定义节点之间的连接关系：
- **普通边**：固定从一个节点指向另一个节点。
- **条件边**：根据 State 的内容决定下一步走向。

### Checkpoint（检查点）
Checkpoint 用于持久化 Agent 的执行状态，支持：
- 任务中断后恢复执行。
- 人工审核（Human-in-the-loop）。
- 时间旅行调试。

## LangGraph 与 LangChain 的关系

LangGraph 可以与 LangChain 配合使用，也可以独立使用：
- LangChain 负责与 LLM 交互、工具定义、RAG 组件。
- LangGraph 负责编排这些组件的执行流程。

## 典型应用场景

1. **多步骤推理 Agent**：Agent 需要多轮思考才能得出结论。
2. **审批工作流**：关键操作需要人工审核后才能执行。
3. **多 Agent 协作**：多个 Agent 按图定义的流程协作。
4. **自适应 RAG**：根据问题类型选择不同的检索策略。

## LangGraph 基础示例

```python
from langgraph.graph import StateGraph, END

class State(TypedDict):
    query: str
    result: str

def search_node(state: State) -> State:
    # 执行检索逻辑
    state["result"] = "检索结果"
    return state

def generate_node(state: State) -> State:
    # 执行生成逻辑
    state["result"] = "生成的回答"
    return state

builder = StateGraph(State)
builder.add_node("search", search_node)
builder.add_node("generate", generate_node)
builder.set_entry_point("search")
builder.add_edge("search", "generate")
builder.add_edge("generate", END)
graph = builder.compile()
```
