# 07 向量数据库 Vector Databases

> 向量数据库是专门为 Embedding 向量的存储和检索设计的数据库系统。它是 RAG 架构的核心组件，决定了知识库的检索效率和准确性。

---

## 1. 概念概述

### 1.1 什么是向量数据库

向量数据库是一种致力于高效存储和检索高维向量的数据库系统。与传统数据库使用精确匹配或关键词匹配不同，向量数据库使用近似最近邻（ANN）算法在向量空间中查找与查询最相似的向量。

### 1.2 为什么需要向量数据库

- **大规模语义搜索**：在百万到亿级的文档集合中实现毫秒级语义搜索
- **比纯内存搜索更高效**：纯 Python 线性搜索在百万级数据时延迟高达数秒
- **持久化和元数据管理**：向量数据需要持久化存储，并支持按元数据过滤
- **生产级可靠性**：支持并发访问、数据备份、容灾恢复

### 1.3 何时使用向量数据库

- 文档数量超过 10 万条
- 需要生产级的高可用和持久化
- 需要复杂元数据过滤（时间范围、类别筛选等）
- 需要多租户支持
- 需要分布式部署和水平扩展

---

## 2. 核心原理

### 2.1 HNSW 算法详解

HNSW（Hierarchical Navigable Small World）是目前最流行的 ANN 算法之一。它构建一个多层级的图结构来加速搜索。

**HNSW 的工作原理**：

1. **构建阶段**：为每个向量构建多层级索引。顶层覆盖整个向量空间（稀疏连接），底层包含所有向量（密集连接）
2. **搜索阶段**：从顶层开始搜索，找到最近的节点，然后逐层向下细化
3. **插入阶段**：新向量被随机分配一个层数，在对应层建立连接

```
# HNSW 层级结构示意
Layer 3:    A --- B                （顶层，稀疏）
              /
Layer 2: A --- B --- C             （中间层）
         |     |     |
Layer 1: A --- B --- C --- D       （底层，密集，包含所有向量）
         |     |     |     |
         v1    v2    v3    v4
```

**HNSW 的关键参数**：

- `M`：每个节点的最大连接数（默认 16）。M 越大，检索越精确但内存越多
- `ef_construction`：构建时动态列表大小（默认 200）。越大索引质量越高
- `ef_search`：搜索时动态列表大小。越大检索越精确但越慢

```python
# Chroma 中 HNSW 参数的配置
collection = client.create_collection(
    name="my_collection",
    metadata={
        "hnsw:space": "cosine",       # 距离度量
        "hnsw:M": 16,                  # 最大连接数
        "hnsw:ef_construction": 200,   # 构建参数
        "hnsw:ef_search": 10,          # 搜索参数
        "hnsw:num_threads": 4,         # 构建线程数
    },
)
```

### 2.2 距离度量

向量数据库支持三种主要距离度量：

```python
import numpy as np


# 1. 余弦距离（Cosine Distance）
def cosine_distance(v1: list[float], v2: list[float]) -> float:
    \"\"\"余弦距离 = 1 - 余弦相似度。范围 [0, 2]。\"\"\"
    a, b = np.array(v1), np.array(v2)
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return 1 - (dot / norm) if norm != 0 else 1.0


# 2. 欧几里得距离（Euclidean Distance）
def euclidean_distance(v1: list[float], v2: list[float]) -> float:
    \"\"\"L2 距离。范围 [0, +inf)。\"\"\"
    return float(np.linalg.norm(np.array(v1) - np.array(v2)))


# 3. 点积距离（Dot Product Distance）
def dot_product_distance(v1: list[float], v2: list[float]) -> float:
    \"\"\"负点积。对于归一化向量，等价于余弦距离。\"\"\"
    return -float(np.dot(np.array(v1), np.array(v2)))


# 选择建议
"""
使用场景                    | 推荐距离
归一化向量（如 BGE）       | cosine（或 dot，结果等价）
未归一化向量                | cosine
向量值本身有意义（如频率）  | euclidean
需要强调方向而非长度        | cosine
推荐系统中的协同过滤        | dot（对隐式反馈效果好）
"""
```

### 2.3 Chroma vs Qdrant vs Pinecone vs Weaviate

这是目前最流行的四个向量数据库：

| 维度 | Chroma | Qdrant | Pinecone | Weaviate |
|------|--------|--------|----------|----------|
| 部署方式 | 嵌入式/Local | 自托管 Docker | 全托管 SaaS | 混合模式 |
| 是否开源 | 是（Apache 2.0） | 是（Apache 2.0） | 否 | 是（BSD 3-Clause） |
| 是否需要 API Key | 否 | 否（自托管） | 是 | 否（自托管） |
| 持久化 | SQLite 文件 | RocksDB/文件 | 自动管理 | BoltDB/文件 |
| 元数据过滤 | 支持（基础） | 支持（丰富） | 支持 | 支持（丰富） |
| 全文检索 | 否 | 是 | 否 | 是 |
| 多租户 | 否 | 是 | 是 | 是 |
| 分布式 | 否 | 是 | 是 | 是 |
| Python SDK | 优秀 | 良好 | 良好 | 良好 |
| 适合规模 | < 100 万向量 | < 1000 万 | 无上限 | < 1000 万 |
| 启动复杂度 | 几行代码 | Docker 部署 | 注册即用 | Docker 部署 |

**选择建议**：

- **Chroma**：开发原型、个人项目、小团队（最简单）
- **Qdrant**：中型项目、自托管、需要丰富过滤功能
- **Pinecone**：企业级、不想运维、需要 SLA 保障
- **Weaviate**：需要混合搜索（向量 + 全文）

### 2.4 元数据过滤

在生产场景中，几乎总是需要结合向量相似度搜索和元数据条件过滤：

```python
# Chroma 元数据过滤
results = collection.query(
    query_embeddings=[query_vector],
    n_results=10,
    where={
        "$and": [
            {"source": {"$eq": "technical_docs"}},  # 来源是技术文档
            {"date": {"$gte": "2025-01-01"}},        # 2025 年后的文档
            {"category": {"$in": ["python", "ai"]}},  # 属于 Python 或 AI 类别
        ],
    },
)

# Qdrant 过滤（更丰富的过滤语法）
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)
results = client.search(
    collection_name="knowledge_base",
    query_vector=query_vector,
    limit=10,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="source",
                match=models.MatchValue(value="technical_docs"),
            ),
            models.FieldCondition(
                key="date",
                range=models.Range(gte="2025-01-01"),
            ),
            models.FieldCondition(
                key="category",
                match=models.MatchAny(any=["python", "ai"]),
            ),
        ],
    ),
)
```

### 2.5 Collection 管理

向量数据库中的 Collection 类似于传统数据库中的表：

```python
from chromadb import PersistentClient
from chromadb.config import Settings


class CollectionManager:
    \"\"\"集合管理工具。\"\"\"

    def __init__(self, persist_dir: str = "./data/chroma"):
        self._client = PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

    def list_collections(self) -> list[str]:
        return [c.name for c in self._client.list_collections()]

    def create_collection(
        self,
        name: str,
        distance_fn: str = "cosine",
        metadata: dict | None = None,
    ):
        return self._client.create_collection(
            name=name,
            metadata={"hnsw:space": distance_fn, **(metadata or {})},
        )

    def get_collection(self, name: str):
        return self._client.get_collection(name)

    def delete_collection(self, name: str):
        self._client.delete_collection(name)

    def get_collection_stats(self, name: str) -> dict:
        collection = self._client.get_collection(name)
        return {
            "name": name,
            "count": collection.count(),
            "metadata": collection.metadata,
        }
```

### 2.6 持久化策略

向量数据库的数据持久化是一个关键的工程决策：

```python
# Chroma 持久化策略
"""
Chroma 使用两种持久化模式：

1. EphemeralClient（内存模式）
   - 数据仅存在于内存
   - 适合测试和原型开发
   - 程序退出后数据丢失

2. PersistentClient（持久化模式，推荐）
   - 数据存储在本地文件系统（SQLite + Parquet）
   - 程序重启后数据恢复
   - 适合单机生产环境
"""

# 内存模式
import chromadb
client = chromadb.EphemeralClient()

# 持久化模式
client = chromadb.PersistentClient(path="./data/chroma")


# 定期备份策略
import shutil
from datetime import datetime


def backup_chroma(persist_dir: str, backup_dir: str):
    \"\"\"备份 Chroma 数据。\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/chroma_backup_{timestamp}"
    shutil.copytree(persist_dir, backup_path)
    print(f"备份完成：{backup_path}")
    return backup_path
```

### 2.7 agent_platform 中的 Chroma 封装

在 `agent_platform/src/vectordb/chroma_store.py` 中，我们封装了完整的向量数据库操作：

```python
class ChromaVectorStore:
    \"\"\"Chroma 向量存储封装。\"\"\"

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        collection_name: str = "knowledge_base",
        embedding: EmbeddingProvider | None = None,
    ) -> None:
        import chromadb
        from chromadb.config import Settings

        # 确保持久化目录存在
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection_name = collection_name
        self._embedding = embedding or get_embedding_provider()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, chunks, *, batch_size=50):
        \"\"\"批量添加文档。\"\"\"
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            embeddings = self._embedding.embed(texts)
            self._collection.add(
                ids=[c.source for c in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=[{"source": c.source, "chunk_index": c.chunk_index} for c in batch],
            )

    def search(self, query, *, top_k=5, where=None):
        \"\"\"语义检索。\"\"\"
        query_embedding = self._embedding.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        # 格式化结果...
        return formatted
```

---

## 3. 实战指南

### 3.1 完整的向量数据库操作

```python
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Document:
    text: str
    source: str
    metadata: dict


class VectorDatabase:
    \"\"\"完整的向量数据库封装。\"\"\"

    def __init__(self, persist_dir: str = "./data/vectordb"):
        import chromadb
        from chromadb.config import Settings

        self._persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collections: dict[str, any] = {}

    def get_or_create(self, name: str) -> any:
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def insert(self, collection: str, docs: list[Document], embeddings: list[list[float]]):
        coll = self.get_or_create(collection)
        coll.add(
            ids=[f"{doc.source}_{i}" for i, doc in enumerate(docs)],
            embeddings=embeddings,
            documents=[doc.text for doc in docs],
            metadatas=[{"source": doc.source, **doc.metadata} for doc in docs],
        )

    def query(
        self, collection: str, query_embedding: list[float],
        top_k: int = 10, filters: dict | None = None,
    ) -> list[dict]:
        coll = self.get_or_create(collection)
        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,
            include=["documents", "metadatas", "distances"],
        )
        output = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                output.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],
                })
        return output
```

### 3.2 混合搜索（向量 + 关键词）

```python
import re
from collections import Counter


class HybridSearch:
    \"\"\"混合搜索：向量搜索 + BM25 关键词搜索。\"\"\"

    def __init__(self, vector_store, alpha: float = 0.5):
        self._vector_store = vector_store
        self._alpha = alpha  # 混合权重：0=纯BM25，1=纯向量

    def _bm25_score(self, query: str, doc: str, avg_doc_len: float, k1: float = 1.5, b: float = 0.75) -> float:
        \"\"\"简化的 BM25 分数计算。\"\"\"
        query_terms = re.findall(r"\\w+", query.lower())
        doc_terms = re.findall(r"\\w+", doc.lower())
        doc_len = len(doc_terms)
        term_freq = Counter(doc_terms)

        score = 0.0
        for term in set(query_terms):
            if term in term_freq:
                tf = term_freq[term]
                idf = 1.0  # 简化处理
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
        return score

    def search(self, query: str, query_vector: list[float], top_k: int = 10) -> list[dict]:
        # 向量搜索
        vector_results = self._vector_store.query(query_vector, top_k=top_k * 2)
        vector_scores = {r["id"]: r["score"] for r in vector_results}

        # 归一化向量分数
        if vector_scores:
            max_vs = max(vector_scores.values())
            min_vs = min(vector_scores.values())
            range_vs = max_vs - min_vs or 1
            for k in vector_scores:
                vector_scores[k] = (vector_scores[k] - min_vs) / range_vs

        # 混合
        hybrid_scores = {}
        for r in vector_results:
            vs = vector_scores.get(r["id"], 0)
            bm25 = self._bm25_score(query, r["text"], 100)
            hybrid_scores[r["id"]] = self._alpha * vs + (1 - self._alpha) * bm25

        # 排序
        ranked = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        id_map = {r["id"]: r for r in vector_results}
        return [id_map[rid] for rid, _ in ranked]
```

---

## 4. 最佳实践

### 4.1 索引参数调优

- **M 值**：默认 16 适用于大多数场景。如果内存充足且追求精度，可增到 32-64
- **ef_construction**：200-500 之间。值越大，索引质量越高，但构建越慢
- **ef_search**：检索时的动态调整参数。从 10 开始，根据精度需求增加到 100-200

### 4.2 数据管理

- 定期对集合进行健康检查
- 使用 batch_size 控制批量写入，避免内存溢出
- 建立索引备份策略
- 监控集合大小和查询延迟

### 4.3 生产部署

- Chroma 适合单机部署（< 100 万向量）
- Qdrant 适合 Docker 容器化部署
- Pinecone 适合完全托管的云部署
- 始终启用持久化，关闭匿名遥测

---

## 5. 常见陷阱与反模式

### 5.1 向量维度和距离度量不匹配

反模式：使用未归一化的向量配合余弦距离。余弦距离假设向量已归一化。正确做法是统一使用归一化向量，或选择正确的距离度量。

### 5.2 忽略元数据过滤

反模式：对所有文档使用单一集合，通过向量相似度搜索后在应用层过滤。这在数据量大时效率极低。正确做法是在向量数据库层面使用 where 条件过滤。

### 5.3 不设批处理大小

反模式：一次性写入所有文档（特别是超过 10 万条时）。这会导致内存溢出或数据库锁死。正确做法是使用 batch_size=50-100 分批写入。

### 5.4 混合不同 Embedding 模型的向量

反模式：在一个集合中混合使用两种不同模型（如 BGE 和 OpenAI）生成的向量。不同模型的向量空间不兼容，无法混合搜索。

### 5.5 不考虑冷启动

反模式：新创建的集合没有数据就进行搜索。空集合的搜索会返回空结果。应该处理这种情况，向用户提示"知识库为空"。

---

## 6. API Key 依赖

- **Chroma**（开源）：不需要任何 API Key
- **Qdrant**（自托管）：不需要 API Key
- **Pinecone**：需要 Pinecone API Key
- **Weaviate**（自托管）：不需要 API Key；Weaviate Cloud：需要 API Key

在 agent_platform 的 `src/vectordb/chroma_store.py` 中，使用 Chroma PersistentClient，数据存储在本地文件系统，不需要任何外部 API Key。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **Embedding** | Embedding 是向量数据库的输入 |
| **RAG** | 向量数据库是 RAG 的检索源 |
| **文档解析** | 解析后的文档通过 Embedding 进入向量数据库 |
| **Agent 系统** | Agent 通过向量数据库实现知识检索 |
| **结构化输出** | 检索结果需要结构化输出格式化后才可被 LLM 消费 |

在 agent_platform 中，`src/vectordb/chroma_store.py` 位于 Embedding 和 Document Parsing 之上，为 RAG 提供检索服务。

---

## 8. 验收清单

- [ ] 理解 HNSW 算法的基本原理
- [ ] 掌握三种距离度量的区别和选择
- [ ] 了解 Chroma、Qdrant、Pinecone、Weaviate 的差异
- [ ] 能够使用 Chroma 进行向量存储和检索
- [ ] 理解元数据过滤的实现方式
- [ ] 掌握集合的创建、删除、管理
- [ ] 了解持久化策略和备份方法
- [ ] 能够调优 HNSW 参数
- [ ] 理解向量搜索的 batch 管理
- [ ] 能在生产环境中选择合适的向量数据库

---

## 9. 推荐学习资源

### 官方文档
- Chroma: https://docs.trychroma.com/
- Qdrant: https://qdrant.tech/documentation/
- Pinecone: https://docs.pinecone.io/
- Weaviate: https://weaviate.io/developers/weaviate

### 论文
- "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs" (Malkov & Yashunin, 2018)
- "Approximate Nearest Neighbor Search on High Dimensional Data" (综述)

### 项目代码参考
- `agent_platform/src/vectordb/chroma_store.py` — Chroma 封装，支持增删查
- `agent_platform/src/embeddings/local_bge.py` — Embedding 提供者，向量数据库的输入
- `agent_platform/src/rag/retriever.py` — 检索器，协调向量数据库和重排序
