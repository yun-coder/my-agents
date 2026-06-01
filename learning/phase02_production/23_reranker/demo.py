"""离线可运行：模拟召回后按关键词覆盖率精排。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    # document_id：原始文档标识。
    document_id: str
    # text：候选文本。
    text: str
    # recall_score：第一阶段向量召回分数。
    recall_score: float


def rerank(query: str, candidates: list[Candidate]) -> list[tuple[float, Candidate]]:
    keywords = set(query.lower().split())
    scored = []
    for candidate in candidates:
        overlap = sum(keyword in candidate.text.lower() for keyword in keywords)
        # 教学公式：精排分数综合关键词覆盖与原始召回分数。
        score = overlap * 10 + candidate.recall_score
        scored.append((score, candidate))
    return sorted(scored, key=lambda item: item[0], reverse=True)


def main() -> None:
    candidates = [
        Candidate("doc-1", "RAG 使用 embedding 召回文档。", 0.91),
        Candidate("doc-2", "RAG 可以在召回后使用 reranker 精排。", 0.82),
    ]
    print(rerank("RAG reranker", candidates))


if __name__ == "__main__":
    main()
