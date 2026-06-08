"""
演示 08: embedding（嵌入向量）类型 observation。

embedding observation 用于将文本/图像转换为向量的调用。
追踪模型、输入数量、向量维度、token 用量和批处理元数据。
除非确实需要调试，否则不要存储巨大的原始向量。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 待向量化的文档列表
    documents = [
        "退款在 30 天内可用。",
        "可以从账单页面下载发票。",
    ]

    with langfuse.start_as_current_observation(
        as_type="embedding",                          # observation 类型：embedding
        name="embed-help-center-documents",            # 名称：帮助中心文档向量化
        model="mock-text-embedding-3-small",           # 模型名称
        input=documents,                               # 输入文档
        metadata={"batch_size": len(documents), "dimensions": 1536},  # 批大小和向量维度
    ) as embedding:
        embedding.update(
            output={"vector_count": len(documents), "stored_vector_preview": "[已省略]"},  # 输出概要
            usage_details={"input": 21, "total": 21},  # token 用量
        )

    flush_and_print(langfuse, "embedding-observation-demo")


if __name__ == "__main__":
    main()
