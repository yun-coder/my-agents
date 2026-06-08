# 14 FastAPI：AI Agent API 服务框架

## 一、概念概述

### 1.1 什么是 FastAPI

FastAPI 是一个现代、高性能的 Python Web 框架，专为构建 API 而设计。它基于 Starlette（底层的 ASGI 框架）和 Pydantic（数据验证库），提供了自动生成 OpenAPI 文档、请求验证、异步支持等开箱即用的功能。

在 AI Agent 平台中，FastAPI 承担着"服务出口"的角色——将 Agent 和 RAG 的能力以 REST API 的形式暴露给前端或其他服务调用。

### 1.2 FastAPI 的核心优势

- **高性能**：与 NodeJS 和 Go 相当的 ASGI 性能
- **自动文档**：自动生成 Swagger UI 和 ReDoc 文档
- **类型安全**：基于 Pydantic 的请求/响应模型和自动验证
- **异步原生**：原生支持 async/await 异步编程
- **依赖注入**：内置依赖注入系统，便于模块化管理
- **生态丰富**：支持 SSE、WebSocket、OAuth2 等高级功能

### 1.3 在 AI Agent 平台中的角色

```text
前端 / 客户端
    |
    v
+-------------------+
|   FastAPI 服务     |    <-- 14_fastapi.md
|                   |
|  +-------------+  |    +------------------+
|  | Route       |  |    | LangGraph Agent  |
|  | /api/v1/... |--+--->|                  |
|  +-------------+  |    |  graph.py        |
|                   |    +------------------+
|  +-------------+  |    +------------------+
|  | Middleware   |  |    | RAG Generator   |
|  | Tracing     |--+--->|                  |
|  +-------------+  |    |  generator.py    |
|                   |    +------------------+
|  +-------------+  |    +------------------+
|  | SSE/WS      |  |    | LangFuse Tracing |
|  | Streaming   |  |    |  tracing.py      |
|  +-------------+  |    +------------------+
+-------------------+
```

---

## 二、核心原理

### 2.1 应用生命周期与入口

参考 `agent_platform/src/api/app.py` 的实现：

```python
# FastAPI 应用入口
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .middleware import TracingMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理：启动和关闭时的钩子。"""
    logger.info("Agent Platform 启动中...")
    # 启动时进行的初始化（连接数据库、加载模型等）
    yield
    logger.info("Agent Platform 已关闭。")
    # 关闭时的清理工作


def create_app() -> FastAPI:
    """应用工厂：创建并配置 FastAPI 应用。"""
    app = FastAPI(
        title="Agent Platform API",
        description="企业级 AI Agent 平台 - RAG + LangGraph + Tool Calling",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS 中间件（允许跨域请求）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 自定义追踪中间件
    app.add_middleware(TracingMiddleware)

    # 注册路由
    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.2 路由定义

参考 `agent_platform/src/api/routes.py` 中的路由实现：

```python
# API 路由定义
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()

# ---- Pydantic 请求/响应模型 ----

class QuestionRequest(BaseModel):
    """问答请求模型。"""
    question: str = Field(..., min_length=1, max_length=5000)
    session_id: str = Field(default="default")

class RAGResponse(BaseModel):
    """RAG 响应模型。"""
    answer: str
    sources: list[str]
    session_id: str

class AgentResponse(BaseModel):
    """Agent 响应模型。"""
    answer: str
    tool_log: list[str]
    session_id: str

class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str
    version: str

class DocumentUploadResponse(BaseModel):
    """文档上传响应。"""
    message: str
    file_count: int
    chunks_processed: int


# ---- API 端点 ----

@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查端点。"""
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/rag/ask", response_model=RAGResponse)
async def rag_ask(req: QuestionRequest):
    """RAG 问答接口。"""
    # 安全检查
    from ..security.guard import SecurityGuard
    from ..security.sanitizer import InputSanitizer

    guard = SecurityGuard()
    sanitizer = InputSanitizer()

    clean = sanitizer.sanitize(req.question)
    violations = guard.check_input(clean)
    if violations:
        raise HTTPException(
            status_code=400,
            detail=f"输入违反安全策略: {'; '.join(violations)}"
        )

    # RAG 生成
    rag = _get_rag()
    try:
        answer = rag.generate(clean)
    except Exception as e:
        logger.error("RAG 生成错误: %s", e)
        raise HTTPException(status_code=500, detail=f"生成回答失败: {e}")

    # 输出安全检测
    violations = guard.check_output(answer.answer)
    final_answer = answer.answer
    if violations:
        final_answer = (
            f"[回答已被安全护栏修改] "
            f"原回答包含违规内容: {'; '.join(violations)}"
        )

    return RAGResponse(
        answer=final_answer,
        sources=answer.sources,
        session_id=req.session_id,
    )


@router.post("/agent/ask", response_model=AgentResponse)
async def agent_ask(req: QuestionRequest):
    """Agent 对话接口。"""
    # ... 安全检查 + Agent 执行 ...
    agent = _get_agent()
    try:
        result = agent.run(clean, req.session_id)
    except Exception as e:
        logger.error("Agent 执行错误: %s", e)
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {e}")

    return AgentResponse(
        answer=result.get("final_answer", "未能生成回答"),
        tool_log=result.get("tool_log", []),
        session_id=req.session_id,
    )
```

### 2.3 依赖注入

FastAPI 的依赖注入系统可以自动解析函数参数，常用于共享资源、权限验证等。

```python
from fastapi import Depends, Header, HTTPException
from typing import Optional

# 定义依赖项
async def get_rag_generator():
    """获取 RAG 生成器实例（懒加载）。"""
    from ..rag.generator import RAGGenerator
    from ..vectordb.chroma_store import ChromaVectorStore
    from ..rag.retriever import Retriever
    from ..embeddings.local_bge import get_embedding_provider
    from ..config import load_config

    cfg = load_config()
    emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
    store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
    retriever = Retriever(store)
    return RAGGenerator(retriever)


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """API Key 鉴权依赖项。"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少 Authorization 头")
    # 验证 API Key 的逻辑
    api_key = authorization.replace("Bearer ", "")
    if not is_valid_api_key(api_key):
        raise HTTPException(status_code=403, detail="无效的 API Key")
    return api_key


async def pagination_params(
    page: int = 1,
    page_size: int = 20,
):
    """分页参数依赖项。"""
    return {"page": page, "page_size": min(page_size, 100)}


# 在路由中使用依赖项
@router.get("/documents")
async def list_documents(
    pagination: dict = Depends(pagination_params),
    api_key: str = Depends(verify_api_key),
    rag: RAGGenerator = Depends(get_rag_generator),
):
    """列出知识库中的文档（需要 API Key）。"""
    # 使用注入的依赖
    return {"page": pagination["page"], "data": [...]}
```

### 2.4 中间件（Middleware）

中间件在请求到达路由之前和响应返回客户端之前执行，适合做日志、追踪、限流等横切关注点。

参考 `agent_platform/src/api/middleware.py` 的 TracingMiddleware 实现：

```python
# 请求追踪中间件
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """为每个请求添加 trace_id 和耗时记录。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 生成或提取 trace_id
        trace_id = request.headers.get(
            "x-trace-id", str(uuid.uuid4())[:8]
        )
        request.state.trace_id = trace_id

        # 记录开始时间
        start = time.perf_counter()

        # 执行下一个中间件或路由
        response = await call_next(request)

        # 计算耗时
        elapsed = (time.perf_counter() - start) * 1000

        # 添加追踪头
        response.headers["x-trace-id"] = trace_id
        response.headers["x-response-time-ms"] = f"{elapsed:.1f}"

        # 日志记录
        logger.info(
            "%s %s -> %s (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
            trace_id,
        )

        return response


# 请求限流中间件
import asyncio
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的请求限流中间件。"""

    def __init__(self, app, max_requests: int = 60, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # 获取客户端 IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 清理过期记录
        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < self.window
        ]

        # 检查是否超过限制
        if len(self._requests[client_ip]) >= self.max_requests:
            return Response(
                content="请求过于频繁，请稍后再试。",
                status_code=429,
            )

        self._requests[client_ip].append(now)
        response = await call_next(request)
        return response
```

### 2.5 SSE 流式响应（Server-Sent Events）

SSE 是 AI Agent 平台中最重要的传输方式之一，用于实现流式输出。

```python
@router.post("/rag/stream")
async def rag_ask_stream(req: QuestionRequest):
    """流式 RAG 问答（SSE）。"""
    from ..security.guard import SecurityGuard
    from ..security.sanitizer import InputSanitizer

    guard = SecurityGuard()
    sanitizer = InputSanitizer()

    clean = sanitizer.sanitize(req.question)
    violations = guard.check_input(clean)
    if violations:
        raise HTTPException(
            status_code=400,
            detail=f"输入违反安全策略: {'; '.join(violations)}"
        )

    rag = _get_rag()

    async def generate():
        """异步生成器：逐块输出。"""
        try:
            for chunk in rag.generate_stream(clean):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [错误: {e}]\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )
```

### 2.6 WebSocket

WebSocket 适合需要双向通信的场景，如 Agent 的实时状态推送。

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """WebSocket 连接管理器。"""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: str):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(session_id)


manager = ConnectionManager()


@router.websocket("/agent/ws/{session_id}")
async def agent_websocket(ws: WebSocket, session_id: str):
    """Agent WebSocket 端点。"""
    await manager.connect(session_id, ws)
    try:
        while True:
            data = await ws.receive_text()
            # 处理用户消息并流式返回
            async for chunk in agent.stream(data, session_id):
                await ws.send_json(chunk)
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

### 2.7 背景任务（Background Tasks）

后台任务用于执行不需要等待结果的操作，如写入日志、发送通知等。

```python
from fastapi import BackgroundTasks

def log_interaction_to_db(question: str, answer: str, session_id: str):
    """将问答记录写入数据库（后台任务）。"""
    # 这里是数据库写入操作
    print(f"[DB] 记录交互: {session_id}")

def send_slack_notification(message: str):
    """发送 Slack 通知（后台任务）。"""
    print(f"[Slack] 通知: {message}")


@router.post("/rag/ask")
async def rag_ask_with_background(
    req: QuestionRequest,
    background_tasks: BackgroundTasks,
):
    """带后台任务的 RAG 问答。"""
    rag = _get_rag()
    answer = rag.generate(req.question)

    # 注册后台任务
    background_tasks.add_task(
        log_interaction_to_db,
        req.question, answer.answer, req.session_id
    )
    background_tasks.add_task(
        send_slack_notification,
        f"新问答: {req.question[:50]}..."
    )

    return RAGResponse(
        answer=answer.answer,
        sources=answer.sources,
        session_id=req.session_id,
    )
```

### 2.8 异常处理

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler

class AgentException(Exception):
    """Agent 平台自定义异常基类。"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class RAGException(AgentException):
    """RAG 相关异常。"""
    pass

class ToolException(AgentException):
    """工具调用异常。"""
    pass


# 注册全局异常处理器
@app.exception_handler(AgentException)
async def agent_exception_handler(request: Request, exc: AgentException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": exc.__class__.__name__,
        },
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": str(exc), "type": "ValidationError"},
    )
```

---

## 三、实战指南

### 3.1 启动与配置

```python
# 启动方式
# 方式1: 直接运行 app.py
python -m src.api.app

# 方式2: uvicorn 命令
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# 方式3: 生产环境启动
uvicorn src.api.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --timeout-keep-alive 120

# 方式4: 使用 uv
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

### 3.2 Pydantic 模型进阶

```python
from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime

class AdvancedQueryRequest(BaseModel):
    """高级查询请求。"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="用户问题",
    )
    session_id: str = Field(
        default="default",
        max_length=100,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="检索文档数量",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成温度",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="标签过滤",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """自定义验证：去除空白并检查内容。"""
        v = v.strip()
        if not v:
            raise ValueError("问题不能为空")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v and len(v) > 10:
            raise ValueError("标签数量不能超过 10 个")
        return v


class StreamingResponseModel(BaseModel):
    """流式响应的元数据模型。"""
    request_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    model: str = "gpt-4"
    finish_reason: Optional[str] = None
```

---

## 四、最佳实践

### 4.1 懒加载（Lazy Initialization）

AI Agent 平台中，RAG 生成器和 Agent 等重量级对象应该懒加载，避免每次请求都重新创建。

参考 `agent_platform/src/api/routes.py` 中的 `_get_rag()` 和 `_get_agent()` 模式：

```python
# 模块级懒加载
_rag = None
_agent = None

def _get_rag():
    global _rag
    if _rag is None:
        from ..vectordb.chroma_store import ChromaVectorStore
        from ..rag.retriever import Retriever
        from ..rag.generator import RAGGenerator
        from ..embeddings.local_bge import get_embedding_provider
        from ..config import load_config

        cfg = load_config()
        emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
        store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
        retriever = Retriever(store)
        _rag = RAGGenerator(retriever)
    return _rag

def _get_agent():
    global _agent
    if _agent is None:
        from ..agent.graph import AgentWorkflow
        _agent = AgentWorkflow(rag_generator=_get_rag())
    return _agent
```

### 4.2 错误处理层次

- **路由层**：捕获业务逻辑异常，转换为 HTTP 错误
- **中间件层**：捕获未处理异常，返回统一的错误格式
- **全局层**：通过异常处理器处理跨切面的错误

### 4.3 配置管理

```python
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    """应用配置，从环境变量读取。"""
    app_name: str = "Agent Platform"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

    # LLM 配置
    llm_api_key: str = ""
    llm_model: str = "gpt-4"

    # 存储配置
    chroma_persist_dir: str = "./chroma_db"
    vector_dimension: int = 768

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = AppConfig()
```

---

## 五、常见陷阱

### 5.1 同步阻塞调用

**陷阱**：在异步路由中调用了同步阻塞操作（如 `requests.get()`），阻塞了事件循环。

**解决**：使用异步客户端（`httpx.AsyncClient`）或将同步操作放入线程池。

```python
# 错误: 阻塞事件循环
@router.get("/blocking")
async def bad_endpoint():
    import requests
    response = requests.get("https://api.example.com/data")  # 阻塞!
    return response.json()

# 正确: 使用异步
@router.get("/non-blocking")
async def good_endpoint():
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### 5.2 SSE 连接泄漏

**陷阱**：客户端断开后，SSE 生成器未正确退出，导致资源泄漏。

**解决**：在生成器中捕获 `CancelledError` 或检查客户端连接状态。

### 5.3 WebSocket 异常处理

**陷阱**：未处理 `WebSocketDisconnect` 异常，导致服务器崩溃。

**解决**：在每个 WebSocket 端点中捕获并优雅处理断开连接。

### 5.4 中间件顺序

**陷阱**：中间件注册顺序错误，导致某些中间件未按预期生效。

**解决**：理解 `add_middleware` 的栈式执行顺序，将通用中间件（CORS、Tracing）放在外层。

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| FastAPI/Starlette | 否 | 纯框架，本地运行 |
| CORS Middleware | 否 | 纯框架功能 |
| Uvicorn | 否 | ASGI 服务器 |
| Pydantic 验证 | 否 | 纯 Python 库 |
| RAG/Agent 调用 | 取决于具体实现 | 见对应章节 |
| 外部 API 路由 | 取决于服务 | 由业务逻辑决定 |

---

## 七、技术关系

```text
FastAPI 生态架构:

ASGI 层
  +-- Uvicorn / Gunicorn + Uvicorn（生产部署）
  +-- ASGI 协议（异步网关接口）

FastAPI 核心
  +-- Starlette（底层的 ASGI 框架）
  +-- Pydantic（数据验证 + 序列化）
  +-- OpenAPI / Swagger（自动文档）

中间件层
  +-- CORSMiddleware（跨域）
  +-- TracingMiddleware（追踪）
  +-- RateLimitMiddleware（限流）

路由层
  +-- GET /health（健康检查）
  +-- POST /rag/ask（RAG 问答）
  +-- POST /rag/stream（SSE 流式）
  +-- POST /agent/ask（Agent 对话）
  +-- POST /documents/upload（文档管理）
  +-- WS /agent/ws（WebSocket）

业务层
  +-- RAG Generator（rag/generator.py）
  +-- Agent Workflow（agent/graph.py）
  +-- LangFuse Tracing（observability/tracing.py）
```

---

## 八、验收清单

- [ ] 理解 FastAPI 应用的生命周期（lifespan 事件）
- [ ] 掌握路由定义和参数验证（Path、Query、Body）
- [ ] 会用 Pydantic 模型定义请求/响应格式
- [ ] 理解依赖注入的原理和使用方式
- [ ] 能编写自定义中间件（Tracing、RateLimit）
- [ ] 掌握 SSE 流式响应的实现
- [ ] 理解 WebSocket 的双向通信模式
- [ ] 能使用 BackgroundTasks 执行异步任务
- [ ] 理解懒加载模式在 AI 服务中的应用
- [ ] 能配置 CORS 和生产环境部署参数

---

## 九、学习资源

- **FastAPI 官方文档**: https://fastapi.tiangolo.com/
- **Pydantic 文档**: https://docs.pydantic.dev/latest/
- **Starlette 文档**: https://www.starlette.io/
- **Uvicorn 部署指南**: https://www.uvicorn.org/deployment/
- **平台参考代码**: agent_platform/src/api/ (app.py, routes.py, middleware.py)
- **SSE 规范**: https://html.spec.whatwg.org/multipage/server-sent-events.html
