# 10 LangChain：LLM 应用开发框架

## 一、概念概述

### 1.1 什么是 LangChain

LangChain 是一个用于构建 LLM 驱动应用的开发框架，于 2022 年 10 月由 Harrison Chase 创建。它提供了一套标准化的抽象层（Abstractions），简化了与 LLM 的交互、提示词管理、输出解析、工具集成等常见任务。

LangChain 设计的核心理念是"可组合性"（Composability）——将复杂的 AI 应用拆解为可复用的组件，通过链式组合或图式编排来实现复杂逻辑。

### 1.2 LangChain 的演进

LangChain 经历了多个重要版本的演进：

- **v0.1（早期）**：以 Chain 为中心，提供了 LLMChain、SimpleSequentialChain 等
- **v0.2（LCEL 时代）**：引入 LangChain Expression Language (LCEL)，使用 `|` 管道符组合组件
- **v0.3（当前）**：全面拥抱 LCEL，淘汰了部分旧 Chain API，引入了 Runnable 协议

重要趋势：LangChain 官方正在将 Agent 能力迁移到 **LangGraph**，LangChain 自身回归"组件库"的定位。

### 1.3 核心抽象层次

```text
LangChain 抽象层级（从高到低）：

Agent（代理）
    +-- 使用 Tool 和 LLM 自主决策
Chain / Runnable（链/可运行对象）
    +-- 组合 Prompt + LLM + OutputParser
Tool（工具）
    +-- 封装外部功能（搜索、计算、API）
LLM / ChatModel（语言模型）
    +-- 统一各类 LLM 的调用接口
Prompt Template（提示词模板）
    +-- 管理提示词的模板化和版本化
Output Parser（输出解析器）
    +-- 将 LLM 文本输出转为结构化数据
```

---

## 二、核心原理

### 2.1 Runnable 协议

Runnable 是 LangChain v0.2+ 中最核心的抽象。任何实现了 Runnable 接口的组件都可以通过 `|` 运算符组合。

```python
from langchain_core.runnables import Runnable
from typing import Any, AsyncIterator, Iterator

# Runnable 需要实现的核心方法
class MyRunnable(Runnable):
    def invoke(self, input: Any) -> Any:
        """同步调用"""
        pass

    async def ainvoke(self, input: Any) -> Any:
        """异步调用"""
        pass

    def stream(self, input: Any) -> Iterator[Any]:
        """流式调用"""
        pass

    async def astream(self, input: Any) -> AsyncIterator[Any]:
        """异步流式调用"""
        pass

    def batch(self, inputs: List[Any]) -> List[Any]:
        """批量调用"""
        pass
```

### 2.2 LCEL（LangChain Expression Language）

LCEL 使用 `|` 管道符将多个 Runnable 组合成一个计算管线。这种设计借鉴了 Unix 管道的哲学：每个组件只做一件事，通过组合实现复杂功能。

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# LCEL 链：Prompt | LLM | OutputParser
prompt = ChatPromptTemplate.from_template(
    "用{language}写一段{code_type}代码，实现以下功能: {description}"
)
model = ChatOpenAI(model="gpt-4")
output_parser = StrOutputParser()

chain = prompt | model | output_parser

# 调用链
result = chain.invoke({
    "language": "Python",
    "code_type": "函数",
    "description": "计算斐波那契数列",
})
print(result)
```

LCEL 自动提供了以下能力：
- **并行执行**：RunnableParallel 可以同时运行多个子链
- **流式支持**：只要最后一个组件支持流式，整个链就支持流式
- **回退机制**：Runnable.with_fallbacks() 实现优雅降级
- **配置绑定**：Runnable.bind() 绑定运行时参数
- **重试机制**：Runnable.with_retry() 自动重试失败调用

### 2.3 Prompt 模板

Prompt 模板是管理提示词的核心工具，支持变量注入、消息角色管理。

```python
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

# 基础模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}专家。请用{style}的风格回答问题。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# 使用 Few-Shot 示例
few_shot_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个翻译助手。"),
    ("human", "Hello"),
    ("ai", "你好"),
    ("human", "Goodbye"),
    ("ai", "再见"),
    ("human", "{text}"),
])

# 模板组合
base_prompt = ChatPromptTemplate.from_template("关于{topic}，请回答：")
suffix_prompt = ChatPromptTemplate.from_template("请用{style}风格回答")
combined = base_prompt + suffix_prompt  # 自动拼接
```

### 2.4 Output Parser

Output Parser 将 LLM 的非结构化文本输出解析为结构化数据。

```python
from langchain_core.output_parsers import (
    StrOutputParser,             # 纯文本
    CommaSeparatedListOutputParser,  # 逗号分隔列表
    JsonOutputParser,            # JSON
    PydanticOutputParser,        # Pydantic 模型
)
from pydantic import BaseModel, Field

# Pydantic 输出解析
class SearchResult(BaseModel):
    title: str = Field(description="结果标题")
    url: str = Field(description="结果链接")
    summary: str = Field(description="结果摘要")

parser = PydanticOutputParser(pydantic_object=SearchResult)

# 自动在 prompt 中添加格式说明
prompt = ChatPromptTemplate.from_messages([
    ("system", "根据用户问题返回搜索结果。\n{format_instructions}"),
    ("human", "{question}"),
]).partial(format_instructions=parser.get_format_instructions())

chain = prompt | model | parser
result: SearchResult = chain.invoke({"question": "什么是 RAG?"})
```

### 2.5 Tool 集成

Tool 是 Agent 与外部世界交互的接口。LangChain 支持多种方式定义工具。

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor

# 1. 使用装饰器定义工具
@tool
def calculate(expression: str) -> str:
    """计算数学表达式。"""
    import ast
    try:
        tree = ast.parse(expression, mode="eval")
        result = eval(compile(tree, "", "eval"),
                      {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_current_time() -> str:
    """获取当前时间。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 2. 使用 BaseTool 定义
from langchain_core.tools import BaseTool

class FileSearchTool(BaseTool):
    name: str = "search_files"
    description: str = "搜索指定目录中的文件"

    def _run(self, pattern: str, path: str = ".") -> str:
        from pathlib import Path
        matches = list(Path(path).rglob(pattern))
        if not matches:
            return "未找到匹配的文件。"
        return "\n".join(str(m) for m in matches[:20])

# 3. 绑定工具到模型
tools = [calculate, get_current_time, FileSearchTool()]
llm_with_tools = model.bind_tools(tools)

# 4. 构建 Agent
agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
)
```

### 2.6 Chain vs Agent vs Runnable

| 概念 | 说明 | 适用场景 |
|------|------|---------|
| **Chain** | 预定义的执行序列（LCEL 链） | 流程固定的任务，如 RAG |
| **Agent** | 自主决策的循环：思考-行动-观察 | 需要工具调用的复杂任务 |
| **Runnable** | 可组合的计算单元（基类） | 所有组件的基础抽象 |

三者关系：
- Runnable 是所有组件的基础接口
- Chain 是 Runnable 的组合产物（LCEL 管道）
- Agent 是一种特殊的 Runnable，它内部包含决策循环

### 2.7 Streaming 与 Callbacks

```python
from langchain_core.callbacks import BaseCallbackHandler

class LoggingCallbackHandler(BaseCallbackHandler):
    """自定义回调处理器，用于追踪 LLM 调用。"""

    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"[LLM 开始] Prompt: {prompts[0][:50]}...")

    def on_llm_end(self, response, **kwargs):
        print(f"[LLM 完成] Token: {response.llm_output or 'N/A'}")

    def on_llm_error(self, error, **kwargs):
        print(f"[LLM 错误] {error}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"[工具调用] {serialized['name']}: {input_str}")

    def on_tool_end(self, output, **kwargs):
        print(f"[工具完成] {output[:100]}")

    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"[链开始] {serialized.get('name', 'unnamed')}")

# 使用回调
chain = prompt | model | output_parser
result = chain.invoke(
    {"topic": "RAG"},
    config={"callbacks": [LoggingCallbackHandler()]}
)

# 流式输出
for chunk in chain.stream({"topic": "LangChain"}):
    print(chunk, end="", flush=True)
```

---

## 三、实战指南

### 3.1 构建一个 RAG Chain

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

# 1. 初始化向量存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 2. 定义 Prompt
template = """你是问答助手。使用以下资料回答问题:

{context}

问题: {question}

回答（请引用来源编号）:"""
prompt = ChatPromptTemplate.from_template(template)

# 3. 构建 RAG Chain（LCEL 方式）
def format_docs(docs):
    return "\n\n".join(
        f"[来源{i+1}]: {doc.page_content}"
        for i, doc in enumerate(docs)
    )

rag_chain = (
    RunnableParallel(
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
    )
    | prompt
    | ChatOpenAI(model="gpt-4")
    | StrOutputParser()
)

# 4. 使用
result = rag_chain.invoke("什么是 RAG 技术?")
print(result)
```

### 3.2 Runnable 的高级组合模式

```python
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableMap,
)

# 条件分支
branch = RunnableBranch(
    (lambda x: len(x) > 100, RunnableLambda(lambda x: f"长文本: {x[:50]}...")),
    (lambda x: len(x) > 50, RunnableLambda(lambda x: f"中等文本: {x}")),
    RunnableLambda(lambda x: f"短文本: {x}"),
)

# 并行执行
chain = RunnableMap({
    "summary": summarize_chain,
    "keywords": extract_keywords_chain,
    "sentiment": analyze_sentiment_chain,
})

result = chain.invoke(text)
# result = {"summary": "...", "keywords": [...], "sentiment": "positive"}

# 动态路由
def route_by_topic(inputs):
    topic = inputs["topic"]
    if "技术" in topic:
        return tech_chain
    elif "科学" in topic:
        return science_chain
    else:
        return general_chain

router = RunnableLambda(route_by_topic)
full_chain = {"topic": RunnablePassthrough(), "input": ...} | router
```

### 3.3 Conversation Memory 集成

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=True,
)

conversation = ConversationChain(
    llm=ChatOpenAI(model="gpt-4"),
    memory=memory,
)

conversation.predict(input="你好，我是小明")
conversation.predict(input="我叫什么名字?")  # 还记得上下文
```

---

## 四、最佳实践

### 4.1 LCEL 优先

- 尽量使用 LCEL（`|` 管道符）而非旧的 Chain API
- LCEL 链自动支持 streaming、async、batch
- 旧 Chain API（如 LLMChain）将逐步被淘汰

### 4.2 使用 RunnableConfig

```python
from langchain_core.runnables import RunnableConfig

config = RunnableConfig(
    max_concurrency=5,
    recursion_limit=10,
    tags=["production", "rag"],
    metadata={"user_id": "123"},
)

chain.invoke(input, config=config)
```

### 4.3 错误处理

```python
# 添加回退模型
main_chain = prompt | ChatOpenAI(model="gpt-4") | parser
fallback_chain = prompt | ChatOpenAI(model="gpt-3.5-turbo") | parser

safe_chain = main_chain.with_fallbacks([fallback_chain])

# 重试机制
retry_chain = safe_chain.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)
```

### 4.4 性能优化

- **批处理**：使用 `chain.batch(inputs)` 替代循环调用
- **流式输出**：对长输出使用 `chain.stream()` 改善用户体验
- **缓存**：使用 `Runnable.cached()` 缓存耗时的 LLM 调用

---

## 五、常见陷阱

### 5.1 过度依赖旧版 Chain

**陷阱**：继续使用 LLMChain、SimpleSequentialChain 等已废弃的 API。

**解决**：迁移到 LCEL + Runnable 模式。旧 Chain API 在 v0.3 中已标记为 deprecated。

### 5.2 Tool Calling 配置错误

**陷阱**：Tool 的 args_schema 定义不正确，导致 LLM 生成的参数不匹配。

**解决**：使用 Pydantic 严格定义 Tool 的输入参数模型，并添加详细描述。

### 5.3 Agent 无限循环

```python
# 设置合理的终止条件
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=5,
    early_stopping_method="generate",
    handle_parsing_errors=True,
)
```

### 5.4 遗忘调用 Callbacks

Callback 是调试和监控的入口，不要忘记注册关键的回调处理器，尤其是生产环境需要追踪 LLM 调用和 Token 消耗。

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| ChatOpenAI / ChatAnthropic | 是 | 需要对应 LLM 提供商的 Key |
| OpenAIEmbeddings | 是 | 需要 OpenAI API Key |
| 本地 Embedding（HuggingFace） | 否 | 使用本地模型 |
| Chroma 向量库 | 否 | 本地运行 |
| Tool（自定义函数） | 否 | 纯代码实现 |
| OutputParser | 否 | 纯代码实现 |

---

## 七、技术关系

```text
LangChain 与周边生态的关系:

LangGraph ----> Agent 工作流编排（图结构）
    |
    +-- 替代了旧的 AgentExecutor
    +-- 使用 LangChain 的组件作为节点

LangChain ----> 核心抽象库
    |
    +-- PromptTemplate / ChatPromptTemplate
    +-- ChatModel / LLM （模型接口）
    +-- Tool / Toolkits （工具集成）
    +-- OutputParser （输出解析）
    +-- Callbacks （回调系统）
    +-- LCEL | 管道 （组合运行时）
            |
            v
LangSmith / LangFuse ----> 可观测性（Trace + 评估）
```

LangGraph 正在逐步替代 LangChain 原有的 AgentExecutor，成为 LangChain 生态中 Agent 编排的标准方案。LangChain 本身则回归"组件库"的定位，专注于提供 Prompt、Tool、OutputParser 等基础抽象。

---

## 八、验收清单

- [ ] 理解 Runnable 协议以及 invoke/stream/batch/ainvoke 方法
- [ ] 掌握 LCEL 的 `|` 管道符组合方式
- [ ] 会用 ChatPromptTemplate 定义多消息提示词
- [ ] 能用 PydanticOutputParser 解析结构化输出
- [ ] 会用 `@tool` 装饰器定义工具
- [ ] 理解 Chain、Agent、Runnable 三者的区别和关系
- [ ] 能使用 Callback 追踪 LLM 调用
- [ ] 理解 LangGraph 为何正在取代 AgentExecutor
- [ ] 掌握 RunnableParallel、RunnableBranch 等高级组合模式
- [ ] 会配置 AgentExecutor 的迭代次数和错误处理

---

## 九、学习资源

- **LangChain 官方文档**: https://python.langchain.com/docs/
- **LCEL 教程**: https://python.langchain.com/docs/expression_language/
- **LangChain v0.3 迁移指南**: https://python.langchain.com/docs/versions/v0_3/
- **LangGraph 文档**: https://langchain-ai.github.io/langgraph/
- **Awesome LangChain**: https://github.com/kyrolabs/awesome-langchain
- **平台参考代码**: 使用 LangChain 组件构建 Agent 工作流（参考 agent_platform 中的 graph.py 和 tools.py）
