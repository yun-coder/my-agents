# 第23章 重排序 Reranker：精排提升 RAG 质量

> 重排序（Reranking）是 RAG 系统的关键质量提升环节。在向量召回返回候选文档后，Reranker 通过更精确的交叉编码器重新评分，确保送入 LLM 的文档是真正最相关的。本章深入分析 Bi-encoder vs Cross-encoder、BGE Reranker、Cohere Rerank API 以及两阶段检索策略。

---

## 1. 概念概述

### 1.1 为什么要重排序

在 RAG 系统中，纯向量检索虽然速度快，但存在以下问题：

1. **语义鸿沟**：向量相似度高不一定代表问题-文档的相关性高
2. **召回噪声**：Top-K 结果中通常混入 30%-50% 的无关文档
3. **LLM 上下文限制**：Token 预算有限，必须筛选最相关的文档送入 LLM

重排序在召回和生成之间增加精排步骤，显著提升最终回答质量。实测数据表明：加入 Reranker 后 RAG 回答准确率提升 15%-30%。

### 1.2 两阶段检索架构

```
用户问题
    │
    ▼
┌─────────────────────┐
│  阶段一：向量召回    │  Bi-encoder（快速，百毫秒级）
│  top_k = 20-50      │  召回候选文档
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  阶段二：重排序      │  Cross-encoder（慢，但精度高）
│  top_n = 3-5        │  对候选重新打分排序
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LLM 生成回答        │  只送入最相关的 top_n 文档
└─────────────────────┘
```

### 1.3 何时需要重排序

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 知识库 < 100 条 | 无需 Reranker | 直接全量检索即可 |
| 知识库 100-10K 条 | 建议使用 | 召回噪声开始明显 |
| 知识库 > 10K 条 | 强烈推荐 | 召回噪声严重，Reranker 收益显著 |
| 高精度场景（医疗/法律） | 必须使用 | 错误答案代价高 |
| 实时对话（< 500ms） | 需权衡 | Reranker 增加 100-500ms 延迟 |
| 离线批量处理 | 推荐使用 | 无延迟压力，追求精度 |

---

## 2. 核心原理

### 2.1 Bi-encoder vs Cross-encoder

**Bi-encoder（双编码器）：**
- 将问题和文档分别编码为独立向量
- 通过余弦相似度计算相关性
- 速度快（可预计算文档向量）
- 精度有限（问题和文档独立编码，缺乏交互）

```
问题 ──→ Encoder ──→ 向量 Q
文档 ──→ Encoder ──→ 向量 D
相关性 = cosine(Q, D)
```

**Cross-encoder（交叉编码器）：**
- 将问题和文档拼接后一起编码
- 直接输出相关性分数
- 精度高（问题和文档深度交互）
- 速度慢（每对都要单独计算，无法预计算）

```
[问题 + 文档] ──→ Encoder ──→ 相关性分数
```

关键区别：

| 维度 | Bi-encoder | Cross-encoder |
|------|-----------|---------------|
| 计算方式 | 独立编码，向量相似度 | 联合编码，直接打分 |
| 推理速度 | 快（可缓存文档向量） | 慢（每对重新计算） |
| 精度 | 中 | 高 |
| 适用阶段 | 召回（阶段一） | 精排（阶段二） |
| 预计算 | 文档向量可离线计算 | 无法预计算 |
| 代表模型 | bge-small-zh, text-embedding-ada | bge-reranker-base, Cohere Rerank |

### 2.2 BGE Reranker 本地部署

BGE Reranker 是由 BAAI（北京智源人工智能研究院）开源的 Cross-encoder 重排序模型，支持本地部署，无需 API Key：

```python
"""本地 BGE Reranker 重排序实现。

参考项目源码：agent_platform/src/rag/reranker.py
"""

from __future__ import annotations

import logging
from typing import Any

from FlagEmbedding import FlagReranker

logger = logging.getLogger(__name__)


class LocalReranker:
    """基于 BGE 的本地重排序器。

    用法:
        reranker = LocalReranker(model_name="BAAI/bge-reranker-base")
        results = reranker.rerank(
            query="什么是RAG？",
            documents=[
                {"id": "doc1", "text": "RAG是检索增强生成..."},
                {"id": "doc2", "text": "LangGraph是状态图框架..."},
                {"id": "doc3", "text": "RAG的核心是召回+生成..."},
            ],
            top_n=2,
        )
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cpu",
        use_fp16: bool = False,
    ):
        self._model_name = model_name
        self._device = device
        self._use_fp16 = use_fp16 and device != "cpu"
        self._model: FlagReranker | None = None

    @property
    def _reranker(self) -> FlagReranker:
        if self._model is None:
            logger.info(
                "加载 Reranker 模型：%s（首次需下载约 1GB）",
                self._model_name,
            )
            self._model = FlagReranker(
                self._model_name,
                use_fp16=self._use_fp16,
                device=self._device,
            )
        return self._model

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        *,
        top_n: int = 5,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """对候选文档重新排序。

        Args:
            query: 用户问题
            documents: 候选文档列表，每项需包含 "text" 字段
            top_n: 返回的最大文档数
            min_score: 最低分数阈值

        Returns:
            按相关性降序排列的文档列表（仅返回分数 >= min_score 的）
        """
        if not documents:
            return []

        # 构建 query-doc 对
        pairs = [[query, doc["text"]] for doc in documents]

        # 批量计算分数
        scores = self._reranker.compute_score(pairs)

        # 兼容单结果返回
        if isinstance(scores, float):
            scores = [scores]

        # 合并并排序
        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        # 过滤低分结果
        filtered = [(doc, score) for doc, score in scored if score >= min_score]

        logger.info(
            "Reranker: %d 候选 -> %d 返回, 最高分 %.4f, 最低分 %.4f",
            len(documents),
            len(filtered),
            filtered[0][1] if filtered else 0,
            filtered[-1][1] if filtered else 0,
        )

        return [doc for doc, _ in filtered[:top_n]]

    def rerank_with_scores(
        self,
        query: str,
        documents: list[dict[str, Any]],
        *,
        top_n: int = 5,
    ) -> list[tuple[dict[str, Any], float]]:
        """返回带分数的重排序结果（用于调试和分析）。"""
        if not documents:
            return []

        pairs = [[query, doc["text"]] for doc in documents]
        scores = self._reranker.compute_score(pairs)

        if isinstance(scores, float):
            scores = [scores]

        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:top_n]
```

### 2.3 Cohere Rerank API

Cohere 提供云端的 Rerank API，使用专有的 Cross-encoder 模型，无需本地 GPU：

```python
"""Cohere Rerank API 调用。"""

from __future__ import annotations

import logging
from typing import Any

import cohere

logger = logging.getLogger(__name__)


class CohereReranker:
    """基于 Cohere API 的云端重排序器。

    用法:
        reranker = CohereReranker(api_key="cohere-api-key")
        results = reranker.rerank("问题", documents, top_n=3)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "rerank-v3.5",
    ):
        self._client = cohere.Client(api_key=api_key)
        self._model = model

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        *,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """调用 Cohere Rerank API。"""
        if not documents:
            return []

        texts = [doc["text"] for doc in documents]

        response = self._client.rerank(
            model=self._model,
            query=query,
            documents=texts,
            top_n=top_n,
        )

        # 按照返回的索引映射回原始文档
        results = []
        for result in response.results:
            doc = documents[result.index]
            doc["relevance_score"] = result.relevance_score
            results.append(doc)

        return results
```

### 2.4 两阶段检索完整实现

将向量召回和 Reranker 精排组合为完整的检索流水线：

```python
"""两阶段检索：向量召回 + Reranker 精排。"""

from __future__ import annotations

import logging
from typing import Any

from ...vectordb.chroma_store import ChromaVectorStore
from ...embeddings.local_bge import LocalBgeEmbedding

logger = logging.getLogger(__name__)


class TwoStageRetriever:
    """两阶段检索器。

    阶段一：向量召回（Bi-encoder，快速广泛）
    阶段二：重排序精排（Cross-encoder，精准筛选）

    用法:
        retriever = TwoStageRetriever(
            vector_store=store,
            reranker=reranker,
        )
        results = retriever.search("什么是RAG？", top_k=5)
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        reranker: Any | None = None,  # LocalReranker 或 CohereReranker
        *,
        recall_k: int = 20,  # 召回阶段取 top_k
        final_n: int = 5,    # 精排阶段保留 top_n
    ):
        self._store = vector_store
        self._reranker = reranker
        self._recall_k = recall_k
        self._final_n = final_n

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """执行两阶段检索。

        Args:
            query: 用户问题
            top_k: 最终返回数量（覆盖默认值）
            where: 过滤条件

        Returns:
            重排序后的文档列表
        """
        final_n = top_k or self._final_n

        # 阶段一：向量召回
        candidates = self._store.search(
            query,
            top_k=self._recall_k,
            where=where,
        )

        if not candidates:
            return []

        if not self._reranker:
            # 没有 Reranker，直接返回前 final_n 个
            return candidates[:final_n]

        # 阶段二：重排序精排
        reranked = self._reranker.rerank(
            query,
            candidates,
            top_n=final_n,
        )

        return reranked

    def search_with_analysis(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """带分析信息的检索（用于调试）。"""
        candidates = self._store.search(query, top_k=self._recall_k)

        result = {
            "query": query,
            "recall_count": len(candidates),
            "recall_results": candidates[:self._recall_k],
            "final_results": [],
            "reranker_used": self._reranker is not None,
        }

        if candidates and self._reranker:
            scored = self._reranker.rerank_with_scores(query, candidates, top_n=top_k)
            result["final_results"] = [
                {"doc": doc, "score": score} for doc, score in scored
            ]
        elif candidates:
            result["final_results"] = candidates[:top_k]

        return result
```

---

## 3. 实战指南

### 3.1 完整的 RAG 检索流水线

以下代码将 Embedding、向量检索、Reranker 和 LLM 生成组合为完整流水线：

```python
"""完整 RAG 流水线：召回 -> 重排序 -> 生成。"""

from __future__ import annotations

import logging
from typing import Any

from ...embeddings.local_bge import LocalBgeEmbedding
from ...vectordb.chroma_store import ChromaVectorStore
from ...llm.client import get_llm_client

logger = logging.getLogger(__name__)


class RAGPipeline:
    """完整的 RAG 流水线。

    处理流程：
    1. Embedding 编码查询
    2. 向量数据库召回 top_k=20
    3. Reranker 精排取 top_n=5
    4. LLM 基于精排结果生成回答
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        reranker: Any | None = None,
        *,
        recall_k: int = 20,
        final_n: int = 5,
    ):
        self._store = vector_store
        self._reranker = reranker
        self._recall_k = recall_k
        self._final_n = final_n
        self._llm = get_llm_client()

    def query(self, question: str) -> dict[str, Any]:
        """执行完整的 RAG 查询。"""
        # 阶段一：向量召回
        candidates = self._store.search(
            question,
            top_k=self._recall_k,
        )
        logger.info("召回阶段：%d 个候选文档", len(candidates))

        # 阶段二：重排序（如果配置了 Reranker）
        if self._reranker and candidates:
            docs = self._reranker.rerank(
                question,
                candidates,
                top_n=self._final_n,
            )
            logger.info("精排阶段：从 %d 候选中选出 %d 个", len(candidates), len(docs))
        else:
            docs = candidates[:self._final_n]

        # 构建上下文
        context = self._format_context(docs)

        # 阶段三：LLM 生成
        answer = self._llm.chat([
            {
                "role": "system",
                "content": f"基于以下资料回答问题：\n\n{context}",
            },
            {"role": "user", "content": question},
        ])

        return {
            "answer": answer,
            "sources": [d.get("metadata", {}).get("source", d["id"]) for d in docs],
            "document_count": len(docs),
            "reranker_used": self._reranker is not None,
        }

    def _format_context(self, documents: list[dict]) -> str:
        """将文档格式化为上下文。"""
        parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get("metadata", {}).get("source", "未知")
            parts.append(f"[文档{i} - {source}]\n{doc['text']}")
        return "\n\n".join(parts)
```

### 3.2 混合检索 + Reranker

结合关键词检索（BM25）和向量检索，再经过 Reranker 精排：

```python
class HybridRetriever:
    """混合检索器：BM25 + 向量 + Reranker。"""

    def __init__(self, vector_store, reranker=None):
        self._vector_store = vector_store
        self._reranker = reranker

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """混合检索 + 重排序。"""
        # 向量检索
        vector_results = self._vector_store.search(query, top_k=top_k * 2)

        # BM25 关键词检索（简化实现）
        bm25_results = self._bm25_search(query, top_k=top_k * 2)

        # 合并去重
        seen_ids = set()
        merged = []
        for doc in vector_results + bm25_results:
            if doc["id"] not in seen_ids:
                seen_ids.add(doc["id"])
                merged.append(doc)

        # 重排序
        if self._reranker and merged:
            return self._reranker.rerank(query, merged, top_n=top_k)

        return merged[:top_k]

    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        """简化的 BM25 检索。"""
        # 实际项目中应使用 whoosh 或 elasticsearch
        return []
```

### 3.3 性能基准测试

评估 Reranker 在不同召回数量下的效果和性能：

```python
"""Reranker 性能基准测试。"""

from __future__ import annotations

import time
from typing import Any


def benchmark_reranker(
    reranker: Any,
    queries: list[str],
    documents: list[dict[str, Any]],
    recall_sizes: list[int] = [10, 20, 50],
    top_n: int = 5,
) -> dict[str, Any]:
    """对 Reranker 进行性能基准测试。

    Returns:
        包含延迟、召回率和精排率的数据
    """
    results = {}

    for recall_k in recall_sizes:
        latencies = []
        candidates = documents[:recall_k]

        for query in queries:
            start = time.perf_counter()
            reranker.rerank(query, candidates, top_n=top_n)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)

        avg_latency = sum(latencies) / len(latencies)
        throughput = 1.0 / avg_latency if avg_latency > 0 else 0

        results[recall_k] = {
            "avg_latency_ms": round(avg_latency * 1000, 2),
            "throughput_qps": round(throughput, 2),
            "candidates": recall_k,
            "final": top_n,
            "compression_ratio": f"{recall_k}:{top_n}",
        }

    return results
```

---

## 4. 最佳实践

1. **召回数量与精度平衡**：建议召回 20 个候选，精排保留 3-5 个。召回太少可能漏掉相关文档，太多增加 Reranker 延迟。

2. **Reranker 模型选择**：本地部署用 BAAI/bge-reranker-base（精度高）或 bge-reranker-small（速度快）；云端用 Cohere Rerank v3.5（无需 GPU）。

3. **批处理优化**：Reranker 支持批量计算，尽量一次传入所有候选文档，避免多次调用。

4. **混合检索**：向量检索 + 关键词检索（BM25/Elasticsearch）互补，Reranker 在融合结果上精排。

5. **分数阈值**：设置最低分数阈值（如 0.1），低于阈值的文档即使排名靠前也舍弃，避免向 LLM 传递噪声。

6. **缓存策略**：相同查询的 Rerank 结果可短期缓存，减少重复计算。

7. **异步调用**：Reranker 推理是 CPU/GPU 密集型操作，使用线程池或异步调用避免阻塞主线程。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| 过排序 | 将不太相关的文档排到前面，丢失了原本正确的召回结果 | 调整召回数量，提高 Reranker 模型质量 |
| Reranker 延迟过高 | 500 个候选全部送 Reranker，耗时数秒 | 限制送入 Reranker 的候选数量（建议 <= 50） |
| 忽略分数分布 | 所有文档分数接近，但强制返回 top_n | 设置 min_score 阈值，宁可少返回也不返回低质量 |
| 文档截断 | 长文档被截断，丢失关键信息 | Reranker 有最大输入长度（通常 512 tokens），截断要注意 |
| API 费用失控 | 高频调用 Cohere Rerank API 产生高额费用 | 本地部署 BGE Reranker 消除 API 费用 |
| 模型版本不一致 | 开发和生产环境使用了不同 Reranker 模型 | 锁定模型版本，记录在配置中 |
| 缺少 A/B 测试 | 上线 Reranker 后没有对比效果 | 在回复中标记是否使用了 Reranker，便于效果评估 |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| BGE Reranker（本地） | 否 | 本地模型推理，无需 Key，需要 GPU（可选） |
| Cohere Rerank API | 是 | 需要 Cohere API Key，按调用量计费 |
| 向量检索（召回阶段） | 否 | 依赖 Embedding 模型，本地 BGE 无需 Key |
| LLM 生成（最终回答） | 是 | 最终回答需要 LLM API Key |

**成本对比：**
- BGE Reranker 本地部署：零 API 成本，需 GPU 硬件
- Cohere Rerank API：按请求计费（约 $0.001/次），无需 GPU

---

## 7. 技术关系

```
用户问题
    │
    ▼
┌──────────────────────┐
│  Embedding 编码       │ ←── LocalBgeEmbedding (embeddings/local_bge.py)
│  Bi-encoder           │     将问题转为向量
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  向量召回             │ ←── ChromaVectorStore (vectordb/chroma_store.py)
│  top_k = 20 候选文档   │     余弦相似度检索
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Reranker 精排        │ ←── LocalReranker (rag/reranker.py)
│  Cross-encoder        │     或 CohereReranker
│  top_n = 5 最相关文档  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LLM 生成回答          │ ←── LLM Client (llm/client.py)
│  基于精排结果回答问题   │
└──────────────────────┘
```

---

## 8. 验收清单

- [ ] 理解 Bi-encoder 和 Cross-encoder 的核心区别
- [ ] 掌握两阶段检索架构的设计原理
- [ ] 学会部署和使用本地 BGE Reranker
- [ ] 学会调用 Cohere Rerank API
- [ ] 掌握召回数量与精排数量的调优策略
- [ ] 理解 Reranker 的分数含义和阈值设置
- [ ] 能够将 Reranker 集成到现有 RAG 流水线
- [ ] 理解 Reranker 的性能特征和资源消耗
- [ ] 判断哪些场景需要 Reranker、哪些不需要
- [ ] 掌握 Reranker 效果的评估方法

---

## 9. 学习资源

- BGE Reranker 仓库：https://github.com/FlagOpen/FlagEmbedding
- BGE Reranker 模型：https://huggingface.co/BAAI/bge-reranker-base
- Cohere Rerank API：https://docs.cohere.com/reference/rerank
- 两阶段检索论文：https://arxiv.org/abs/2304.09542
- RAG 评估框架：https://docs.ragas.io/
- 项目源码参考：agent_platform/src/rag/reranker.py
- 嵌入式模型对比：https://huggingface.co/spaces/mteb/leaderboard
- Cross-encoder 教程：https://www.sbert.net/examples/applications/cross-encoder/README.html
