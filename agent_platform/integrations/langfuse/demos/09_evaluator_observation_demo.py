"""
演示 09: evaluator（评估器）类型 observation。

evaluator observation 用于 LLM-as-a-judge（LLM 当裁判）、启发式检查
或离线评估步骤。将 evaluator observation 与评分（score）配合使用，
结果将出现在 Langfuse 的评估和分析视图中。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="evaluator",                          # observation 类型：evaluator
        name="answer-relevance-evaluator",             # 名称：答案相关性评估器
        input={
            "question": "退款窗口是多久？",
            "answer": "退款在 30 天内可用。",
        },
        metadata={"evaluator": "heuristic-keyword-match"},  # 评估方法：启发式关键词匹配
        version="evaluator-0.2.0",                     # 版本号
    ) as evaluator:
        relevance = 0.98                               # 相关性分数
        evaluator.update(output={"relevance": relevance, "reason": "答案直接说明了窗口期。"})

        # score 方法将评分附加到 observation 上。
        # 此评分属于 evaluator observation，可用于筛选和对比。
        evaluator.score(
            name="answer_relevance",                   # 评分名称
            value=relevance,                           # 评分值
            data_type="NUMERIC",                       # 数据类型：数值型
            comment="模拟评估器给出的高相关性评分。",
        )

    flush_and_print(langfuse, "evaluator-observation-demo")


if __name__ == "__main__":
    main()
