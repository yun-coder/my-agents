"""RAG 评估的最小离线示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class RagCase:
    """一条可重复执行的 RAG 黄金样本。"""

    question: str  # 用户问题。
    expected_keywords: tuple[str, ...]  # 答案依据中应覆盖的关键词。
    retrieved_contexts: tuple[str, ...]  # 检索器返回的上下文片段。
    answer: str  # Agent 最终生成的答案。
    citations: tuple[str, ...]  # 答案引用的来源标识。


def ratio(found: int, total: int) -> float:
    """将命中数量转换为 0 到 1 之间的分数。"""

    return round(found / total, 3) if total else 1.0


def evaluate(case: RagCase) -> dict[str, float]:
    """计算适合本地回归测试的确定性指标。"""

    contexts = " ".join(case.retrieved_contexts).lower()
    answer = case.answer.lower()
    keywords = [keyword.lower() for keyword in case.expected_keywords]
    return {
        "keyword_recall": ratio(sum(keyword in contexts for keyword in keywords), len(keywords)),
        "answer_coverage": ratio(sum(keyword in answer for keyword in keywords), len(keywords)),
        "citation_coverage": 1.0 if case.citations else 0.0,
    }


def main() -> None:
    case = RagCase(
        question="LangGraph 如何恢复中断后的工作流？",
        expected_keywords=("thread_id", "checkpointer", "resume"),
        retrieved_contexts=(
            "LangGraph uses a checkpointer and thread_id to persist graph state.",
            "Resume an interrupted graph with Command(resume=value).",
        ),
        answer="使用 checkpointer 保存状态，以 thread_id 找回线程，再通过 resume 恢复执行。",
        citations=("langgraph-persistence-docs",),
    )
    print(json.dumps({"case": asdict(case), "metrics": evaluate(case)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
