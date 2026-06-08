"""
演示 06: chain（链/管道）类型 observation。

chain observation 用于确定性或半确定性的处理管道，
将多个步骤串联起来，例如 提示构建 -> 检索 -> 生成。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="chain",                              # observation 类型：chain
        name="rag-answer-chain",                      # 名称：RAG 回答链
        input={"question": "退款窗口是多久？"},          # 输入问题
        metadata={"chain": "simple-rag"},             # 链标识
        version="rag-chain-0.1.0",                    # 版本号
    ) as chain:
        # 链中的子步骤：格式化 prompt
        with langfuse.start_as_current_observation(
            as_type="span",
            name="format-prompt",                     # 格式化prompt步骤
            input={"template": "policy-answer-v1"},   # 使用的模板
        ) as span:
            span.update(output={"prompt_chars": 312})  # 输出：prompt 字符数

        # 更新链的最终输出
        chain.update(output={"answer": "退款在 30 天内可用。"})

    flush_and_print(langfuse, "chain-observation-demo")


if __name__ == "__main__":
    main()
