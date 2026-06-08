# 03 OpenAI API 深入解析

> OpenAI API 是当前最成熟、生态最完善的 LLM API 之一。理解其核心概念和最佳实践是构建 AI Agent 的基础。

---

## 1. 概念概述

### 1.1 什么是 OpenAI API

OpenAI API 是一组 RESTful 接口，允许开发者以编程方式访问 OpenAI 的大语言模型。主要包括：

- **Chat Completions API**（/v1/chat/completions）：对话补全，最核心的 API
- **Responses API**（/v1/responses）：较新的 API，融合了工具调用和文件处理
- **Embeddings API**（/v1/embeddings）：文本向量化
- **Assistants API**（/v1/assistants）：托管式 Agent 服务
- **Batches API**（/v1/batches）：批量异步处理

对于构建 AI Agent 系统，Chat Completions API 和 Responses API 是最核心的两个。

### 1.2 为什么需要深入理解 OpenAI API

- **成本控制**：不同的模型和参数设置直接影响 token 消耗和成本
- **性能优化**：流式、批处理、缓存等技术可大幅提升响应速度
- **健壮性**：正确的错误处理机制决定生产系统的稳定性
- **模型选择**：理解模型能力边界，选择最合适的"性价比"方案

### 1.3 Chat Completions API vs Responses API

OpenAI 在 2024 年底引入了 Responses API，两种 API 的关键区别如下：

| 特性 | Chat Completions API | Responses API |
|------|---------------------|---------------|
| 核心概念 | messages 数组轮次 | response（含工具调用结果） |
| 工具调用 | tool_calls 元组 | 直接返回工具结果 |
| 文件处理 | 需自行处理 | 原生支持文件上传和处理 |
| 状态管理 | 无状态，需客户端维护 | 有状态，服务端维护 |
| 成熟度 | 非常成熟 | 较新，持续更新中 |

---

## 2. 核心原理

### 2.1 Chat Completions API 调用流程

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个 AI 助手。"},
        {"role": "user", "content": "什么是 RAG？"},
    ],
    temperature=0.1,
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

**底层的请求-响应流程**：

1. 客户端将 messages 数组序列化为 JSON，通过 HTTPS POST 发送
2. OpenAI 服务端对 messages 进行 tokenize，计算 prompt tokens
3. 模型执行推理，逐 token 生成补全
4. 服务端将生成的 completion tokens 组装为响应
5. 客户端解析响应，提取 message.content

**messages 数组中的角色**：

- `system`：系统指令，设置模型行为
- `user`：用户输入
- `assistant`：模型回复（在多轮对话中用于传递上下文）
- `tool`：工具调用结果

### 2.2 Token 管理

Token 是 LLM 的最基本计量单位。理解 Token 管理对控制成本和优化性能至关重要。

```python
# 估算 Token 数量（tiktoken 库）
import tiktoken


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    \"\"\"计算文本的 token 数量。\"\"\"
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def truncate_to_limit(
    text: str, max_tokens: int, model: str = "gpt-4o"
) -> str:
    \"\"\"将文本截断到指定 token 数。\"\"\"
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])
```

**Token 消耗的组成部分**：

- **Prompt Tokens**：输入部分的 token 数（包括 system、user、assistant 消息）
- **Completion Tokens**：输出部分的 token 数
- **总 Token 数** = Prompt Tokens + Completion Tokens

**Token 定价机制**：

OpenAI 的定价通常按每 1M tokens 计费，且输入和输出价格不同：

```
Model      | 输入价格 (per 1M tokens) | 输出价格 (per 1M tokens)
gpt-4o     | $2.50                     | $10.00
gpt-4o-mini| $0.15                     | $0.60
o3-mini    | $1.10                     | $4.40
```

### 2.3 流式输出（Streaming）

流式输出允许模型逐 token 返回结果，而非等待完整的响应。这对用户体验至关重要——用户不需要等待数十秒的空白。

```python
# 流式输出示例
def stream_chat(messages: list[dict]) -> str:
    \"\"\"流式对话，每次 yield 一个 token。\"\"\"
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True,
    )
    full_content = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            full_content += delta.content
            yield delta.content
    return full_content


# 使用示例
print("助手：", end="", flush=True)
for token in stream_chat([
    {"role": "system", "content": "用中文简短回答。"},
    {"role": "user", "content": "解释什么是机器学习。"},
]):
    print(token, end="", flush=True)
```

**流式处理的关键点**：

- 每个 chunk 的 `choices[0].delta` 可能包含 content 或 tool_calls
- 流式模式下，最后一个 chunk 的 `choices[0].finish_reason` 为 "stop" 或 "length"
- 流式模式下仍然可以获取完整结果——只需在客户端拼接所有 delta

### 2.4 速率限制和错误处理

OpenAI API 有严格的速率限制（Rate Limits），生产系统中必须正确处理。

```python
import time
from openai import RateLimitError, APIError


class OpenAIClientWithRetry:
    \"\"\"带重试和速率限制处理的 OpenAI 客户端。\"\"\"

    def __init__(self, api_key: str, max_retries: int = 3):
        self._client = OpenAI(api_key=api_key)
        self._max_retries = max_retries

    def chat_with_retry(self, **kwargs) -> str:
        \"\"\"带指数退避重试的对话调用。\"\"\"
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except RateLimitError as e:
                wait = min(2 ** attempt * 5, 60)  # 指数退避
                print(f"速率限制，等待 {wait} 秒后重试...")
                time.sleep(wait)
            except APIError as e:
                if e.status_code >= 500 and attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    print(f"服务端错误 ({e.status_code})，等待 {wait} 秒...")
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                raise RuntimeError(f"API 调用失败：{e}")
        raise RuntimeError("超过最大重试次数")
```

**常见的错误码**：

| 状态码 | 含义 | 处理策略 |
|--------|------|----------|
| 400 | Bad Request（无效参数） | 检查请求参数，不可重试 |
| 401 | Authentication（API Key 无效） | 检查 API Key，不可重试 |
| 429 | Rate Limit（速率限制） | 指数退避重试 |
| 500 | Server Error（服务端错误） | 指数退避重试 |
| 503 | Service Unavailable | 延迟后重试 |

### 2.5 模型选择策略

OpenAI 当前提供多类模型，选择合适的模型需要在能力、速度、成本之间权衡：

**GPT-4o 系列**（多模态、高智能、中速）：
- GPT-4o：全功能旗舰模型，适合复杂推理、工具调用、结构化输出
- GPT-4o-mini：轻量版，成本降低约 10 倍，适合简单任务

**o 系列**（推理模型，慢但准确）：
- o3-mini：强推理能力，适合数学、编程、科学问题
- o1：高级推理，适合需要深度思考的复杂问题

**GPT-4 Turbo**（旧旗舰，逐步淘汰）：
- 已被 GPT-4o 取代，不建议在新项目中使用

```python
# 模型选择策略
def select_model(task_type: str, complexity: str) -> str:
    \"\"\"根据任务类型和复杂度选择模型。\"\"\"
    model_map = {
        "simple_chat": {
            "low": "gpt-4o-mini",
            "medium": "gpt-4o-mini",
            "high": "gpt-4o",
        },
        "tool_calling": {
            "low": "gpt-4o-mini",
            "medium": "gpt-4o",
            "high": "gpt-4o",
        },
        "reasoning": {
            "low": "gpt-4o",
            "medium": "o3-mini",
            "high": "o3-mini",
        },
        "code_generation": {
            "low": "gpt-4o-mini",
            "medium": "gpt-4o",
            "high": "o3-mini",
        },
    }
    return model_map.get(task_type, {}).get(complexity, "gpt-4o")
```

### 2.6 agent_platform 中的 OpenAI 客户端封装

在 `agent_platform/src/llm/client.py` 中，OpenAI 客户端被封装为 LLMClient，提供了三个核心方法：

```python
# src/llm/client.py 核心逻辑
class LLMClient:
    \"\"\"统一 LLM 客户端，封装 OpenAI 兼容 API。\"\"\"

    def __init__(self, settings: LLMSettings | None = None) -> None:
        cfg = settings or load_config().llm
        self._client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        self._model = cfg.model

    def chat(self, messages, *, temperature=0.1, max_tokens=2048) -> str:
        \"\"\"普通对话，返回纯文本。\"\"\"
        response = self._client.chat.completions.create(
            model=self._model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def chat_stream(self, messages, *, temperature=0.1, max_tokens=2048):
        \"\"\"流式输出生成器。\"\"\"
        stream = self._client.chat.completions.create(
            model=self._model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def chat_with_tools(self, messages, tools, *, temperature=0.0):
        \"\"\"工具调用，返回原始 Complettion 对象。\"\"\"
        return self._client.chat.completions.create(
            model=self._model, messages=messages,
            temperature=temperature, tools=tools,
        )
```

---

## 3. 实战指南

### 3.1 多轮对话管理

```python
class ConversationSession:
    \"\"\"管理多轮对话历史。\"\"\"

    def __init__(self, system_prompt: str, max_context_tokens: int = 8000):
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def trim_context(self):
        \"\"\"当上下文超出限制时，移除最早的用户-助手轮次。\"\"\"
        while self._count_tokens() > self.max_context_tokens:
            if len(self.messages) <= 1:
                break
            # 移除最早的一条对话（索引 1 之后，因为索引 0 是 system）
            if len(self.messages) >= 3:
                self.messages.pop(1)  # 移除最早的 user message
                if len(self.messages) >= 3:
                    self.messages.pop(1)  # 移除对应的 assistant message
            else:
                break

    def _count_tokens(self) -> int:
        encoding = tiktoken.encoding_for_model("gpt-4o")
        return sum(
            len(encoding.encode(m.get("content", "")))
            for m in self.messages
        )

    def get_messages(self) -> list[dict]:
        self.trim_context()
        return self.messages
```

### 3.2 Token 使用量监控

```python
class TokenTracker:
    \"\"\"追踪 API 调用的 token 消耗。\"\"\"

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0

    PRICING = {
        "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "o3-mini": {"input": 1.10 / 1_000_000, "output": 4.40 / 1_000_000},
    }

    def track(self, response, model: str = "gpt-4o"):
        \"\"\"记录一次 API 调用的 token 消耗。\"\"\"
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.call_count += 1

        pricing = self.PRICING.get(model, self.PRICING["gpt-4o"])
        cost = prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]
        self.total_cost += cost

    def report(self) -> dict:
        return {
            "total_calls": self.call_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost, 6),
        }
```

### 3.3 Batch API 批量处理

```python
import json
from pathlib import Path


class BatchProcessor:
    \"\"\"使用 Batch API 批量处理请求（节省 50% 成本）。\"\"\"

    def __init__(self, client: OpenAI):
        self._client = client

    def create_batch_file(
        self, requests: list[dict], output_path: str
    ) -> str:
        \"\"\"创建批量请求文件。\"\"\"
        lines = []
        for i, req in enumerate(requests):
            batch_line = {
                "custom_id": f"request-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": req["messages"],
                    "max_tokens": req.get("max_tokens", 512),
                },
            }
            lines.append(json.dumps(batch_line, ensure_ascii=False))

        filepath = Path(output_path)
        filepath.write_text("\\n".join(lines), encoding="utf-8")

        # 上传文件
        with open(filepath, "rb") as f:
            upload = self._client.files.create(
                file=f, purpose="batch"
            )
        return upload.id

    def submit_batch(self, file_id: str) -> str:
        \"\"\"提交批量任务。\"\"\"
        batch = self._client.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        return batch.id

    def retrieve_results(self, batch_id: str) -> list[dict]:
        \"\"\"获取批量处理结果。\"\"\"
        batch = self._client.batches.retrieve(batch_id)
        if batch.status != "completed":
            return [{"status": batch.status, "message": "任务尚未完成"}]

        result_file_id = batch.output_file_id
        content = self._client.files.content(result_file_id)
        results = []
        for line in content.text.strip().split("\\n"):
            if line:
                results.append(json.loads(line))
        return results
```

---

## 4. 最佳实践

### 4.1 成本控制

- 优先使用 `gpt-4o-mini` 处理简单任务，仅在需要更多智能时使用 `gpt-4o`
- 使用 Batch API 处理非实时任务，成本降低 50%
- 使用 Prompt Caching（需手动标记）减少重复 token 的开销
- 监控 token 消耗，设置月度预算上限
- 利用 `max_tokens` 参数控制输出长度，避免超额

### 4.2 性能优化

- 对流式输出使用 Server-Sent Events（SSE）而非轮询
- 使用连接池（`httpx` 或 `aiohttp`）减少连接建立开销
- 设置合理的超时时间（建议 connect=10s, read=60s）
- 对于非关键性请求，使用异步客户端（`AsyncOpenAI`）

### 4.3 安全性

- API Key 存储在环境变量或密钥管理服务中，**绝不**硬编码
- 使用 API Key 权限隔离：为不同服务创建不同的 API Key
- 设置 Usage Limits，防止意外超额
- 监控异常调用模式（如短时间内大量调用）

---

## 5. 常见陷阱与反模式

### 5.1 忽略 Token 限制

反模式：不检查上下文窗口是否溢出。GPT-4o 的上下文窗口是 128K tokens，当 messages 累积太多时，模型会丢失早期信息或直接报错。正确做法是实现 token 计数和上下文截断。

### 5.2 错误的重试逻辑

反模式：对所有错误不加区分地重试。401 认证错误和 400 请求错误即使重试也无法成功。正确做法是区分可重试错误（429、5xx）和不可重试错误（4xx 除 429）。

### 5.3 流式输出时的异常处理

反模式：在流式生成过程中不做错误处理。如果流在中间中断，用户只能看到部分回答。正确做法是在流式调用外层包装 try-except，在中断时给出提示。

### 5.4 盲目使用最新模型

反模式：无脑使用最新模型，忽略实际任务的需求。o3-mini 虽然推理能力强，但推理时间长、成本高。对于简单的分类任务，gpt-4o-mini 更合适。

---

## 6. API Key 依赖

OpenAI API **需要**有效的 API Key。获取方式：

1. 访问 https://platform.openai.com/api-keys 创建 API Key
2. 设置环境变量 `OPENAI_API_KEY`
3. 或通过配置文件传入

注意：API Key 是敏感信息，必须保密存储。在 agent_platform 中，API Key 通过 `src/config.py` 加载配置，`src/llm/client.py` 中的 LLMClient 使用配置中的 API Key 初始化 OpenAI 客户端。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **Prompt Engineering** | Chat Completions API 是 Prompt Engineering 的运行载体 |
| **结构化输出** | 通过 response_format 参数实现结构化输出 |
| **Function Calling** | tools 参数实现，由 Chat Completions API 原生支持 |
| **Embedding** | 使用独立的 Embeddings API |
| **向量数据库** | Embedding API 的输出写入向量数据库检索 |

agent_platform 的 `src/llm/client.py` 封装了 OpenAI 兼容 API，所有上层模块（Agent、RAG、结构化提取）都通过 LLMClient 调用。

---

## 8. 验收清单

- [ ] 理解 Chat Completions API 的消息结构
- [ ] 掌握流式输出的实现方式
- [ ] 理解 Token 计数和消耗的计算方法
- [ ] 能够实现正确的错误处理和重试逻辑
- [ ] 了解不同模型的适用场景和定价
- [ ] 理解 Chat API 和 Responses API 的区别
- [ ] 掌握 Batch API 的使用方法
- [ ] 理解 Rate Limit 管理策略
- [ ] 能够在异步环境中使用 AsyncOpenAI
- [ ] 了解 Prompt Caching 的使用场景

---

## 9. 推荐学习资源

### 官方文档
- OpenAI API Reference: https://platform.openai.com/docs/api-reference
- Model Overview: https://platform.openai.com/docs/models
- Pricing: https://openai.com/pricing

### 开发库
- OpenAI Python SDK: https://github.com/openai/openai-python
- tiktoken: https://github.com/openai/tiktoken
- OpenAI Cookbook: https://github.com/openai/openai-cookbook

### 项目代码参考
- `agent_platform/src/llm/client.py` — LLMClient 封装，包含 chat、chat_stream、chat_with_tools
- `agent_platform/src/llm/structured.py` — 结构化输出，使用 Instructor + OpenAI
- `agent_platform/src/config.py` — 配置管理，包含 API Key、模型、基础 URL
