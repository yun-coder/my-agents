"""用离线样本演示 DSPy 式候选策略优化。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class Example:
    """一条带标准答案的优化样本。"""

    text: str  # 待分类文本。
    expected: str  # 标准分类结果。


@dataclass(frozen=True)
class Strategy:
    """可被评分和选择的分类策略。"""

    name: str  # 策略名称。
    billing_keywords: tuple[str, ...]  # 命中后归入 billing 的关键词。


def classify(text: str, strategy: Strategy) -> str:
    normalized = text.lower()
    return "billing" if any(keyword in normalized for keyword in strategy.billing_keywords) else "general"


def score(strategy: Strategy, examples: tuple[Example, ...]) -> float:
    hits = sum(classify(item.text, strategy) == item.expected for item in examples)
    return round(hits / len(examples), 3)


def main() -> None:
    examples = (Example("申请退款", "billing"), Example("invoice error", "billing"), Example("如何修改昵称", "general"))
    strategies = (Strategy("basic", ("退款",)), Strategy("expanded", ("退款", "invoice")))
    ranked = sorted(({"strategy": asdict(item), "score": score(item, examples)} for item in strategies), key=lambda item: item["score"], reverse=True)
    print(json.dumps(ranked, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
