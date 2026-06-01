# 阶段二综合项目：安全知识工作流

这个项目将阶段二的重点串成一条可离线运行的工作流：

1. 接收用户任务和外部检索内容。
2. 扫描间接 Prompt Injection 风险信号。
3. 按工具白名单判断是否允许调用。
4. 对 `send_email` 等高风险工具创建人工审批暂停点。
5. 使用 SQLite 保存任务状态和审计事件。
6. 使用同一个 `task_id` 恢复被暂停的工作流。

## 运行

```powershell
python .\learning\phase02_production\projects\secure_workflow\cli.py
```

## 设计边界

- 这是学习项目，不是真正的生产安全网关。
- 风险扫描只提供启发式信号，不能代替权限隔离和人工审批。
- SQLite 便于本地学习；分布式部署应评估 PostgreSQL、Redis 或框架自带 checkpointer。
