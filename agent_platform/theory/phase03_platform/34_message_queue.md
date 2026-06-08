# 34 消息队列 — Agent 异步任务与事件驱动架构

## 1. 概念概述

### 1.1 消息队列在 Agent 系统中的角色

消息队列（Message Queue）是 Agent 系统中实现异步任务、解耦组件和削峰填谷的核心基础设施。在一个复杂的 Agent 应用中，不是所有任务都需要同步完成——知识库索引、文档处理、批量推理、通知发送等耗时的后台任务应该通过消息队列异步执行。

Agent 系统中消息队列的核心价值：
- **任务解耦**：Agent 逻辑与后台处理分离
- **流量削峰**：突发请求先入队，Worker 按能力消费
- **失败重试**：失败任务自动重试，不丢失
- **负载均衡**：多个 Worker 并行消费消息
- **任务编排**：链式任务、扇出/扇入模式

### 1.2 主流消息队列对比

| 特性 | Celery + Redis | RabbitMQ | Apache Kafka | Redis Streams |
|------|---------------|---------|-------------|--------------|
| 定位 | 分布式任务队列 | AMQP 消息代理 | 事件流平台 | 轻量消息队列 |
| 持久化 | Redis 后端 | 内建持久化 | 磁盘持久化 | RDB/AOF |
| 消息顺序 | 不保证 | 队列内有序 | 分区内有序 | 组内有序 |
| 吞吐量 | ~10K/s | ~50K/s | ~1M/s | ~20K/s |
| 延迟 | ~1ms | ~1ms | ~10ms | ~1ms |
| 消息回溯 | 不支持 | 有限 | 支持 | 部分支持 |
| 部署复杂度 | 低 | 中 | 高 | 低 |
| 适用场景 | Agent 后台任务 | 服务间消息 | 事件溯源/流处理 | 轻量任务队列 |

### 1.3 消息模型

三种核心消息模型：
1. **点对点（Queue）**：一条消息被一个消费者消费
2. **发布订阅（Pub/Sub）**：一条消息被所有订阅者消费
3. **流（Stream）**：消息持久化存储，支持回溯消费

Agent 系统中最常用的是点对点队列（后台任务）和发布订阅（事件通知）。

## 2. 核心原理

### 2.1 Celery 架构

Celery 是 Python 生态中最成熟的分布式任务队列，其架构包括：

- **Producer**：产生任务的应用程序
- **Broker**：消息中间件（Redis / RabbitMQ）
- **Worker**：执行任务的进程
- **Result Backend**：存储任务结果

任务执行流程：
```
Agent -> task.delay() -> Broker (Redis) -> Worker -> 执行 -> 结果存储
```

### 2.2 消息确认机制

消息队列的可靠性核心在于确认机制（ACK）：

- **自动确认**：Worker 收到消息立即确认，处理中断则消息丢失
- **手动确认**：Worker 完成任务后确认，处理中断则重新投递

```python
# Celery 手动确认
@app.task(acks_late=True)
def process_document(doc_id: str):
    try:
        # 处理文档
        result = do_process(doc_id)
        return result
    except Exception:
        # 处理失败，消息重新入队
        raise
```

### 2.3 死信队列（DLQ）

死信队列用于存储无法成功处理的消息。触发条件：
- 消息被消费者拒绝
- 消息过期（TTL 到期）
- 队列达到最大长度

死信处理流程：
```
消息 -> 多次重试失败 -> 死信交换机 -> 死信队列 -> 人工介入/自动降级
```

### 2.4 指数退避重试

失败任务的智能重试策略：每次重试的等待时间呈指数增长，避免雪崩效应。

```python
# 重试间隔：2s, 4s, 8s, 16s, 32s, ...
retry_delays = [2 ** n for n in range(6)]  # [1, 2, 4, 8, 16, 32]
```

## 3. 实战指南

### 3.1 Celery + Redis 入门

```python
# celery_app.py — Celery 应用定义
from celery import Celery

# 创建 Celery 应用
celery_app = Celery(
    "agent_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分钟
    task_soft_time_limit=25 * 60,  # 25 分钟软限制
)
```

```python
# tasks.py — Agent 后台任务定义
from celery_app import celery_app
from typing import Any
import time
import logging

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,  # 基础重试延迟 5 秒
    acks_late=True,  # 任务完成后才确认
)
def process_document(self, doc_id: str, content: str) -> dict:
    """处理文档：提取关键信息并索引。"""
    try:
        logger.info(f"开始处理文档: {doc_id}")
        # 模拟文档处理
        time.sleep(2)

        # 模拟 LLM 调用
        summary = f"文档 {doc_id} 的摘要内容"
        keywords = ["AI", "机器学习", "深度学习"]

        result = {
            "doc_id": doc_id,
            "summary": summary,
            "keywords": keywords,
            "status": "completed",
        }
        logger.info(f"文档处理完成: {doc_id}")
        return result

    except Exception as exc:
        logger.error(f"文档处理失败: {doc_id}, 错误: {exc}")
        # 指数退避重试
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=5)
def send_notification(self, user_id: str, message: str) -> dict:
    """发送通知（邮件/短信/推送）。"""
    try:
        logger.info(f"发送通知给用户: {user_id}")
        # 模拟通知发送
        time.sleep(1)
        return {"status": "sent", "user_id": user_id}

    except Exception as exc:
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task
def index_knowledge_base(kb_id: str, documents: list[dict]) -> dict:
    """索引知识库文档。"""
    total = len(documents)
    logger.info(f"开始索引知识库 {kb_id}, 共 {total} 篇文档")

    success_count = 0
    failed_count = 0

    for doc in documents:
        try:
            # 模拟向量化索引
            time.sleep(0.1)
            success_count += 1
        except Exception:
            failed_count += 1

    return {
        "kb_id": kb_id,
        "total": total,
        "success": success_count,
        "failed": failed_count,
    }
```

### 3.2 Agent 中集成 Celery 任务

```python
# agent_integration.py — 在 Agent 中调用异步任务
from tasks import process_document, send_notification
from celery.result import AsyncResult
import asyncio
from typing import Any

class AgentTaskManager:
    """Agent 任务管理器：将耗时的 Agent 操作异步化。"""

    def __init__(self):
        self.pending_tasks: dict[str, AsyncResult] = {}

    def dispatch_task(self, task_name: str, *args, **kwargs) -> str:
        """分发任务到 Celery Worker。"""
        task_map = {
            "process_document": process_document,
            "send_notification": send_notification,
        }

        if task_name not in task_map:
            raise ValueError(f"未知任务: {task_name}")

        task_func = task_map[task_name]
        result = task_func.delay(*args, **kwargs)

        self.pending_tasks[result.id] = result
        return result.id

    def get_task_status(self, task_id: str) -> dict:
        """查询任务状态。"""
        result = self.pending_tasks.get(task_id)
        if not result:
            return {"status": "NOT_FOUND"}

        if result.ready():
            if result.successful():
                return {
                    "status": "SUCCESS",
                    "result": result.get(),
                }
            else:
                return {
                    "status": "FAILURE",
                    "error": str(result.result),
                }
        else:
            return {"status": "PENDING"}

    def wait_for_tasks(self, task_ids: list[str], timeout: int = 300) -> list[Any]:
        """等待多个任务完成。"""
        from celery import group
        tasks = [self.pending_tasks[tid] for tid in task_ids]
        return [t.get(timeout=timeout) for t in tasks]


# 在 Agent 工具函数中使用
def agent_tool_process_document(doc_id: str, content: str) -> dict:
    """Agent 工具：异步处理文档。"""
    manager = AgentTaskManager()
    task_id = manager.dispatch_task("process_document", doc_id, content)
    return {
        "task_id": task_id,
        "message": f"文档 {doc_id} 已加入处理队列",
        "status_check": f"/task/{task_id}",
    }
```

### 3.3 RabbitMQ 模式示例

```python
# rabbitmq_agent.py — 使用 RabbitMQ 进行 Agent 通信
import pika
import json
import uuid
from typing import Optional

class AgentMessageQueue:
    """基于 RabbitMQ 的 Agent 消息队列。"""

    def __init__(self, host: str = "localhost", port: int = 5672):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, port=port)
        )
        self.channel = self.connection.channel()

        # 声明交换机和队列
        self.channel.exchange_declare(
            exchange="agent_tasks",
            exchange_type="direct",
            durable=True,
        )

    def publish_task(self, routing_key: str, task_data: dict) -> str:
        """发布任务消息。"""
        task_id = str(uuid.uuid4())
        task_data["task_id"] = task_id

        self.channel.basic_publish(
            exchange="agent_tasks",
            routing_key=routing_key,
            body=json.dumps(task_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 持久化消息
                content_type="application/json",
                priority=task_data.get("priority", 5),
            ),
        )
        return task_id

    def declare_worker_queue(self, queue_name: str, routing_key: str):
        """声明 Worker 队列。"""
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(
            exchange="agent_tasks",
            queue=queue_name,
            routing_key=routing_key,
        )

    def start_worker(self, queue_name: str, callback):
        """启动 Worker 消费消息。"""
        self.channel.basic_qos(prefetch_count=1)  # 一次只处理一条消息

        def on_message(ch, method, properties, body):
            try:
                task_data = json.loads(body)
                callback(task_data)
                # 手动确认
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"处理失败: {e}")
                # 拒绝消息，不重新入队（进入死信队列）
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message,
        )
        print(f"Worker 已启动，监听队列: {queue_name}")
        self.channel.start_consuming()


# 使用示例
mq = AgentMessageQueue()
task_id = mq.publish_task("document.process", {
    "doc_id": "doc_001",
    "action": "summarize",
    "priority": 8,
})
print(f"任务已发布: {task_id}")
```

### 3.4 Redis Streams 实现

```python
# redis_streams.py — 使用 Redis Streams 实现消息队列
import redis
import json
import time
import uuid
from typing import Optional, Callable

class RedisStreamQueue:
    """基于 Redis Streams 的轻量级消息队列。"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.client = redis.from_url(redis_url)
        self.stream_key: Optional[str] = None
        self.group_name: Optional[str] = None

    def create_stream(self, stream_key: str, group_name: str = "agent_workers"):
        """创建消费者组。"""
        self.stream_key = stream_key
        self.group_name = group_name
        try:
            self.client.xgroup_create(stream_key, group_name, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def publish(self, message: dict, maxlen: int = 10000) -> str:
        """发布消息到流。"""
        message_id = self.client.xadd(
            self.stream_key,
            fields=message,
            maxlen=maxlen,
            approximate=True,
        )
        return message_id

    def consume(self, consumer_name: str, batch_size: int = 1, timeout: int = 5) -> list:
        """消费消息。"""
        results = self.client.xreadgroup(
            groupname=self.group_name,
            consumername=consumer_name,
            streams={self.stream_key: ">"},  # ">" 表示未投递的消息
            count=batch_size,
            block=timeout * 1000,  # 阻塞等待
        )
        return results

    def ack(self, message_id: str):
        """确认消息处理完成。"""
        self.client.xack(self.stream_key, self.group_name, message_id)

    def get_pending(self) -> list:
        """查看待处理消息。"""
        return self.client.xpending(self.stream_key, self.group_name)


class AgentTaskOrchestrator:
    """使用 Redis Streams 编排 Agent 任务。"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.queue = RedisStreamQueue(redis_url)
        self.queue.create_stream("agent:document_tasks")
        self.queue.create_stream("agent:index_tasks")
        self.queue.create_stream("agent:notification_tasks")

    def create_index_pipeline(self, documents: list[dict]) -> str:
        """创建文档索引管道。"""
        pipeline_id = str(uuid.uuid4())
        for doc in documents:
            self.queue.publish(doc)
        return pipeline_id


# Worker 示例
def document_worker():
    """文档处理 Worker。"""
    queue = RedisStreamQueue()
    queue.create_stream("agent:document_tasks")
    consumer_id = f"worker-{uuid.uuid4().hex[:8]}"

    print(f"文档处理 Worker 已启动: {consumer_id}")
    while True:
        messages = queue.consume(consumer_id, batch_size=1, timeout=5)
        if messages:
            for stream_key, entries in messages:
                for msg_id, data in entries:
                    print(f"处理文档: {data}")
                    time.sleep(1)  # 模拟处理
                    queue.ack(msg_id)
                    print(f"文档 {data.get('doc_id')} 处理完成")
```

### 3.5 Flower 任务监控

```bash
# 安装 Flower
pip install flower

# 启动 Flower 监控面板（默认端口 5555）
celery -A celery_app flower --port=5555 --loglevel=info

# 使用 Basic Auth 保护面板
celery -A celery_app flower \
    --port=5555 \
    --basic-auth=admin:secret123
```

```python
# 以编程方式启动 Flower
from flower.app import Flower
from flower.utils import configure

def start_monitor():
    app = Flower(
        celery_app="celery_app",
        address="0.0.0.0",
        port=5555,
        basic_auth=["admin:secret123"],
    )
    app.start()
```

### 3.6 链式任务与工作流

```python
# workflow.py — 链式任务编排
from celery import chain, group, chord
from celery_app import celery_app

@celery_app.task
def extract_document(doc_id: str) -> str:
    """第一步：提取文档内容。"""
    content = f"文档 {doc_id} 的原始内容"
    return content

@celery_app.task
def summarize_text(content: str) -> dict:
    """第二步：生成摘要。"""
    return {"summary": f"摘要: {content[:50]}..."}

@celery_app.task
def index_vectors(data: dict) -> dict:
    """第三步：向量化索引。"""
    return {**data, "indexed": True}

@celery_app.task
def notify_completion(result: dict) -> None:
    """第四步：通知完成。"""
    print(f"处理完成: {result}")

# 链式任务：顺序执行
def run_pipeline(doc_id: str):
    pipeline = chain(
        extract_document.s(doc_id),
        summarize_text.s(),
        index_vectors.s(),
        notify_completion.s(),
    )
    result = pipeline()
    return result.id

# 扇出任务：并行执行
def parallel_processing(doc_ids: list[str]):
    task_group = group(
        extract_document.s(doc_id) for doc_id in doc_ids
    )
    result = task_group()
    return result

# Chord：扇出后聚合
def fan_out_aggregate(doc_ids: list[str]):
    callback = summarize_text.s()
    task_chord = chord(
        header=[extract_document.s(doc_id) for doc_id in doc_ids],
        body=callback,
    )
    result = task_chord()
    return result.id
```

### 3.7 启动 Worker

```bash
# 启动 Celery Worker
celery -A celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --prefetch-multiplier=1

# 启动多个队列的 Worker
celery -A celery_app worker \
    -Q document_queue,index_queue \
    --loglevel=info

# 使用 Pool 类型（prefork/gevent/thread）
celery -A celery_app worker \
    --pool=gevent \
    --concurrency=16
```

## 4. 最佳实践

### 4.1 任务设计原则

1. **幂等性**：任务多次执行结果一致，支持重复投递
2. **最小化状态**：任务参数尽量精简，大对象通过外部存储传递
3. **超时设置**：为每个任务设置合理的超时时间
4. **错误隔离**：一个任务失败不影响同队列的其他任务

### 4.2 可靠性保障

1. **持久化消息**：RabbitMQ 队列 durable=True，消息 delivery_mode=2
2. **手动 ACK**：使用 acks_late=True，确保任务完成才确认
3. **死信队列**：配置死信交换机，集中处理失败消息
4. **监控告警**：队列堆积超过阈值时告警

### 4.3 Agent 任务优化

1. **大任务拆分**：10 分钟的任务拆分为 10 个 1 分钟的子任务
2. **结果缓存**：相同参数的任务结果缓存，避免重复执行
3. **优先级队列**：高优先级任务使用独立的 Worker
4. **任务合并**：短时间内相同类型的任务合并处理

### 4.4 监控关键指标

- **队列深度**：当前待处理消息数
- **Lag（延迟）**：消息从发布到消费的时间差
- **成功率**：成功完成任务的比例
- **Worker 负载**：每个 Worker 的 CPU/内存使用率

## 5. 常见陷阱

### 5.1 任务参数过大

```python
# 错误：传递大对象
task.delay(large_data=open("big_file.bin", "rb").read())

# 正确：传递引用
file_id = save_to_storage("big_file.bin")
task.delay(file_id=file_id)
```

### 5.2 忽略序列化问题

自定义对象作为任务参数时需要确保可序列化（JSON）。

### 5.3 无限重试循环

没有设置最大重试次数导致任务永远在队列中循环。

### 5.4 数据库连接耗尽

每个 Worker 都创建独立的数据库连接池导致连接数暴增。

### 5.5 消息重复消费

网络分区可能导致消息被多个 Worker 同时消费，需要幂等设计。

## 6. API Key 依赖

| 组件 | 需要 Key | 说明 |
|------|---------|------|
| Redis | 不需要 | 本地部署，无需 API |
| RabbitMQ | 不需要 | 本地部署，无需 API |
| CloudAMQP | 需要 | 托管的 RabbitMQ 服务 |
| Redis Cloud | 需要 | 托管的 Redis 服务 |
| Confluent Kafka | 需要 | 托管的 Kafka 服务 |
| Flower | 不需要 | 本地监控面板 |

## 7. 技术关系

- **上层**：Agent 任务编排 -> 业务逻辑
- **本层**：消息队列 -> 异步任务调度
- **下层**：Redis / RabbitMQ / Kafka -> 消息存储和路由
- **监控**：Flower / RedisInsight -> 任务可视化
- **结果存储**：PostgreSQL / Redis -> 任务结果持久化

## 8. 验收清单

- [ ] 理解消息队列在 Agent 系统中的作用
- [ ] 掌握 Celery + Redis 的安装和配置
- [ ] 能够定义 Celery 任务并正确使用重试机制
- [ ] 理解指数退避重试和死信队列的原理
- [ ] 掌握 RabbitMQ 的核心概念（Exchange/Queue/Routing Key）
- [ ] 能够使用 Redis Streams 实现轻量级消息队列
- [ ] 理解消息确认（ACK）机制
- [ ] 掌握链式任务和并行任务的编排方法
- [ ] 能够使用 Flower 监控任务状态
- [ ] 了解大任务拆分和幂等性设计

## 9. 学习资源

- Celery 官方文档：https://docs.celeryq.dev
- RabbitMQ 教程：https://www.rabbitmq.com/tutorials
- Kafka 文档：https://kafka.apache.org/documentation
- Redis Streams 介绍：https://redis.io/docs/data-types/streams
- Flower 监控：https://flower.readthedocs.io
- Celery 最佳实践：https://docs.celeryq.dev/en/stable/userguide/tasks.html
