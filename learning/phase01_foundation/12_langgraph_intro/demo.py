"""离线可运行：LangGraph 条件分支。"""

from __future__ import annotations

from typing import Literal, TypedDict


class State(TypedDict):
    # question：用户输入，图中的所有节点都可以读取。
    question: str
    # route：分类节点写入的路由结果，供条件边选择下一节点。
    route: str
    # answer：最终答案，由实际处理节点写入。
    answer: str


def main() -> None:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        print("缺少 langgraph，请按阶段 README 安装依赖。")
        return

    def classify(state: State) -> dict[str, str]:
        route = "python" if "python" in state["question"].lower() else "fallback"
        return {"route": route}

    def answer_python(_: State) -> dict[str, str]:
        return {"answer": "Python 是一门强调可读性的编程语言。"}

    def answer_fallback(_: State) -> dict[str, str]:
        return {"answer": "这个演示只处理 Python 问题。"}

    def route(state: State) -> Literal["answer_python", "answer_fallback"]:
        return "answer_python" if state["route"] == "python" else "answer_fallback"

    builder = StateGraph(State)
    # 节点是接收 State 并返回“局部状态更新”的普通 Python 函数。
    builder.add_node("classify", classify)
    builder.add_node("answer_python", answer_python)
    builder.add_node("answer_fallback", answer_fallback)
    # START 和 END 是图的入口与出口，不是业务节点。
    builder.add_edge(START, "classify")
    # 条件边根据 route 函数的返回值选择一个后续节点。
    builder.add_conditional_edges("classify", route)
    builder.add_edge("answer_python", END)
    builder.add_edge("answer_fallback", END)
    graph = builder.compile()

    print(graph.invoke({"question": "Python 是什么？", "route": "", "answer": ""}))


if __name__ == "__main__":
    main()
