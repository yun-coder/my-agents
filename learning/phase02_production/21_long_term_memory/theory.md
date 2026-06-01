# 21 长期记忆 Mem0 / Zep

## 核心概念

长期记忆用于跨会话保存稳定事实、偏好和历史摘要。Mem0 的记忆操作会围绕用户、会话或运行标识组织数据，并支持增加与检索。

## 工程边界

- 记忆不是完整聊天日志。
- 写入前要判断是否值得长期保存。
- 用户应能查看、更新和删除记忆。
- 多租户系统必须隔离用户与租户命名空间。

## 参考资料

- [Mem0 Memory Operations](https://docs.mem0.ai/core-concepts/memory-operations)
- [Zep Documentation](https://help.getzep.com/)
