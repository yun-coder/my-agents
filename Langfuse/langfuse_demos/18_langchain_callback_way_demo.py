"""
Demo: LangChain callback integration.

Langfuse listens to LangChain/LangGraph runs via CallbackHandler. The handler
captures chains, LLM calls, tools, retrievers, latency, and errors produced by
LangChain's callback system.

Required for a real call:
    pip install langchain-openai langchain-core langfuse
    set OPENAI_API_KEY=...
"""

from __future__ import annotations

import os

from langfuse import propagate_attributes

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="langchain-callback-demo-skipped",
            input={"reason": "OPENAI_API_KEY is not set"},
            metadata={"integration": "langfuse.langchain.CallbackHandler"},
        ) as span:
            span.update(output={"next_step": "Install LangChain packages and set OPENAI_API_KEY."})
        flush_and_print(langfuse, "langchain-callback-way-demo-skipped")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    prompt = ChatPromptTemplate.from_template("Answer briefly: {question}")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    chain = prompt | llm

    with propagate_attributes(
        trace_name="langchain-callback-demo",
        user_id="user_langchain_001",
        session_id="session_langchain_001",
        tags=["demo", "langchain"],
    ):
        result = chain.invoke(
            {"question": "What can Langfuse observe in LangChain?"},
            config={
                "callbacks": [handler],
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
