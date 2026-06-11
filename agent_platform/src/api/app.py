"""FastAPI 应用入口。

启动方式:
    uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000
"""

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
    logger.info("Agent Platform 启动中...")
    # 兜底 init_tracing —— 直接 uvicorn 启动不走 CLI 时也能开启追踪
    try:
        from src.observability import init_tracing
        if init_tracing():
            logger.info("LangFuse 追踪已就绪。")
    except Exception as e:
        logger.warning("LangFuse 初始化异常：%s", e)
    yield
    logger.info("Agent Platform 已关闭。")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent Platform API",
        description="企业级 AI Agent 平台 - RAG + LangGraph + Tool Calling",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TracingMiddleware)

    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
