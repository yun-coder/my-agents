# LangSmith vs LangFuse 对比分析

## 概念概述

### 什么是 LLM 可观测性平台

LLM 可观测性平台是专门为大语言模型应用设计的监控、调试和评估工具。它们记录每次 LLM 调用的完整生命周期——从输入到输出、从 Token 消耗到延迟、从 Prompt 版本到模型响应——帮助开发者理解和优化 LLM 应用的行为。

两个最主要的开源/商用方案是 LangSmith（由 LangChain 开发）和 LangFuse（德国开源项目）。

### 为什么需要可观测性

在开发 Agent 应用时，开发者面临以下挑战：

- 黑盒问题：LLM 的推理过程不可见，难以排查错误原因
- 成本失控：Token 消耗难以追踪，API 费用不可预测
- 质量评估：没有系统的评估方法，依赖人工逐条检查
- Prompt 迭代：Prompt 版本管理混乱，无法对比不同版本效果

可观测性平台正是为了解决这些问题而生。

---

## LangSmith 详解

### LangSmith 是什么

LangSmith 是 LangChain 团队开发的 LLM 可观测性平台，与 LangChain 框架深度集成。它提供 Tracing、评估、Prompt 管理、数据集管理等功能。

### 核心特性

```python
# LangSmith 的基本用法
from langsmith import Client

client = Client(api_key="ls__YOUR_API_KEY")

# 创建一个追踪运行
with client.trace(
    project="my-agent",
    name="agent_run"
) as run:
    # LLM 调用
    llm_result = client.track_llm(
        model="gpt-4o",
        prompt="Hello",
        output="World",
        tokens={"input": 10, "output": 5}
    )

    # 工具调用
    tool_result = client.track_tool(
        name="search",
        input={"query": "weather"},
        output={"result": "sunny"}
    )
```

### LangSmith 的局限性

1. **本地部署需要官方 API Key**：LangSmith 虽然提供自托管选项，但自托管版本仍然需要官方的 API Key 进行鉴权。这意味着没有真正的离线使用方式。

2. **数据隐私风险**：即使在自托管模式下，元数据和鉴权信息仍会与 LangSmith 服务器通信。

3. **定价模式**：免费层有严格的用量限制（每月 1000 次追踪），超出后需要付费。

4. **LangChain 强绑定**：虽然支持非 LangChain 应用，但最佳体验需要 LangChain 生态。

---

## LangFuse 详解

### LangFuse 是什么

LangFuse 是一个开源的 LLM 可观测性平台，由德国团队开发。它提供与 LangSmith 类似的功能——追踪、评估、Prompt 管理——但一个关键区别在于：LangFuse 支持真正的完全自托管，无需任何外部 API Key。

### 核心特性

```python
# LangFuse 的基本用法
from langfuse import LangFuse

langfuse = LangFuse(
    secret_key="sk-lf-...",
    public_key="pk-lf-...",
    host="http://localhost:3000"  # 自托管地址
)

# 创建追踪
trace = langfuse.trace(
    name="agent-execution",
    user_id="user-123",
    session_id="session-456",
    metadata={"env": "production"}
)

# 记录 LLM 调用
generation = trace.generation(
    name="chat-completion",
    model="gpt-4o",
    model_parameters={"temperature": 0.7},
    input=[{"role": "user", "content": "Hello"}],
    output={"role": "assistant", "content": "Hi there!"},
    usage={"input": 10, "output": 5, "total": 15}
)

# 记录工具调用
span = trace.span(
    name="search_tool",
    input={"query": "weather"},
    output={"result": "sunny"}
)
```

### LangFuse 的优势

1. **真正的完全自托管**：Docker Compose 一键部署，不需要任何外部 API Key
2. **开源**：MIT 许可证，代码完全可见
3. **数据本地化**：所有数据存储在自己的数据库中
4. **无用量限制**：自托管没有追踪次数限制
5. **丰富的 SDK**：支持 Python、JS/TS、OpenAI SDK 集成
6. **OpenTelemetry 兼容**：可以与标准 Observability 生态集成

---

## 功能对比

| 特性              | LangSmith              | LangFuse              |
|-------------------|------------------------|-----------------------|
| 开源              | 部分（监控功能不开源） | 完全开源（MIT）        |
| 自托管            | 需要 API Key           | 完全独立              |
| 数据本地化        | 有限                   | 完全本地              |
| Docker 部署       | 支持                   | 支持                  |
| Python SDK        | 完善                   | 完善                  |
| JS/TS SDK         | 完善                   | 完善                  |
| Prompt 管理       | 有                     | 有                    |
| 评估/打标         | 有                     | 有                    |
| 数据集管理        | 有                     | 有                    |
| 在线 Playground   | 有                     | 有                    |
| Webhook 告警      | 有                     | 有                    |
| SSO/团队协作      | 企业版                 | 企业版                |
| 免费层追踪数      | 1000/月                | 无限制（自托管）       |
| LangChain 集成    | 原生                   | 深度（通过回调）       |
| OpenAI SDK 集成   | 通过 LangChain         | 原生（@observe）      |
| OpenTelemetry 支持 | 有限                  | 原生支持              |

### 关键差异分析

LangSmith 和 LangFuse 在功能上高度相似，但有一个决定性的差异点：

**LangSmith 的本地部署仍然需要官方 API Key。** 这意味着即使你在自己的服务器上运行 LangSmith，每次追踪调用时仍然需要与 LangSmith 的官方服务进行鉴权通信。如果 LangSmith 官方服务不可用，你的追踪也会失败。

**LangFuse 自托管完全不需要任何外部依赖。** Docker Compose 启动后，所有功能——追踪、评估、Prompt 管理——都在本地运行，与外部网络完全隔离。这在以下场景中至关重要：

- 企业内部部署，数据不能出内网
- 开发/测试环境，没有互联网连接
- 合规要求严格，需要数据完全本地化
- 大规模使用，不受免费层限制

---

## 为什么 agent_platform 选择 LangFuse

agent_platform 选择 LangFuse 而非 LangSmith 的核心原因：

### 1. 真正的本地开发体验

```python
# agent_platform 中使用 LangFuse
from agent_platform.observability.tracing import get_tracer

tracer = get_tracer()

# 自动追踪 Agent 执行
@tracer.observe()
async def run_agent(task: str):
    """
    使用 @observe 装饰器自动追踪
    不需要手动创建 trace/span
    """
    result = await agent.execute(task)
    return result
```

所有追踪数据存储在本地 Docker 容器中，不依赖任何外部服务。

### 2. 成本可控

自托管 LangFuse 的唯一成本是服务器资源（一个 Docker 主机），没有按量计费。对于每天数千次 LLM 调用的开发团队来说，这可以节省大量成本。

### 3. 数据安全

Agent 应用中常涉及敏感的业务数据（客户信息、内部文档）。LangFuse 自托管确保这些数据不会离开自己的网络边界。

---

## 从 LangSmith 迁移到 LangFuse

### 迁移步骤

```python
# 步骤 1: 安装 LangFuse SDK
# pip install langfuse

# 步骤 2: 初始化 LangFuse 客户端
from langfuse import LangFuse

langfuse = LangFuse(
    secret_key="sk-lf-...",
    public_key="pk-lf-...",
    host="http://localhost:3000"
)

# 步骤 3: 替换 LangSmith 的追踪调用

# 之前 (LangSmith):
# from langsmith import Client
# client = Client(api_key="ls__...")
# with client.trace(project="my-agent") as run:
#     result = llm.invoke(prompt)
#     run.end(output=result)

# 之后 (LangFuse):
trace = langfuse.trace(name="agent-execution")
generation = trace.generation(
    name="llm-call",
    model="gpt-4o",
    input=prompt,
    output=result
)
generation.end()
trace.end()
```

### 使用 LangFuse 装饰器模式

对于新项目，推荐直接使用 LangFuse 的装饰器模式，这比 LangSmith 的上下文管理器模式更简洁：

```python
from langfuse.decorators import observe

@observe()
def my_agent_function(query: str):
    """自动追踪输入、输出和 LLM 调用"""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content
```

---

## API Key 需求

| 平台      | 本地部署需要 API Key | 获取方式             |
|-----------|---------------------|----------------------|
| LangSmith | 是（即使自托管也需要）| smith.langchain.com  |
| LangFuse  | 否（自托管完全独立）  | 本地生成（Docker）    |

```bash
# LangSmith（本地部署仍然需要）
LANGSMITH_API_KEY=ls__xxxxxxxxxxxx
LANGSMITH_PROJECT=my-agent

# LangFuse（自托管）
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxx
LANGFUSE_HOST=http://localhost:3000
```

LangSmith 的 API Key 是必须的——没有它，即使是本地部署也无法使用。LangFuse 的 Key 是在 Docker 启动时自动生成的，完全由本地环境控制。

---

## 实用迁移清单

### 数据迁移

LangSmith 到 LangFuse 的数据无法直接迁移（两者数据模型不同）。推荐的做法是：

1. 保留 LangSmith 的历史数据作为只读存档
2. 从迁移日期开始，所有新追踪数据写入 LangFuse
3. 如需对照历史数据，通过 CSV 导出 LangSmith 数据后导入 LangFuse

### 代码迁移清单

```python
# 迁移检查清单

# [ ] 1. 替换 SDK 导入
#   之前: from langsmith import Client, traceable
#   之后: from langfuse import LangFuse
#         from langfuse.decorators import observe

# [ ] 2. 替换环境变量
#   之前: LANGSMITH_API_KEY, LANGSMITH_PROJECT
#   之后: LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST

# [ ] 3. 替换装饰器
#   之前: @traceable
#   之后: @observe()

# [ ] 4. 替换手动追踪
#   之前: client.trace(...) / run.end(...)
#   之后: langfuse.trace(...) / trace.end(...)

# [ ] 5. 替换评估方式
#   之前: LangSmith 数据集 + 自动评估
#   之后: LangFuse score() + 自定义评估函数
```

### 关键集成模式对比

```python
# ======== LangSmith 模式 ========
# 使用 context manager
from langsmith import traceable
from langsmith import Client

client = Client()

@traceable(project="my-agent")
def agent_call(query: str):
    """LangSmith 通过装饰器自动追踪"""
    response = llm.invoke(query)
    return response

# 手动追踪
with client.trace(project="my-agent", name="search") as run:
    run.add_inputs({"query": query})
    result = search(query)
    run.add_outputs({"result": result})

# ======== LangFuse 模式 ========
# 使用装饰器
from langfuse.decorators import observe

@observe()
def agent_call(query: str):
    """LangFuse 同样支持装饰器模式"""
    response = llm.invoke(query)
    return response

# 手动追踪
trace = langfuse.trace(name="search")
trace.span(name="search-execution", input={"query": query}, output={"result": result})
trace.end()

# 上下文管理器模式 (LangFuse)
with trace.span(name="search") as span:
    result = search(query)
    span.update(output={"result": result})
```

### 部署架构对比

```yaml
# LangSmith 自部署架构
services:
  langsmith:
    image: langsmith/langsmith:latest
    environment:
      # 即使自部署也需要这些 API Key
      LANGCHAIN_API_KEY: ls__xxxxx  # 必须从 LangChain 官网获取
    ports:
      - "1984:1984"

# LangFuse 自部署架构
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: local_pass  # 本地密码，无需外部服务

  langfuse:
    image: ghcr.io/langfuse/langfuse:latest
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://langfuse:local_pass@postgres:5432/langfuse
      # 不需要任何外部 API Key
      NEXTAUTH_SECRET: local-secret
    ports:
      - "3000:3000"
```

### LangSmith Local 模式的真相

LangSmith 的本地部署（self-hosted）模式有一个关键的限制容易被忽视：

**即使你运行自己的 LangSmith 服务器，每个 LangSmith SDK 实例在初始化时仍然需要向 LangSmith 的官方 API 服务器发送鉴权请求。** 这意味着：

- 如果官方服务器宕机，你的本地追踪也会停止工作
- 如果网络断开，SDK 初始化会失败
- 追踪数据虽存储在本地，但鉴权依赖外部服务
- 元数据（如 API Key 使用量）仍然会上传至官方服务器

这一设计决策意味着 LangSmith 并不是"真正的"本地部署，而是"数据存储本地化但控制面仍在云端"的混合模式。对于需要完全离线运行、数据不出内网的企业场景，这是一个重大限制。

## 总结

LangSmith 和 LangFuse 都是优秀的 LLM 可观测性平台。但 LangSmith 的"本地部署仍需 API Key"的架构设计，使得它并不适合需要完全本地化、离线运行、数据不出网的场景。对于 agent_platform 这样的本地开发优先的 Agent 框架，LangFuse 是更合适的选择。

LangFuse 的真正自托管能力意味着：
- 开发环境可以完全离线工作
- 生产环境数据不会离开内网
- 大规模使用无需担心配额限制
- 全部代码开源，可审计可定制

### 建议

| 场景           | 推荐方案   | 原因                         |
|----------------|-----------|------------------------------|
| 个人学习       | LangFuse  | 免费、本地运行、无限制        |
| 企业内部应用   | LangFuse  | 数据本地化、无外部依赖        |
| 与 LangChain 深度集成 | LangSmith | 原生集成、调试方便     |
| 需要离线开发   | LangFuse  | 完全离线、无鉴权依赖          |
| 合规要求严格   | LangFuse  | 数据不出网、代码开源可审计    |
ENDOFFILE