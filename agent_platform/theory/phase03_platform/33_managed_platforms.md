# 33 Agent 托管平台 — LangGraph Platform / Modal / Vertex AI

## 1. 概念概述

### 1.1 什么是 Agent 托管平台

Agent 托管平台是为 AI Agent 提供部署、运行、扩缩容和监控的一站式解决方案。与传统的云计算服务不同，Agent 托管平台针对 LLM 工作负载进行了专门优化，包括流式响应支持、GPU 资源管理、LLM 缓存、请求排队等特性。

核心价值主张：
- **零基础设施管理**：无需手动配置服务器、GPU、负载均衡器
- **自动扩缩容**：根据请求量自动调整计算资源
- **内置观测性**：请求追踪、Token 用量、延迟监控开箱即用
- **快速迭代**：代码推送即部署，无需复杂的 CI/CD 管线

### 1.2 三大平台对比

| 特性 | LangGraph Platform | Modal | Vertex AI Agent Builder |
|------|-------------------|-------|----------------------|
| 定位 | Agent 编排部署平台 | Serverless 计算平台 | 全栈 AI 平台 |
| 部署方式 | LangGraph Cloud CLI | modal deploy | gcloud CLI / Console |
| 冷启动 | 较快 (~2s) | 快 (~1s) | 中等 (~5s) |
| GPU 支持 | 通过自托管 | 原生 GPU 支持 | 原生 GPU 支持 |
| 流式响应 | 原生支持 | 支持 | 支持 |
| 自动扩缩 | 内建 | 内建 | GKE 自动扩缩 |
| 最大并发 | 取决于套餐 | 近乎无限 | 取决于配额 |
| 厂商锁定 | 中等 (LangGraph 生态) | 低 (标准 Python) | 高 (GCP 生态) |
| 定价模式 | 月费 + 按量 | 按运行时长 | 按 API 调用 + 资源 |

### 1.3 适用场景对比

- **LangGraph Platform**：已有 LangGraph Agent 代码，需要快速部署为 API
- **Modal**：需要灵活的计算资源（含 GPU），偏向函数即服务（FaaS）模式
- **Vertex AI Agent Builder**：企业级 GCP 用户，需要与 Google 生态集成
- **自托管 K8s**：对成本敏感，需要完全控制基础设施

## 2. 核心原理

### 2.1 Serverless 架构原理

Agent 托管平台普遍采用 Serverless 架构，核心机制包括：

1. **事件驱动触发**：HTTP 请求到达时动态分配计算资源
2. **按需计费**：仅在请求处理期间计费，空闲无成本
3. **透明伸缩**：平台自动管理副本数量，开发者无需关心

Serverless Agent 的生命周期：
```
请求到达 -> 容器分配/唤醒 -> 加载依赖 -> 执行 Agent 逻辑 -> 返回响应 -> 容器进入空闲
```

### 2.2 冷启动问题

冷启动（Cold Start）是 Serverless 架构的核心挑战。Agent 应用的冷启动尤为严重，因为：
- 加载 Python 运行时 (~200ms)
- 导入 Agent 框架和大模型 SDK (~500ms-1s)
- 建立 LLM API 连接 (~200ms)
- 加载工具函数和提示词模板 (~300ms)

缓解冷启动的策略：
- **保持最小活跃容器数**（Warm Workers）
- **使用轻量依赖**（避免 Docker 镜像过大）
- **延迟加载**（按需导入非核心模块）

### 2.3 Agent 有状态性挑战

Agent 应用通常有状态（对话历史、工具调用状态），而 Serverless 平台天然无状态。解决方案：
- **外部化状态**：将状态存储到 Redis / PostgreSQL
- **Sticky Sessions**：相同用户的请求路由到同一容器
- **状态快照**：每次调用后将状态持久化

## 3. 实战指南

### 3.1 Modal 平台部署 Agent

Modal 是最简洁的 Agent 托管平台之一，支持 GPU 和 Python 生态。

```python
# app.py — Modal Agent 部署示例
import modal
from pydantic import BaseModel

# 定义 Modal App
app = modal.App("my-agent-app")

# 定义容器镜像（安装依赖）
image = modal.Image.debian_slim().pip_install(
    "pydantic-ai",
    "openai",
    "httpx",
)

# 定义 Agent 类
class AgentRequest(BaseModel):
    prompt: str
    session_id: str | None = None

class AgentResponse(BaseModel):
    result: str
    token_count: int

@app.cls(
    image=image,
    gpu="T4",  # 可选 GPU
    secrets=[modal.Secret.from_name("openai-api-key")],
    container_idle_timeout=300,  # 5 分钟空闲后自动停止
    keep_warm=1,  # 保持 1 个预热实例
)
class MyAgent:
    def __init__(self):
        self.sessions: dict[str, list] = {}

    @modal.build()
    def build(self):
        """构建时预加载模型和依赖。"""
        import os
        # 验证 API Key 存在
        assert os.environ.get("OPENAI_API_KEY"), "需要设置 OPENAI_API_KEY"

    @modal.enter()
    def enter(self):
        """每次容器启动时执行。"""
        self.sessions = {}
        print("Agent 容器已启动")

    @modal.web_endpoint(method="POST", label="agent-chat")
    def chat(self, request: AgentRequest) -> AgentResponse:
        """Web API 端点。"""
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIModel

        model = OpenAIModel("gpt-4o-mini")
        agent = Agent(
            model=model,
            system_prompt="你是一个智能助手。",
        )

        import asyncio
        result = asyncio.run(agent.run(request.prompt))

        return AgentResponse(
            result=result.data,
            token_count=len(result.data),
        )

    @modal.asgi_app()
    def fastapi_app(self):
        """FastAPI 应用部署。"""
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        web_app = FastAPI(title="Agent API")
        web_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @web_app.post("/chat")
        async def chat_endpoint(request: AgentRequest):
            from pydantic_ai import Agent
            from pydantic_ai.models.openai import OpenAIModel

            model = OpenAIModel("gpt-4o-mini")
            agent = Agent(model=model)
            result = await agent.run(request.prompt)
            return {"result": result.data}

        return web_app

# 部署命令
# modal deploy app.py
```

### 3.2 LangGraph Platform 部署

LangGraph Platform 提供了直接从 LangGraph Agent 到部署 API 的最短路径。

```python
# agent.py — LangGraph Agent 定义
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# 定义状态
class AgentState(TypedDict):
    messages: list
    next_step: str

# 定义工具
def search_database(query: str) -> str:
    """搜索知识库。"""
    return f"找到关于'{query}'的信息..."

def calculate(expression: str) -> str:
    """执行数学计算。"""
    try:
        return str(eval(expression))
    except:
        return "计算错误"

# 创建 LangGraph Agent
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

tools = [search_database, calculate]

# 使用预构建的 ReAct Agent
agent = create_react_agent(model, tools)

# 编译为可执行图
graph = agent.compile(
    checkpointer=MemorySaver(),  # 启用状态持久化
)

# LangGraph Platform 配置文件
# langgraph.json:
# {
#   "python_version": "3.12",
#   "dependencies": ["."],
#   "graphs": {
#     "agent": "./agent.py:graph"
#   },
#   "env": {
#     "OPENAI_API_KEY": "sk-..."
#   }
# }
```

```bash
# 部署到 LangGraph Cloud
# 1. 安装 CLI
pip install langgraph-cli

# 2. 本地测试
langgraph dev

# 3. 部署到云端
langgraph deploy

# 4. 使用 API
curl -X POST https://api.langgraph.cloud/v1/runs \
  -H "Authorization: Bearer $LANGGRAPH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "agent",
    "input": {
      "messages": [{"role": "user", "content": "搜索人工智能的最新进展"}]
    }
  }'
```

### 3.3 Vertex AI Agent Builder

Google Cloud 的企业级 Agent 构建和托管平台。

```python
# Vertex AI Agent 部署示例
import vertexai
from vertexai.preview import reasoning_engines
from google.cloud import aiplatform

# 初始化 Vertex AI
vertexai.init(project="my-project", location="us-central1")

# 定义 Agent 类
class CustomerSupportAgent:
    """客户支持 Agent。"""

    def __init__(self):
        import vertexai.generative_models as gen_ai
        self.model = gen_ai.GenerativeModel("gemini-2.0-flash")
        self.tools = []

    def add_tool(self, name: str, func: callable, description: str):
        """注册工具。"""
        self.tools.append({
            "name": name,
            "function": func,
            "description": description,
        })

    def query(self, user_input: str) -> str:
        """处理用户查询。"""
        prompt = f"""你是一个客服助手。
请回答用户的问题。如果需要更多信息，请询问。

用户问题: {user_input}
"""
        response = self.model.generate_content(prompt)
        return response.text

# 部署到 Vertex AI
agent = CustomerSupportAgent()
agent.add_tool(
    "check_order_status",
    lambda order_id: f"订单 {order_id} 状态：已发货",
    "查询订单状态",
)

# 创建 Reasoning Engine
remote_agent = reasoning_engines.ReasoningEngine.create(
    agent.query,
    display_name="customer-support-agent",
    description="客户支持 Agent",
)

print(f"Agent 已部署: {remote_agent.resource_name}")

# 调用部署的 Agent
response = remote_agent.query(user_input="我的订单 12345 状态如何？")
print(response)
```

### 3.4 平台选择决策模型

```python
"""Agent 托管平台选择器。"""

PLATFORM_SCORES = {
    "langgraph": {
        "langgraph_experience": 10,
        "agent_complexity": 9,
        "need_streaming": 10,
        "budget_under_100": 6,
    },
    "modal": {
        "langgraph_experience": 5,
        "agent_complexity": 7,
        "need_streaming": 8,
        "budget_under_100": 9,
    },
    "vertex_ai": {
        "langgraph_experience": 3,
        "agent_complexity": 6,
        "need_streaming": 7,
        "budget_under_100": 4,
    },
    "self_hosted_k8s": {
        "langgraph_experience": 4,
        "agent_complexity": 10,
        "need_streaming": 9,
        "budget_under_100": 3,
    },
}

def recommend_platform(
    has_langgraph_exp: bool,
    complex_agent: bool,
    streaming_required: bool,
    monthly_budget_usd: float,
) -> str:
    """根据条件推荐最佳平台。"""
    scores = {}
    for platform, criteria in PLATFORM_SCORES.items():
        score = 0
        score += criteria["langgraph_experience"] if has_langgraph_exp else 0
        score += criteria["agent_complexity"] if complex_agent else 0
        score += criteria["need_streaming"] if streaming_required else 0
        score += criteria["budget_under_100"] if monthly_budget_usd < 100 else 0
        scores[platform] = score
    return max(scores, key=scores.get)

# 使用示例
print(recommend_platform(
    has_langgraph_exp=True,
    complex_agent=True,
    streaming_required=True,
    monthly_budget_usd=200,
))  # 推荐 langgraph
```

### 3.5 成本估算器

```python
"""Agent 托管成本估算。"""

def estimate_monthly_cost(
    requests_per_day: int,
    avg_latency_seconds: float,
    platform: str = "modal",
    gpu_hourly_cost: float = 0.50,
) -> dict:
    """估算每月托管成本。"""
    monthly_requests = requests_per_day * 30
    total_compute_hours = (monthly_requests * avg_latency_seconds) / 3600

    if platform == "modal":
        # Modal: GPU $0.50/hr + CPU $0.10/hr
        compute_cost = total_compute_hours * (gpu_hourly_cost + 0.10)
        # 冷启动开销 +20%
        compute_cost *= 1.2
        storage_cost = 5.0  # 文件存储
        total = compute_cost + storage_cost
        return {
            "platform": "Modal",
            "compute_hours": round(total_compute_hours, 1),
            "compute_cost": round(compute_cost, 2),
            "storage_cost": storage_cost,
            "total_monthly": round(total, 2),
        }
    elif platform == "langgraph":
        # LangGraph: $99/月起步 + 按量
        base_plan = 99.0
        overage = max(0, (monthly_requests - 100000) / 1000 * 0.05)
        total = base_plan + overage
        return {
            "platform": "LangGraph Platform",
            "base_plan": base_plan,
            "overage": round(overage, 2),
            "total_monthly": round(total, 2),
        }
    elif platform == "vertex_ai":
        # Vertex AI: 按 API 调用 + 资源
        api_calls_cost = monthly_requests * 0.002
        compute_cost = total_compute_hours * gpu_hourly_cost
        total = api_calls_cost + compute_cost
        return {
            "platform": "Vertex AI",
            "api_calls_cost": round(api_calls_cost, 2),
            "compute_cost": round(compute_cost, 2),
            "total_monthly": round(total, 2),
        }

    return {"error": "未知平台"}

# 估算 10000 请求/天，平均延迟 5s 的成本
cost = estimate_monthly_cost(10000, 5)
print(f"平台: {cost['platform']}")
print(f"每月总成本: ${cost['total_monthly']}")
```

## 4. 最佳实践

### 4.1 部署策略

1. **先 Modal 验证**：Modal 上手最快，适合原型验证
2. **规模后迁移**：当业务稳定后评估是否需要迁移到 K8s
3. **混合部署**：Agent 逻辑在托管平台，状态存储用托管数据库
4. **多区域部署**：对延迟敏感的场景部署到多个区域

### 4.2 成本优化

1. **合理设置 keep_warm**：Modal 的 keep_warm=0 最低成本，但首次请求慢
2. **使用轻量模型**：gpt-4o-mini 替代 gpt-4o 降低成本 10x
3. **缓存重复请求**：语义缓存减少相同问题的重复调用
4. **请求合并**：将多个简单请求合并为一个 Agent 调用

### 4.3 避免厂商锁定

1. **代码与平台解耦**：Agent 核心逻辑与部署代码分离
2. **使用标准接口**：OpenAI 兼容 API 格式便于切换
3. **状态外部化**：状态存储在 Redis / PostgreSQL，而非平台内存
4. **容器化**：使用 Docker 确保环境一致性

### 4.4 监控策略

1. **请求级追踪**：记录每次 Agent 调用的完整轨迹
2. **成本告警**：设置每日/每月成本上限
3. **错误率监控**：Agent 调用失败率 > 5% 告警
4. **延迟分位数**：关注 p95/p99 延迟，不仅看平均值

## 5. 常见陷阱

### 5.1 冷启动导致超时

未预热容器时，首次请求可能耗时 10s+，导致客户端超时。

### 5.2 忽视最大请求超时

Modal 默认请求超时 300s，LangGraph Platform 有 60s 限制。复杂 Agent 
超过限制将被中断。

### 5.3 状态丢失

Serverless 平台容器随时可能被回收，内存状态不可靠。

### 5.4 成本失控

未设置预算限制时，突发的流量高峰可能产生巨额账单。

### 5.5 GPU 利用率低

GPU 按秒计费，Agent 推理中的非 GPU 计算（如工具调用）也在计费。

## 6. API Key 依赖

所有托管平台都需要注册账号和 API Key：

| 平台 | 注册地址 | 认证方式 | 免费额度 |
|------|---------|---------|---------|
| Modal | modal.com | API Token | $30/月 GPU 额度 |
| LangGraph Platform | langchain.dev | API Key | 14 天试用 |
| Vertex AI | cloud.google.com | GCP 服务账号 | $300 新用户额度 |
| Railway | railway.app | API Token | $5 免费额度 |

## 7. 技术关系

- **上层**：Agent 应用代码 -> 实际业务逻辑
- **本层**：托管平台 API -> 部署和运行
- **下层**：Kubernetes / Docker -> 容器编排
- **并行**：自托管方案 -> 手动管理的基础设施
- **状态**：Redis / PostgreSQL -> 外部状态存储

## 8. 验收清单

- [ ] 理解 Serverless Agent 架构的核心原理
- [ ] 掌握 Modal 平台的 Agent 部署流程
- [ ] 了解 LangGraph Platform 的部署配置
- [ ] 熟悉 Vertex AI Agent Builder 的基本用法
- [ ] 理解冷启动问题及其缓解策略
- [ ] 能够估算不同平台的托管成本
- [ ] 掌握 Agent 状态的外部化存储方案
- [ ] 了解厂商锁定风险和解耦策略
- [ ] 设置监控和成本告警
- [ ] 完成至少一个平台的端到端部署

## 9. 学习资源

- Modal 文档：https://modal.com/docs
- LangGraph Platform：https://langchain-ai.github.io/langgraph/cloud/
- Vertex AI Agent Builder：https://cloud.google.com/vertex-ai
- Serverless 架构模式：https://serverless.com
- LangGraph Cloud 快速入门：https://langchain-ai.github.io/langgraph/cloud/quick_start/
