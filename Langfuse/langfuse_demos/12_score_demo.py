"""
演示 12: score（评分）。

score 是附加到 trace 或特定 observation 上的评估结果。Langfuse
支持数值型（NUMERIC）、布尔型（BOOLEAN）、类别型（CATEGORICAL）
和文本型评分。评分可用于用户反馈、自动评估、质量门禁和回归测试。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="scored-generation",                    # 被评分的 generation
        model="mock-gpt-4o-mini",
        input="退款窗口是多久？",
    ) as generation:
        generation.update(output="退款在 30 天内可用。")

        # 对当前 span（generation observation）进行评分
        langfuse.score_current_span(
            name="answer_relevance",                  # 评分名称
            value=0.97,                               # 分值
            data_type="NUMERIC",                      # 数据类型：数值型
            comment="直接回答了用户问题。",
            metadata={"evaluator": "mock-rule"},
        )

        # 对整个 trace 进行评分。常见场景是用户反馈。
        langfuse.score_current_trace(
            name="user_feedback",                     # 评分名称
            value=1.0,                                # 分值
            data_type="BOOLEAN",                      # 数据类型：布尔型
            comment="用户在 UI 中点击了赞。",
        )

    flush_and_print(langfuse, "score-demo")


if __name__ == "__main__":
    main()
