"""
演示 07: retriever（检索器）类型 observation。

retriever observation 用于搜索/RAG 检索步骤。记录查询内容、
过滤条件、检索到的文档ID、相关性分数和简短摘要，
有助于调试是否给模型提供了正确的上下文。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="retriever",                          # observation 类型：retriever
        name="policy-vector-search",                  # 名称：策略向量搜索
        input={"query": "refund window", "top_k": 3, "filters": {"locale": "en-US"}},  # 查询和过滤
        metadata={"index": "help-center-vectors"},    # 向量索引名称
    ) as retriever:
        # 输出检索到的文档列表，包含文档ID、分数和片段
        retriever.update(
            output=[
                {"doc_id": "policy_refunds", "score": 0.94, "snippet": "退款在30天内可用。"},
                {"doc_id": "policy_exchanges", "score": 0.72, "snippet": "换货遵循相同的窗口期。"},
            ]
        )

    flush_and_print(langfuse, "retriever-observation-demo")


if __name__ == "__main__":
    main()
