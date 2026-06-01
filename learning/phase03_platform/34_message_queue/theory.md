# 34. 消息队列：RabbitMQ / Kafka / Redis Streams / Celery

## 学习目标

- 理解为什么耗时 Agent 任务适合异步执行。
- 区分消息代理、事件流与任务队列框架。
- 会处理重试、幂等和失败任务。

## 核心概念

HTTP 请求适合快速响应。长时间运行的 Agent 任务更适合先入队，再由 worker 执行。

| 技术 | 常见定位 |
| --- | --- |
| RabbitMQ | 可靠消息代理，适合路由和确认机制 |
| Kafka | 高吞吐事件流与历史回放 |
| Redis Streams | 基于 Redis 的轻量事件流 |
| Celery | Python 分布式任务队列，可搭配 RabbitMQ 或 Redis |

队列不能自动解决重复执行。worker 崩溃、网络重试和确认超时都可能让同一任务再次到达，因此工具操作要尽量幂等，并用稳定的 `task_id` 做去重。

## 示例说明

`demo.py` 使用标准库 `deque` 模拟 worker 重试。它展示的是任务生命周期，不替代真正的消息代理。

## 运行

```powershell
python .\learning\phase03_platform\34_message_queue\demo.py
```

## 延伸阅读

- [RabbitMQ 官方文档](https://www.rabbitmq.com/docs)
- [Apache Kafka 官方文档](https://kafka.apache.org/documentation/)
- [Redis Streams 官方文档](https://redis.io/docs/latest/develop/data-types/streams/)
- [Celery 官方文档](https://docs.celeryq.dev/)
