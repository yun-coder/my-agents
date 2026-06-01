# 12 LangGraph 入门

## 学习目标

- 理解 State、Node、Edge、条件分支和循环。
- 把 Agent 流程看成状态机，而不是无限 while 循环。
- 为阶段二的持久化、人工审核和恢复执行打基础。

## 核心概念

| 概念 | 说明 |
|---|---|
| State | 流程中持续传递的数据 |
| Node | 接收状态并返回状态更新的函数 |
| Edge | 节点之间的执行方向 |
| Conditional Edge | 根据状态选择下一节点 |
| Checkpointer | 保存执行状态，阶段二深入 |

LangGraph v1 保留了图原语与执行模型。LangChain 的高层 Agent 也建立在 LangGraph 上。

## 本章流程

```text
START -> classify -> answer_python 或 fallback -> END
```

## 参考资料

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph v1](https://docs.langchain.com/oss/python/releases/langgraph-v1)

## 验收清单

- 能解释 State 与普通局部变量的区别。
- 能新增一个条件分支。
- 能说明什么场景需要持久化与人工审核。
