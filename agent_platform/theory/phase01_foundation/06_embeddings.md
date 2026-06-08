# 06 Embedding 模型 文本向量化与语义表示

> Embedding 是将文本转换为数值向量的技术，是语义搜索、RAG、聚类、分类等任务的基石。
> 理解 Embedding 的原理和工程实践，是构建高质量 AI Agent 的关键。

---

## 1. 概念概述

### 1.1 什么是 Embedding

Embedding（嵌入/向量化）是将自然语言文本映射到高维向量空间的技术。在这个空间中，语义相似的文本在几何距离上更接近，不相似的文本距离更远。这种"语义到几何"的映射是 LLM 时代信息检索的基础。

### 1.2 为什么需要 Embedding

- **语义搜索**：基于意思而非关键词匹配搜索
- **RAG 检索**：从知识库中找到与问题语义最相关的文档片段
- **文本聚类**：将相似文档自动分组
- **文本分类**：基于向量距离进行分类
- **异常检测**：识别与正常模式偏离的文本
- **推荐系统**：基于内容相似度推荐相关物品

### 1.3 何时使用 Embedding

- 构建知识库检索系统（RAG）
- 需要在大规模文本集合中进行语义查找
- 在线分类或聚类任务
- 多语言语义匹配（跨语言 Embedding）
- 配合向量数据库实现持久化存储和检索

---

## 2. 核心原理

### 2.1 文本向量化的基本原理

文本向量化将变长的文本转换为固定长度的数值向量。不同的模型产生不同维度的向量：

- BGE-small-zh-v1.5：384 维
- BGE-base-zh-v1.5：768 维
- text-embedding-3-small：1536 维
- text-embedding-3-large：3072 维

向量维度的选择涉及权衡：

```
低维度（384-768）：计算快、存储小，但对细粒度语义区分不够
中等维度（1024-1536）：平衡之道，大多数场景推荐
高维度（2048+）：区分能力强，但计算和存储成本高
```

### 2.2 Cosine Similarity（余弦相似度）

余弦相似度是最常用的向量相似度度量方式：

```python
import numpy as np


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    \"\"\"计算两个向量的余弦相似度。\"\"\"
    a = np.array(v1)
    b = np.array(v2)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


def cosine_similarities(
    query_vector: list[float], vectors: list[list[float]]
) -> list[float]:
    \"\"\"计算查询向量与多个向量的余弦相似度。\"\"\"
    q = np.array(query_vector)
    v = np.array(vectors)
    dot_products = np.dot(v, q)
    norms = np.linalg.norm(v, axis=1)
    q_norm = np.linalg.norm(q)
    return (dot_products / (norms * q_norm)).tolist()
```

**余弦相似度的取值范围**：

- 1.0：完全同向（语义完全相同）
- 0.0：正交（语义不相关）
- -1.0：完全反向（语义相反，较少见）

### 2.3 归一化向量（Normalized Embeddings）

归一化向量是指向量被缩放到单位长度（L2 范数为 1）。归一化后，余弦相似度等价于点积（Dot Product）：

```python
def normalize_vector(v: np.ndarray) -> np.ndarray:
    \"\"\"L2 归一化向量。\"\"\"
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


# 归一化后，cosine_similarity == dot_product
v1_normalized = normalize_vector(np.array(v1))
v2_normalized = normalize_vector(np.array(v2))

# 以下两式等价
cos_sim = np.dot(v1_normalized, v2_normalized)
dot_prod = np.dot(v1_normalized, v2_normalized)  # 等价

print(f"归一化后余弦相似度：{cos_sim}")
```

在 agent_platform 的 `src/embeddings/local_bge.py` 中，BGE 模型默认启用了归一化：

```python
embeddings = self._encoder.encode(
    texts,
    normalize_embeddings=True,  # 自动归一化
    show_progress_bar=len(texts) > 50,
)
```

### 2.4 BGE 模型（BAAI General Embedding）

BGE（BAAI General Embedding）是北京智源研究院（BAAI）开发的开源 Embedding 模型系列。它是中文 Embedding 任务的首选之一。

**BGE 模型的关键特性**：

- 支持中文和英文
- 使用 instruction 前缀优化检索性能（BGE 在检索场景下自动为 query 添加 "为这个句子生成表示以用于检索相关文章："）
- 开源，可在本地部署，无需 API Key
- 兼容 sentence-transformers 生态
- 在 C-MTEB（中文 MTEB）榜单上表现优秀

```python
# BGE 模型的 instruction 前缀
# 在检索场景下，BGE 会自动处理 query 和 document 的不同前缀：

QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："

def bge_query_transform(query: str) -> str:
    \"\"\"BGE 查询变换：添加检索前缀。\"\"\"
    return f"{QUERY_INSTRUCTION}{query}"


# 对于文档（documents），BGE 不添加前缀
# 对于查询（queries），BGE 添加检索前缀
# 这样 query 和 document 的向量在语义空间中更加接近
```

### 2.5 MTEB 榜单

MTEB（Massive Text Embedding Benchmark）是评估 Embedding 模型的标准榜单。它包含 8 个任务：

1. **分类**（Classification）
2. **聚类**（Clustering）
3. **语义相似度**（Pair Classification）
4. **重排序**（Reranking）
5. **检索**（Retrieval）— RAG 场景中最关键
6. **语义文本相似度**（STS）
7. **总结**（Summarization）
8. **排序**（StackExchange Duplicate Questions）

C-MTEB 是 MTEB 的中文版本。选择 Embedding 模型时，应优先参考 C-MTEB 的 Retrieval 分数。

```
# 典型模型的 C-MTEB Retrieval 分数
BAAI/bge-large-zh-v1.5:  72.4
BAAI/bge-base-zh-v1.5:   69.5
BAAI/bge-small-zh-v1.5:  64.2
text-embedding-3-large:    ~68 (中文)
text-embedding-3-small:    ~62 (中文)
```

### 2.6 OpenAI Embeddings

OpenAI 也提供 Embedding API，优势是无需本地 GPU，调用简单：

```python
from openai import OpenAI


class OpenAIEmbedding:
    \"\"\"OpenAI Embedding 封装。\"\"\"

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def dimension(self) -> int:
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        return dimensions.get(self._model, 1536)

    def embed(self, texts: list[str]) -> list[list[float]]:
        \"\"\"批量向量化。\"\"\"
        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]


# OpenAI 支持维度截断（dimensions 参数）
# 可以在不重新生成向量的情况下降低维度
response = client.embeddings.create(
    model="text-embedding-3-large",
    input="测试文本",
    dimensions=512,  # 从 3072 降维到 512
)
```

**BGE vs OpenAI Embeddings 对比**：

| 维度 | BGE | OpenAI |
|------|-----|--------|
| 是否需要 API Key | 否 | 是 |
| 是否需要 GPU | 是（或 CPU 慢） | 否 |
| 中文效果 | 优秀 | 良好 |
| 自定义 | 支持微调 | 无法微调 |
| 成本 | 免费（硬件成本） | 按 token 计费 |
| 隐私 | 数据本地处理 | 数据发送到云端 |
| 维度 | 384-1024 | 1536-3072 |

### 2.7 缓存策略

在生产环境中，重复计算相同文本的 Embedding 是浪费的。缓存可以显著提升性能：

```python
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional


class EmbeddingCache:
    \"\"\"Embedding 结果缓存，使用 SQLite 持久化。\"\"\"

    def __init__(self, cache_path: str = "./data/embedding_cache.db"):
        self._db_path = Path(cache_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                text_hash TEXT PRIMARY KEY,
                text TEXT,
                model_name TEXT,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str, model_name: str) -> Optional[list[float]]:
        \"\"\"从缓存中获取 Embedding。\"\"\"
        text_hash = self._hash(text)
        cursor = self._conn.execute(
            "SELECT embedding FROM embeddings WHERE text_hash=? AND model_name=?",
            (text_hash, model_name),
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def set(self, text: str, model_name: str, embedding: list[float]):
        \"\"\"写入缓存。\"\"\"
        text_hash = self._hash(text)
        self._conn.execute(
            "INSERT OR REPLACE INTO embeddings (text_hash, text, model_name, embedding) VALUES (?, ?, ?, ?)",
            (text_hash, text, model_name, json.dumps(embedding)),
        )
        self._conn.commit()

    def embed_with_cache(
        self, texts: list[str], model, model_name: str
    ) -> list[list[float]]:
        \"\"\"带缓存的 Embedding 计算。\"\"\"
        results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cached = self.get(text, model_name)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)

        if uncached_texts:
            new_embeddings = model.embed(uncached_texts)
            for text, emb in zip(uncached_texts, new_embeddings):
                self.set(text, model_name, emb)
            for idx, emb in zip(uncached_indices, new_embeddings):
                results[idx] = emb

        return results
```

---

## 3. 实战指南

### 3.1 BGE 本地 Embedding（agent_platform 实现）

```python
# src/embeddings/local_bge.py 的核心逻辑
from functools import lru_cache
from typing import Protocol


class EmbeddingProvider(Protocol):
    \"\"\"Embedding 提供者协议。\"\"\"
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
    @property
    def dimension(self) -> int: ...


class BGEBatchEmbedding:
    \"\"\"批量 BGE Embedding。\"\"\"

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cpu",
    ):
        self._model_name = model_name
        self._device = device
        self._model = None

    @property
    def _encoder(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._model_name, device=self._device
            )
        return self._model

    @property
    def dimension(self) -> int:
        return self._encoder.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._encoder.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]
```

### 3.2 批量 Embedding 处理

```python
def batch_embed(
    texts: list[str],
    embedder: EmbeddingProvider,
    batch_size: int = 32,
    show_progress: bool = False,
) -> list[list[float]]:
    \"\"\"分批向量化，防止内存溢出。\"\"\"
    all_embeddings = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        embeddings = embedder.embed(batch)
        all_embeddings.extend(embeddings)

        if show_progress:
            progress = min(i + batch_size, total)
            print(f"处理进度：{progress}/{total} ({progress/total*100:.0f}%)")

    return all_embeddings
```

### 3.3 语义相似度搜索（纯 Python）

```python
import heapq


class SimpleVectorSearch:
    \"\"\"纯 Python 向量搜索（无需向量数据库，适合小规模数据）。\"\"\"

    def __init__(self, embedding_provider: EmbeddingProvider):
        self._embedder = embedding_provider
        self._documents: list[dict] = []  # [{text, embedding, metadata}]

    def add_documents(self, texts: list[str], metadatas: list[dict] | None = None):
        \"\"\"添加文档并向量化。\"\"\"
        embeddings = self._embedder.embed(texts)
        for i, text in enumerate(texts):
            self._documents.append({
                "text": text,
                "embedding": embeddings[i],
                "metadata": metadatas[i] if metadatas else {},
            })

    def search(
        self, query: str, top_k: int = 5
    ) -> list[dict]:
        \"\"\"语义搜索。\"\"\"
        query_vector = self._embedder.embed_query(query)
        heap: list[tuple[float, int]] = []  # (similarity, index)

        for i, doc in enumerate(self._documents):
            sim = cosine_similarity(query_vector, doc["embedding"])
            if len(heap) < top_k:
                heapq.heappush(heap, (sim, i))
            elif sim > heap[0][0]:
                heapq.heapreplace(heap, (sim, i))

        results = []
        while heap:
            sim, idx = heapq.heappop(heap)
            results.append({
                "text": self._documents[idx]["text"],
                "metadata": self._documents[idx]["metadata"],
                "similarity": sim,
            })
        return list(reversed(results))
```

### 3.4 Embedding 维度的降维与截断

```python
from sklearn.decomposition import PCA


class EmbeddingReducer:
    \"\"\"Embedding 维度缩减。\"\"\"

    def __init__(self, target_dim: int):
        self._pca = PCA(n_components=target_dim)
        self._fitted = False

    def fit(self, embeddings: list[list[float]]):
        \"\"\"在代表性的数据集上拟合 PCA。\"\"\"
        self._pca.fit(np.array(embeddings))
        self._fitted = True

    def transform(self, embeddings: list[list[float]]) -> list[list[float]]:
        if not self._fitted:
            raise RuntimeError("请先调用 fit 方法")
        return self._pca.transform(np.array(embeddings)).tolist()

    def explain_variance(self) -> list[float]:
        \"\"\"查看各维度解释的方差比例。\"\"\"
        return self._pca.explained_variance_ratio_.tolist()
```

---

## 4. 最佳实践

### 4.1 模型选择

- **中文为主**：优先选择 BGE 系列（如 bge-large-zh-v1.5）
- **英文为主 + 云端部署**：使用 OpenAI text-embedding-3 系列
- **隐私敏感场景**：必须使用本地模型，选择 BGE 或 M3E
- **移动端/边缘设备**：使用 bge-small 或 MobileBERT
- **多语言场景**：使用 bge-m3 或 intfloat/multilingual-e5

### 4.2 质量提升

- 对长文档先分段再分别 Embedding，取平均或拼接
- 使用 instruction 前缀（BGE 自动处理，其他模型需要手动加）
- 使用重排序（Reranker）作为第二阶段精排
- 定期评估 Embedding 效果（在验证集上计算 Recall@K）

### 4.3 性能优化

- 使用 Embedding 缓存，避免重复计算
- 批量 Embedding（通常 batch_size=32-64 最优）
- 使用归一化向量，简化相似度计算为点积
- 使用更小的模型（如 bge-small 代替 bge-large）在效果可接受的情况下

---

## 5. 常见陷阱与反模式

### 5.1 忽略 Instruction 前缀

反模式：查询和文档使用相同的向量化方式，未添加任何指令前缀。这会导致检索效果显著下降。BGE 模型默认会为 query 添加前缀，但如果手动调用 encode 方法需要确保正确处理。

### 5.2 未归一化向量

反模式：直接使用原始向量计算相似度。未归一化的向量长度变化会影响余弦相似度的计算。建议始终使用归一化向量。

### 5.3 不区分向量维度和质量

反模式：认为维度越高越好。在高维空间中，向量分布会更稀疏（维度灾难），反而可能降低检索质量。选择适合任务的数据集验证的维度。

### 5.4 忽略 Embedding 模型的更新

反模式：一次部署后从不评估和更新 Embedding 模型。新的 Embeding 模型（如 BGE v1.5）在检索任务上有显著提升，应该定期评估和迁移。

---

## 6. API Key 依赖

- **BGE 等开源模型**：不需要 API Key，需要本地 GPU 或 CPU 运行
- **OpenAI Embeddings**：需要 OpenAI API Key
- **其他云服务**（Cohere, Google, 阿里云）：需要各自的 API Key

在 agent_platform 中，`src/embeddings/local_bge.py` 使用 BGE 模型，完全在本地运行，不需要任何 API Key，首次使用会自动从 HuggingFace 下载模型（约 100MB）。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **向量数据库** | Embedding 是向量数据库的输入数据 |
| **RAG** | Embedding 检索是 RAG 流水线的第一步 |
| **文档解析** | 解析后的文档需要 Embedding 才能被检索 |
| **Prompt Engineering** | Embedding 检索结果为 Prompt 提供上下文 |
| **Agent 系统** | Agent 可以通过 Embedding 搜索知识库 |

在 agent_platform 中，`src/embeddings/local_bge.py` 提供 Embedding 能力，`src/vectordb/chroma_store.py` 使用 Embedding 进行向量检索，`src/rag/` 依赖二者构建 RAG 流水线。

---

## 8. 验收清单

- [ ] 理解 Embedding 的基本原理和向量化的含义
- [ ] 掌握余弦相似度的计算和含义
- [ ] 理解归一化向量的作用
- [ ] 会用 BGE 模型进行本地 Embedding
- [ ] 了解 C-MTEB 榜单和模型选择
- [ ] 掌握 Batch Embedding 的实现
- [ ] 理解 Embedding 缓存的重要性
- [ ] 了解 BGE 和 OpenAI Embeddings 的差异
- [ ] 能实现简单的向量搜索
- [ ] 理解 Embedding 在 RAG 中的作用

---

## 9. 推荐学习资源

### 模型
- BGE on HuggingFace: https://huggingface.co/BAAI/bge-small-zh-v1.5
- Sentence-Transformers: https://www.sbert.net/
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- C-MTEB Leaderboard: https://github.com/FlagOpen/FlagEmbedding

### 官方文档
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings
- sentence-transformers 文档: https://www.sbert.net/docs/

### 论文
- "BGE: BAAI General Embedding" (2023)
- "Text Embeddings by Weakly-Supervised Contrastive Pre-training" (Li et al., 2023)
- "MTEB: Massive Text Embedding Benchmark" (Muennighoff et al., 2022)

### 项目代码参考
- `agent_platform/src/embeddings/local_bge.py` — BGE 本地 Embedding 封装
- `agent_platform/src/vectordb/chroma_store.py` — Chroma 向量库，依赖 Embedding
- `agent_platform/src/rag/retriever.py` — 检索器，使用 Embedding 搜索
