"""离线可运行：用 LangChain Runnable 组合文本处理步骤。"""

from __future__ import annotations


def main() -> None:
    try:
        from langchain_core.runnables import RunnableLambda
    except ImportError:
        print("缺少 langchain-core，请按阶段 README 安装依赖。")
        return

    # 第一步：统一文本格式。RunnableLambda 把普通函数包装成可组合步骤。
    normalize = RunnableLambda(lambda text: text.strip().lower())
    # 第二步：产生结构化结果。真实项目中可替换为模型、Retriever 或 Tool。
    classify = RunnableLambda(
        lambda text: {
            "text": text,
            "contains_rag": "rag" in text,
            "length": len(text),
        }
    )
    # `|` 将两个 Runnable 串成一条顺序执行的管道。
    chain = normalize | classify
    print(chain.invoke("  RAG 需要检索外部知识。  "))


if __name__ == "__main__":
    main()
