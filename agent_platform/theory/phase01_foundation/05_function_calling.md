# 05 Function Calling / Tool Use 函数调用与工具使用

> Function Calling（函数调用/Tool Use）是 LLM 与外部世界交互的核心机制。它让语言模型不仅能够"说话"，还能"做事"——调用 API、查询数据库、操作文件系统。

---

## 1. 概念概述

### 1.1 什么是 Function Calling

Function Calling 是指 LLM 在生成回复时，识别出需要调用外部函数，并输出结构化的函数调用参数的能力。它并不是让 LLM 直接执行代码，而是让 LLM 决定"什么时候需要调用什么函数，参数是什么"，然后由应用程序执行实际的函数并返回结果。

### 1.2 为什么需要 Function Calling

- **突破知识边界**：模型训练数据有截止日期，无法知道实时信息（天气、股价、新闻）
- **与环境交互**：让模型能够操作数据库、文件系统、API 等外部系统
- **增强计算能力**：模型不擅长精确计算或处理大规模数据，可以委托给专门的函数
- **构建 Agent 系统**：Function Calling 是 ReAct Agent 的"行动"环节

### 1.3 何时使用 Function Calling

- **信息查询**：获取实时数据（天气、时间、地理位置）
- **数据操作**：读写数据库、文件系统
- **外部 API 调用**：调用第三方服务的 REST API
- **计算任务**：精确数学计算、数据处理
- **系统控制**：控制外部设备或系统
- **工具链编排**：将多个函数串联成工作流

---

## 2. 核心原理

### 2.1 Tool 定义：JSON Schema

每个工具/函数的定义是一个 JSON Schema 对象，描述了函数的名称、描述、参数结构。这个 Schema 被传递给 LLM，让模型理解可用工具及其用法。

```python
# 一个标准的工具定义
tool_definition = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的实时天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称（中文），如 北京、上海",
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位",
                    "default": "celsius",
                },
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}
```

**JSON Schema 字段详解**：

- `name`：函数名称，LLM 通过此名称选择函数。使用蛇形命名，清晰描述功能
- `description`：函数描述。这是 LLM 理解函数用途的关键。描述越清晰，LLM 选择越准确
- `parameters.properties`：参数定义。每个参数需包含 type 和 description
- `parameters.required`：必填参数列表
- `additionalProperties: false`：严格模式，防止 LLM 传入未定义的参数

### 2.2 Tool Call 生命周期

一个完整的工具调用生命周期包含 6 个步骤：

```
1. 系统准备：定义工具列表和 System Prompt
       ↓
2. LLM 推理：模型分析用户输入，决定调用哪个工具
       ↓
3. 工具调用请求：LLM 返回 tool_calls，包含函数名和参数
       ↓
4. 工具执行：应用程序执行实际的函数调用
       ↓
5. 工具结果返回：将函数执行结果作为 tool message 发回给 LLM
       ↓
6. LLM 综合回答：基于工具结果生成最终回答（或再次调用工具）
```

**Step-by-step 实现**：

```python
from openai import OpenAI

client = OpenAI()

# Step 1: 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "搜索航班信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "出发城市"},
                    "destination": {"type": "string", "description": "目的城市"},
                    "date": {"type": "string", "description": "出发日期 YYYY-MM-DD"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
]

# Step 2: LLM 决定调用工具
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "明天从北京到上海的航班有哪些？"}],
    tools=tools,
)

# Step 3: 解析 tool_calls
choice = response.choices[0]
if choice.message.tool_calls:
    for tc in choice.message.tool_calls:
        func_name = tc.function.name
        func_args = json.loads(tc.function.arguments)
        print(f"调用工具：{func_name}")
        print(f"参数：{func_args}")

        # Step 4: 执行实际函数
        result = search_flights(**func_args)

        # Step 5: 将结果返回给 LLM
        messages = [
            {"role": "user", "content": "明天从北京到上海的航班有哪些？"},
            choice.message,
            {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            },
        ]

        # Step 6: LLM 综合回答
        final = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )
        print(final.choices[0].message.content)
```

### 2.3 并行工具调用（Parallel Tool Calls）

OpenAI 支持在一次 LLM 调用中同时返回多个工具调用：

```python
# LLM 可能会同时返回多个 tool_calls
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "帮我搜索北京和上海的天气"}],
    tools=[weather_tool],
)

# 并行执行所有工具调用
import asyncio


async def execute_parallel(tool_calls):
    \"\"\"并行执行多个工具调用。\"\"\"
    async def execute_one(tc):
        func_name = tc.function.name
        func_args = json.loads(tc.function.arguments)
        executor = TOOL_EXECUTORS.get(func_name)
        if executor:
            result = await asyncio.to_thread(executor, **func_args)
            return {
                "tool_call_id": tc.id,
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
            }
        return None

    tasks = [execute_one(tc) for tc in tool_calls]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


# 使用并行执行
tool_calls = response.choices[0].message.tool_calls
tool_results = asyncio.run(execute_parallel(tool_calls))
```

### 2.4 Agent 中的工具编排（agent_platform 实现）

在 agent_platform 中，工具定义和工具执行是分离的：

```python
# src/agent/tools.py — 工具定义和实现
from typing import Any, Callable

# 工具定义（JSON Schema 数组）
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "在指定目录中搜索匹配模式的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "搜索目录路径"},
                    "pattern": {"type": "string", "description": "文件匹配模式，如 *.py"},
                },
                "required": ["directory", "pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "安全计算算术表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "算术表达式，如 (3+5)*2",
                    },
                },
                "required": ["expression"],
            },
        },
    },
]

# 工具执行器映射
TOOL_EXECUTORS: dict[str, Callable[..., str]] = {
    "search_files": _search_files,
    "get_current_time": _get_current_time,
    "read_file": _read_file,
    "calculate": _calculate,
}
```

在 `src/agent/graph.py` 中，工具调用通过 LangGraph 编排：

```python
# _agent_node：LLM 推理，输出 tool_calls 或 final_answer
# _tool_node：执行工具，返回 tool_result
# _router：根据状态判断下一步（继续工具调用 or 结束）

def _tool_node(self, state: AgentState) -> AgentState:
    \"\"\"执行 LLM 请求的所有工具调用。\"\"\"
    messages = state.get("messages", [])
    if not messages:
        return state

    last_message = messages[-1]
    tool_calls = last_message.get("tool_calls", [])

    tool_results = []
    for tc in tool_calls:
        func_name = tc["function"]["name"]
        func_args = json.loads(tc["function"]["arguments"])
        executor = TOOL_EXECUTORS.get(func_name)
        if executor:
            result = executor(**func_args)
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    state["messages"] = messages + tool_results
    return state
```

### 2.5 工具选择策略（tool_choice）

OpenAI 支持通过 `tool_choice` 参数控制工具的选择行为：

```python
# 1. auto：模型自主决定是否调用工具（默认）
response = client.chat.completions.create(
    tools=tools, tool_choice="auto", ...
)

# 2. required：强制模型必须调用至少一个工具
response = client.chat.completions.create(
    tools=tools, tool_choice="required", ...
)

# 3. none：禁止模型调用工具
response = client.chat.completions.create(
    tools=tools, tool_choice="none", ...
)

# 4. 指定工具：强制模型调用特定工具
response = client.chat.completions.create(
    tools=tools, tool_choice={
        "type": "function", "function": {"name": "get_weather"}
    }, ...
)
```

---

## 3. 实战指南

### 3.1 安全的工具执行器

```python
import ast
import operator
from typing import Any, Callable


class SafeCalculator:
    \"\"\"安全的数学计算器，仅允许基本算术操作。\"\"\"

    ALLOWED_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }

    def calculate(self, expression: str) -> str:
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = self._eval(tree.body)
            return str(result)
        except Exception as e:
            return f"计算错误：{e}"

    def _eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in self.ALLOWED_OPS:
            return self.ALLOWED_OPS[type(node.op)](
                self._eval(node.left), self._eval(node.right)
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.ALLOWED_OPS:
            return self.ALLOWED_OPS[type(node.op)](self._eval(node.operand))
        raise ValueError("不支持的表达式")
```

### 3.2 动态工具注册器

```python
from typing import Any, Callable, get_type_hints
import inspect
import json


class ToolRegistry:
    \"\"\"动态工具注册器，从函数签名自动生成 JSON Schema。\"\"\"

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._definitions: list[dict] = []

    def register(self, func: Callable):
        \"\"\"注册一个函数作为可用工具。\"'\"
        name = func.__name__
        doc = inspect.getdoc(func) or ""
        sig = inspect.signature(func)
        hints = get_type_hints(func)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = hints.get(param_name, str)
            json_type = self._type_to_json(param_type)

            properties[param_name] = {
                "type": json_type,
                "description": f"参数 {param_name}",
            }
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        definition = {
            "type": "function",
            "function": {
                "name": name,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

        self._tools[name] = func
        self._definitions.append(definition)
        return self

    def _type_to_json(self, tp: type) -> str:
        mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        return mapping.get(tp, "string")

    def get_definitions(self) -> list[dict]:
        return self._definitions

    def execute(self, name: str, **kwargs) -> str:
        func = self._tools.get(name)
        if not func:
            return f"未找到工具：{name}"
        try:
            result = func(**kwargs)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"执行失败：{e}"


# 使用示例
registry = ToolRegistry()


@registry.register
def get_weather(city: str) -> dict:
    \"\"\"获取指定城市的天气。\"\"\"
    # 实际项目中调用天气 API
    return {"city": city, "temperature": 25, "condition": "晴"}


@registry.register
def calculate(expression: str) -> str:
    \"\"\"安全计算表达式。\"\"\"
    return SafeCalculator().calculate(expression)


tools = registry.get_definitions()
```

### 3.3 工具调用的错误处理

```python
class ToolErrorHandler:
    \"\"\"工具调用错误的层次化处理。\"\"\"

    @staticmethod
    def handle_execution_error(
        func_name: str, error: Exception, tool_call_id: str
    ) -> dict:
        \"\"\"格式化工具执行错误为 LLM 可读的消息。\"\"\"
        error_type = type(error).__name__
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps({
                "status": "error",
                "error_type": error_type,
                "error_message": str(error),
                "suggestion": f"工具 {func_name} 执行失败。"
                f"请检查参数后重试，或使用其他方法。",
            }, ensure_ascii=False),
        }

    @staticmethod
    def handle_timeout(func_name: str, timeout: float, tool_call_id: str) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps({
                "status": "timeout",
                "error_message": f"工具 {func_name} 执行超时（{timeout}秒）",
                "suggestion": "请简化请求或稍后重试。",
            }, ensure_ascii=False),
        }

    @staticmethod
    def handle_invalid_params(
        func_name: str, params: dict, validation_error: str, tool_call_id: str
    ) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps({
                "status": "invalid_params",
                "error_message": f"参数校验失败：{validation_error}",
                "received_params": params,
                "suggestion": "请提供合法的参数值。",
            }, ensure_ascii=False),
        }
```

---

## 4. 最佳实践

### 4.1 工具描述设计

- **名称清晰**：函数名使用动词 + 名词，如 search_files、get_weather
- **描述详细**：描述中说明函数的功能、适用场景、使用限制
- **参数描述精确**：每个参数都要有清晰的中文描述，包括可能的值范围
- **使用枚举约束**：当参数有固定可选值时，使用 enum 字段

### 4.2 安全检查

- **输入验证**：在工具执行前验证参数合法性，不信任 LLM 的输出
- **权限隔离**：工具执行在沙箱环境或最小权限上下文中
- **执行限时**：为每个工具设置超时时间
- **资源限制**：限制工具的调用次数、数据量、访问范围
- **审计日志**：记录所有工具调用，包括调用时间、参数、结果

### 4.3 工具调用循环控制

- 设置最大迭代次数（通常 5-10 轮），防止无限循环
- 监控工具调用链，检测循环模式（反复调用相同工具）
- 在迭代超限后给出友好提示

---

## 5. 常见陷阱与反模式

### 5.1 将敏感逻辑放在工具参数中

反模式：在工具参数中传递 API Key、密码等敏感信息。这些信息会被记录在 LLM 的上下文中。正确做法是敏感信息通过环境变量或配置注入。

### 5.2 假设 LLM 永远选择正确的工具

反模式：不加验证地执行 LLM 建议的工具调用。LLM 可能选择错误的工具或传入错误的参数。正确做法是始终验证参数并在执行前进行检查。

### 5.3 忽略并行调用的结果

反模式：当 LLM 返回多个 tool_calls 时，只处理第一个。正确做法是处理所有 tool_calls 并将所有结果返回给 LLM。

### 5.4 工具描述不足

反模式：工具描述过于简短，导致 LLM 不理解何时使用。描述"获取天气"不如"获取指定城市在指定日期的实时天气预报信息，支持中国主要城市"准确。

### 5.5 不处理工具错误

反模式：工具执行失败时不返回结果或抛出异常。正确做法是工具无论如何都要返回结构化的结果消息，让 LLM 可以基于错误信息做出下一步决策。

---

## 6. API Key 依赖

Function Calling 本身**不需要**额外的 API Key——它是 LLM API 的内置功能。但：

- **调用 LLM API** 需要 API Key（OpenAI / Anthropic）
- **工具实现**可能需要自己的 API Key（如天气 API 需要天气服务的 Key）
- **工具执行**本身在本地运行，不需要 Key

在 agent_platform 中，TOOL_DEFINITIONS 和 TOOL_EXECUTORS 在 `src/agent/tools.py` 中定义，工具的 API Key 通过配置或环境变量管理。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **Prompt Engineering** | ReAct Prompt 定义了工具调用的推理模式 |
| **结构化输出** | 工具参数定义是结构化输出的应用 |
| **Agent 系统** | Function Calling 是 Agent 的行动机制 |
| **OpenAI API** | Function Calling 是 Chat Completions API 的原生功能 |
| **安全** | 工具调用的输入验证和权限隔离是 Agent 安全的关键 |

在 agent_platform 中，`src/agent/tools.py` 定义工具，`src/agent/graph.py` 通过 LangGraph 编排工具调用循环。两者配合实现了完整的 Agent 行动能力。

---

## 8. 验收清单

- [ ] 理解 Tool 的 JSON Schema 定义结构
- [ ] 掌握 Tool Call 的完整生命周期
- [ ] 能够实现并行工具调用
- [ ] 理解 tool_choice 参数的使用
- [ ] 掌握工具执行错误处理
- [ ] 能够设计安全的工具执行器
- [ ] 理解工具调用的安全检查措施
- [ ] 能使用 LangGraph 编排工具调用循环
- [ ] 了解不同 LLM 提供商的工具调用差异
- [ ] 能够在实际 Agent 系统中设计和实现工具

---

## 9. 推荐学习资源

### 官方文档
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Anthropic Tool Use: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- LangChain Tools: https://python.langchain.com/docs/modules/agents/tools/

### 项目代码参考
- `agent_platform/src/agent/tools.py` — 工具定义、安全执行器、JSON Schema
- `agent_platform/src/agent/graph.py` — LangGraph 工具调用编排
- `agent_platform/src/llm/client.py` — LLMClient.chat_with_tools 方法

### 论文
- "Toolformer: Language Models Can Teach Themselves to Use Tools" (Schick et al., 2023)
- "Gorilla: Large Language Model Connected with Massive APIs" (Patil et al., 2023)
