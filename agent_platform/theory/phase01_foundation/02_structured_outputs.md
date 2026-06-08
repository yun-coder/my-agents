# 02 结构化输出 Structured Outputs

> 结构化输出是指强制大语言模型生成符合预定义 Schema 的数据，将自然语言输出转化为程序可直接消费的强类型数据结构。
> 它是连接 LLM 的"模糊世界"与软件的"精确世界"的桥梁。

---

## 1. 概念概述

### 1.1 什么是结构化输出

结构化输出（Structured Outputs）是一种让 LLM 的输出严格按照预先定义的 JSON Schema 或 Pydantic 模型格式返回的技术。与传统的"在 Prompt 中要求返回 JSON"不同，结构化输出在 API 层面或库层面强制约束模型的输出格式，确保输出的数据类型正确、字段完整、结构一致。

### 1.2 为什么需要结构化输出

在 AI Agent 系统中，LLM 的输出很少是最终结果——它通常需要传递给下游函数、数据库或 API：

- **类型安全**：确保输出是合法的 JSON，字段类型正确
- **可预测性**：输出结构固定，无需编写脆弱的正则表达式解析逻辑
- **自动验证**：Pydantic 模型自动验证字段类型、范围、约束
- **失败重试**：当输出不符合 Schema 时自动重试，提升系统鲁棒性
- **IDE 支持**：强类型输出提供代码补全和静态类型检查

### 1.3 何时使用结构化输出

- **信息抽取**：从非结构化文本中提取结构化数据（姓名、日期、金额等）
- **工具调用**：Function Calling 的参数定义本身就是结构化输出
- **Agent 状态管理**：Agent 的输出需要写入结构化状态
- **分类任务**：将输出限制为预定义的枚举值
- **数据转换**：将一种格式的数据转换为另一种结构

---

## 2. 核心原理

### 2.1 JSON Mode 的工作原理

JSON Mode 是 OpenAI 在 Chat Completions API 中提供的一种模式。当设置 `response_format={"type": "json_object"}` 时，模型被强制生成合法的 JSON 字符串。

```python
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "提取信息并输出 JSON。"},
        {"role": "user", "content": "张三，25岁，北京"},
    ],
)
print(response.choices[0].message.content)
# {"name": "张三", "age": 25, "city": "北京"}
```

JSON Mode 的局限性在于它只保证输出是合法的 JSON，但不保证 JSON 的 Schema 符合预期。如果你需要一个特定结构的 JSON，JSON Mode 本身无法约束——它可能产生任意结构的 JSON。

### 2.2 Structured Outputs（API 原生）

OpenAI 在 2024 年推出了 Strict Structured Outputs 功能，通过在 API 层面使用 JSON Schema 约束输出：

```python
from pydantic import BaseModel


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]


response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": "下周五下午3点开会，叫上张三和李四。"}],
    response_format=CalendarEvent,
)
event = response.choices[0].message.parsed
print(event.name)  # 会议
print(event.participants)  # ["张三", "李四"]
```

Structured Outputs 使用了一种称为"constrained decoding"的技术——在模型生成 token 的同时进行 Schema 约束，而不是先生成再验证。这保证了输出的 JSON 100% 符合 Schema。

### 2.3 Instructor 库的运作机制

Instructor 库是目前最流行的结构化输出第三方库。它通过"拦截 + 重试"模式工作：

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel


# Step 1: 将 OpenAI 客户端包装为 Instructor 客户端
client = instructor.from_openai(OpenAI())


class UserDetail(BaseModel):
    name: str
    age: int
    email: str | None = None


# Step 2: 调用时传入 response_model
user = client.chat.completions.create(
    model="gpt-4o",
    response_model=UserDetail,
    messages=[{"role": "user", "content": "张三，25岁"}],
)
```

Instructor 的运作机制：

1. **模式注入**：在 API 调用前，Instructor 将 Pydantic 模型的 Schema 转换为 JSON Schema，注入到 system prompt 或使用 response_format 参数
2. **响应捕获**：拦截 API 返回的 JSON 字符串
3. **Pydantic 验证**：使用 Pydantic 的 `model_validate` 方法验证 JSON 是否符合模型定义
4. **重试循环**：如果验证失败（字段缺失、类型错误等），自动将错误信息反馈给模型并重试
5. **返回模型实例**：最终返回类型安全的 Pydantic 模型实例

```python
# Instructor 的重试机制（简化版）
def extract_with_retry(client, response_model, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                response_format={"type": "json_object"},
                messages=messages,
            )
            raw = response.choices[0].message.content
            # 尝试验证
            instance = response_model.model_validate_json(raw)
            return instance
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            # 将验证错误反馈给模型
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"验证失败：{e}\\n请修正后重新输出。",
            })
```

### 2.4 Pydantic 模型设计

Pydantic v2 是结构化输出的核心。模型设计的好坏直接决定了输出的质量和鲁棒性。

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class Address(BaseModel):
    city: str = Field(description="城市名称")
    district: str | None = Field(None, description="区/县")
    street: str = Field(description="街道地址")


class PersonInfo(BaseModel):
    \"\"\"个人信息提取模型。\"\"\"
    name: str = Field(description="姓名")
    age: int = Field(ge=0, le=150, description="年龄（0-150）")
    gender: Literal["男", "女", "未知"] = Field(default="未知")
    address: Address | None = Field(None, description="地址信息")
    tags: list[str] = Field(default_factory=list, description="标签列表")

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()
```

**Pydantic 模型设计原则**：

- 使用 `Field(description=...)` 提供字段语义信息——这些描述会被转换为 JSON Schema 的 description 字段，传递给 LLM
- 合理使用 Optional 和默认值，避免过于严格的约束
- 使用 `Literal` 类型约束枚举值
- 使用 `field_validator` 进行自定义验证（如格式校验、范围检查）
- 使用嵌套模型表达复杂结构

### 2.5 Retry 逻辑与 Validation

完整的结构化输出流水线包含多级错误处理：

```python
import logging
from typing import TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class StructuredExtractor:
    \"\"\"结构化提取器，带重试和验证。\"\"\"

    def __init__(self, client, max_retries: int = 3):
        self._client = client
        self._max_retries = max_retries

    def extract(
        self,
        text: str,
        model_class: type[T],
        system_prompt: str | None = None,
    ) -> T:
        messages = [
            {
                "role": "system",
                "content": system_prompt or "你是一个信息提取专家。",
            },
            {"role": "user", "content": text},
        ]

        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=messages,
                )
                raw = response.choices[0].message.content
                if not raw:
                    raise ValueError("LLM 返回空内容")
                return model_class.model_validate_json(raw)
            except ValidationError as e:
                last_error = e
                logger.warning(
                    "验证失败（第%d次）：%s", attempt + 1, e
                )
                # 将错误和原始输出反馈给模型
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": f"输出格式错误：{e}\\n请修正。",
                })
            except Exception as e:
                last_error = e
                logger.error("提取失败：%s", e)
                if attempt < self._max_retries - 1:
                    messages.append({
                        "role": "user",
                        "content": "出现错误，请重试。",
                    })

        raise RuntimeError(
            f"经过 {self._max_retries} 次重试后仍然失败：{last_error}"
        )
```

### 2.6 agent_platform 中的结构化输出实现

在 `agent_platform/src/llm/structured.py` 中，结构化输出的实现使用 Instructor 库：

```python
# src/llm/structured.py 的核心逻辑
def extract_structured(
    prompt: str,
    response_model: type[BaseModel],
    *,
    system: str = "你是一个精确的信息提取专家。",
) -> BaseModel:
    client = get_llm_client()
    instructor_client = instructor.from_openai(client._client)
    return instructor_client.chat.completions.create(
        model=client.model,
        response_model=response_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )


def extract_structured_with_retry(
    prompt: str,
    response_model: type[BaseModel],
    *,
    max_retries: int = 3,
    system: str = "你是一个精确的信息提取专家。",
) -> BaseModel:
    client = get_llm_client()
    instructor_client = instructor.from_openai(client._client)
    return instructor_client.chat.completions.create(
        model=client.model,
        response_model=response_model,
        max_retries=max_retries,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
```

---

## 3. 实战指南

### 3.1 从自然语言中提取结构化信息

```python
from pydantic import BaseModel, Field
from typing import Literal
import instructor
from openai import OpenAI


# 定义提取 Schema
class Transaction(BaseModel):
    \"\"\"银行交易记录。\"\"\"
    date: str = Field(description="交易日期，格式 YYYY-MM-DD")
    amount: float = Field(description="交易金额，正数为收入，负数为支出")
    currency: str = Field(default="CNY", description="货币类型")
    category: Literal["餐饮", "交通", "购物", "工资", "其他"] = Field(
        description="交易类别"
    )
    merchant: str = Field(description="商户名称")
    notes: str | None = Field(None, description="备注")


# 批量提取
client = instructor.from_openai(OpenAI())

texts = [
    "6月1日在星巴克消费35元买咖啡",
    "6月5日收到工资15000元",
    "6月8日滴滴打车花了28.5元",
]

transactions = []
for text in texts:
    tx = client.chat.completions.create(
        model="gpt-4o",
        response_model=Transaction,
        messages=[{"role": "user", "content": text}],
    )
    transactions.append(tx)

for tx in transactions:
    print(f"{tx.date} | {tx.merchant} | {tx.amount} | {tx.category}")
```

### 3.2 嵌套结构的场景

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date


class MedicalRecord(BaseModel):
    \"\"\"医疗记录提取。\"\"\"
    patient_name: str = Field(description="患者姓名")
    visit_date: date = Field(description="就诊日期")
    symptoms: list[str] = Field(description="症状列表")
    diagnosis: str = Field(description="诊断结果")
    prescriptions: list["Prescription"] = Field(
        default_factory=list, description="处方列表"
    )


class Prescription(BaseModel):
    \"\"\"处方信息。\"\"\"
    drug_name: str = Field(description="药品名称")
    dosage: str = Field(description="剂量，如 500mg")
    frequency: str = Field(description="用药频率，如 每日三次")
    duration_days: int = Field(description="用药天数")


# 使用
client = instructor.from_openai(OpenAI())
record = client.chat.completions.create(
    model="gpt-4o",
    response_model=MedicalRecord,
    messages=[{
        "role": "user",
        "content": (
            "患者王丽，2025年6月3日就诊。"
            "主诉头痛、发烧、咳嗽三天。"
            "诊断：上呼吸道感染。"
            "处方：阿莫西林500mg每日三次，连用7天；布洛芬200mg发烧时服用。"
        ),
    }],
)
print(record.model_dump_json(indent=2, ensure_ascii=False))
```

### 3.3 结合 Tool Calling 的结构化输出

```python
from pydantic import BaseModel, Field
import json


class WeatherQuery(BaseModel):
    \"\"\"天气查询意图提取。\"\"\"
    city: str = Field(description="城市名")
    date: str | None = Field(None, description="日期，默认当天")
    query_type: str = Field(
        description="查询类型：temperature/precipitation/wind/overall"
    )


def parse_weather_intent(user_input: str) -> WeatherQuery:
    \"\"\"提取天气查询意图，然后调用天气 API。\"\"\"
    client = instructor.from_openai(OpenAI())

    query = client.chat.completions.create(
        model="gpt-4o",
        response_model=WeatherQuery,
        messages=[{
            "role": "user",
            "content": f"从以下查询中提取意图：{user_input}",
        }],
    )
    return query


# 使用示例
result = parse_weather_intent("北京明天会下雨吗？")
print(f"城市：{result.city}")  # 北京
print(f"日期：{result.date}")  # 明天（映射为具体日期）
print(f"类型：{result.query_type}")  # precipitation
```

---

## 4. 最佳实践

### 4.1 Field 描述的重要性

Pydantic 的 `Field(description=...)` 不仅仅是文档——它会被转换为 JSON Schema 的 description 字段，直接传递给 LLM。详细的描述可以显著提升 LLM 的提取准确率。

```python
# 不好的设计
class Product(BaseModel):
    name: str
    price: float

# 好的设计
class Product(BaseModel):
    name: str = Field(description="产品全称，包括品牌和型号")
    price: float = Field(
        ge=0.01,
        le=999999.99,
        description="产品价格（元），精确到分",
    )
```

### 4.2 错误处理策略

- **第一级：API 重试**：网络错误或服务端错误（5xx），使用指数退避重试
- **第二级：验证重试**：Pydantic ValidationError，将错误反馈给 LLM 修正
- **第三级：默认值兜底**：为可选字段提供合理的默认值
- **第四级：人工审核**：无法自动修复的极端情况，标记为人工处理

### 4.3 性能优化

- 对于简单模型（3-5 个字段），优先使用 JSON Mode，性能更好
- 对于复杂模型（嵌套结构、大量枚举），使用 Instructor + Pydantic
- 批量提取时先合并为一条 Prompt 调用，再拆分结果
- 使用 `model_validate_json()` 而非 `model_validate()` 解析 JSON 字符串

---

## 5. 常见陷阱与反模式

### 5.1 Schema 过于严格

反模式：所有字段都是必填的，不允许任何容错。这会导致频繁的验证失败和重试。正确做法是对非关键字段使用 Optional，提供合理的默认值。

### 5.2 忽略 JSON Mode 的限制

反模式：认为 JSON Mode 可以保证输出结构符合预期。实际上 JSON Mode 只保证输出是合法 JSON，不保证 Schema 匹配。需要使用 Pydantic 验证作为第二道防线。

### 5.3 过度依赖重试

反模式：设置 max_retries=10，希望 LLM 在多次重试后总能输出正确的格式。正确做法是限制重试次数（3 次以内），超出后使用人工兜底。

### 5.4 未处理嵌套模型的验证错误

反模式：嵌套模型的某个字段验证失败时，错误信息不完整，导致 LLM 无法理解需要修正什么。正确做法是在 `field_validator` 中提供清晰的错误消息。

### 5.5 在 Prompt 和 Schema 中重复定义

反模式：同时使用 Prompt 描述和 Field(description) 定义相同约束。维护两份定义会导致不一致。正确做法是将约束放在 Pydantic Field 中，Prompt 只描述任务目标。

---

## 6. API Key 依赖

结构化输出**需要** LLM API 的 API Key。具体依赖情况：

- **OpenAI JSON Mode**：需要 OpenAI API Key
- **OpenAI Structured Outputs**：需要 OpenAI API Key
- **Instructor + OpenAI**：需要 OpenAI API Key
- **Instructor + Anthropic**：需要 Anthropic API Key
- **Instructor + 本地模型**：需要本地运行的开源模型（如 Llama、Qwen），无需 API Key 但需要 GPU 资源

在 `agent_platform/src/llm/structured.py` 中，结构化输出复用 LLMClient，通过 `get_llm_client()` 获取配置中的 API Key。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **Prompt Engineering** | 结构化输出的 Schema 定义影响 Prompt 设计 |
| **Function Calling** | Tool 的 JSON Schema 定义本质是结构化输出的一种形式 |
| **Agent 系统** | Agent 的状态转移和工具返回结果需要结构化输出保证一致性 |
| **RAG** | 检索结果的排序和筛选需要结构化 Schema |
| **文档解析** | 解析后的文档需要结构化输出提取关键信息 |

在 agent_platform 的架构中，`src/llm/structured.py` 位于 LLM 接入层之上，为 Agent、RAG、文档处理等上层模块提供类型安全的结构化数据提取能力。

---

## 8. 验收清单

- [ ] 理解 JSON Mode 和 Structured Outputs 的核心区别
- [ ] 掌握 Instructor 库的安装和使用
- [ ] 能够独立设计 Pydantic 模型用于信息提取
- [ ] 理解验证重试的完整流程
- [ ] 知道如何处理嵌套结构的验证错误
- [ ] 能够结合 Tool Calling 使用结构化输出
- [ ] 了解不同 LLM 提供商的结构化输出支持程度
- [ ] 理解 Field(description) 对 LLM 输出质量的影响
- [ ] 能在生产环境中部署结构化提取流水线
- [ ] 会调试 LLM 输出验证失败的场景

---

## 9. 推荐学习资源

### 官方文档
- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
- Instructor 文档: https://python.useinstructor.com/
- Pydantic v2 文档: https://docs.pydantic.dev/latest/

### 开源项目
- Instructor: https://github.com/jxnl/instructor
- Outlines（结构化生成框架）: https://github.com/outlines-dev/outlines
- JSONFormer: https://github.com/1rgs/jsonformer

### 项目代码参考
- `agent_platform/src/llm/structured.py` — Instructor 封装，支持普通和带重试的提取
- `agent_platform/src/llm/client.py` — 底层 OpenAI 客户端，被 structured.py 复用
- `agent_platform/src/agent/tools.py` — Tool 定义的 JSON Schema 也是结构化输出的应用
