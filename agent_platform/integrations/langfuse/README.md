# LangFuse 集成指南

## 概述

LangFuse 是一个开源的 LLM 可观测性平台，提供追踪（Tracing）、评估（Evaluation）、Prompt 管理等功能。与 LangSmith 不同，LangFuse 支持真正的完全自托管——不需要任何外部 API Key，所有数据存储在自己的基础设施中。

在 agent_platform 中，LangFuse 通过 `src/observability/tracing.py` 模块提供统一的追踪接口，用于记录 Agent 执行过程中的所有关键事件——LLM 调用、RAG 检索、工具执行、Agent 规划等。

---

## Docker Compose 自托管部署

### 前提条件

- Docker Engine 24+
- Docker Compose v2+
- 至少 2GB 可用内存
- 4GB 磁盘空间

### 快速部署

```yaml
# docker-compose.yml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse"]
      interval: 5s
      timeout: 5s
      retries: 5

  langfuse:
    image: ghcr.io/langfuse/langfuse:latest
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse_pass@postgres:5432/langfuse
      NEXTAUTH_SECRET: my-random-secret-change-in-production
      NEXTAUTH_URL: http://localhost:3000
      SALT: my-salt-value
    ports:
      - "3000:3000"
    volumes:
      - langfuse_data:/data

volumes:
  postgres_data:
  langfuse_data:
```

```bash
# 启动 LangFuse
docker-compose up -d

# 查看日志
docker-compose logs -f langfuse

# 停止
docker-compose down

# 停止并删除数据
docker-compose down -v
```

启动后访问 `http://localhost:3000`，注册首个用户即可使用。

### 获取 API Key

在 LangFuse Web UI 中：
1. 登录 `http://localhost:3000`
2. 进入 Settings > API Keys
3. 点击 "Create new API key"
4. 复制 `Secret Key` 和 `Public Key`

```bash
# .env 文件
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxx
LANGFUSE_HOST=http://localhost:3000
```

---

## SDK 集成模式

LangFuse 提供三种集成模式，适用于不同的使用场景。

### 模式一：@observe 装饰器

最推荐的模式。通过装饰器自动追踪函数的输入、输出和执行时间。

```python
from langfuse.decorators import observe

@observe()
def search_knowledge_base(query: str) -> list[str]:
    """搜索知识库，自动追踪输入 query 和输出结果"""
    results = vector_db.similarity_search(query, k=5)
    return [doc.page_content for doc in results]

@observe(as_type="generation")
def call_llm(messages: list[dict]) -> str:
    """调用 LLM，自动追踪为 generation 类型"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content
```

装饰器参数说明：
- `as_type`: 追踪类型，可选 "generation"（LLM 调用）或 "span"（一般操作）
- `name`: 自定义追踪名称，默认为函数名
- `capture_input`: 是否捕获输入参数（默认 True）
- `capture_output`: 是否捕获输出（默认 True）

### 模式二：上下文管理器

手动控制追踪的生命周期，适用于需要精细控制的场景。

```python
from langfuse import LangFuse

langfuse = LangFuse()

def execute_agent(task: str) -> str:
    """手动管理 trace 和 span 的上下文"""

    # 创建主 trace
    trace = langfuse.trace(
        name="agent-execution",
        input=task,
        metadata={"version": "1.0", "env": "production"}
    )

    try:
        # 规划阶段
        with trace.span(name="planning") as span:
            plan = planner.plan(task)
            span.update(output=plan)

        # 检索阶段
        with trace.span(name="retrieval") as span:
            docs = retriever.retrieve(plan.query)
            span.update(output={"count": len(docs)})

        # 生成阶段
        with trace.generation(
            name="response-generation",
            model="gpt-4o",
            model_parameters={"temperature": 0.7}
        ) as gen:
            response = llm.generate(plan, docs)
            gen.update(
                output=response,
                usage={"input": 150, "output": 50, "total": 200}
            )

        trace.update(output=response)
        return response

    except Exception as e:
        trace.update(
            status="error",
            metadata={"error": str(e)}
        )
        raise
```

### 模式三：手动 API

最灵活的模式，完全手动创建和管理 trace、span、generation。

```python
from langfuse import LangFuse

langfuse = LangFuse()

def manual_tracing():
    """完全手动控制追踪的创建和结束"""

    # 创建 trace
    trace = langfuse.trace(
        name="manual-agent",
        user_id="user-123",
        session_id="session-456"
    )

    # 创建 span（子步骤）
    span = trace.span(
        name="step-1",
        input={"action": "search"}
    )
    # ... 执行操作
    span.end(output={"results": ["doc1", "doc2"]})

    # 创建 generation（LLM 调用）
    gen = trace.generation(
        name="llm-step",
        model="gpt-4o",
        input=[{"role": "user", "content": "Hello"}],
        output={"role": "assistant", "content": "Hi!"},
        usage={"input": 10, "output": 5, "total": 15}
    )
    gen.end()

    # 结束 trace
    trace.end()
```

---

## 核心数据类型

LangFuse 定义了四种核心的追踪数据类型。

### Trace（追踪）

Trace 是追踪的顶层容器，代表一次完整的请求或执行流程。

```python
trace = langfuse.trace(
    name="process-invoice",          # 追踪名称
    user_id="user-123",              # 用户 ID（可选）
    session_id="session-456",       # 会话 ID（可选）
    metadata={"env": "prod"},        # 元数据（可选）
    tags=["finance", "ocr"],         # 标签（可选）
    version="1.0.0",                 # 版本号（可选）
    release="release-2024-06"        # 发布版本（可选）
)
```

### Span（跨度）

Span 代表一段操作，可以嵌套（子 span）。适用于 RAG 检索、工具调用、API 请求等。

```python
span = trace.span(
    name="vector-search",            # span 名称
    input={"query": "如何配置SSL"},   # 输入（可选）
    output={"count": 3},             # 输出（可选）
    metadata={"index": "prod-docs"}, # 元数据（可选）
    start_time=datetime.now(),       # 开始时间（可选，用于历史数据）
    level="DEFAULT",                 # 级别：DEFAULT/WARNING/ERROR
    status="success"                 # 状态：success/error（可选）
)
```

### Generation（生成）

Generation 是 Span 的特化类型，专门用于 LLM 调用。它包含模型参数、Token 用量等信息。

```python
generation = trace.generation(
    name="chat-completion",          # 生成名称
    model="gpt-4o",                  # 模型名称
    model_parameters={               # 模型参数
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.9
    },
    input=[                           # 输入（完整 prompt）
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"}
    ],
    output={                          # 输出（完整 response）
        "role": "assistant",
        "content": "你好！有什么可以帮助的？"
    },
    usage={                           # Token 用量
        "input": 25,
        "output": 15,
        "total": 40
    },
    prompt_id="prompt-123",           # Prompt ID（可选）
    prompt_version=1                   # Prompt 版本（可选）
)
```

### Event（事件）

Event 是轻量级的日志点，用于记录中间状态或关键事件。

```python
trace.event(
    name="milestone",                 # 事件名称
    input={"phase": "validation"},    # 输入（可选）
    output={"status": "passed"},      # 输出（可选）
    metadata={"threshold": 0.8},      # 元数据（可选）
    level="DEFAULT"                   # 级别：DEFAULT/WARNING/ERROR
)
```

---

## 评分与评估

### 手动评分

```python
# 对 trace 评分
trace.score(
    name="accuracy",                  # 评分指标名称
    value=0.95,                       # 评分值
    comment="回答准确无误",            # 备注（可选）
    data_type="NUMERIC"               # 数据类型（NUMERIC/BOOLEAN/CATEGORICAL）
)

# 对 generation 评分
generation.score(
    name="helpfulness",
    value=1,                          # 布尔值：0 或 1
    data_type="BOOLEAN"
)

# 分类评分
trace.score(
    name="quality",
    value="good",                     # 分类值
    data_type="CATEGORICAL"
)
```

### 自动评估

```python
# 使用 LangFuse 内置评估函数
from langfuse.evaluation import evaluate

def accuracy_evaluator(output, expected):
    """自定义评估函数"""
    return {"score": 1.0 if output == expected else 0.0}

# 运行评估
results = evaluate(
    trace_id="trace-123",
    evaluators=[accuracy_evaluator],
    data=[{"output": "北京", "expected": "北京"}]
)
```

---

## Dashboard 使用

LangFuse Web UI 提供以下核心仪表盘：

### Traces 页面

查看所有追踪记录，支持过滤、搜索和排序。每个追踪展开后可以看到完整的 span 树。

关键信息：
- 追踪耗时（总时间）
- Token 消耗（输入 + 输出）
- 模型调用次数
- 错误日志

### Generations 页面

专门查看所有 LLM 调用的聚合视图。

关键指标：
- 模型使用分布
- 平均延迟
- Token 消耗趋势
- 成本估算

### Evaluations 页面

查看评分记录和评估结果，追踪模型质量随时间的变化趋势。

---

## agent_platform 集成

agent_platform 在 `src/observability/tracing.py` 中封装了 LangFuse 追踪功能。

### 初始化

```python
from agent_platform.observability.tracing import init_tracing, trace_generation

# 初始化追踪
init_tracing(
    public_key="pk-lf-xxxxx",
    secret_key="sk-lf-xxxxx",
    host="http://localhost:3000"
)

# 如果 LangFuse 不可用，自动降级为日志模式
# 不会抛出异常
```

### 记录 LLM 调用

```python
# 记录一次 LLM 生成
trace_generation(
    name="chat-completion",
    input_data="用户提问：什么是 RAG？",
    output_data="RAG 是检索增强生成...",
    model="gpt-4o",
    usage={"input": 50, "output": 200, "total": 250}
)
```

### 记录 RAG 检索

```python
# 记录一次检索
trace_retrieval(
    name="knowledge-search",
    query="RAG 架构",
    results=[{"text": "RAG 是一种..."}]
)
```

### 上下文管理器

```python
from agent_platform.observability.tracing import traced_operation

# 自动追踪一段操作
with traced_operation("execute-task", env="test"):
    result = agent.execute(task)
```

---

## 故障排除

### 连接问题

```bash
# 检查 LangFuse 是否运行
curl http://localhost:3000/health

# 查看容器日志
docker-compose logs langfuse
```

### 追踪不出现

- 检查 API Key 是否正确
- 检查 host 地址是否可访问
- 检查是否调用了 `flush()`
- 查看应用日志中是否有 "LangFuse 追踪已启用" 信息

### 性能问题

- 减少 `flush()` 调用频率（每 10 次追踪 flush 一次）
- 启用采样（见 theory.md）
- 使用异步模式

---

## 相关文档

- [LangFuse Theory](theory.md)：OpenTelemetry、Trace 结构、采样策略
- [LangSmith Comparison](../langsmith/comparison.md)：LangSmith vs LangFuse 对比
- [LangFuse 官方文档](https://langfuse.com/docs)
ENDOFFILE