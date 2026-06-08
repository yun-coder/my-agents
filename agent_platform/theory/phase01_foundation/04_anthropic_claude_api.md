# 04 Anthropic Claude API 深入解析

> Anthropic Claude API 是构建 AI Agent 的另一大主流选择。Claude 在长上下文、工具调用、安全性方面表现突出，其独特的 Extended Thinking 机制为复杂推理任务提供了新的范式。

---

## 1. 概念概述

### 1.1 什么是 Anthropic Claude API

Anthropic Claude API 提供对 Claude 系列模型的编程访问。Claude 以"宪法 AI"（Constitutional AI）训练方法著称，强调安全性、诚实性和有用性。核心 API 包括：

- **Messages API**：对话接口，类似于 OpenAI 的 Chat Completions
- **Tool Use / Function Calling**：工具调用能力
- **Extended Thinking**：扩展思考模式，支持可见的推理过程
- **Message Batches**：批量 API
- **Computer Use（Beta）**：让模型操控计算机的接口

### 1.2 Claude 模型系列

| 模型 | 定位 | 特点 |
|------|------|------|
| Claude 4 Sonnet | 全场景旗舰 | 速度快、推理强、适合 Agent 系统 |
| Claude 4 Opus | 智能巅峰 | 最强推理能力、适合复杂问题 |
| Claude 3.5 Sonnet | 性价比之选 | 被广泛使用的上一代主力模型 |
| Claude 3.5 Haiku | 快速轻量 | 低延迟、低成本、适合简单任务 |

### 1.3 与 OpenAI API 的核心区别

| 维度 | OpenAI API | Anthropic Claude API |
|------|-----------|---------------------|
| 消息格式 | messages 数组 | messages 数组（content 为 content block 数组） |
| 系统提示 | 单独的 system role | 单独的 system 参数（顶层） |
| 工具调用 | tools 参数，tool_choice | tools 参数，tool_choice |
| 流式输出 | server-sent events | server-sent events（不同的事件类型） |
| 推理模式 | 无（o 系列除外） | Extended Thinking（原生支持） |
| 上下文窗口 | 128K (GPT-4o) | 200K (Claude 4) |
| 输出 Token | 最高 16K | 最高 64K+（含思考 Token） |
| 多模态 | text + image | text + image + PDF |

---

## 2. 核心原理

### 2.1 Messages API 基础

```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="你是一个专业的 AI 助手。始终用中文回答。",
    messages=[
        {"role": "user", "content": "什么是向量数据库？"},
    ],
)

print(response.content[0].text)
```

**Messages API 的关键参数**：

- `model`：模型标识符，如 "claude-sonnet-4-20250514"
- `max_tokens`：输出最大 token 数（包括思考 token）
- `system`：系统提示，与 messages 分离的顶级参数，这比 OpenAI 的 system message 更安全
- `messages`：对话历史，每个元素包含 role 和 content
- `temperature`：生成多样性（0.0-1.0）
- `top_p`：核采样参数
- `stop_sequences`：停止序列

### 2.2 Content Block 架构

Claude API 的一个独特设计是 content block 架构。每个消息的 `content` 字段是一个数组，支持多种块类型：

```python
# Content Block 类型示例
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "分析这张图片中的表格："},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_image,
                    },
                },
            ],
        },
    ],
)

# 响应中的 content blocks
for block in response.content:
    if block.type == "text":
        print(f"文本：{block.text}")
    elif block.type == "tool_use":
        print(f"工具调用：{block.name}")
        print(f"参数：{block.input}")
```

支持的 Content Block 类型：

- `text`：纯文本
- `image`：图片（base64 或 URL）
- `tool_use`：模型发起的工具调用
- `tool_result`：工具执行结果
- `document`：文档（PDF 等，Claude 4 支持原生 PDF 解析）

### 2.3 System Prompt 设计（Claude 特有考虑）

Claude 的 system prompt 在 API 中是独立的顶层参数，而非 messages 数组中的一条。这为安全性带来了优势：

```python
# Claude 的 system prompt 设计
system_prompt = """
# 角色
你是一个专业的代码审查助手。

# 行为准则
1. 每次只审查一个代码段
2. 先总结代码功能，再指出问题
3. 提供可执行的改进建议
4. 使用中文输出

# 输出格式
{
  "summary": "代码功能总结",
  "issues": [
    {"severity": "high", "description": "问题描述", "suggestion": "修改建议"}
  ],
  "score": 85
}
"""
```

**Claude 系统提示的最佳实践**：

- Claude 对结构化格式的系统提示响应更好（使用 Markdown 标题组织）
- 将角色定义放在开头，规则放在后面
- Claude 对 "请一步一步思考"（CoT）有天生的倾向
- Claude 支持在 system prompt 中使用 XML 标签，效果很好
- 使用 `\\n` 分隔不同的指令区块

### 2.4 Extended Thinking（扩展思考）

Extended Thinking 是 Claude 最独特的功能之一。它允许模型在回答之前进行深度推理，并且推理过程对用户可见。这对于数学、编程、逻辑推理等复杂任务特别有用。

```python
# 启用扩展思考
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8192,  # 必须足够大以容纳思考 + 最终输出
    thinking={
        "type": "enabled",
        "budget_tokens": 4096,  # 分配给思考的 token 预算
    },
    messages=[
        {"role": "user", "content": "证明：对于任意正整数 n，n^5 - n 能被 30 整除。"},
    ],
)

# 获取思考过程和最终答案
thinking_block = None
text_block = None
for block in response.content:
    if hasattr(block, "type"):
        if block.type == "thinking":
            thinking_block = block.thinking
        elif block.type == "text":
            text_block = block.text

print("=== 思考过程 ===")
print(thinking_block)
print("\\n=== 最终答案 ===")
print(text_block)
```

**Extended Thinking 的工作原理**：

1. 模型使用 "thinking" 模式的 special tokens 进行推理
2. 分配的 budget_tokens 决定了模型可以思考多深
3. 思考过程的 token 会计入 max_tokens 但不计入输出 token 计费（或单独计费）
4. 模型在思考完成后输出可见的最终答案
5. 思考过程对用户是完全可见的，这在调试 Agent 行为时非常有用

### 2.5 Prompt Caching（提示缓存）

Claude API 支持 Prompt Caching，可以显著减少重复使用相同 system prompt 或上下文的 token 成本：

```python
# 使用 Prompt Caching
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": LONG_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        },
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "根据以下文档回答问题...",
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": user_query,
                },
            ],
        },
    ],
)

# 检查缓存命中情况
print(f"缓存命中：{response.usage.cache_read_input_tokens > 0}")
```

**Prompt Caching 的关键点**：

- 需要至少 1024 tokens 才会触发缓存
- 缓存在 5 分钟无访问后过期
- 适用于 system prompt、few-shot 示例、长篇上下文
- Cache Hit 的 token 成本只有正常输入 token 的 10%
- 在 Agent 系统中，可以将固定的 system prompt 和工具定义标记为可缓存

### 2.6 工具调用（Tool Use）

Claude 的工具调用实现与 OpenAI 类似，但有一些微妙差异：

```python
tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD"},
            },
            "required": ["city"],
        },
    },
]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
)

# Claude 的 tool_use 响应
for block in response.content:
    if block.type == "tool_use":
        print(f"调用工具：{block.name}")
        print(f"参数：{block.input}")
        print(f"工具调用 ID：{block.id}")
```

**Claude 工具调用与 OpenAI 的区别**：

- Claude 使用 `input_schema` 而非 `parameters`
- Claude 的 tool_use 是 content block 而非单独的 tool_calls 字段
- Claude 使用 `tool_choice` 参数控制工具的选择策略：auto、any、none、tool
- Claude 在 tool_use 中没有 `function` 包装器，更直接

---

## 3. 实战指南

### 3.1 完整的 Agent 循环

```python
from anthropic import Anthropic


class ClaudeAgent:
    \"\"\"基于 Claude 的简单 Agent 实现。\"\"\"

    def __init__(self, api_key: str, system_prompt: str, tools: list[dict]):
        self._client = Anthropic(api_key=api_key)
        self._system = system_prompt
        self._tools = tools
        self._messages: list[dict] = []

    def run(self, user_input: str, max_turns: int = 5) -> str:
        self._messages.append({"role": "user", "content": user_input})

        for turn in range(max_turns):
            response = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self._system,
                messages=self._messages,
                tools=self._tools,
            )

            # 处理响应
            has_tool_call = False
            for block in response.content:
                if block.type == "tool_use":
                    has_tool_call = True
                    result = self._execute_tool(block.name, block.input)
                    self._messages.append({
                        "role": "assistant",
                        "content": [block.model_dump()],
                    })
                    self._messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result),
                            }
                        ],
                    })
                elif block.type == "text":
                    final_answer = block.text

            if not has_tool_call:
                # 没有工具调用，说明 Agent 给出了最终答案
                self._messages.append({
                    "role": "assistant",
                    "content": response.content,
                })
                return final_answer if 'final_answer' in dir() else ""

        return "已达到最大交互轮次。"

    def _execute_tool(self, name: str, params: dict) -> str:
        tool_map = {
            "get_weather": lambda: f"{params['city']}：25°C，晴",
            "calculate": lambda: str(eval(params.get("expression", "0"))),
        }
        func = tool_map.get(name)
        if func:
            try:
                return func()
            except Exception as e:
                return f"工具执行错误：{e}"
        return f"未知工具：{name}"
```

### 3.2 流式输出处理

```python
def stream_claude(
    api_key: str, system: str, messages: list[dict], tools: list[dict] | None = None
):
    \"\"\"流式处理 Claude 响应。\"\"\"
    client = Anthropic(api_key=api_key)

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system,
        messages=messages,
        tools=tools,
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    yield ("text", event.delta.text)
                elif event.delta.type == "thinking_delta":
                    yield ("thinking", event.delta.thinking)
            elif event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    yield ("tool_start", event.content_block.name)

            # 获取最终消息
            final = stream.get_final_message()
            yield ("done", final)
```

### 3.3 比较：Claude API 与 OpenAI API

```python
# OpenAI 调用方式
def call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个助手。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


# Claude 调用方式（等价的）
def call_claude(prompt: str) -> str:
    from anthropic import Anthropic
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="你是一个助手。",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# 核心区别总结
"""
OpenAI:
- system 是 messages 中的一条
- content 是字符串
- tool_calls 在 message 级别
- streaming 使用 SimpleChatCompletion

Claude:
- system 是顶级参数
- content 是 block 数组
- tool_use 是 content block
- streaming 有独立的事件类型
- 支持 thinking block
"""
```

---

## 4. 最佳实践

### 4.1 System Prompt 设计

- Claude 对清晰、结构化的指令响应最佳。使用"做"而非"不做"的表述方式
- 将角色定义放在开头，如"你是一个...", 这有助于锚定模型行为
- 使用 XML 标签（`<task>`, `<rules>`, `<output>`）组织指令
- Claude 的 system prompt 长度对性能影响不大，可以放详细指令

### 4.2 Token 管理

- 始终设置 `max_tokens`，避免无限等待
- 启用 Extended Thinking 时，`max_tokens` 必须大于 `thinking.budget_tokens`
- 利用 Prompt Caching 标记固定部分（system prompt、工具定义）
- 监控 `usage` 对象中的 `input_tokens`、`output_tokens`、`cache_read_input_tokens`

### 4.3 错误处理和重试

```python
import time
from anthropic import (
    Anthropic,
    RateLimitError,
    APIError,
    APITimeoutError,
)


def claude_with_retry(client, **kwargs):
    \"\"\"带重试的 Claude API 调用。\"\"\"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except RateLimitError as e:
            wait = min(2 ** attempt * 10, 60)
            print(f"速率限制，{wait} 秒后重试...")
            time.sleep(wait)
        except APITimeoutError:
            print(f"超时，重试中...")
        except APIError as e:
            if e.status_code >= 500:
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("超过最大重试次数")
```

---

## 5. 常见陷阱与反模式

### 5.1 忽略 Content Block 结构

反模式：假设 content 总是字符串。在 Claude 中，当有 tool_use 时，content 是 block 数组。需要检查 content 的类型。

### 5.2 忘记设置 max_tokens

反模式：不设置或设置过小的 max_tokens。Claude 在复杂推理时可能需要大量输出 token。特别是在使用 Extended Thinking 时，max_tokens 需要足够大。

### 5.3 跨 API 提供商直接迁移 Prompt

反模式：不做任何修改直接将 OpenAI 的 Prompt 用在 Claude 上。两个模型对 System Prompt 的解析方式不同，需要针对 Claude 的"个性"进行调整。

### 5.4 忽略 Extended Thinking 的 Token 消耗

反模式：启用 Extended Thinking 但未调整 max_tokens。thinking budget 和 max_tokens 需要协调——max_tokens 必须大于 budget_tokens。

---

## 6. API Key 依赖

Anthropic Claude API **需要**独立的 API Key，与 OpenAI 不互通。获取方式：

1. 访问 https://console.anthropic.com/ 注册账号
2. 在 API Keys 页面创建 Key
3. 设置环境变量 `ANTHROPIC_API_KEY`
4. 或使用配置文件传入

在 agent_platform 中，如果需要接入 Claude 需要在配置中添加 Anthropic 的 base_url 和 API Key，或创建一个独立的 AnthropicClient 类。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **Prompt Engineering** | Claude 的 System Prompt 设计有其独特的最优实践 |
| **结构化输出** | Claude 支持通过 Tool Use 实现结构化输出 |
| **Function Calling** | Claude 的 Tool Use 是 Function Calling 的实现 |
| **OpenAI API** | 两种 API 在概念上对应，但在实现细节上有差异 |
| **Agent 系统** | Claude 的长上下文和 Extended Thinking 特别适合复杂 Agent 任务 |

---

## 8. 验收清单

- [ ] 理解 Messages API 的基本用法和参数
- [ ] 掌握 Content Block 架构的概念
- [ ] 了解 System Prompt 在 Claude 中的设计方式
- [ ] 理解 Extended Thinking 的启用和使用场景
- [ ] 掌握 Tool Use 的完整流程
- [ ] 理解 Prompt Caching 的工作原理
- [ ] 能够实现流式输出
- [ ] 了解与 OpenAI API 的核心区别
- [ ] 掌握 Claude 的错误处理和重试策略
- [ ] 能够在实际项目中合理选择 Claude 模型

---

## 9. 推荐学习资源

### 官方文档
- Anthropic API Reference: https://docs.anthropic.com/en/api/getting-started
- Prompt Engineering with Claude: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
- Tool Use: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- Extended Thinking: https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

### SDK
- Anthropic Python SDK: https://github.com/anthropics/anthropic-sdk-python
- Anthropic Cookbook: https://github.com/anthropics/anthropic-cookbook

### 论文
- "Constitutional AI: Harmlessness from AI Feedback" (Bai et al., 2022)
- "Claude 3 Model Card"

### 对比参考
- OpenAI Chat Completions vs Anthropic Messages API
- 注意：agent_platform 当前基于 OpenAI 兼容 API 构建，接入 Claude 需要适配
