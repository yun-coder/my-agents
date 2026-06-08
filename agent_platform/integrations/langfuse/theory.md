# LangFuse 理论：OpenTelemetry 与 LLM 追踪

## 概念概述

### 什么是 LLM 可观测性

LLM 可观测性（Observability）是传统软件可观测性在大语言模型领域的延伸。传统可观测性关注三个支柱——日志（Logs）、指标（Metrics）、追踪（Traces）——而 LLM 可观测性在此基础上增加了 LLM 特定的维度：

- 模型行为：输入/输出内容、推理路径
- Token 消耗：每次调用的 Token 计数和成本
- 质量评估：回答的准确性、相关性、安全性
- Prompt 版本：使用的 Prompt 模板和版本历史

LangFuse 是实现 LLM 可观测性的开源工具，它以 Trace 为核心数据结构，记录 LLM 应用的完整执行链路。

### OpenTelemetry 标准

OpenTelemetry（OTel）是云原生计算基金会（CNCF）的观测性标准。它定义了如何生成、收集和导出遥测数据。LangFuse 的 Trace 结构本质上是对 OpenTelemetry 语义约定的 LLM 扩展。

```
OpenTelemetry 核心概念:
┌─────────────────────────────────────────────┐
│  Trace（追踪）: 一次请求的完整链路            │
│    ├── Span（跨度）: 链路中的单个操作         │
│    │    ├── Attributes（属性）: 键值对元数据   │
│    │    ├── Events（事件）: 时间戳标记        │
│    │    └── Status（状态）: 成功/错误/未设置   │
│    └── SpanContext（上下文）: 跨进程传播      │
└─────────────────────────────────────────────┘
```

LangFuse 在 OTel Span 的基础上扩展了 Generation 类型，专门用于表示 LLM 调用。

---

## Trace 结构

### 完整的数据模型

LangFuse 的 Trace 数据模型采用树形结构：

```
Trace (root)
├── id: string          — 唯一标识
├── name: string        — 追踪名称
├── timestamp: datetime — 开始时间
├── metadata: dict      — 用户自定义元数据
├── tags: list[str]     — 标签
├── user_id: str        — 关联用户
├── session_id: str     — 关联会话
│
├── Span (child)
│   ├── id, name, timestamp
│   ├── input: any      — Span 的输入
│   ├── output: any     — Span 的输出
│   ├── level: DEFAULT|WARNING|ERROR
│   ├── status: success|error
│   │
│   ├── Span (sub-child)
│   │   └── ...
│   │
│   └── Event
│       ├── name
│       ├── timestamp
│       └── metadata
│
├── Generation (child)
│   ├── id, name, timestamp
│   ├── model: string          — 模型名称
│   ├── model_parameters: dict — 模型参数
│   ├── usage: dict            — Token 用量
│   ├── prompt_id: str         — Prompt 标识
│   └── completion_start_time  — 首 Token 时间
│
└── Observation (union type)
    ├── Span 或 Generation 的抽象基类
    ├── 公共字段: id, name, start_time, end_time
    ├── 公共字段: input, output, metadata
    ├── 公共字段: level, status, version
    └── 公共方法: .end(), .update(), .score()
```

### Trace ID 和 Span ID 生成

```python
import uuid
import time

def generate_trace_id() -> str:
    """生成 Trace ID（UUID v4）"""
    return str(uuid.uuid4())

def generate_span_id() -> str:
    """生成 Span ID（16 位十六进制）"""
    return uuid.uuid4().hex[:16]

# Trace 的时间戳通常用毫秒级 Unix 时间戳
current_timestamp = int(time.time() * 1000)
```

---

## Observation 类型深度解析

### Observation 继承体系

LangFuse 的核心抽象是 Observation（观测），它是 Span 和 Generation 的共同基类。

```
Observation（抽象基类）
│
├── Span
│   ├── 用途：记录一般操作（检索、工具调用、API 请求）
│   ├── 特点：可以有子 Span
│   └── 典型场景：RAG 检索、代码执行、文件操作
│
└── Generation（Span 的特化）
    ├── 用途：记录 LLM 调用
    ├── 额外字段：model, model_parameters, usage
    ├── 特点：不可有子 Generation
    └── 典型场景：Chat Completion、Embedding、Image Generation
```

### 何时创建 Span vs Generation

这是一个常见的架构决策问题。以下是指南：

```python
# 应该用 Generation 的场景（LLM 调用）
def call_llm():
    """LLM 调用必须使用 Generation"""
    trace.generation(
        name="chat-gpt4o",
        model="gpt-4o",
        input=messages,
        output=response,
        usage={"input": 100, "output": 50}
    )

# 应该用 Span 的场景（非 LLM 操作）
def retrieve_documents():
    """检索操作使用 Span，不是 Generation"""
    trace.span(
        name="vector-search",
        input={"query": query},
        output={"results": docs}
    )

# 应该用嵌套 Span 的场景（复杂操作含子操作）
def complex_pipeline():
    """复杂管道：主 span 包含多个子 span"""
    with trace.span(name="pipeline") as pipeline:
        with pipeline.span(name="step-1"):
            step1_result = do_step1()

        with pipeline.span(name="step-2"):
            step2_result = do_step2()

        # 内嵌 LLM 调用
        pipeline.generation(
            name="refine",
            model="gpt-4o",
            input=f"Refine: {step1_result}",
            output=refined
        )
```

### 核心原则

1. **一个 LLM 调用 = 一个 Generation**：每次调用大模型（包括 embedding）都应该记录为一个 Generation
2. **一个操作步骤 = 一个 Span**：非 LLM 操作（检索、计算、文件读写）使用 Span
3. **Span 可以嵌套**：父 Span 可以包含子 Span
4. **Generation 不可嵌套**：Generation 是最小单元
5. **Event 用于标记**：Event 用于记录时间点事件，不包含子结构

---

## 上下文传播

### 什么是上下文传播

在多 Agent 系统或微服务架构中，一个 Trace 可能跨越多个进程甚至多个服务。上下文传播（Context Propagation）是指将 Trace 的上下文信息（Trace ID、Span ID）传递到下游服务，使得所有相关操作能关联到同一个 Trace。

### LangFuse 的上下文传播

```python
from langfuse import LangFuse
from langfuse.api.core.api_client import ApiClient

langfuse = LangFuse()

def parent_function():
    """父函数创建 trace"""
    trace = langfuse.trace(name="parent-task")

    # 传播 trace_id 到子函数
    child_function(trace.id)

def child_function(parent_trace_id: str):
    """
    子函数通过 parent_trace_id 关联到父 trace

    在 LangFuse 中，可以通过 metadata 传递 trace_id
    """
    child_trace = langfuse.trace(
        name="child-task",
        metadata={"parent_trace_id": parent_trace_id}
    )

    # 或者使用 trace_id 覆盖
    # langfuse.trace(id=parent_trace_id)
```

### 在分布式系统中的传播

```python
# 服务 A：接收 HTTP 请求并传播上下文
import httpx

def service_a_handler(request):
    # 从请求头获取 trace 上下文
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))

    trace = langfuse.trace(
        id=trace_id,
        name="distributed-flow"
    )

    # 将 trace_id 传播到服务 B
    response = httpx.post(
        "http://service-b/api",
        headers={"X-Trace-Id": trace_id}
    )

    trace.end()

# 服务 B：接收并关联 trace
def service_b_handler(request):
    trace_id = request.headers.get("X-Trace-Id")

    trace = langfuse.trace(
        id=trace_id,  # 使用相同的 trace_id
        name="service-b-step"
    )
    # ... 执行操作
    trace.end()
```

### Context 变量管理

```python
from contextvars import ContextVar
from typing import Optional

# 使用 contextvars 实现线程安全的上下文传播
_current_trace_id: ContextVar[Optional[str]] = ContextVar(
    "current_trace_id", default=None
)
_current_span_id: ContextVar[Optional[str]] = ContextVar(
    "current_span_id", default=None
)

def set_trace_context(trace_id: str, span_id: Optional[str] = None):
    """设置当前线程的 trace 上下文"""
    _current_trace_id.set(trace_id)
    if span_id:
        _current_span_id.set(span_id)

def get_trace_context() -> tuple[Optional[str], Optional[str]]:
    """获取当前线程的 trace 上下文"""
    return _current_trace_id.get(), _current_span_id.get()

def clear_trace_context():
    """清除当前线程的 trace 上下文"""
    _current_trace_id.set(None)
    _current_span_id.set(None)
```

---

## 异步追踪

### 异步函数追踪

LangFuse 原生支持异步操作：

```python
import asyncio
from langfuse.decorators import observe

@observe()
async def async_agent_task(query: str):
    """异步 Agent 任务"""
    # LLM 调用
    response = await async_llm_call(query)

    # 检索调用
    docs = await async_retrieval(query)

    return {"response": response, "sources": docs}

# 运行异步追踪
result = asyncio.run(async_agent_task("查询天气"))
```

### 并发追踪

当多个 LLM 调用并发执行时，LangFuse 通过 Span 嵌套关系确保 Trace 结构正确：

```python
import asyncio

@observe()
async def parallel_processing(tasks: list[str]):
    """
    并发处理多个子任务

    每个子任务都是独立的 Span，共享同一个父 Trace
    """
    async def process_one(task: str):
        with trace.span(name=f"process-{task}"):
            result = await async_llm_call(task)
            return result

    # 并发执行
    results = await asyncio.gather(*[
        process_one(task) for task in tasks
    ])

    return results
```

### 异步 Flush

```python
from langfuse import LangFuse

langfuse = LangFuse()

async def async_flush_example():
    """异步刷新追踪数据"""
    trace = langfuse.trace(name="async-example")
    trace.generation(name="llm-call", input="Hello", output="World")

    # 异步 flush 确保数据发送完成
    await langfuse.aflush()

    # 或者批量处理后一次性 flush
    # await langfuse.aflush()
```

---

## Flush 策略

### 为什么需要 Flush

LangFuse 的 SDK 默认将追踪数据缓冲在内存中，然后批量发送到服务器。这样可以减少网络请求次数，提高性能。但如果没有正确 flush，可能导致数据丢失。

### Flush 触发时机

```python
from langfuse import LangFuse

langfuse = LangFuse()

def flush_strategies():
    """三种 flush 策略"""

    # 策略 1：手动 flush（最可靠）
    trace = langfuse.trace(name="critical-path")
    trace.generation(name="llm", input="x", output="y")
    langfuse.flush()  # 立即发送所有缓冲数据

    # 策略 2：定时 flush（性能优先）
    # SDK 默认每 30 秒自动 flush 一次
    # 可以通过配置调整
    config_langfuse = LangFuse(
        flush_at=20,          # 每 20 个事件自动 flush
        flush_interval=60     # 每 60 秒自动 flush
    )

    # 策略 3：程序退出时 flush
    import atexit

    @atexit.register
    def cleanup():
        langfuse.flush()
        langfuse.shutdown()
```

### 生产环境的 Flush 配置

```python
def production_langfuse_config() -> LangFuse:
    """生产环境推荐配置"""
    return LangFuse(
        # 核心配置
        secret_key="sk-lf-...",
        public_key="pk-lf-...",
        host="http://localhost:3000",

        # Flush 配置
        flush_at=50,              # 累积 50 个事件后发送
        flush_interval=30,        # 最多 30 秒发送一次

        # 超时配置
        request_timeout=10,       # HTTP 请求超时（秒）

        # 重试配置
        max_retries=3,            # 失败重试次数
        retry_delay=1,            # 重试间隔（秒）

        # 采样配置
        # 见下方采样策略
    )
```

---

## 采样策略

对于高流量应用，记录每一次 LLM 调用可能会产生大量数据。采样（Sampling）可以在保留统计意义的同时减少数据量。

### 头部采样（Head-based Sampling）

在 Trace 开始时决定是否记录。通常基于 Trace ID 的哈希值。

```python
class HeadBasedSampler:
    """头部采样：在 Trace 创建时决定"""

    def __init__(self, sample_rate: float = 0.1):
        self.sample_rate = sample_rate

    def should_sample(self, trace_id: str) -> bool:
        """基于 trace_id 的哈希决定是否采样"""
        hash_val = hash(trace_id) & 0xFFFFFFFF
        return (hash_val % 10000) < (self.sample_rate * 10000)

# 使用示例
sampler = HeadBasedSampler(sample_rate=0.1)  # 10% 采样

def create_traced_call():
    trace_id = generate_trace_id()
    if sampler.should_sample(trace_id):
        trace = langfuse.trace(id=trace_id, name="sampled-call")
        # ... 执行操作
        trace.end()
```

### 尾部采样（Tail-based Sampling）

记录所有 Trace，但只在分析时采样。不常用，因为需要存储所有数据。

### 动态采样

根据条件动态调整采样率：

```python
class DynamicSampler:
    """
    动态采样器

    根据特征调整采样率：
    - 错误请求：100% 采样
    - 高延迟请求：100% 采样
    - 首次请求：100% 采样
    - 正常请求：按配置比例采样
    """

    def __init__(self, default_rate: float = 0.05):
        self.default_rate = default_rate

    def should_sample(self, trace_data: dict) -> bool:
        # 错误请求全部采样
        if trace_data.get("error"):
            return True

        # 高延迟请求全部采样
        if trace_data.get("latency_ms", 0) > 5000:
            return True

        # 特定用户全部采样
        if trace_data.get("user_id") in ["vip-001", "vip-002"]:
            return True

        # 其他请求按比例采样
        trace_id = trace_data.get("trace_id", "")
        hash_val = hash(trace_id) & 0xFFFFFFFF
        return (hash_val % 10000) < (self.default_rate * 10000)
```

### 生产环境采样配置

```python
def production_sampling_config():
    """生产环境采样策略推荐"""
    return {
        # API 调用追踪
        "api_traces": {
            "sample_rate": 0.1,        # 10% API 请求被追踪
            "error_full": True,        # 错误请求 100% 追踪
            "slow_full": True,         # 慢请求 100% 追踪
        },
        # LLM 生成追踪
        "llm_generations": {
            "sample_rate": 0.2,        # 20% LLM 调用被追踪
            "cost_tracking": True,      # 成本追踪始终开启
        },
        # 后台任务
        "background_jobs": {
            "sample_rate": 0.01,       # 1% 后台任务被追踪
        }
    }
```

---

## 与 OpenTelemetry 集成

```python
# LangFuse 与 OpenTelemetry 结合使用
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 设置 OTel Tracer
provider = TracerProvider()
processor = BatchSpanProcessor(span_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# 在 LangFuse 中关联 OTel Trace
langfuse.trace(
    name="otel-integrated",
    metadata={
        "otel_trace_id": trace.get_current_span().get_span_context().trace_id
    }
)
```

---

## 总结

LangFuse 的追踪模型基于 OpenTelemetry 标准设计，通过 Trace、Span、Generation 三层结构完整记录 LLM 应用的执行链路。理解这些概念对于正确使用追踪功能至关重要：

- Trace 代表一次完整的请求
- Span 代表一段操作
- Generation 是特化的 Span 用于 LLM 调用
- 上下文传播确保分布式场景下的链路完整性
- 采样策略帮助在高流量场景下控制数据量
- Flush 策略确保数据不丢失
ENDOFFILE