"""
演示 18: LangChain 回调集成方式。

Langfuse 通过 CallbackHandler 监听 LangChain/LangGraph 的运行。
该 handler 捕获 LangChain 回调系统产生的 chain、LLM 调用、
工具调用、检索器、延迟和错误信息。

实际调用所需依赖：
    pip install langchain-openai langchain-core langfuse
    设置环境变量 OPENAI_API_KEY=...
"""

from __future__ import annotations

import os

from langfuse import propagate_attributes

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 未设置 API Key 时跳过实际调用
    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="langchain-callback-demo-skipped",
            input={"reason": "OPENAI_API_KEY 未设置"},
            metadata={"integration": "langfuse.langchain.CallbackHandler"},
        ) as span:
            span.update(output={"next_step": "安装 LangChain 相关包并设置 OPENAI_API_KEY。"})
        flush_and_print(langfuse, "langchain-callback-way-demo-skipped")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langfuse.langchain import CallbackHandler

    # 创建 Langfuse 回调处理器
    handler = CallbackHandler()
    prompt = ChatPromptTemplate.from_template("简要回答: {question}")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    chain = prompt | llm                              # 使用 LCEL 构建链

    # propagate_attributes 将 trace 属性注入 LangChain 回调
    with propagate_attributes(
        trace_name="langchain-callback-demo",
        user_id="user_langchain_001",
        session_id="session_langchain_001",
        tags=["demo", "langchain"],
    ):
        # invoke 时传入 callbacks 配置，Langfuse 自动捕获所有步骤
        result = chain.invoke(
            {"question": "Langfuse 在 LangChain 中能观测到什么？"},
            config={
                "callbacks": [handler],                # 注册 Langfuse 回调
                "metadata": {
                    "langfuse_user_id": "user_langchain_001",
                    "langfuse_session_id": "session_langchain_001",
                    "langfuse_tags": ["demo", "langchain", "metadata-route"],
                },
            },
        )
        print(result.content)

    flush_and_print(langfuse, "langchain-callback-way-demo")


if __name__ == "__main__":
    main()
