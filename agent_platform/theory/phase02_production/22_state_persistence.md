# 第22章 Agent 状态持久化：生产级状态管理

> 状态持久化是生产级 Agent 系统的基础设施。当用户中断对话、系统重启或流量分发到不同实例时，状态持久化确保用户可以从上次中断的地方无缝继续。本章深入分析 Redis、PostgreSQL 以及 LangGraph Checkpoint 等状态管理方案。

---

## 1. 概念概述

### 1.1 什么是 Agent 状态

Agent 状态是 Agent 在运行过程中需要保存的所有数据，包括：

- **会话状态**：当前对话的消息历史、工具调用记录
- **执行状态**：当前正在执行的步骤、已完成和待完成的节点
- **上下文状态**：注入的 RAG 结果、临时变量
- **审计状态**：操作日志、Token 消耗、执行时间

### 1.2 为什么需要状态持久化

| 场景 | 无持久化的问题 | 持久化的好处 |
|------|---------------|-------------|
| 服务重启 | 所有会话丢失 | 重启后恢复进行中的会话 |
| 多实例部署 | 请求路由到不同实例，上下文丢失 | 共享状态存储，任意实例可恢复 |
| 长时间任务 | 连接超时导致任务中断 | 任务可在后台继续，用户随时查看进度 |
| 审计合规 | 无法追溯历史操作 | 完整的操作日志和状态快照 |
| 错误恢复 | 异常退出后无法恢复 | 从最后一个检查点继续执行 |

### 1.3 状态持久化的层次

```
应用层状态  ──→  Agent 会话上下文（消息历史、工具记录）
     │
执行层状态  ──→  LangGraph 检查点（当前节点、执行进度）
     │
存储层状态  ──→  Redis（快速会话缓存）、PostgreSQL（审计日志）
```

---

## 2. 核心原理

### 2.1 Redis 会话状态管理

Redis 适合存储高频访问的会话状态，利用 TTL 自动过期机制管理生命周期：

```python
"""Redis 会话状态管理器。"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisSessionManager:
    """基于 Redis 的会话状态管理。

    用法:
        mgr = RedisSessionManager("redis://localhost:6379/0")
        await mgr.set_session("user-123", {"messages": [...]})
        state = await mgr.get_session("user-123")
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        session_ttl: int = 3600,  # 1 小时
    ):
        self._redis_url = redis_url
        self._session_ttl = session_ttl
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def set_session(
        self,
        session_id: str,
        state: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """保存会话状态。"""
        r = await self._get_redis()
        key = f"session:{session_id}"
        await r.setex(
            key,
            ttl or self._session_ttl,
            json.dumps(state, ensure_ascii=False, default=str),
        )

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """获取会话状态。"""
        r = await self._get_redis()
        key = f"session:{session_id}"
        data = await r.get(key)
        if data:
            return json.loads(data)
        return None

    async def update_session(
        self,
        session_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """部分更新会话状态。"""
        state = await self.get_session(session_id)
        if state is None:
            return None
        state.update(updates)
        await self.set_session(session_id, state)
        return state

    async def delete_session(self, session_id: str) -> None:
        """删除会话。"""
        r = await self._get_redis()
        await r.delete(f"session:{session_id}")

    async def extend_ttl(self, session_id: str, ttl: int = 3600) -> None:
        """延长会话过期时间。"""
        r = await self._get_redis()
        await r.expire(f"session:{session_id}", ttl)

    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在。"""
        r = await self._get_redis()
        return await r.exists(f"session:{session_id}") > 0

    async def close(self) -> None:
        """关闭 Redis 连接。"""
        if self._redis:
            await self._redis.close()
            self._redis = None
```

### 2.2 PostgreSQL 审计日志

PostgreSQL 适合存储不可变、需要强一致性的审计日志和状态快照：

```python
"""PostgreSQL 审计日志管理器。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class AuditLogger:
    """基于 PostgreSQL 的审计日志。

    用法:
        logger = AuditLogger("postgresql://user:pass@localhost:5432/agent")
        await logger.log_action("user-123", "tool_call", {"tool": "search"})
        history = await logger.get_history("user-123", limit=50)
    """

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=2,
                max_size=10,
            )
            await self._init_tables()
        return self._pool

    async def _init_tables(self) -> None:
        """初始化表结构。"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_audit_log (
                    id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(128) NOT NULL,
                    user_id VARCHAR(128) NOT NULL,
                    action_type VARCHAR(64) NOT NULL,
                    action_data JSONB,
                    llm_model VARCHAR(64),
                    token_count INTEGER DEFAULT 0,
                    execution_time_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    INDEX idx_audit_session (session_id),
                    INDEX idx_audit_user (user_id),
                    INDEX idx_audit_created (created_at)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_checkpoints (
                    id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(128) NOT NULL,
                    checkpoint_type VARCHAR(32) NOT NULL,
                    state_snapshot JSONB NOT NULL,
                    parent_checkpoint_id BIGINT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    INDEX idx_checkpoint_session (session_id)
                );
            """)

    async def log_action(
        self,
        session_id: str,
        user_id: str,
        action_type: str,
        action_data: dict[str, Any] | None = None,
        *,
        llm_model: str | None = None,
        token_count: int = 0,
        execution_time_ms: int = 0,
    ) -> int:
        """记录操作日志。"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO agent_audit_log
                   (session_id, user_id, action_type, action_data,
                    llm_model, token_count, execution_time_ms)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   RETURNING id""",
                session_id,
                user_id,
                action_type,
                json.dumps(action_data, ensure_ascii=False) if action_data else None,
                llm_model,
                token_count,
                execution_time_ms,
            )
            return row["id"]

    async def save_checkpoint(
        self,
        session_id: str,
        state: dict[str, Any],
        checkpoint_type: str = "agent_state",
        parent_id: int | None = None,
    ) -> int:
        """保存状态检查点。"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO agent_checkpoints
                   (session_id, checkpoint_type, state_snapshot, parent_checkpoint_id)
                   VALUES ($1, $2, $3, $4)
                   RETURNING id""",
                session_id,
                checkpoint_type,
                json.dumps(state, ensure_ascii=False, default=str),
                parent_id,
            )
            return row["id"]

    async def get_latest_checkpoint(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        """获取最新的检查点。"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT id, state_snapshot, created_at
                   FROM agent_checkpoints
                   WHERE session_id = $1
                   ORDER BY id DESC
                   LIMIT 1""",
                session_id,
            )
            if row:
                return {
                    "id": row["id"],
                    "state": json.loads(row["state_snapshot"]),
                    "created_at": row["created_at"].isoformat(),
                }
            return None

    async def get_history(
        self,
        session_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """查询审计历史。"""
        pool = await self._get_pool()
        conditions = []
        params = []
        param_idx = 1

        if session_id:
            conditions.append(f"session_id = ${param_idx}")
            params.append(session_id)
            param_idx += 1
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        query = f"""SELECT id, session_id, user_id, action_type, action_data,
                           llm_model, token_count, execution_time_ms, created_at
                    FROM agent_audit_log
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_idx} OFFSET ${param_idx + 1}"""

        params.extend([limit, offset])
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [
                {
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "user_id": r["user_id"],
                    "action_type": r["action_type"],
                    "action_data": json.loads(r["action_data"]) if r["action_data"] else None,
                    "llm_model": r["llm_model"],
                    "token_count": r["token_count"],
                    "execution_time_ms": r["execution_time_ms"],
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows
            ]

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
```

### 2.3 LangGraph Checkpoint 后端集成

```python
"""LangGraph Checkpoint 与外部存储集成。"""

from __future__ import annotations

from typing import Any
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver


def create_pg_checkpointer(
    dsn: str,
    *,
    pool_size: int = 5,
    max_retries: int = 3,
) -> PostgresSaver:
    """创建 PostgreSQL 检查点后端。"""
    return PostgresSaver.from_conn_string(
        dsn,
        pool_size=pool_size,
        max_retries=max_retries,
    )


def create_sqlite_checkpointer(db_path: str) -> SqliteSaver:
    """创建 SQLite 检查点后端（单机部署）。"""
    return SqliteSaver.from_conn_string(db_path)
```

### 2.4 任务中断与恢复

实现完整的任务中断-恢复生命周期：

```python
"""Agent 任务管理器：中断与恢复。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)

TaskID = str


class InterruptableTaskManager:
    """可中断任务管理器。

    支持：
    - 任务暂停/恢复
    - 进度追踪
    - 超时控制
    - 错误恢复
    """

    def __init__(self, state_manager: RedisSessionManager):
        self._state = state_manager
        self._active_tasks: dict[TaskID, asyncio.Task] = {}
        self._pause_events: dict[TaskID, asyncio.Event] = {}

    async def start_task(
        self,
        task_id: TaskID,
        coro_factory: Callable[[], asyncio.coroutine],
        user_id: str,
    ) -> dict[str, Any]:
        """启动一个可中断的任务。"""
        # 保存初始状态
        await self._state.set_session(task_id, {
            "task_id": task_id,
            "user_id": user_id,
            "status": "running",
            "progress": 0.0,
            "started_at": datetime.now().isoformat(),
            "paused_at": None,
            "error": None,
            "result": None,
        })

        # 创建暂停事件
        self._pause_events[task_id] = asyncio.Event()
        self._pause_events[task_id].set()  # 默认不暂停

        # 启动后台任务
        task = asyncio.create_task(self._run_task(task_id, coro_factory))
        self._active_tasks[task_id] = task
        return await self._state.get_session(task_id)

    async def _run_task(
        self,
        task_id: TaskID,
        coro_factory: Callable,
    ) -> None:
        """运行任务（支持暂停检查）。"""
        try:
            # 每执行一步之前检查是否被暂停
            await self._check_paused(task_id)
            await self._update_progress(task_id, 0.1)

            coro = coro_factory()
            result = await coro

            await self._state.update_session(task_id, {
                "status": "completed",
                "progress": 1.0,
                "result": result,
                "completed_at": datetime.now().isoformat(),
            })
        except asyncio.CancelledError:
            await self._state.update_session(task_id, {
                "status": "cancelled",
                "completed_at": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error("任务 %s 失败：%s", task_id, e)
            await self._state.update_session(task_id, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat(),
            })
        finally:
            self._active_tasks.pop(task_id, None)
            self._pause_events.pop(task_id, None)

    async def pause_task(self, task_id: TaskID) -> bool:
        """暂停任务。"""
        if task_id not in self._pause_events:
            return False
        self._pause_events[task_id].clear()
        await self._state.update_session(task_id, {
            "status": "paused",
            "paused_at": datetime.now().isoformat(),
        })
        return True

    async def resume_task(self, task_id: TaskID) -> bool:
        """恢复已暂停的任务。"""
        if task_id not in self._pause_events:
            return False
        self._pause_events[task_id].set()
        await self._state.update_session(task_id, {
            "status": "running",
            "paused_at": None,
        })
        return True

    async def cancel_task(self, task_id: TaskID) -> bool:
        """取消任务。"""
        task = self._active_tasks.get(task_id)
        if task is None:
            return False
        task.cancel()
        return True

    async def get_task_status(self, task_id: TaskID) -> dict[str, Any] | None:
        """获取任务状态。"""
        return await self._state.get_session(task_id)

    async def _check_paused(self, task_id: TaskID) -> None:
        """检查是否被暂停，如果是则等待恢复。"""
        event = self._pause_events.get(task_id)
        if event is None:
            return
        await event.wait()  # 如果暂停，这里会阻塞直到 resume

    async def _update_progress(self, task_id: TaskID, progress: float) -> None:
        """更新进度。"""
        await self._state.update_session(task_id, {"progress": progress})

    async def close(self) -> None:
        """清理所有任务。"""
        for task_id in list(self._active_tasks.keys()):
            await self.cancel_task(task_id)
        await self._state.close()
```

---

## 3. 实战指南

### 3.1 生产级状态管理集成

将 Redis、PostgreSQL 和 LangGraph Checkpoint 集成到统一的状态管理：

```python
"""生产级状态管理器：集成 Redis + PostgreSQL + Checkpoint。"""

from __future__ import annotations

import logging
from typing import Any

from .redis_manager import RedisSessionManager
from .audit_logger import AuditLogger
from .task_manager import InterruptableTaskManager
from ...agent.graph import AgentWorkflow

logger = logging.getLogger(__name__)


class ProductionStateManager:
    """统一的状态管理器。"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        pg_dsn: str = "postgresql://localhost:5432/agent",
    ):
        self.session = RedisSessionManager(redis_url, session_ttl=7200)
        self.audit = AuditLogger(pg_dsn)
        self.tasks = InterruptableTaskManager(self.session)
        self._workflows: dict[str, AgentWorkflow] = {}

    async def execute_agent(
        self,
        workflow: AgentWorkflow,
        session_id: str,
        user_id: str,
        query: str,
    ) -> dict[str, Any]:
        """执行 Agent 并持久化状态。"""
        # 1. 检查是否有已暂停的会话
        previous_state = await self.session.get_session(session_id)

        # 2. 记录开始
        start_time = __import__("time").time()
        await self.audit.log_action(
            session_id, user_id, "agent_start",
            {"query": query},
        )

        try:
            # 3. 执行 Agent
            result = workflow.run(query, session_id=session_id)

            # 4. 保存状态到 Redis
            await self.session.set_session(session_id, result)

            # 5. 记录审计日志
            elapsed_ms = int((__import__("time").time() - start_time) * 1000)
            await self.audit.log_action(
                session_id, user_id, "agent_complete",
                {"final_answer": result.get("final_answer", "")[:200]},
                llm_model=workflow._llm.model,
                token_count=result.get("token_count", 0),
                execution_time_ms=elapsed_ms,
            )

            # 6. 保存检查点
            await self.audit.save_checkpoint(session_id, result)

            return result

        except Exception as e:
            logger.error("Agent 执行失败：%s", e)
            await self.audit.log_action(
                session_id, user_id, "agent_error",
                {"error": str(e)},
            )
            raise

    async def close(self) -> None:
        """关闭所有连接。"""
        await self.session.close()
        await self.audit.close()
        await self.tasks.close()
```

---

## 4. 最佳实践

1. **冷热数据分离**：Redis 存储热数据（进行中的会话），PostgreSQL 存储冷数据（完成的会话和审计日志）。

2. **TTL 策略**：Redis 会话设置合理的 TTL（建议 1-2 小时），超时后自动清理。

3. **幂等性设计**：每个操作生成唯一 ID，存储层做去重，确保重复请求不影响状态一致性。

4. **乐观锁**：在更新状态时使用版本号或时间戳，防止并发冲突。

5. **定期快照**：长时间运行的任务定期保存检查点，减少恢复时的重复计算。

6. **审计完整性**：审计日志只追加不修改，采用 Append-Only 模式，保证可追溯性。

7. **连接池管理**：数据库连接使用连接池，避免频繁创建销毁连接。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| Redis 数据丢失 | 未设置持久化导致重启后数据丢失 | 启用 RDB/AOF 持久化，或使用 Redis Sentinel |
| 并发状态覆盖 | 多实例同时更新同一会话导致数据覆盖 | 使用 Redis WATCH 或 Lua 脚本做原子更新 |
| 审计日志膨胀 | 日志表无限增长，查询变慢 | 定期归档旧日志，保留最近 90 天数据 |
| 检查点过大 | 保存完整 State 导致存储暴涨 | 只保存增量变化，全量快照定期做 |
| 连接泄露 | 未关闭数据库连接导致连接池耗尽 | 使用上下文管理器（async with）确保释放 |
| 断线恢复失败 | Agent 断线后状态已过期无法恢复 | 实现 Graceful Degradation，过期则新建会话 |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| Redis | 否 | 开源缓存服务，无需 API Key |
| PostgreSQL | 否 | 开源关系数据库，配置连接字符串即可 |
| LangGraph Checkpoint | 否 | 框架内置功能，无需额外 Key |
| LLM 客户端 | 是 | Agent 依赖 LLM API Key |
| Redis Cloud（可选） | 是 | 托管 Redis 需要云服务 API Key |
| PostgreSQL Cloud（可选） | 是 | 托管数据库需要云服务连接凭证 |

---

## 7. 技术关系

```
Agent 工作流
    │
    ├── 每次节点执行 ──→ LangGraph Checkpointer ──→ PostgreSQL 检查点表
    │
    ├── 会话状态 ──→ Redis Session Manager
    │   ├── get_session(session_id)
    │   ├── set_session(session_id, state)
    │   └── delete_session(session_id)
    │
    ├── 审计日志 ──→ PostgreSQL Audit Logger
    │   ├── log_action(session, user, action, data)
    │   └── get_history(session_id)
    │
    └── 任务管理 ──→ InterruptableTaskManager
        ├── pause / resume
        ├── checkpoint / restore
        └── timeout / cancel
```

---

## 8. 验收清单

- [ ] 理解 Redis 和 PostgreSQL 在状态管理中的不同定位
- [ ] 学会使用 Redis 存储和读取会话状态
- [ ] 学会使用 PostgreSQL 记录审计日志
- [ ] 掌握 LangGraph Checkpoint 与 PostgreSQL 的集成
- [ ] 理解任务中断和恢复的实现原理
- [ ] 掌握幂等性设计的基本原则
- [ ] 理解冷热数据分离的架构模式
- [ ] 能设计审计日志表结构
- [ ] 掌握连接池管理和资源清理
- [ ] 理解 TTL 策略和过期数据清理

---

## 9. 学习资源

- Redis 官方文档：https://redis.io/docs/
- asyncpg PostgreSQL 驱动：https://magicstack.github.io/asyncpg/
- LangGraph Persistence：https://langchain-ai.github.io/langgraph/concepts/persistence/
- PostgreSQL JSONB 文档：https://www.postgresql.org/docs/current/datatype-json.html
- 项目源码参考：agent_platform/src/api/middleware.py
- Redis TTL 设计模式：https://redis.io/glossary/redis-ttl/
