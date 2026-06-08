"""
演示 03: generation（LLM生成）类型 observation。

generation observation 用于 LLM 调用。Langfuse 可以展示模型名称、
模型参数、prompt/消息、补全输出、token 用量和费用。
本演示使用模拟的模型回复，无需 LLM API 密钥即可运行。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 构建消息列表（system 提示 + 用户问题）
    messages = [
        {"role": "system", "content": "请用一句简洁的话回答。"},
        {"role": "user", "content": "Langfuse 追踪什么？"},
    ]

    with langfuse.start_as_current_observation(
        as_type="generation",                         # observation 类型：generation
        name="mock-chat-completion",                  # 名称
        model="mock-gpt-4o-mini",                     # 模型名称
        model_parameters={"temperature": 0.2, "max_tokens": 64},  # 模型参数
        input=messages,                               # 输入消息
    ) as generation:
        output = "Langfuse 追踪 LLM 应用的步骤、模型调用、元数据和评分。"

        # usage_details（用量详情）和 cost_details（费用详情）专门用于
        # generation observation。生产环境中应从模型返回的响应中复制这些值。
        generation.update(
            output=output,
            usage_details={"input": 24, "output": 15, "total": 39},  # token 用量
            cost_details={"input": 0.000012, "output": 0.000009, "total": 0.000021},  # 费用
            metadata={"provider": "mock", "finish_reason": "stop"},  # 提供方和结束原因
        )

    flush_and_print(langfuse, "generation-observation-demo")


if __name__ == "__main__":
    main()
