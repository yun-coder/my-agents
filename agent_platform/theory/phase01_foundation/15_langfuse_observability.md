# 15 LangFuse 可观测性：AI Agent 监控与追踪

## 一、概念概述

### 1.1 什么是可观测性（Observability）

在 AI Agent 系统中，可观测性是理解系统内部状态和行为的关键能力。由于 LLM 调用涉及昂贵的 Token 消耗和复杂的多步推理，传统的日志和指标监控不足以满足需求。AI 可观测性需要回答以下问题：

- 每次 LLM 调用了多少 Token？花了多少钱？
- Agent 为什么做了某个决策？它经过了哪些步骤？
- RAG 检索到了哪些文档？哪个文档最终影响了回答？
- 这个 Prompt 的效果如何？哪里需要优化？
- 模型的回答质量如何？用户满意度如何？

### 1.2 什么是 LangFuse

LangFuse 是一个开源的 LLM 可观测性平台，提供 trace-based 的监控、评估和调试能力。它主要对标 LangSmith（LangChain 的付费商业产品），但 LangFuse **支持自托管部署**（Self-Hosted），无需付费 API Key。

LangFuse 的核心功能：
- **Tracing**：记录每次 LLM 调用的完整链路
- **Evaluation**：对模型输出进行评分和评估
- **Prompt Management**：版本化管理提示词
- **Datasets**：管理测试数据集
- **Cost Tracking**：追踪 Token 消耗和成本

### 1.3 LangFuse vs LangSmith

| 维度 | LangFuse | LangSmith |
|------|---------|-----------|
| 定价 | 开源免费，可自托管 | 商业产品，按量付费 |
| API Key | 自托管无需付费 Key | 需要付费 API Key |
| 部署方式 | Docker 自托管 / Cloud | 仅 Cloud |
| 数据隐私 | 数据保留在自有服务器 | 数据发送到 LangChain 服务器 |
| 功能完整性 | 核心功能完整 | 更丰富的评估工具 |
| 社区生态 | 开源社区驱动 | LangChain 官方维护 |

---

## 二、核心原理

### 2.1 Trace、Span、Generation 概念

LangFuse 的数据模型借鉴了 OpenTelemetry 的 Tracing 概念：

```
Trace（追踪）
  +-- 代表一次完整的请求链路
  |
  +-- Span（跨度）
  |     +-- 代表一个操作单元
  |     |
  |     +-- Generation（生成）
  |     |     +-- 代表一次 LLM 调用
  |     |     +-- 包含 input / output / model / usage / cost
  |     |
  |     +-- Event（事件）
  |           +-- 代表一个日志事件或自定义事件
  |           +-- 包含 level / message / metadata
  |
  +-- Score（评分）
        +-- 对 Trace 或 Span 的质量评分
```

### 2.2 LangFuse 自托管部署

LangFuse 自托管是本平台的首选方案，因为它：
- 不需要付费 API Key（只需自建 Docker 服务）
- 数据保留在本地，保证隐私
- 可以通过 `localhost:3000` 访问 Web 界面

```yaml
# docker-compose.yml 示例（LangFuse 自托管）
version: "3.8"
services:
  langfuse-server:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - NEXTAUTH_SECRET=my-secret-key
      - SALT=my-salt-value
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - langfuse-data:/var/lib/postgresql/data

volumes:
  langfuse-data:
```

### 2.3 SDK 核心用法

参考 `agent_platform/src/observability/tracing.py` 的实现：

```python
# LangFuse 追踪集成
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
    """初始化 LangFuse 追踪客户端。

    Args:
        public_key: LangFuse 公钥（自托管可随意填写）
        secret_key: LangFuse 密钥（自托管可随意填写）
        host: LangFuse 服务地址，默认指向 Docker 自托管
    """
    global _langfuse_client, _tracing_enabled
    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        _tracing_enabled = True
        logger.info("LangFuse 追踪已启用: %s", host)
    except Exception as e:
        logger.warning("LangFuse 初始化失败，追踪已禁用: %s", e)
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
    """记录一次 LLM 生成调用（Generation）。

    Args:
        name: 生成名称
        input_data: 输入（Prompt）
        output_data: 输出（Completion）
        model: 模型名称
        usage: Token 用量 {"prompt_tokens": N, "completion_tokens": N}
        metadata: 额外的元数据
    """
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
        logger.debug("LangFuse 记录失败: %s", e)


def trace_retrieval(
    name: str,
    query: str,
    results: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    """记录一次 RAG 检索操作（Span）。

    Args:
        name: 检索名称
        query: 检索查询
        results: 检索结果列表
        metadata: 额外的元数据
    """
    if not _tracing_enabled or _langfuse_client is None:
        return
    try:
        trace = _langfuse_client.trace(name=name)
        trace.span(
            name=f"{name}-retrieval",
            input=query,
            output={
                "documents": [r.get("text", "")[:200] for r in results]
            },
            metadata=metadata or {},
        )
        _langfuse_client.flush()
    except Exception as e:
        logger.debug("LangFuse 记录失败: %s", e)
```

### 2.4 @observe 装饰器

LangFuse 提供 `@observe` 装饰器，可以自动追踪函数的执行。

```python
from langfuse.decorators import observe
from langfuse.openai import openai  # 自动追踪 OpenAI 调用

# 自动追踪整个函数
@observe()
def generate_answer(query: str) -> str:
    """生成回答（自动追踪 Token、耗时、输入输出）。"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": query}],
    )
    return response.choices[0].message.content


# 嵌套追踪
@observe()
def rag_pipeline(query: str) -> str:
    """RAG 完整流程追踪。"""
    # 1. 检索
    docs = retrieve_documents(query)

    # 2. 重排序
    docs = rerank_documents(query, docs)

    # 3. 生成
    answer = generate_answer_with_context(query, docs)

    return answer


# 自定义追踪名称和捕获输入
@observe(name="agent_executor", capture_input=True)
def agent_execute(query: str, session_id: str = "default"):
    """Agent 执行器追踪。"""
    result = agent.run(query, session_id)
    return result
```

### 2.5 Context Manager

使用上下文管理器精确控制追踪范围。

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 手动创建 Trace
trace = langfuse.trace(
    name="rag-query",
    user_id="user_001",
    session_id="session_001",
    metadata={"environment": "production"},
)

# 添加 Span
span = trace.span(
    name="retrieve-documents",
    input={"query": "什么是 RAG?"},
)

# 模拟检索
import time
time.sleep(0.5)

span.end(
    output={"num_docs": 5, "documents": [...]},
    level="DEFAULT",
)

# 添加 Generation
generation = trace.generation(
    name="llm-response",
    model="gpt-4",
    model_parameters={"temperature": 0.7},
    input=[{"role": "user", "content": "什么是 RAG?"}],
    output="RAG 是检索增强生成...",
    usage={
        "input": 150,
        "output": 80,
        "unit": "TOKENS",
    },
)

trace.update(
    output="RAG 是检索增强生成...",
)

# 刷新到服务端
langfuse.flush()
```

### 2.6 Scoring（评分系统）

LangFuse 支持对 Trace 或 Span 进行评分，用于评估 LLM 输出质量。

```python
# 创建评分
trace.score(
    name="answer_relevance",
    value=0.95,
    comment="回答准确且引用了来源",
)

# 分类评分
trace.score(
    name="hallucination_check",
    value=1.0,
    comment="没有发现幻觉内容",
)

# 布尔评分
span.score(
    name="retrieval_success",
    value=True,
    comment="成功检索到相关文档",
)

# 通过 score 方法
langfuse.score(
    trace_id=trace.id,
    name="user_satisfaction",
    value=4.5,
    comment="用户反馈良好",
)
```

### 2.7 Datasets（数据集管理）

LangFuse 的 Dataset 功能可以管理测试数据，用于评估和回归测试。

```python
# 创建数据集
dataset = langfuse.create_dataset(
    name="rag-eval-set",
    description="RAG 问答评估数据集",
)

# 添加测试项
dataset.create_item(
    input="什么是 RAG?",
    expected_output="RAG 是检索增强生成...",
    metadata={"category": "basic_concept"},
)

dataset.create_item(
    input="LangGraph 和 AgentExecutor 有什么区别?",
    expected_output="LangGraph 使用图结构编排...",
    metadata={"category": "comparison"},
)

# 运行评估
for item in dataset.items:
    actual_output = rag_pipeline(item.input)
    # 比较 actual_output 和 item.expected_output
    run_score(langfuse, trace, item, actual_output)
```

### 2.8 Prompt Management（提示词管理）

LangFuse 的 Prompt 管理功能可以版本化管理提示词模板。

```python
# 在 LangFuse Web UI 中创建 Prompt
# Prompt name: "rag-system-prompt"
# Prompt content: "你是一个基于知识库的问答助手..."

# 在代码中获取 Prompt
prompt = langfuse.get_prompt("rag-system-prompt", version=1)
compiled = prompt.compile(
    context="检索到的参考资料...",
    question="用户的问题...",
)

print(compiled)
# 输出: "你是一个基于知识库的问答助手..."
```

---

## 三、实战指南

### 3.1 完整追踪集成到 Agent

参考 `agent_platform/src/observability/tracing.py` 中的 `traced_operation` 上下文管理器：

```python
@contextmanager
def traced_operation(name: str, **metadata: Any):
    """上下文管理器：自动追踪一段操作的耗时和结果。

    用法:
        with traced_operation("RAG检索", query="什么是RAG"):
            docs = retriever.search("什么是RAG")

    即使出错，也会记录耗时和错误信息。
    """
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
            logger.info(
                "[LangFuse] %s 失败 (%.1fms): %s",
                name, elapsed, error,
            )
        else:
            logger.info(
                "[LangFuse] %s 完成 (%.1fms)", name, elapsed,
            )


# 在 RAG 管线中使用
class TracedRAGGenerator(RAGGenerator):
    """带追踪能力的 RAG 生成器。"""

    def generate(self, query: str) -> RAGAnswer:
        with traced_operation("RAG-检索", query=query):
            docs = self.retrieve(query)

        if not docs:
            return RAGAnswer(answer="根据现有资料无法回答该问题。")

        if _tracing_enabled:
            trace_retrieval("RAG-检索", query, docs)

        context = self._retriever.format_context(docs)

        with traced_operation("RAG-生成", query=query):
            answer = self._llm.chat(messages)

        if _tracing_enabled:
            trace_generation(
                "RAG-生成",
                input_data=str(messages),
                output_data=answer,
                model="gpt-4",
                usage={"prompt_tokens": 500, "completion_tokens": 200},
            )

        return RAGAnswer(
            answer=answer,
            sources=self._retriever.format_sources(docs),
        )
```

### 3.2 初始化配置

```python
# config.py 中的 LangFuse 配置
from pydantic_settings import BaseSettings

class LangFuseConfig(BaseSettings):
    """LangFuse 配置。"""
    # 自托管模式：host 指向本地 Docker 服务
    LANGFUSE_HOST: str = "http://localhost:3000"
    LANGFUSE_PUBLIC_KEY: str = "pk-local-xxx"
    LANGFUSE_SECRET_KEY: str = "sk-local-xxx"
    LANGFUSE_ENABLE: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 在应用启动时初始化
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：初始化 LangFuse 追踪。"""
    cfg = LangFuseConfig()
    if cfg.LANGFUSE_ENABLE:
        init_tracing(
            public_key=cfg.LANGFUSE_PUBLIC_KEY,
            secret_key=cfg.LANGFUSE_SECRET_KEY,
            host=cfg.LANGFUSE_HOST,
        )
    yield
```

### 3.3 LangFuse Web UI 功能

启动 LangFuse 自托管后，通过 `http://localhost:3000` 访问：

- **Traces 页面**：查看所有 Trace 的列表，包括耗时、Token 消耗、成本
- **Trace Detail 页面**：查看单个 Trace 的完整链路（Span Tree）
- **Generations 页面**：查看所有 LLM 调用记录
- **Scores 页面**：查看评分和评估结果
- **Datasets 页面**：管理测试数据集和运行评估
- **Prompts 页面**：管理提示词模板和版本

---

## 四、最佳实践

### 4.1 追踪粒度

| 追踪范围 | 粒度 | 适用场景 |
|---------|------|---------|
| 全链路 Trace | 粗 | 每次用户请求 |
| LLM 调用 Generation | 细 | 每次模型调用 |
| RAG 检索 Span | 中 | 每次检索操作 |
| 工具执行 Span | 中 | 每次工具调用 |
| 自定义 Event | 极细 | 关键决策点、异常 |

### 4.2 成本追踪

```python
# 估算每次 LLM 调用的成本
MODEL_COST_PER_1K_TOKENS = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """估算 LLM 调用的成本（美元）。"""
    rates = MODEL_COST_PER_1K_TOKENS.get(model, {"input": 0, "output": 0})
    input_cost = (input_tokens / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]
    return round(input_cost + output_cost, 6)
```

### 4.3 采样策略

高并发场景下，不必追踪每一次请求。

```python
import random

class SampledTracer:
    """采样的追踪器，降低存储开销。"""

    def __init__(self, sample_rate: float = 1.0):
        self.sample_rate = sample_rate

    def should_trace(self) -> bool:
        return random.random() < self.sample_rate

    @contextmanager
    def trace_if_sampled(self, name: str):
        if self.should_trace():
            with traced_operation(name):
                yield
        else:
            yield

# 生产环境：采样 10%
tracer = SampledTracer(sample_rate=0.1)
```

### 4.4 优雅降级

LangFuse 不应成为系统的关键依赖。当 LangFuse 不可用时，应该优雅降级为纯日志模式。

```python
# init_tracing 已包含 try-except 降级逻辑
if not _tracing_enabled:
    # 降级为普通日志
    logger.info("[Tracing Disabled] 使用日志模式")
```

---

## 五、常见陷阱

### 5.1 未调用 flush()

**陷阱**：追踪数据缓存在内存中，未调用 `flush()` 导致数据丢失。

**解决**：在每次追踪操作后调用 `_langfuse_client.flush()`，或在应用关闭时执行一次 `langfuse.shutdown()`。

### 5.2 自托管配置错误

**陷阱**：Docker 容器未正确启动，或 LANGFUSE_HOST 指向了错误的地址。

**解决**：先通过 `curl http://localhost:3000/api/public/health` 验证服务是否正常。

### 5.3 过度追踪

**陷阱**：追踪了所有内部函数调用，导致追踪数据量过大，存储和性能开销高。

**解决**：只追踪关键的 LLM 调用、检索操作和工具执行，使用采样策略控制数据量。

### 5.4 隐私泄露

**陷阱**：将用户的敏感信息（密码、API Key、个人身份信息）记录到了 Trace 中。

**解决**：在记录前对输入输出进行脱敏处理，或配置 LangFuse 的数据保留策略。

```python
def sanitize_for_tracing(text: str) -> str:
    """脱敏处理，过滤敏感信息。"""
    import re
    # 隐藏 API Key
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-***', text)
    # 隐藏邮箱
    text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.]+', '***@***.***', text)
    return text[:2000]  # 截断过长内容
```

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| LangFuse 自托管 | 否 | Docker 本地部署，无需付费 Key |
| LangFuse Cloud | 是 | 需要注册获取 API Key |
| @observe 装饰器 | 取决于部署方式 | 自托管不需要，Cloud 需要 |
| LLM 调用追踪 | 是（LLM 本身需要 Key） | 追踪的是 LLM 调用行为 |
| 评分/数据集功能 | 取决于部署方式 | 自托管不需要 Key |

**LangFuse 自托管是本平台的默认方案**，因为它完全免费且数据保留在本地。

---

## 七、技术关系

```text
LangFuse 可观测性体系:

应用程序层
  +-- Agent 工作流（graph.py）
  +-- RAG 管线（retriever.py, generator.py）
  +-- API 端点（routes.py）
       |
       +-- @observe 装饰器自动追踪
       +-- trace_generation() 手动追踪
       +-- traced_operation() 上下文管理器
       |
       v
LangFuse SDK
  +-- Trace（请求链路）
  +-- Span（操作跨度）
  +-- Generation（LLM 调用）
  +-- Event（自定义事件）
  +-- Score（质量评分）
       |
       +-- HTTP API
       |
       v
LangFuse Server（自托管 :3000）
  +-- Web UI（可视化仪表盘）
  +-- PostgreSQL（数据持久化）
  +-- API（查询和数据管理）

对比方案:
  LangSmith（Paid Cloud）<------ 被 LangFuse Self-Hosted 替代
  OpenTelemetry（通用 Tracing）<- 可以与 LangFuse 互补
```

---

## 八、验收清单

- [ ] 理解 Trace、Span、Generation、Event 四个核心概念
- [ ] 掌握 LangFuse 自托管部署方式（Docker Compose）
- [ ] 理解 LangFuse 与 LangSmith 的对比和选择理由
- [ ] 能用 @observe 装饰器自动追踪函数
- [ ] 能用 context manager 手动创建和结束 Trace/Span
- [ ] 掌握 Generation 记录的参数（model, usage, cost）
- [ ] 能使用 Scoring 系统评估输出质量
- [ ] 理解 Datasets 和 Prompt Management 的用途
- [ ] 理解优雅降级机制（LangFuse 不可用时转为日志模式）
- [ ] 理解采样策略和隐私保护措施

---

## 九、学习资源

- **LangFuse 官方文档**: https://langfuse.com/docs
- **LangFuse 自托管指南**: https://langfuse.com/docs/deployment/self-hosted
- **LangFuse Docker 部署**: https://langfuse.com/docs/deployment/docker
- **LangFuse GitHub**: https://github.com/langfuse/langfuse
- **OpenTelemetry 概念**: https://opentelemetry.io/docs/concepts/
- **平台参考代码**: agent_platform/src/observability/tracing.py (LangFuse 集成实现)
