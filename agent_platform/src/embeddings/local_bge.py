"""本地 BGE Embedding 模型：使用 sentence-transformers，无需 API Key。

首次运行会自动从 HuggingFace 下载模型（约 100MB），之后由本地缓存。
支持中文和英文，384 维向量（bge-small）。
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Embedding 提供者协议，方便切换不同实现。"""

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...

    @property
    def dimension(self) -> int:
        ...


class BGEBatchEmbedding:
    """批量模式的 BGE Embedding，适合一次性处理大量文档。

    用法:
        emb = BGEBatchEmbedding("BAAI/bge-small-zh-v1.5")
        vectors = emb.embed(["文档1", "文档2"])
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu") -> None:
        self._model_name = model_name
        self._device = device
        self._model = None

    @property
    def _encoder(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("加载本地 Embedding 模型：%s（首次运行需下载约100MB）", self._model_name)
            self._model = SentenceTransformer(self._model_name, device=self._device)
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
        """单条查询向量化。BGE 模型会自动添加 instruction 前缀。"""
        return self.embed([text])[0]


@lru_cache(maxsize=1)
def get_embedding_provider(
    model_name: str = "BAAI/bge-small-zh-v1.5",
    device: str = "cpu",
) -> BGEBatchEmbedding:
    """全局单例 Embedding 提供者。"""
    return BGEBatchEmbedding(model_name, device)
