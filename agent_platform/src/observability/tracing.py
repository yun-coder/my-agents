"""LangFuse 追踪集成（兼容 langfuse v2/v3/v4）。

设计目标：
- 业务代码只 import `traced_operation` 一个上下文管理器，零侵入
- 自动建立 trace + span 树，函数返回值 / 异常自动入库
- 进程退出时统一 flush
- 失败优雅降级为纯日志，绝不阻塞主流程

v4 SDK 关键变更（相对 v2/3）：
    - 入口从 `client.trace()` / `client.span()` 改为 `client.start_as_current_observation()`
    - 嵌套通过 OpenTelemetry context 自动完成，无需手动维护 span 栈
    - usage 字段改名为 `usage_details`、模型参数叫 `model_parameters`
"""

from __future__ import annotations

import atexit
import logging
import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

logger = logging.getLogger(__name__)

_client: Any | None = None
_enabled: bool = False
_init_lock = threading.Lock()
_fail_count: int = 0          # 启动期失败次数；>0 时不再重试
_sdk_version: tuple[int, ...] = (0,)  # 检测到 (4, 6, 1) 时走 v4 路径


def _get_settings() -> tuple[bool, str, str, str]:
    """从 dev.json / dev.local.json / 环境变量汇总配置。

    优先级: 环境变量 > dev.local.json > dev.json。
    """
    enabled = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sk = os.getenv("LANGFUSE_SECRET_KEY", "")

    if not pk or not sk:
        try:
            from src.config import load_config  # 延迟导入，避免循环
            cfg = load_config()
            if cfg.langfuse:
                host = host or cfg.langfuse.host
                pk = pk or cfg.langfuse.public_key
                sk = sk or cfg.langfuse.secret_key
                enabled = enabled and cfg.langfuse.enabled
        except Exception:
            pass

    return enabled, host, pk, sk


def _detect_sdk_version() -> tuple[int, ...]:
    """返回 (major, minor, patch)，失败时返回 (0,)。"""
    try:
        from langfuse import __version__ as v
        parts: list[int] = []
        for chunk in v.split(".")[:3]:
            try:
                parts.append(int(chunk))
            except ValueError:
                break
        return tuple(parts) or (0,)
    except Exception:
        return (0,)


def init_tracing(
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str | None = None,
) -> bool:
    """初始化 LangFuse 客户端。失败返回 False（不抛）。"""
    global _client, _enabled, _fail_count, _sdk_version
    with _init_lock:
        if _enabled:
            return True
        if _fail_count > 0:
            return False

        enabled, default_host, default_pk, default_sk = _get_settings()
        if not enabled:
            logger.info("LangFuse 追踪被配置禁用（LANGFUSE_ENABLED=false）")
            return False

        pk = public_key or default_pk
        sk = secret_key or default_sk
        h = host or default_host

        # 占位符检测：源码默认 key 是 sk-lf-...4914 这种中间带 ... 的，识别并拒掉
        if not pk or not sk or "..." in pk or "..." in sk:
            logger.warning(
                "LangFuse 密钥缺失或为占位符（含 '...'），追踪已禁用。请在 "
                "dev.local.json / 环境变量里填写真实 pk-lf- / sk-lf- 密钥。"
            )
            _fail_count = 1
            return False

        try:
            from langfuse import Langfuse
            _client = Langfuse(public_key=pk, secret_key=sk, host=h)
            _sdk_version = _detect_sdk_version()
            _enabled = True
            logger.info(
                "LangFuse 追踪已启用：%s (sdk v%s)",
                h, ".".join(map(str, _sdk_version)),
            )
            atexit.register(_shutdown)
            return True
        except Exception as e:
            logger.warning("LangFuse 初始化失败，追踪已禁用：%s", e)
            _fail_count = 1
            return False


def _shutdown() -> None:
    if _client is not None:
        try:
            _client.flush()
        except Exception:
            pass


def flush() -> None:
    """手动 flush —— 烟测 / 短脚本退出前调用。"""
    _shutdown()


def is_enabled() -> bool:
    return _enabled and _client is not None


class _NullOp:
    """降级占位：业务代码 `op.update(...)` 不报错。"""

    def update(self, **_kwargs: Any) -> None:
        pass

    def score(self, **_kwargs: Any) -> None:
        pass

    def end(self, **_kwargs: Any) -> None:
        pass


# ──────────── 内部：构造一次 observation 并把业务 op 包裹起来 ────────────


class _Observation:
    """统一包装层：把 v4 start_as_current_observation / v2-v3 trace+span
    的差异藏起来，对外只暴露 update / end 两个方法。"""

    def __init__(self, raw: Any) -> None:
        self._raw = raw

    def update(
        self,
        *,
        output: Any = None,
        metadata: dict[str, Any] | None = None,
        usage: dict[str, int] | None = None,
    ) -> None:
        """更新 observation 的输出 / 元数据 / token 用量。"""
        kwargs: dict[str, Any] = {}
        if output is not None:
            kwargs["output"] = output
        if metadata is not None:
            kwargs["metadata"] = metadata
        if usage is not None:
            # v4 用 usage_details / v2-3 用 usage；按 SDK 版本分派
            if _sdk_version >= (3,):
                kwargs["usage_details"] = usage
            else:
                kwargs["usage"] = usage
        try:
            if hasattr(self._raw, "update"):
                self._raw.update(**kwargs)
        except Exception as e:
            logger.debug("observation update 失败：%s", e)

    def end(self) -> None:
        try:
            if hasattr(self._raw, "end"):
                self._raw.end()
        except Exception:
            pass


@contextmanager
def traced_operation(
    name: str,
    *,
    input: Any = None,
    metadata: dict[str, Any] | None = None,
    as_type: str = "span",          # "span" | "generation"
    model: str | None = None,
    usage: dict[str, int] | None = None,
) -> Iterator[_Observation]:
    """统一追踪入口——业务代码只 use 这一个。

    用法::

        with traced_operation("llm.generate",
                              input=messages, model=cfg.model,
                              as_type="generation") as op:
            response = client.chat(messages)
            op.update(output=response.content,
                      usage={"input": n, "output": m, "total": n+m})

    行为：
        - 启用时：v4 走 `start_as_current_observation`（自动挂 OTel 上下文），
                  v2/3 走 `trace() + span/generation`（手工管理）
        - 禁用时：降级为 _NullOp + 日志耗时打印，业务完全无感
        - 异常时：原样向上抛，不吞
    """
    if not is_enabled():
        t0 = time.perf_counter()
        try:
            yield _NullOp()  # type: ignore[return-value]
        except Exception as e:
            logger.info(
                "[trace↓] %s 失败 (%.1fms): %s",
                name, (time.perf_counter() - t0) * 1000, e,
            )
            raise
        else:
            logger.info(
                "[trace↓] %s 完成 (%.1fms)",
                name, (time.perf_counter() - t0) * 1000,
            )
        return

    # 启用态
    try:
        if _sdk_version >= (3,):
            # v3/v4: start_as_current_observation 本身就是 context manager
            cm = _open_observation(name, input=input, metadata=metadata,
                                   as_type=as_type, model=model, usage=usage)
            with cm as opened:
                yield _Observation(opened)
        else:
            # v2: trace()/span()/generation() 返回普通对象，需手动 .end()
            op_obj = _open_observation(name, input=input, metadata=metadata,
                                       as_type=as_type, model=model, usage=usage)
            try:
                yield _Observation(op_obj)
            finally:
                try:
                    op_obj.end()
                except Exception:
                    pass
    except Exception as e:
        logger.warning("LangFuse 追踪失败（%s）：%s", name, e)
        yield _NullOp()  # type: ignore[return-value]


def _open_observation(
    name: str,
    *,
    input: Any,
    metadata: dict[str, Any] | None,
    as_type: str,
    model: str | None,
    usage: dict[str, int] | None,
) -> Any:
    """按 SDK 版本分派到对应的 API。"""
    if _sdk_version >= (3,):
        # v3/v4 推荐 API：start_as_current_observation，自动 OTel 上下文
        kwargs: dict[str, Any] = {
            "name": name,
            "as_type": "generation" if as_type == "generation" else "span",
            "input": input,
        }
        if metadata:
            kwargs["metadata"] = metadata
        if model:
            kwargs["model"] = model
        if usage:
            kwargs["usage_details"] = usage
        return _client.start_as_current_observation(**kwargs)  # type: ignore[union-attr]

    # v2 旧 API：trace() + span/generation
    if as_type == "generation" and model:
        trace = _client.trace(name=name, metadata=metadata or {})  # type: ignore[union-attr]
        return trace.generation(name=name, model=model, input=input)
    trace = _client.trace(name=name, metadata=metadata or {})  # type: ignore[union-attr]
    return trace.span(name=name, input=input)
