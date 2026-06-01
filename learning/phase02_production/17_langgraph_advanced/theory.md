# 17 LangGraph 深入

## 核心概念

LangGraph 的持久化层会在图执行过程中保存 checkpoint，并按 `thread_id` 组织状态。它支持：

- 中断后恢复
- Human-in-the-loop 审批
- 会话记忆
- 故障恢复与调试

`interrupt()` 适合在高风险动作前暂停执行，恢复时使用同一 `thread_id` 和 `Command(resume=...)`。

## 工程提醒

- 内存 checkpointer 只适合本地演示。
- 生产环境应使用持久化后端。
- 审批节点必须记录操作人、时间、参数和决策。

## 参考资料

- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
