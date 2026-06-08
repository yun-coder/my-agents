# 11 LlamaIndex：数据索引框架

## 一、概念概述

### 1.1 什么是 LlamaIndex

LlamaIndex（原名 GPT Index）是一个专门为 LLM 应用提供数据索引和检索能力的数据框架（Data Framework）。它的核心定位是"连接 LLM 与外部数据"——解决如何将私有数据高效地加载、索引、检索并接入 LLM 的问题。

与 LangChain 的"通用 LLM 应用开发框架"定位不同，LlamaIndex 更专注于**数据索引与检索**领域，提供了更丰富的索引类型、查询引擎和检索策略。

### 1.2 LlamaIndex 的核心优势

- **丰富的索引类型**：VectorStoreIndex、SummaryIndex、TreeIndex、KeywordTableIndex 等
- **灵活的查询引擎**：支持路由查询、子问题查询、多步推理查询
- **完善的 Ingestion Pipeline**：从数据加载到索引构建的完整管线
- **原生 Agent 支持**：内置 Agent 能力，可自主选择查询策略
- **与 LangChain 互补**：可以嵌入到 LangChain 的工作流中使用

### 1.3 LlamaIndex 与 LangChain 的对比

| 维度 | LlamaIndex | LangChain |
|------|-----------|-----------|
| 核心定位 | 数据索引与检索 | 通用 LLM 应用框架 |
| 索引类型 | 丰富（向量、树、摘要、关键词） | 有限（主要是向量） |
| 查询引擎 | 内置 RouterQueryEngine、SubQuestionQueryEngine | 需自行构建 RAG Chain |
| 数据接入 | 丰富的数据连接器（Loader） | 通过 Document Loader |
| Agent 能力 | 内置（QueryEngine Agent、Tool Agent） | 通过 AgentExecutor / LangGraph |
| 学习曲线 | 中等（概念较多） | 平缓（抽象较直观） |
| 最佳场景 | 数据密集型 RAG 应用 | 通用 LLM 应用编排 |

---

## 二、核心原理

### 2.1 Ingestion Pipeline（数据摄取管线）

LlamaIndex 的 Ingestion Pipeline 将原始数据转换为可索引的 Node 对象。

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import (
    TitleExtractor,
    SummaryExtractor,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

# 1. 读取文档
documents = SimpleDirectoryReader("./data").load_data()

# 2. 构建摄取管线
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=64),
        TitleExtractor(),
        SummaryExtractor(summaries=["prev", "self"]),
        HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5"),
    ],
    vector_store=ChromaVectorStore(
        chroma_collection=chroma_collection
    ),
)

# 3. 执行管线
nodes = pipeline.run(documents=documents)
print(f"生成了 {len(nodes)} 个节点")
```

Ingestion Pipeline 的 Transformations 步骤：
1. Node Parser：将 Document 切分为 Node（文本片段）
2. Metadata Extractor：提取标题、摘要等元数据
3. Embedding：生成向量嵌入
4. Storage：存入向量存储

### 2.2 Node Parser（节点解析器）

Node 是 LlamaIndex 中的基本数据单元，比 LangChain 的 Document 更丰富。

```python
from llama_index.core.node_parser import (
    SentenceSplitter,              # 按句子边界切分
    TokenTextSplitter,             # 按 Token 数切分
    SemanticSplitterNodeParser,    # 语义分块
    HierarchicalNodeParser,        # 层级分块
)

# 语义分块（基于嵌入相似度检测语义边界）
semantic_parser = SemanticSplitterNodeParser(
    embed_model=OpenAIEmbedding(),
    buffer_size=1,
    breakpoint_percentile_threshold=95,
)

# 层级分块（适合长文档）
hierarchical_parser = HierarchicalNodeParser(
    chunk_sizes=[2048, 512, 128],  # 三级层级
    chunk_overlap=64,
)

# 自定义 Node
from llama_index.core.schema import TextNode

node1 = TextNode(
    text="RAG 是一种检索增强生成技术...",
    metadata={"source": "rag_intro.md", "page": 1},
)
node2 = TextNode(
    text="LangGraph 是图结构的 Agent 编排框架...",
    metadata={"source": "langgraph_intro.md", "page": 2},
)
```

### 2.3 索引类型

LlamaIndex 提供了多种索引类型，适用于不同的场景。

#### VectorStoreIndex（向量索引）

最常用的索引类型，适合语义相似度搜索。

```python
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")

# 从文档构建
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=embed_model,
)

# 从已有向量存储构建
index = VectorStoreIndex.from_vector_store(
    vector_store=ChromaVectorStore(chroma_collection=collection),
    embed_model=embed_model,
)

# 查询
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query("什么是 RAG 技术?")
```

#### SummaryIndex（摘要索引）

将文档按顺序存储，适合需要对整个文档进行摘要的任务。

```python
from llama_index.core import SummaryIndex

summary_index = SummaryIndex.from_documents(documents)

query_engine = summary_index.as_query_engine(
    response_mode="tree_summarize",
)
response = query_engine.query("这篇文档的主要内容是什么?")
```

#### TreeIndex（树索引）

构建层级树结构，适合需要多步推理的复杂查询。

```python
from llama_index.core import TreeIndex

tree_index = TreeIndex.from_documents(documents)

query_engine = tree_index.as_query_engine(
    child_branch_factor=2,
)
response = query_engine.query("比较 RAG 和微调的区别")
```

#### KeywordTableIndex（关键词索引）

基于关键词的索引，适合精确匹配场景。

```python
from llama_index.core import KeywordTableIndex

keyword_index = KeywordTableIndex.from_documents(documents)

query_engine = keyword_index.as_query_engine()
response = query_engine.query("什么是 RAG")
```

### 2.4 查询引擎（Query Engine）

查询引擎是 LlamaIndex 的查询入口，封装了检索和合成的逻辑。

```python
from llama_index.core.query_engine import (
    RetrieverQueryEngine,         # 基础检索查询
    RouterQueryEngine,            # 智能路由
    SubQuestionQueryEngine,       # 子问题分解
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import (
    TreeSummarize,
    CompactAndRefine,
)

# 1. 基础检索查询
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=5,
)
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=TreeSummarize(),
)

# 2. 路由器查询（自动选择子引擎）
from llama_index.core.tools import QueryEngineTool, ToolMetadata

list_tool = QueryEngineTool(
    query_engine=list_query_engine,
    metadata=ToolMetadata(
        name="summary",
        description="适合摘要和概括性问题",
    ),
)
vector_tool = QueryEngineTool(
    query_engine=vector_query_engine,
    metadata=ToolMetadata(
        name="vector_search",
        description="适合具体知识点检索",
    ),
)

router_engine = RouterQueryEngine.from_defaults(
    query_engine_tools=[list_tool, vector_tool],
    verbose=True,
)
response = router_engine.query("本文档的核心观点是什么?")

# 3. 子问题分解查询
sub_query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[vector_tool, list_tool],
    verbose=True,
)
response = sub_query_engine.query("RAG 和微调各自的优缺点是什么?")
```

### 2.5 检索器（Retriever）

LlamaIndex 提供了丰富的检索策略。

```python
from llama_index.core.retrievers import (
    VectorIndexRetriever,         # 向量检索
    SummaryIndexRetriever,        # 顺序检索
    KeywordTableSimpleRetriever,  # 关键词检索
    RouterRetriever,              # 路由检索
    AutoMergingRetriever,         # 自动合并检索
)

# 自定义混合检索器
class HybridRetriever(BaseRetriever):
    """自定义混合检索器：向量 + BM25。"""

    def __init__(self, vector_retriever, keyword_retriever):
        self._vector = vector_retriever
        self._keyword = keyword_retriever

    def _retrieve(self, query):
        vec_nodes = self._vector._retrieve(query)
        kw_nodes = self._keyword._retrieve(query)

        # RRF 融合排序
        scores = {}
        for i, n in enumerate(vec_nodes):
            scores[n.node_id] = scores.get(n.node_id, 0) + 1.0 / (i + 1)
        for i, n in enumerate(kw_nodes):
            scores[n.node_id] = scores.get(n.node_id, 0) + 1.0 / (i + 1)

        all_ids = list(set(scores.keys()))
        all_ids.sort(key=lambda nid: scores.get(nid, 0), reverse=True)
        return [n for n in vec_nodes + kw_nodes
                if n.node_id in all_ids[:top_k]]
```

### 2.6 Agent 系统

LlamaIndex 内置的 Agent 能力，可以让 LLM 自主选择查询策略。

```python
from llama_index.core.agent import (
    ReActAgent,                # ReAct 模式 Agent
    OpenAIAgent,               # OpenAI Function Calling Agent
)
from llama_index.core.tools import QueryEngineTool, ToolMetadata

# 定义查询工具
tools = [
    QueryEngineTool(
        query_engine=vector_engine,
        metadata=ToolMetadata(
            name="knowledge_search",
            description="搜索知识库中的技术文档",
        ),
    ),
    QueryEngineTool(
        query_engine=summary_engine,
        metadata=ToolMetadata(
            name="document_summary",
            description="获取文档的整体摘要",
        ),
    ),
    QueryEngineTool(
        query_engine=code_engine,
        metadata=ToolMetadata(
            name="code_search",
            description="搜索代码库中的实现",
        ),
    ),
]

# 创建 Agent
agent = ReActAgent.from_tools(
    tools,
    verbose=True,
    max_iterations=10,
)

# Agent 自动决定先搜索知识库，再查看代码实现
response = agent.chat("RAG 中的重排序是如何实现的? 代码中怎么写的?")
```

---

## 三、实战指南

### 3.1 完整 RAG 应用构建

```python
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI

# 1. 全局设置
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-zh-v1.5"
)
Settings.llm = OpenAI(model="gpt-4")
Settings.chunk_size = 512
Settings.chunk_overlap = 64

# 2. 加载文档
reader = SimpleDirectoryReader("./data")
documents = reader.load_data()

# 3. 构建索引
index = VectorStoreIndex.from_documents(
    documents,
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=64),
    ],
)

# 4. 配置查询引擎
query_engine = index.as_query_engine(
    similarity_top_k=5,
    response_mode="compact",
    verbose=True,
)

# 5. 执行查询
response = query_engine.query(
    "什么是 RAG 技术? 它有哪些关键组件?"
)
print(f"回答: {response}")
print(f"来源: {[n.node.metadata for n in response.source_nodes]}")
```

### 3.2 对话记忆集成

```python
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine

memory = ChatMemoryBuffer.from_defaults(token_limit=4000)

chat_engine = CondensePlusContextChatEngine.from_defaults(
    index=index,
    memory=memory,
    context_prompt=(
        "以下是已有的对话上下文: \n{chat_history}\n"
        "请基于知识库回答用户的问题。"
    ),
    verbose=True,
)

response = chat_engine.chat("RAG 是什么?")
response = chat_engine.chat("它的检索步骤是怎样的?")  # 知道上文
```

---

## 四、最佳实践

### 4.1 索引策略选择

| 场景 | 推荐索引 | 原因 |
|------|---------|------|
| 语义相似度搜索 | VectorStoreIndex | 支持模糊匹配和语义理解 |
| 文档摘要/综述 | SummaryIndex | 保留完整顺序信息 |
| 复杂推理 | TreeIndex | 层级结构支持多步推理 |
| 精确关键词匹配 | KeywordTableIndex | 检索速度快，精确度高 |
| 综合场景 | RouterQueryEngine | 自动选择最合适的子引擎 |

### 4.2 性能优化

```python
# 缓存嵌入结果
from llama_index.core import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore

storage_context = StorageContext.from_defaults(
    docstore=SimpleDocumentStore(),
)

# 批量处理
index = VectorStoreIndex.from_documents(
    documents,
    show_progress=True,
    num_workers=4,
)

# 持久化
storage_context.persist(persist_dir="./storage")

# 恢复
from llama_index.core import load_index_from_storage
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

### 4.3 与 LangChain 互操作

```python
# LangChain 中使用 LlamaIndex
from llama_index.core.langchain_helpers import LangChainLLM

llm = LangChainLLM(llm=OpenAI())
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(llm=llm)

# LlamaIndex 工具 + LangChain Agent
from langchain.agents import Tool

tools = [
    Tool(
        name="LlamaIndex RAG",
        func=lambda q: str(query_engine.query(q)),
        description="搜索知识库",
    )
]
```

---

## 五、常见陷阱

### 5.1 Settings 全局状态污染

**陷阱**：Settings 是模块级全局变量，多线程环境中容易出现竞态问题。

**解决**：在函数/请求级别显式传递配置，避免依赖全局 Settings。

### 5.2 Node 解析导致的语义丢失

**陷阱**：默认的 SentenceSplitter 可能将完整的代码块或公式截断。

**解决**：使用 SemanticSplitterNodeParser 或自定义 Splitter，对特殊内容进行保护。

### 5.3 RouterQueryEngine 配置不当

**陷阱**：路由器的 Tool 描述不准确，导致 LLM 选错子引擎。

**解决**：每个 Tool 的 description 字段要写清楚适用场景，包含正例和反例。

### 5.4 过度查询导致 Token 浪费

**陷阱**：SubQuestionQueryEngine 会生成大量子问题，消耗大量 Token。

**解决**：设置 max_sub_questions 限制子问题数量，或在简单查询时使用普通引擎。

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| SimpleDirectoryReader | 否 | 本地文件读取 |
| SentenceSplitter | 否 | 纯本地文本处理 |
| HuggingFaceEmbedding | 否 | 使用本地模型 |
| ChromaVectorStore | 否 | 本地向量数据库 |
| OpenAI LLM | 是 | 需要 OpenAI API Key |
| OpenAIEmbedding | 是 | 需要 OpenAI API Key |
| ReActAgent (OpenAI) | 是 | 需要 OpenAI API Key |

---

## 七、技术关系

```text
LlamaIndex 生态架构:

数据源层
  +-- SimpleDirectoryReader（目录读取）
  +-- PDF Reader / HTML Reader
  +-- Database Reader（SQL, MongoDB）

Ingestion Pipeline
  +-- Node Parser（文本分块）
  +-- Metadata Extractor（元数据提取）
  +-- Embedding（向量化）

索引层
  +-- VectorStoreIndex       <-- 最常用，语义搜索
  +-- SummaryIndex           <-- 全文摘要
  +-- TreeIndex              <-- 层级推理
  +-- KeywordTableIndex      <-- 关键词匹配
  +-- PropertyGraphIndex     <-- 知识图谱

查询层
  +-- RetrieverQueryEngine
  +-- RouterQueryEngine      <-- 路由到最佳引擎
  +-- SubQuestionQueryEngine <-- 复杂问题分解
  +-- Custom Query Engine

Agent 层
  +-- ReActAgent / OpenAIAgent <-- 自主决策查询

与 LangChain 集成
  +-- LangChainLLM / LangChain tools
```

---

## 八、验收清单

- [ ] 理解 Ingestion Pipeline 的概念和流程
- [ ] 掌握 Node Parser 的各种策略（SentenceSplitter、SemanticSplitter）
- [ ] 理解 VectorStoreIndex、SummaryIndex、TreeIndex 的适用场景
- [ ] 能使用 RetrieverQueryEngine 进行基本查询
- [ ] 掌握 RouterQueryEngine 的配置和路由策略
- [ ] 了解 SubQuestionQueryEngine 的多步推理机制
- [ ] 理解 LlamaIndex Agent（ReActAgent）的工作方式
- [ ] 理解 LlamaIndex 与 LangChain 的核心定位差异
- [ ] 掌握索引的持久化和恢复
- [ ] 了解 Settings 全局配置的最佳实践

---

## 九、学习资源

- **LlamaIndex 官方文档**: https://docs.llamaindex.ai/en/stable/
- **LlamaIndex 概念指南**: https://docs.llamaindex.ai/en/stable/getting_started/concepts/
- **LlamaIndex 组件模块**: https://docs.llamaindex.ai/en/stable/module_guides/
- **LlamaIndex + LangChain 集成**: https://docs.llamaindex.ai/en/stable/community/integrations/langchain/
- **对比 LangChain 与 LlamaIndex 的 RAG 实现**: 参考 agent_platform 中的 RAG 实现（retriever.py, generator.py）
