"""RAG 生成器：组装上下文 + Prompt + LLM 调用，生成带来源引用的回答。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..llm.client import get_llm_client
from .retriever import Retriever
from .reranker import LocalReranker


@dataclass
class RAGAnswer:
    """RAG 回答，包含答案文本和来源引用。"""

    answer: str
    sources: list[str] = field(default_factory=list)
    context_docs: list[str] = field(default_factory=list)


RAG_SYSTEM_PROMPT = """你是一个基于知识库的问答助手。严格遵守以下规则：
1. 只根据提供的资料回答问题，不要使用你自己的知识。
2. 如果资料不足以回答问题，明确说"根据现有资料无法回答"。
3. 回答时引用来源编号，例如 [来源1]、[来源2]。
4. 保持回答简洁、准确。
5. 不要编造任何不在资料中的信息。"""


class RAGGenerator:
    """RAG 生成器：检索 + (可选)重排序 + 生成回答。

    用法:
        generator = RAGGenerator(retriever)
        answer = generator.generate("什么是 RAG")
        print(answer.answer)
        print(answer.sources)
    """

    def __init__(
        self,
        retriever: Retriever,
        reranker: LocalReranker | None = None,
        *,
        top_k_retrieval: int = 10,
        top_n_rerank: int = 5,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._top_k = top_k_retrieval
        self._top_n = top_n_rerank
        self._llm = get_llm_client()

    def retrieve(self, query: str) -> list[dict[str, Any]]:
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
            {
                "role": "user",
                "content": f"<资料>\n{context}\n</资料>\n\n问题：{query}",
            },
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
            {
                "role": "user",
                "content": f"<资料>\n{context}\n</资料>\n\n问题：{query}",
            },
        ]
        yield from self._llm.chat_stream(messages)
