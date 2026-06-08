"""Chroma 向量数据库封装：本地持久化，无需外部 Key。

功能：
- 创建/加载集合
- 批量写入文档向量
- 语义检索（返回 top_k）
- 带元数据过滤的检索
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..embeddings.local_bge import EmbeddingProvider, get_embedding_provider
from ..parsing.document import TextChunk

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Chroma 向量存储封装。

    用法:
        store = ChromaVectorStore("./data/chroma")
        store.add_documents(chunks)  # 向量化并写入
        results = store.search("什么是 RAG", top_k=5)
    """

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        collection_name: str = "knowledge_base",
        embedding: EmbeddingProvider | None = None,
    ) -> None:
        import chromadb
        from chromadb.config import Settings

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

    @property
    def count(self) -> int:
        return self._collection.count()

    @property
    def embedding_dimension(self) -> int:
        return self._embedding.dimension

    def add_documents(
        self,
        chunks: list[TextChunk],
        *,
        batch_size: int = 50,
    ) -> None:
        """将文本分块向量化后写入 Chroma。

        对于大量文档，分批处理以减少内存使用。
        """
        total = len(chunks)
        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            ids = [c.source for c in batch]
            metadatas = [
                {
                    "source": c.source,
                    "chunk_index": c.chunk_index,
                    **c.metadata,
                }
                for c in batch
            ]

            embeddings = self._embedding.embed(texts)
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            logger.info(
                "写入向量：%d/%d (%.0f%%)", min(i + batch_size, total), total,
                min(i + batch_size, total) / total * 100,
            )

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """语义检索：返回 top_k 个最相似的文档。"""
        query_embedding = self._embedding.embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        formatted: list[dict[str, Any]] = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append(
                    {
                        "id": doc_id,
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                )
        return formatted

    def delete_collection(self) -> None:
        self._client.delete_collection(self._collection_name)
        logger.info("已删除集合：%s", self._collection_name)
