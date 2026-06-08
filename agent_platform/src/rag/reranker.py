"""本地 BGE Reranker：使用 FlagEmbedding 本地重排序模型，无需外部 Key。

重排序（Reranking）是 RAG 质量的关键环节：
1. 召回阶段：向量检索返回 top_k=20 候选文档
2. 精排阶段：Reranker 重新打分，取 top_n=5 最相关的送入 LLM

"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class LocalReranker:
    """使用本地 BGE Reranker 模型进行重排序。

    首次运行会自动下载模型（约 1GB），之后使用本地缓存。

    用法:
        reranker = LocalReranker()
        scored = reranker.rerank("什么是RAG", [doc1, doc2, doc3], top_n=3)
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cpu",
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._model = None

    @property
    def _reranker(self):
        if self._model is None:
            from FlagEmbedding import FlagReranker

            logger.info("加载本地 Reranker 模型：%s（首次需下载约1GB）", self._model_name)
            self._model = FlagReranker(
                self._model_name,
                use_fp16=self._device != "cpu",
                device=self._device,
            )
        return self._model

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        *,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """对候选文档重新排序，返回 top_n 个最相关的结果。

        Args:
            query: 用户问题
            documents: 候选文档列表，每项需包含 "text" key
            top_n: 返回的最大文档数

        Returns:
            按相关性降序排列的文档列表
        """
        if not documents:
            return []

        pairs = [[query, doc["text"]] for doc in documents]
        scores = self._reranker.compute_score(pairs)

        if isinstance(scores, float):
            scores = [scores]

        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_n]]


@lru_cache(maxsize=1)
def get_reranker(
    model_name: str = "BAAI/bge-reranker-base",
    device: str = "cpu",
) -> LocalReranker:
    """全局单例 Reranker。"""
    return LocalReranker(model_name, device)
