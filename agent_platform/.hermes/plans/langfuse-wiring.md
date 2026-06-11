# LangFuse 监听接入方案

> **目标**：让 `agent_platform` 的 LLM 调用、RAG 检索、Agent 工具调用三类事件在自托管 LangFuse（`http://localhost:3000`）的 Traces 页面可见。
> **前提**：LangFuse Docker 容器已起好，`curl http://localhost:3000/api/public/health` 返 200；已重新生成一对真 `pk-lf-...` / `sk-lf-...`（dev.json 里那两个 `sk-lf-...` 是占位符，不能用）。

---

## 调整总览

| 步骤 | 文件 | 动作 | 关键点 |
|---|---|---|---|
| 1 | `agent_platform/compose.yaml` | 追加 `langfuse` + `postgres` 服务 | 跟 README 模板对齐 |
| 2 | `.gitignore` | 忽略 `dev.local.json` / `.env` | 密钥不再入库 |
| 3 | `dev.local.json`（新建） | 写真实密钥 | 优先级最高 |
| 4 | `src/observability/tracing.py` | 改 `init_tracing` 默认值 + 真实用 key | 顺手把日志也升级 |
| 5 | `src/observability/__init__.py` | 导出公共 API | 让 `from ...observability import init_tracing` 干净 |
| 6 | `src/config.py` | 加 `enabled` 默认值读取 + 优先 `dev.local.json` | — |
| 7 | `src/llm/client.py` | 启动期自动 `init_tracing` | **关键接入点** |
| 8 | `src/rag/generator.py` | 检索与生成处插入 span/generation | — |
| 9 | `src/rag/retriever.py` | 检索子层记 span | （视情况） |
| 10 | `src/agent/graph.py` | Agent 工具调用包 span | — |
| 11 | `src/api/app.py` | FastAPI lifespan 里兜底 init | 防止直接 uvicorn 启动漏掉 |
| 12 | 烟测脚本 | 验证 trace 真的进了 dashboard | — |

---

## 步骤 1：补 LangFuse Docker 服务

`agent_platform/compose.yaml` 当前**没有 langfuse 服务**——这是为什么 `localhost:3000` 死活起不来的根本原因。

`integrations/langfuse/README.md` 给了完整 docker-compose 模板，把它合并进 `agent_platform/compose.yaml`（一个文件管全栈）：

```yaml
# 在 agent_platform/compose.yaml 末尾追加：
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse_pass
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse"]
      interval: 5s
      timeout: 5s
      retries: 5

  langfuse:
    image: ghcr.io/langfuse/langfuse:3
    depends_on:
      postgres: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse_pass@postgres:5432/langfuse
      NEXTAUTH_SECRET: change-me-in-prod-32bytes
      NEXTAUTH_URL: http://localhost:3000
      SALT: change-me-salt
    ports: ["3000:3000"]
    volumes: [langfuse_data:/data]

volumes:
  postgres_data:
  langfuse_data:
```

> ⚠️ 容器里**不能写 `localhost:3000`**——容器 `localhost` 是自己。`init_tracing` 用 host 的 `http://localhost:3000` 是因为 Python 进程跑在 host 上；如果以后也走容器内互调，要把 host 改成 `http://langfuse:3000`。

启动 + 健康检查：

```bash
cd agent_platform
docker compose up -d postgres langfuse
docker compose logs -f langfuse   # 看到 "ready" 字样再 Ctrl-C
curl -sS http://localhost:3000/api/public/health
# 期望: 200 OK + {"status":"ok"...}
```

---

## 步骤 2 & 3：密钥隔离（不 commit 真 key）

`D:/学习院/my-agents/.gitignore` 加：

```
dev.local.json
.env
.env.local
```

新建 `D:/学习院/my-agents/dev.local.json`（**不进 git**）：

```json
{
  "langfuse": {
    "enabled": true,
    "host": "http://localhost:3000",
    "public_key": "pk-lf-真-public-key",
    "secret_key": "sk-lf-真-secret-key-完整无省略"
  }
}
```

---

## 步骤 4：升级 `src/observability/tracing.py`

现版 4 个问题要修：
1. 默认值是源码里硬编码的旧 key → 改用 `None` 强制显式传参
2. `trace_generation` / `trace_retrieval` 每次都 `flush()`，高频场景会卡 → 改成只在关闭时/异常时 flush
3. 没有 `trace_event` / `score` / 主 trace 概念 → 加个 `traced_operation` 升级版，能把多个 span 串成一条 trace
4. 错误吞在 `logger.debug` 里，dev 阶段看不到 → 升级为 `warning` + 一次性计数器

**新签名（替换整个文件）**：

```python
"""LangFuse 追踪集成。

设计目标：
- 业务代码只 import `traced_operation` 上下文管理器，零侵入
- 上下文管理器自动建立 trace + span 树，函数返回值 / 异常自动入库
- 进程退出时统一 flush
- 失败优雅降级为纯日志，绝不阻塞主流程
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
_fail_count = 0   # 启动期失败次数；>0 时不再重试


def _get_settings() -> tuple[bool, str, str, str]:
    """从 dev.json / dev.local.json / 环境变量汇总配置。"""
    enabled = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sk = os.getenv("LANGFUSE_SECRET_KEY", "")
    # dev.local.json 兜底（仅当环境变量未设时）
    if not pk or not sk:
        try:
            from src.config import load_config  # 避免循环
            cfg = load_config()
            if cfg.langfuse:
                host = host or cfg.langfuse.host
                pk = pk or cfg.langfuse.public_key
                sk = sk or cfg.langfuse.secret_key
                enabled = enabled and cfg.langfuse.enabled
        except Exception:
            pass
    return enabled, host, pk, sk


def init_tracing(
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str | None = None,
) -> bool:
    """初始化 LangFuse 客户端。失败返回 False（不抛）。"""
    global _client, _enabled
    with _init_lock:
        if _enabled:
            return True
        if _fail_count > 0:    # 避免反复尝试
            return False

        enabled, default_host, default_pk, default_sk = _get_settings()
        if not enabled:
            logger.info("LangFuse 追踪被配置禁用（LANGFUSE_ENABLED=false）")
            return False

        pk = public_key or default_pk
        sk = secret_key or default_sk
        h  = host or default_host

        if not pk or not sk or "..." in sk or "..." in pk:
            logger.warning("LangFuse 密钥缺失或为占位符（sk-lf-...），追踪已禁用")
            _fail_count = 1
            return False

        try:
            from langfuse import Langfuse
            _client = Langfuse(public_key=pk, secret_key=sk, host=h)
            _enabled = True
            logger.info("LangFuse 追踪已启用：%s", h)
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


def is_enabled() -> bool:
    return _enabled and _client is not None


# ─────────────────────── 业务层 API ───────────────────────

@contextmanager
def traced_operation(
    name: str,
    *,
    input: Any = None,
    metadata: dict[str, Any] | None = None,
    as_type: str = "span",          # "span" | "generation"
    model: str | None = None,
) -> Iterator[Any]:
    """统一追踪入口——业务代码只 use 这一个。

    用法:
        with traced_operation("llm.generate", input=prompt, model=cfg.model) as op:
            response = client.chat(prompt)
            op.update(output=response, usage={"input":n,"output":m})
    """
    if not is_enabled():
        # 降级：只打日志，业务完全无感
        t0 = time.perf_counter()
        try:
            yield _NullOp()
        except Exception as e:
            logger.info("[trace] %s 失败 (%.1fms): %s", name, (time.perf_counter()-t0)*1000, e)
            raise
        else:
            logger.info("[trace] %s 完成 (%.1fms)", name, (time.perf_counter()-t0)*1000)
        return

    try:
        parent = _current_span.get()
        if as_type == "generation" and parent is None:
            trace = _client.trace(name=name, metadata=metadata or {})
            op = trace.generation(name=name, model=model, input=input)
        elif parent is None:
            trace = _client.trace(name=name, metadata=metadata or {})
            op = trace.span(name=name, input=input)
        else:
            op = parent.span(name=name, input=input)

        _span_stack.append(op)
        try:
            yield op
        finally:
            _span_stack.pop()
    except Exception as e:
        logger.warning("LangFuse 追踪失败：%s", e)
        yield _NullOp()


# 内部栈：支持嵌套 span
import contextvars
_span_stack: contextvars.ContextVar = contextvars.ContextVar("_span_stack", default=[])
_current_span = _span_stack  # 别名


class _NullOp:
    """降级占位：业务代码 op.update(...) 不报错。"""
    def update(self, **_): pass
    def score(self, **_):  pass
    def end(self, **_):    pass
```

> 把这个当成「唯一 API」。后续所有业务层调用都用 `traced_operation(...)` 一个入口，不再 import `trace_generation` / `trace_retrieval` / `traced_operation`（旧版）——它们已删除。

---

## 步骤 5：`src/observability/__init__.py`

```python
from .tracing import (
    init_tracing,
    is_enabled,
    traced_operation,
)

__all__ = ["init_tracing", "is_enabled", "traced_operation"]
```

---

## 步骤 6：`src/config.py` 微调

两件事：
1. `_load_dev_json` 优先 `dev.local.json` → `dev.json`（local 优先即可）
2. 缺省 `enabled` 字段时默认为 `True`（dev 环境默认开）

```python
def _load_dev_json() -> dict[str, Any]:
    # 优先级: dev.local.json > dev.json > 都不存在则报错
    for name in ("dev.local.json", "dev.json"):
        p = REPO_ROOT / name
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
    raise ConfigError(f"缺少 dev.json（路径：{REPO_ROOT}）")
```

`LangFuseSettings` 默认 `enabled=True`：

```python
@dataclass(frozen=True)
class LangFuseSettings:
    enabled: bool = True
    host: str = ""
    public_key: str = ""
    secret_key: str = ""
```

`load_config` 里：

```python
if lf_section:
    langfuse = LangFuseSettings(
        enabled=os.getenv("LANGFUSE_ENABLED",
                          str(lf_section.get("enabled", True))).lower() == "true",
        host=os.getenv("LANGFUSE_HOST",       str(lf_section.get("host", ""))),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", str(lf_section.get("public_key", ""))),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", str(lf_section.get("secret_key", ""))),
    )
```

---

## 步骤 7：`src/llm/client.py`——**最关键的接入点**

让 **所有 LLM 调用**自动被追踪。在 `get_llm_client()` 里包一层：

```python
def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is None:
        from src.observability import init_tracing
        init_tracing()                          # 幂等
        _client_instance = LLMClient()
    return _client_instance
```

`LLMClient.chat` / `chat_stream` / `chat_with_tools` 三个方法各加 5 行：

```python
def chat(self, messages, *, temperature=0.1, max_tokens=2048) -> str:
    from src.observability import traced_operation
    with traced_operation(
        "llm.chat",
        input=messages,
        model=self._model,
        as_type="generation",
        metadata={"temperature": temperature, "max_tokens": max_tokens},
    ) as op:
        response = self._client.chat.completions.create(
            model=self._model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        op.update(output=content, usage=_extract_usage(response))
        return content
```

`_extract_usage` 辅助：

```python
def _extract_usage(resp) -> dict[str, int] | None:
    u = getattr(resp, "usage", None)
    if not u: return None
    return {
        "input":  getattr(u, "prompt_tokens",     0),
        "output": getattr(u, "completion_tokens", 0),
        "total":  getattr(u, "total_tokens",      0),
    }
```

`chat_stream` / `chat_with_tools` 同模板（流式用法 `op.update(output="".join(chunks))`）。

---

## 步骤 8：`src/rag/generator.py`——把检索 + 生成绑成一条 trace

**目标**：dashboard 上一次 `rag.generate` 是一条 trace，里面两个 child span：`retrieval` 和 `llm.chat`。这样能看到「检索慢还是 LLM 慢」。

```python
def generate(self, query: str) -> RAGAnswer:
    from src.observability import traced_operation
    with traced_operation("rag.generate", input={"query": query}) as op:
        docs = self.retrieve(query)
        op.update(metadata={"retrieved": len(docs)})

        if not docs:
            return RAGAnswer(answer="根据现有资料无法回答该问题。")

        context  = self._retriever.format_context(docs)
        sources  = self._retriever.format_sources(docs)
        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user",   "content": f"<资料>\n{context}\n</资料>\n\n问题：{query}"},
        ]
        # 这里 LLMClient.chat 内部会自己开 llm.chat sub-span，自动嵌套
        answer = self._llm.chat(messages)
        op.update(output=answer, metadata={"sources": sources})
        return RAGAnswer(answer=answer, sources=sources,
                         context_docs=[d["text"] for d in docs])
```

---

## 步骤 9：`src/rag/retriever.py`（可选，但推荐）

在 `Retriever.search` 内层加 span，方便对比「向量检索 vs reranker」耗时：

```python
def search(self, query: str, *, top_k: int = 10) -> list[dict]:
    from src.observability import traced_operation
    with traced_operation("rag.retrieval",
                          input={"query": query, "top_k": top_k}) as op:
        hits = self._store.search(query, top_k=top_k)
        op.update(output={"hits": len(hits)})
        return hits
```

---

## 步骤 10：`src/agent/graph.py`——Agent 工具调用追踪

每个工具调用包一个 span；如果用 LangGraph，把整个 graph 跑成一条 trace：

```python
def run(self, task: str) -> dict:
    from src.observability import traced_operation
    with traced_operation("agent.run", input={"task": task}) as op:
        # ... 原 graph 调用逻辑 ...
        result = self._compiled.invoke(state, config=...)
        op.update(output=result.get("final_answer", ""))
        return result
```

工具层（`tools/*.py`）同理：

```python
@traced_operation("tool.calculator", as_type="span")  # 装饰器模式也可
def calculator(expr: str) -> float: ...
```

---

## 步骤 11：`src/api/app.py`——FastAPI lifespan 兜底

直接 `uvicorn src.api.app:app` 启动时不会走 `get_llm_client()`，因此 lifespan 里加：

```python
from contextlib import asynccontextmanager
from src.observability import init_tracing

@asynccontextmanager
async def lifespan(app):
    init_tracing()
    yield

app = FastAPI(lifespan=lifespan, ...)
```

---

## 步骤 12：端到端烟测

`scripts/trace_smoke_test.py`（新建在 `agent_platform/scripts/`，加进 git）：

```python
"""发 3 条 trace 到 LangFuse，验证链路通畅。"""
from src.observability import init_tracing, traced_operation, is_enabled
from src.llm.client import LLMClient, get_llm_client
from src.config import load_config

cfg = load_config()
ok = init_tracing()
print(f"enabled={is_enabled()}, ok={ok}")
print(f"host={cfg.langfuse.host}, pk={cfg.langfuse.public_key[:12]}...")

# 1) 纯 LLM
llm = get_llm_client()
with traced_operation("smoke.llm", input="ping", model=llm.model, as_type="generation") as op:
    out = llm.chat([{"role": "user", "content": "用一句话说 hi"}])
    op.update(output=out)

# 2) 完整 RAG
from src.rag.generator import RAGGenerator
from src.rag.retriever import Retriever
from src.vectordb.chroma_store import ChromaVectorStore
from src.embeddings.local_bge import get_embedding_provider

emb = get_embedding_provider(cfg.embedding.model_name)
store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
if store.count > 0:
    rag = RAGGenerator(Retriever(store))
    ans = rag.generate("用一句话总结资料")
    print(f"rag.answer={ans.answer[:60]}")

# 3) 强制 flush
from src.observability.tracing import _client
if _client: _client.flush()

print("✅ 完成。打开 http://localhost:3000 查看 Traces 页面。")
```

跑：

```bash
cd "D:/学习院/my-agents"
./.venv/Scripts/python.exe -m agent_platform.scripts.trace_smoke_test
# 然后浏览器: http://localhost:3000 → 项目 → Traces → 看到 smoke.llm / rag.generate
```

---

## 验收 checklist

- [ ] `curl http://localhost:3000/api/public/health` 返 200
- [ ] `dev.local.json` 已填真 key，且 `git status` 看不到它
- [ ] 日志里看到 `LangFuse 追踪已启用：http://localhost:3000`
- [ ] 烟测脚本运行无 `LangFuse 追踪失败` warning
- [ ] dashboard Traces 页面**实时**（≤5s 延迟）出现 `smoke.llm` / `rag.generate` 两条
- [ ] 点开 `rag.generate`，能看到子 span `llm.chat` 和 `rag.retrieval`，且耗时合理
- [ ] 关闭 LangFuse 容器（`docker compose stop langfuse`）后业务**仍能跑**（降级为日志）

---

## 易踩的坑

1. **`pk-lf-...` / `sk-lf-...` 里带 `...` 一定是不合法 key**——新版 `init_tracing` 已加 `"..." in sk` 检测并直接拒。
2. **容器内调用**要把 `host` 改成 `http://langfuse:3000`（服务名）。
3. **`flush()` 频率**：新版只在进程退出时 flush；高频场景可加一个 60s 定时 flush（按需）。
4. **Python 多线程**：`contextvars` 已处理；如用 `asyncio`，把 `_span_stack` 换成 `ContextVar`（其实 `contextvars` 原生就支持 asyncio）。
5. **Span 名字不要带 PII**（用户输入），会把敏感信息送进 LangFuse 数据库；输入应放 `metadata.query_hash` 之类的派生字段。
