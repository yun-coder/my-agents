"""RAG 检索器：基础语义检索 + 混合检索（可选关键词增强）。"""

from __future__ import annotations

from typing import Any

from ..vectordb.chroma_store import ChromaVectorStore


class Retriever:
    """语义检索器：封装 Chroma 向量检索。

    用法:
        retriever = Retriever(vector_store)
        results = retriever.search("什么是 LangGraph", top_k=5)
    """

    def __init__(self, vector_store: ChromaVectorStore) -> None:
        self._store = vector_store

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """执行语义检索，返回 top_k 个最相似文档。"""
        from ..observability import traced_operation
        with traced_operation(
            "rag.retrieval",
            input={"query": query, "top_k": top_k},
        ) as op:
            hits = self._store.search(query, top_k=top_k, where=where)
            op.update(output={"hits": len(hits)})
            return hits

    def format_context(self, results: list[dict[str, Any]]) -> str:
        """将检索结果格式化为 LLM 可用的上下文文本。"""
        if not results:
            return ""
        parts: list[str] = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", r["id"])
            parts.append(f"[来源{i}: {source}]\n{r['text']}")
        return "\n\n".join(parts)

    def format_sources(self, results: list[dict[str, Any]]) -> list[str]:
        """提取检索结果的来源列表。"""
        seen: set[str] = set()
        sources: list[str] = []
        for r in results:
            source = r.get("metadata", {}).get("source", r["id"])
            base = source.split("#")[0]
            if base not in seen:
                seen.add(base)
                sources.append(base)
        return sources
