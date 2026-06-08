# 31 Pydantic AI — 结构化 Agent 框架深度解析

## 1. 概念概述

### 1.1 什么是 Pydantic AI

Pydantic AI 是一个基于 Pydantic 模型构建的 Python Agent 框架，核心设计理念是"类型安全优先"。它利用 Pydantic v2 的类型系统为 LLM Agent 提供结构化输入输出验证，使开发者能够以声明式方式定义 Agent 的行为、工具和结果模型。

与 LangChain、Instructor 等框架相比，Pydantic AI 的独特优势在于：
- **原生 Pydantic 集成**：Agent 的输入输出天然是 Pydantic 模型，无需额外的解析层
- **模型无关架构**：通过统一的 `Model` 接口支持 OpenAI、Anthropic、Gemini、Groq 等多种后端
- **`@agent` 装饰器模式**：使用 Python 装饰器优雅地定义 Agent 及其工具
- **依赖注入系统**：内建依赖注入，无需手动管理 Agent 的上下文状态
- **流式输出与验证**：支持流式结果的实时验证，而不是等待完整响应

### 1.2 与同类框架对比

| 特性         | Pydantic AI | Instructor | LangChain | AutoGen |
|-------------|-------------|-----------|-----------|---------|
| 类型安全     | 原生 Pydantic v2 | 基于 Pydantic | 需要额外配置 | 有限支持 |
| 装饰器风格   | @agent      | 无         | @tool     | 无      |
| 依赖注入     | 内建         | 无         | LCEL 链   | 需要手动 |
| 模型支持     | 6+ 提供商    | 30+        | 100+      | 仅 OpenAI |
| 流式验证     | 支持         | 支持       | 有限       | 不支持   |
| 学习曲线     | 低           | 低         | 中高       | 中       |

### 1.3 适用场景

- **企业级 API 开发**：需要强类型验证的生产环境
- **工具调用密集型 Agent**：多个工具相互协作的复杂场景
- **多模型切换**：需要在不同 LLM 提供商之间切换
- **流式 UI 集成**：实时显示 Agent 推理过程的交互式应用

## 2. 核心原理

### 2.1 Agent 定义与生命周期

Pydantic AI 的 Agent 是其核心抽象，每个 Agent 包含以下要素：
- **系统提示词（System Prompt）**：定义 Agent 的角色和行为
- **工具集（Tools）**：Agent 可以调用的函数集合
- **结果类型（Result Type）**：Agent 输出的 Pydantic 模型
- **模型后端（Model）**：具体的 LLM 实现

Agent 的生命周期分为三个阶段：
1. **初始化阶段**：创建 Agent 实例，注册工具
2. **运行阶段**：接收用户输入，循环执行 LLM 调用和工具执行
3. **完成阶段**：返回验证后的结构化结果

### 2.2 依赖注入机制

Pydantic AI 的依赖注入系统是其区别于其他框架的关键特性。机制如下：

```python
from dataclasses import dataclass

@dataclass
class UserContext:
    user_id: str
    role: str
    permissions: list[str]

agent = Agent[UserContext](model=model)
```

依赖注入在每次 run 时解析，避免了全局状态和手动上下文传递。

### 2.3 工具注册与执行流程

工具注册支持三种方式：
1. **函数装饰器**：`@agent.tool` 装饰器注册
2. **类方法**：在 Agent 子类中定义
3. **动态注册**：运行时注册工具

执行流程为：
用户输入 -> LLM 选择工具 -> 执行工具 -> 工具结果回传 -> LLM 继续推理 -> 最终输出

### 2.4 流式处理架构

Pydantic AI 的流式处理分为两层：
1. **文本流**：LLM 生成的 token 逐个到达
2. **结构化流**：部分结果实时验证和返回

流式处理使用 `StreamedRunResult` 对象，支持 `async for` 迭代。

## 3. 实战指南

### 3.1 环境准备与安装

```bash
pip install pydantic-ai pydantic openai
```

设置环境变量：
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### 3.2 基础 Agent 示例

```python
import asyncio
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# 定义结果模型
class WeatherResult(BaseModel):
    city: str
    temperature: float
    unit: str = "celsius"
    condition: str
    humidity: float | None = None

# 创建模型实例
model = OpenAIModel("gpt-4o-mini")

# 定义 Agent
weather_agent = Agent(
    model=model,
    result_type=WeatherResult,
    system_prompt="你是一个天气助手，分析天气数据并返回结构化结果。"
)

# 运行 Agent
async def main():
    result = await weather_agent.run("北京的天气怎么样？")
    print(f"城市: {result.data.city}")
    print(f"温度: {result.data.temperature}{result.data.unit}")
    print(f"天气状况: {result.data.condition}")
    print(f"湿度: {result.data.humidity}")

asyncio.run(main())
```

### 3.3 使用 @agent.tool 注册工具

```python
import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from dataclasses import dataclass

@dataclass
class Database:
    conn_str: str

model = OpenAIModel("gpt-4o-mini")
agent = Agent[Database](model=model, system_prompt="从数据库查询用户信息。")

@agent.tool
async def get_user_email(ctx: RunContext[Database], user_name: str) -> str:
    """根据用户名获取用户的电子邮件地址。"""
    print(f"连接到数据库: {ctx.deps.conn_str}")
    database = {
        "张三": "zhangsan@example.com",
        "李四": "lisi@example.com",
    }
    return database.get(user_name, "未找到用户")

@agent.tool
async def send_notification(ctx: RunContext[Database], email: str, message: str) -> dict:
    """向指定邮箱发送通知消息。"""
    print(f"向 {email} 发送消息: {message}")
    return {"status": "sent", "email": email, "message_length": len(message)}

async def main():
    db = Database(conn_str="postgresql://localhost:5432/users")
    result = await agent.run("查询张三的邮箱并发送欢迎通知", deps=db)
    print("最终结果:", result.data)

asyncio.run(main())
```

### 3.4 流式输出与实时验证

```python
import asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

class ArticleResult(BaseModel):
    title: str = Field(description="文章的标题")
    summary: str = Field(description="文章摘要，不超过200字")
    keywords: list[str] = Field(description="关键词列表")

model = OpenAIModel("gpt-4o-mini")
agent = Agent(model=model, result_type=ArticleResult)

async def main():
    async with agent.run_stream("写一篇关于人工智能的文章") as result:
        print("正在流式生成...")
        async for chunk in result.stream():
            print(chunk, end="", flush=True)

        print("\n\n=== 最终结构化数据 ===")
        data = await result.get_data()
        print(f"标题: {data.title}")
        print(f"摘要: {data.summary}")
        print(f"关键词: {', '.join(data.keywords)}")

asyncio.run(main())
```

### 3.5 多模型切换与模型无关设计

```python
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from typing import Literal

class ModelRouter:
    """模型路由器：根据任务选择不同的后端模型。"""

    def __init__(self):
        self.models = {
            "gpt4": OpenAIModel("gpt-4o"),
            "claude": AnthropicModel("claude-sonnet-4-20250514"),
            "gemini": GeminiModel("gemini-2.0-flash"),
        }

    def get_agent(self, backend: Literal["gpt4", "claude", "gemini"]) -> Agent:
        model = self.models[backend]
        return Agent(
            model=model,
            system_prompt="你是一个多语言助手。",
        )

async def main():
    router = ModelRouter()
    agents = {
        "GPT-4o": router.get_agent("gpt4"),
        "Claude": router.get_agent("claude"),
        "Gemini": router.get_agent("gemini"),
    }
    for name, agent in agents.items():
        result = await agent.run(f"用{name}风格介绍你自己")
        print(f"\n=== {name} ===")
        print(result.data)

asyncio.run(main())
```

### 3.6 复杂结果验证与重试

```python
import asyncio
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.exceptions import ModelRetry

class CodeReviewResult(BaseModel):
    score: int = Field(ge=0, le=100, description="代码质量评分")
    issues: list[str] = Field(min_length=1, description="发现的问题列表")
    suggestions: list[str] = Field(min_length=1)

    @field_validator("score")
    @classmethod
    def score_must_be_reasonable(cls, v):
        if v < 30 or v > 95:
            raise ValueError("评分应在30-95之间，避免极端值")
        return v

model = OpenAIModel("gpt-4o-mini")

agent = Agent(
    model=model,
    result_type=CodeReviewResult,
    system_prompt="""你是一个代码审查助手。
请仔细分析代码并提供合理的评分和具体的改进建议。
评分应该在30-95之间，避免给出极端分数。""",
    retries=3,
)

async def main():
    code = """
def add(a,b):
    return a+b
"""
    try:
        result = await agent.run(f"审查这段代码:\n```python\n{code}\n```")
        print(f"评分: {result.data.score}")
        print(f"问题: {result.data.issues}")
        print(f"建议: {result.data.suggestions}")
    except ModelRetry as e:
        print(f"验证重试失败: {e}")

asyncio.run(main())
```

### 3.7 异步工具与并发执行

```python
import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from dataclasses import dataclass
import httpx

@dataclass
class HTTPClient:
    client: httpx.AsyncClient

model = OpenAIModel("gpt-4o-mini")
agent = Agent[HTTPClient](model=model, system_prompt="同时查询多个数据源。")

@agent.tool
async def fetch_weather(ctx: RunContext[HTTPClient], city: str) -> dict:
    """获取指定城市的天气信息。"""
    await asyncio.sleep(0.5)
    return {"city": city, "temperature": 25, "condition": "晴"}

@agent.tool
async def fetch_news(ctx: RunContext[HTTPClient], topic: str) -> list:
    """获取指定主题的最新新闻。"""
    await asyncio.sleep(0.3)
    return [f"{topic}新闻1", f"{topic}新闻2", f"{topic}新闻3"]

@agent.tool
async def fetch_stock(ctx: RunContext[HTTPClient], symbol: str) -> dict:
    """获取股票实时数据。"""
    await asyncio.sleep(0.4)
    return {"symbol": symbol, "price": 150.25, "change": 2.5}

async def main():
    async with httpx.AsyncClient() as client:
        deps = HTTPClient(client=client)
        result = await agent.run(
            "同时查询北京天气、AI领域新闻和AAPL股票",
            deps=deps,
        )
        print(result.data)

asyncio.run(main())
```

## 4. 最佳实践

### 4.1 结果模型设计原则

1. **字段精细化**：每个字段添加 `description`，帮助 LLM 理解预期输出
2. **验证规则明确**：使用 Pydantic 的 `Field` 约束（`ge`, `le`, `min_length` 等）
3. **可选字段策略**：不确定的字段使用 `Optional` 类型，避免强制 LLM 生成虚假信息
4. **嵌套模型**：复杂结构使用嵌套 Pydantic 模型，保持类型层次清晰

### 4.2 工具函数设计

1. **单一职责**：每个工具只做一件事，保持函数简洁
2. **详细 docstring**：工具的描述直接影响 LLM 的调用准确性
3. **参数类型提示**：使用 Python 类型注解，帮助 LLM 推断参数格式
4. **错误处理**：工具内部捕获异常，返回友好的错误信息而非抛出异常

### 4.3 依赖注入模式

```python
from dataclasses import dataclass

@dataclass
class AppDependencies:
    db_url: str
    redis_url: str
    api_key: str
```

### 4.4 系统提示词优化

1. **明确角色定位**：告诉 Agent 它应该扮演什么角色
2. **提供输出格式示例**：展示期望的响应格式
3. **边界条件说明**：告诉 Agent 什么情况下应该拒绝回答
4. **工具使用策略**：指导 Agent 何时调用特定工具

## 5. 常见陷阱

### 5.1 类型验证过于严格

```python
# 错误：过于严格的验证导致频繁重试
class StrictResult(BaseModel):
    score: int = Field(ge=50, le=80)

# 正确：保留合理范围
class FlexibleResult(BaseModel):
    score: int = Field(ge=0, le=100)
```

### 5.2 忽略结果类型变化

当升级 Pydantic 或 pydantic-ai 版本时，结果类型的序列化行为可能变化：
Pydantic v2 默认使用 `model_dump()` 而非 `dict()`，升级后需要更新序列化逻辑。

### 5.3 工具函数副作用

```python
# 错误：工具函数内修改全局状态
counter = 0
@agent.tool
async def increment(ctx: RunContext) -> int:
    global counter
    counter += 1
    return counter
```

### 5.4 流式处理中错误处理缺失

流式处理中，部分结果可能验证失败。始终使用 try/except 包裹流处理代码。

### 5.5 依赖注入对象不可序列化

Agent 运行在多线程或分布式环境中时，确保依赖对象是可序列化的。

## 6. API Key 依赖

| 模型后端   | API Key 来源              | 环境变量              |
|-----------|--------------------------|---------------------|
| OpenAI    | platform.openai.com      | OPENAI_API_KEY      |
| Anthropic | console.anthropic.com    | ANTHROPIC_API_KEY   |
| Gemini    | ai.google.dev            | GEMINI_API_KEY      |
| Groq      | console.groq.com         | GROQ_API_KEY        |
| Mistral   | console.mistral.ai       | MISTRAL_API_KEY     |

安全建议：
- 不要在代码中硬编码 API Key
- 使用 `.env` 文件加载环境变量
- 生产环境使用密钥管理服务（如 AWS Secrets Manager）

## 7. 技术关系

Pydantic AI 在 Agent 技术栈中的位置：
- **上层**：FastAPI + Pydantic AI Agent -> Web API
- **本层**：Pydantic AI 核心 -> Agent 定义与编排
- **下层**：LLM API SDK (openai, anthropic) -> 模型调用
- **并行**：Instructor (同类), LangChain (更通用的编排)
- **基础设施**：Pydantic v2 -> 类型验证

## 8. 验收清单

- [ ] 理解 Pydantic AI 与 Instructor/LangChain 的核心区别
- [ ] 掌握 @agent 装饰器和 Agent 类的基本用法
- [ ] 能够定义 Pydantic 结果模型并进行结构化输出
- [ ] 理解依赖注入机制并正确使用 RunContext
- [ ] 实现至少 3 个工具函数并注册到 Agent
- [ ] 完成流式输出的实现和验证
- [ ] 掌握多模型切换的配置方法
- [ ] 理解结果验证和自动重试机制
- [ ] 能够处理工具调用中的异常和边界情况
- [ ] 完成异步并发工具的编写和测试

## 9. 学习资源

- 官方文档：https://ai.pydantic.dev
- GitHub：https://github.com/pydantic/pydantic-ai
- Pydantic v2 文档：https://docs.pydantic.dev
- Discord 社区：Pydantic AI Discord
- 示例项目：https://github.com/pydantic/pydantic-ai/examples
- API 参考：https://ai.pydantic.dev/api/agent/
- 快速入门教程：https://ai.pydantic.dev/tutorial/
