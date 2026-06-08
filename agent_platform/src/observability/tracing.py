"""LangFuse 追踪集成：自动记录 LLM 调用、RAG 检索、工具执行。

本模块封装 LangFuse 自托管（Docker, localhost:3000）的追踪能力。
如果 LangFuse 不可用，优雅降级为纯日志模式。
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

_langfuse_client = None
_tracing_enabled = False


def init_tracing(
    public_key: str,
    secret_key: str,
    host: str = "http://localhost:3000",
) -> None:
    """初始化 LangFuse 追踪客户端。"""
    global _langfuse_client, _tracing_enabled
    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        _tracing_enabled = True
        logger.info("LangFuse 追踪已启用：%s", host)
    except Exception as e:
        logger.warning("LangFuse 初始化失败，追踪已禁用：%s", e)
        _tracing_enabled = False


def trace_generation(
    name: str,
    input_data: str,
    output_data: str,
    *,
    model: str = "",
    usage: dict[str, int] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """记录一次 LLM 生成调用。"""
    if not _tracing_enabled or _langfuse_client is None:
        return
    try:
        trace = _langfuse_client.trace(name=name)
        trace.generation(
            name=f"{name}-generation",
            model=model,
            input=input_data,
            output=output_data,
            usage=usage,
            metadata=metadata or {},
        )
        _langfuse_client.flush()
    except Exception as e:
        logger.debug("LangFuse 记录失败：%s", e)


def trace_retrieval(
    name: str,
    query: str,
    results: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    """记录一次 RAG 检索操作。"""
    if not _tracing_enabled or _langfuse_client is None:
        return
    try:
        trace = _langfuse_client.trace(name=name)
        trace.span(
            name=f"{name}-retrieval",
            input=query,
            output={"documents": [r.get("text", "")[:200] for r in results]},
            metadata=metadata or {},
        )
        _langfuse_client.flush()
    except Exception as e:
        logger.debug("LangFuse 记录失败：%s", e)


@contextmanager
def traced_operation(name: str, **metadata: Any):
    """上下文管理器：自动追踪一段操作的耗时和结果。"""
    import time

    start = time.perf_counter()
    error = None
    try:
        yield
    except Exception as e:
        error = e
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        if error:
            logger.info("[LangFuse] %s 失败 (%.1fms): %s", name, elapsed, error)
        else:
            logger.info("[LangFuse] %s 完成 (%.1fms)", name, elapsed)
