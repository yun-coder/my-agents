# 09 RAG 基础：检索增强生成

## 一、概念概述

### 1.1 什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与大型语言模型（LLM）相结合的架构模式。其核心思想是：在 LLM 生成回答之前，先从外部知识库中检索相关文档，将这些文档作为上下文提供给 LLM，从而让模型基于真实的、最新的信息进行生成。

RAG 解决了纯 LLM 的两个根本性问题：
- **知识陈旧**：LLM 的训练数据有截止日期，无法获取最新信息
- **幻觉问题**：LLM 可能编造不存在的知识，尤其是涉及具体数据或专有知识时
- **缺乏可解释性**：纯 LLM 的回答无法追溯到具体来源

### 1.2 RAG 的典型应用场景

- **企业知识库问答**：将企业内部文档（技术手册、产品规格、政策文件）向量化后提供问答能力
- **客服系统**：结合产品文档和 FAQ，生成准确、一致的客户回复
- **法律/合规审查**：从大量法律法规文档中检索相关条款，辅助法律分析
- **学术研究辅助**：基于论文库检索，帮助研究者快速了解特定领域
- **代码文档助手**：检索 API 文档和代码库，辅助开发

### 1.3 RAG 与微调的比较

| 维度 | RAG | 微调（Fine-tuning） |
|------|-----|---------------------|
| 知识更新 | 即时更新，替换知识库即可 | 需要重新训练，成本高 |
| 幻觉控制 | 强（基于检索结果约束） | 弱（模型可能偏离训练数据） |
| 可解释性 | 强（可追溯来源） | 弱（黑盒生成） |
| 推理成本 | 较高（检索 + 生成） | 较低（仅生成） |
| 实现复杂度 | 中等（需搭建检索管线） | 较高（需训练基础设施） |
| 适用场景 | 知识密集型、需要引用的场景 | 风格模仿、行为对齐 |

---

## 二、核心原理

### 2.1 RAG 五步管线

一个标准的 RAG 流程包含五个核心步骤：解析（Parse）-> 分块（Chunk）-> 嵌入（Embed）-> 检索（Retrieve）-> 生成（Generate）。

#### 步骤一：文档解析（Parse）

将原始文档（PDF、Word、Markdown、HTML 等）转换为纯文本或结构化文本。这一步的质量直接影响后续所有环节。

```python
# 文档解析示例：支持多种格式
from pathlib import Path

def parse_document(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    elif suffix == ".md":
        return path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif suffix in (".docx", ".doc"):
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"不支持的格式: {suffix}")
```

#### 步骤二：文本分块（Chunking）

将长文档切分为语义完整的短片段，这是 RAG 质量的关键因素。分块策略直接影响检索精度。

```python
# 文本分块：支持多种策略
from typing import List

def chunk_text(text: str, strategy: str = "recursive",
               chunk_size: int = 512, overlap: int = 64) -> List[str]:
    if strategy == "recursive":
        return recursive_chunk(text, chunk_size, overlap)
    elif strategy == "fixed":
        return fixed_size_chunk(text, chunk_size, overlap)
    elif strategy == "sentence":
        return sentence_chunk(text)
    else:
        raise ValueError(f"未知分块策略: {strategy}")

def recursive_chunk(text: str, chunk_size: int, overlap: int) -> List[str]:
    """递归分块：优先按段落切分，再按句子，最后按固定大小。"""
    segments = text.split("\n\n")  # 先按段落切分
    chunks = []
    current_chunk = ""
    for seg in segments:
        if len(current_chunk) + len(seg) < chunk_size:
            current_chunk += seg + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = seg + "\n\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def fixed_size_chunk(text: str, chunk_size: int, overlap: int) -> List[str]:
    """固定长度分块（带重叠）。"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def sentence_chunk(text: str) -> List[str]:
    """按句子边界分块。"""
    import re
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)
    return [s.strip() for s in sentences if s.strip()]
```

#### 步骤三：向量嵌入（Embedding）

将文本片段转换为向量表示，使得语义相似的文本在向量空间中距离更近。

```python
# 嵌入生成示例：使用本地 BGE 模型
class LocalEmbeddingProvider:
    """使用本地 BGE 嵌入模型，无需外部 API Key。"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5",
                 device: str = "cpu"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name, device=device)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量列表。"""
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """将查询文本转为向量。"""
        return self.embed([text])[0]
```

#### 步骤四：向量检索（Retrieval）

在向量数据库中执行相似度搜索，找到与用户查询最相关的文档片段。

参考 `agent_platform/src/rag/retriever.py` 的实现：

```python
# 语义检索器的核心实现
from typing import Any, Dict, List, Optional

class Retriever:
    """语义检索器：封装向量数据库检索。"""

    def __init__(self, vector_store: Any) -> None:
        self._store = vector_store

    def search(self, query: str, *, top_k: int = 5,
               where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行语义检索，返回 top_k 个最相似文档。"""
        return self._store.search(query, top_k=top_k, where=where)

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """将检索结果格式化为 LLM 可用的上下文文本。"""
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", r["id"])
            parts.append(f"[来源{i}: {source}]\n{r['text']}")
        return "\n\n".join(parts)

    def format_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """提取检索结果的来源列表（去重）。"""
        seen = set()
        sources = []
        for r in results:
            source = r.get("metadata", {}).get("source", r["id"])
            base = source.split("#")[0]
            if base not in seen:
                seen.add(base)
                sources.append(base)
        return sources
```

#### 步骤五：生成回答（Generation）

将检索结果作为上下文注入 LLM，生成带来源引用的回答。

参考 `agent_platform/src/rag/generator.py` 的实现：

```python
# RAG 生成器的核心实现
from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class RAGAnswer:
    """RAG 回答，包含答案文本和来源引用。"""
    answer: str
    sources: List[str] = field(default_factory=list)
    context_docs: List[str] = field(default_factory=list)


RAG_SYSTEM_PROMPT = """你是一个基于知识库的问答助手。严格遵守以下规则：
1. 只根据提供的资料回答问题，不要使用你自己的知识。
2. 如果资料不足以回答问题，明确说"根据现有资料无法回答"。
3. 回答时引用来源编号，例如 [来源1]、[来源2]。
4. 保持回答简洁、准确。
5. 不要编造任何不在资料中的信息。"""


class RAGGenerator:
    """RAG 生成器：检索 + (可选)重排序 + 生成回答。"""

    def __init__(self, retriever: Retriever,
                 reranker: Optional[Any] = None,
                 top_k_retrieval: int = 10,
                 top_n_rerank: int = 5):
        self._retriever = retriever
        self._reranker = reranker
        self._top_k = top_k_retrieval
        self._top_n = top_n_rerank
        self._llm = get_llm_client()

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """检索 + 可选重排序。"""
        docs = self._retriever.search(query, top_k=self._top_k)
        if not docs:
            return []
        if self._reranker and len(docs) > self._top_n:
            docs = self._reranker.rerank(query, docs, top_n=self._top_n)
        return docs

    def generate(self, query: str) -> RAGAnswer:
        """执行完整 RAG 流程：检索 -> 生成回答。"""
        docs = self.retrieve(query)
        if not docs:
            return RAGAnswer(answer="根据现有资料无法回答该问题。")

        context = self._retriever.format_context(docs)
        sources = self._retriever.format_sources(docs)

        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user",
             "content": f"<资料>\n{context}\n</资料>\n\n问题: {query}"},
        ]
        answer = self._llm.chat(messages)
        return RAGAnswer(
            answer=answer,
            sources=sources,
            context_docs=[d["text"] for d in docs],
        )

    def generate_stream(self, query: str):
        """流式生成回答。"""
        docs = self.retrieve(query)
        if not docs:
            yield "根据现有资料无法回答该问题。"
            return
        context = self._retriever.format_context(docs)
        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user",
             "content": f"<资料>\n{context}\n</资料>\n\n问题: {query}"},
        ]
        yield from self._llm.chat_stream(messages)
```

### 2.2 重排序（Reranking）

重排序是 RAG 流程中提升质量的关键环节。向量检索返回 top_k 候选文档后，Reranker 使用交叉编码器重新计算相关性得分，选出最相关的文档送入 LLM。

参考 `agent_platform/src/rag/reranker.py` 的实现：

```python
# 本地 BGE Reranker 实现
class LocalReranker:
    """使用本地 BGE Reranker 模型进行重排序。"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base",
                 device: str = "cpu"):
        self._model_name = model_name
        self._device = device
        self._model = None

    @property
    def _reranker(self):
        if self._model is None:
            from FlagEmbedding import FlagReranker
            self._model = FlagReranker(
                self._model_name,
                use_fp16=self._device != "cpu",
                device=self._device,
            )
        return self._model

    def rerank(self, query: str, documents: List[Dict[str, Any]],
               top_n: int = 5) -> List[Dict[str, Any]]:
        """对候选文档重新排序，返回 top_n 个最相关的结果。"""
        if not documents:
            return []
        pairs = [[query, doc["text"]] for doc in documents]
        scores = self._reranker.compute_score(pairs)
        if isinstance(scores, float):
            scores = [scores]
        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_n]]
```

### 2.3 混合检索

仅依赖语义检索在某些场景下不够精确。混合检索结合语义检索和关键词检索（如 BM25），可以兼顾语义理解和精确匹配。

```python
# 混合检索（语义 + 关键词）
class HybridRetriever:
    """混合检索器：语义检索 + BM25 关键词检索。"""

    def __init__(self, vector_retriever: Retriever, bm25_weight: float = 0.3):
        self._vector = vector_retriever
        self._bm25_weight = bm25_weight
        self._bm25_index = None

    def build_bm25_index(self, texts: List[str]):
        from rank_bm25 import BM25Okapi
        import jieba
        tokenized = [list(jieba.cut(t)) for t in texts]
        self._bm25_index = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        vec_results = self._vector.search(query, top_k=top_k * 2)
        if self._bm25_index is None:
            return vec_results[:top_k]

        tokenized_query = list(jieba.cut(query))
        bm25_scores = self._bm25_index.get_scores(tokenized_query)

        # 加权融合
        combined = []
        for i, doc in enumerate(vec_results):
            vec_score = 1.0 / (i + 1)
            bm25_score = bm25_scores[i] if i < len(bm25_scores) else 0
            combined.append({
                "doc": doc,
                "score": ((1 - self._bm25_weight) * vec_score +
                          self._bm25_weight * bm25_score),
            })

        combined.sort(key=lambda x: x["score"], reverse=True)
        return [c["doc"] for c in combined[:top_k]]
```

### 2.4 上下文窗口管理

LLM 的上下文窗口有限，需要精打细算。推荐分配策略（以 8K 上下文为例）：

- 系统提示词：约 500 tokens
- 检索结果（5-10 个片段）：约 3000-4000 tokens
- 对话历史（最近 5-10 轮）：约 2000 tokens
- 用户问题：约 500 tokens
- 留有余量：约 1000 tokens

### 2.5 来源归属与幻觉降低

RAG 降低幻觉的两个关键机制：
1. **约束生成**：System Prompt 强制要求"只根据提供的资料回答"
2. **来源引用**：每个回答段落都附上来源编号，让用户/下游系统可以验证

---

## 三、实战指南

### 3.1 完整 RAG 组合示例

```python
from retriever import Retriever
from reranker import LocalReranker
from generator import RAGGenerator

# 1. 准备向量存储
from chroma_store import ChromaVectorStore
from local_bge import get_embedding_provider

emb = get_embedding_provider("BAAI/bge-small-zh-v1.5", device="cpu")
store = ChromaVectorStore("./chroma_db", embedding=emb)

# 2. 构建检索器
retriever = Retriever(store)

# 3. 可选：添加重排序器
reranker = LocalReranker(device="cpu")

# 4. 构建 RAG 生成器
rag = RAGGenerator(
    retriever=retriever,
    reranker=reranker,
    top_k_retrieval=10,
    top_n_rerank=5,
)

# 5. 问答
answer = rag.generate("什么是 RAG 技术?")
print(f"回答: {answer.answer}")
print(f"来源: {answer.sources}")
```

### 3.2 流式生成

```python
for chunk in rag.generate_stream("什么是 LangGraph?"):
    print(chunk, end="", flush=True)
```

### 3.3 文档导入

参考 `agent_platform/src/api/routes.py` 中的文档上传路由：

```python
def import_documents(directory: str):
    """批量导入文档目录到知识库。"""
    from parsing.document import parse_and_chunk, SUPPORTED_SUFFIXES

    p = Path(directory)
    files = [f for f in p.iterdir() if f.suffix.lower() in SUPPORTED_SUFFIXES]

    all_chunks = []
    for f in files:
        try:
            chunks = parse_and_chunk(f)
            all_chunks.extend(chunks)
            print(f"解析完成: {f.name} -> {len(chunks)} 个分块")
        except Exception as e:
            print(f"解析失败 {f.name}: {e}")

    if all_chunks:
        store.add_documents(all_chunks)

    return {"file_count": len(files), "chunks": len(all_chunks)}
```

---

## 四、最佳实践

### 4.1 分块策略选择

| 文档类型 | 推荐策略 | 块大小 | 重叠 |
|---------|---------|--------|------|
| 技术文档（Markdown） | 按章节分块 | 256-512 tokens | 32-64 |
| 学术论文（PDF） | 按段落 + 引文 | 512-1024 tokens | 64-128 |
| 代码库 | 按函数/类分块 | 128-256 tokens | 16-32 |
| 对话记录 | 按轮次分块 | 256 tokens | 0 |

### 4.2 检索调优

- **top_k 设置**：推荐初始值 10，避免遗漏相关信息
- **相似度阈值**：余弦相似度推荐 0.7-0.8，低于此值的结果应丢弃
- **多样性惩罚**：MMR（Maximum Marginal Relevance）避免检索结果过于相似

### 4.3 提示词工程

- System Prompt 中明确约束："只根据提供的资料回答"
- 使用 XML 标签分隔资料和问题，降低 LLM 的混淆
- 添加"如果资料不足请明确说不知道"的指令

### 4.4 RAG 评估指标

- **检索精度**：检索结果中相关文档的比例
- **召回率**：所有相关文档中被检索到的比例
- **生成忠实度**：回答是否忠实于检索到的资料（可使用 LLM 评估）
- **答案有用性**：回答是否真正解决了用户问题

---

## 五、常见陷阱

### 5.1 分块破坏语义完整性

**陷阱**：在段落中间切分，导致一个完整的知识点被分成两段。

**解决**：使用语义分块（Semantic Chunking），在语义转换处切分。

### 5.2 检索不到相关内容

**陷阱**：用户问题的表述与知识库文档差异太大。

**解决**：使用混合检索（语义 + BM25）、查询重写（Query Rewriting）、查询扩展（Query Expansion）。

### 5.3 上下文窗口溢出

**陷阱**：检索结果 + 对话历史超出 LLM 上下文窗口限制。

**解决**：实现 Token 预算管理，动态裁剪检索结果数量。

### 5.4 LLM 忽略检索结果

**陷阱**：LLM 过度依赖自身知识而忽略检索到的资料。

**解决**：强化 System Prompt 约束，将检索结果排在用户问题之前，使用 XML 标签强分隔。

---

## 六、API Key 依赖

| 组件 | 需要 API Key? | 说明 |
|------|--------------|------|
| 文档解析 | 否 | 纯本地操作 |
| 文本分块 | 否 | 纯本地操作 |
| 向量嵌入（BGE） | 否 | 使用本地 Sentence Transformer |
| 向量检索 | 否 | 使用本地 Chroma 数据库 |
| 重排序（BGE Reranker） | 否 | 使用本地 FlagEmbedding |
| LLM 生成 | 是 | 需要 OpenAI/Anthropic 等 API Key |
| 混合检索（BM25） | 否 | 纯本地关键词检索 |

---

## 七、技术关系

```text
用户查询
    |
    v
+--------------+     +--------------+
|  查询重写     |---->|  Embedding   |
|  Query       |     |  模型        |
|  Rewriting   |     |  (BGE)       |
+--------------+     +------+-------+
                            |
                            v
                   +------------------+
                   |  向量数据库       |
                   |  (Chroma)        |<---+
                   +--------+---------+    |
                            |              |
                            v              |
                   +------------------+    |
                   |  粗排 (top-k)     |    |
                   +--------+---------+    |
                            |              |
                            v              |
                   +------------------+    |
                   |  精排 (Reranker)  |    |
                   +--------+---------+    |
                            |              |
                            v              |
                   +------------------+    |
                   |  Prompt 组装     |    |
                   +--------+---------+    |
                            |              |
                            v              |
                   +------------------+    |
                   |  LLM 生成回答    |    |
                   +--------+---------+    |
                            |              |
                            v              |
                   +------------------+    |
                   |  回答 + 来源引用  |    |
                   +------------------+    |
                                          |
                   文档解析 -> 分块 -> Embed -> 存入数据库 ---+
```

---

## 八、验收清单

- [ ] 理解 RAG 五步管线：Parse -> Chunk -> Embed -> Retrieve -> Generate
- [ ] 掌握至少两种分块策略（固定长度、递归分块）
- [ ] 能独立实现 Retriever 的 search、format_context、format_sources 方法
- [ ] 理解重排序的作用和实现方式
- [ ] 理解混合检索的动机（语义 + 关键词互补）
- [ ] 知道如何管理 Token 预算，防止上下文溢出
- [ ] 理解 RAG 降低幻觉的两个机制：约束生成和来源引用
- [ ] 能搭建完整的 RAG 管线（从文档导入到问答）
- [ ] 了解 RAG 与微调的区别和各自适用场景
- [ ] 掌握 RAG 常见陷阱及解决方案

---

## 九、学习资源

- **LangChain RAG 文档**: https://python.langchain.com/docs/use_cases/question_answering/
- **LlamaIndex RAG 文档**: https://docs.llamaindex.ai/en/stable/getting_started/concepts/
- **Chroma 向量数据库**: https://docs.trychroma.com/
- **BGE Embedding 模型**: https://github.com/FlagOpen/FlagEmbedding
- **平台参考代码**: agent_platform/src/rag/ (retriever.py, generator.py, reranker.py)
- **论文**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
