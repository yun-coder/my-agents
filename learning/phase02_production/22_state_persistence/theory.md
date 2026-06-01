# 22 Agent 状态持久化

## 核心概念

状态持久化解决长流程中断恢复。需要保存：

- 任务 ID 与租户 ID
- 当前步骤
- 输入摘要与中间结果
- 状态版本
- 更新时间与审计信息

Redis 适合高速临时状态，PostgreSQL 适合需要查询和审计的持久状态。LangGraph checkpointer 可以管理图执行 checkpoint。

## 参考资料

- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Redis Documentation](https://redis.io/docs/latest/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
