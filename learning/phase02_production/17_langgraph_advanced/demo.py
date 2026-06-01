"""离线可运行：LangGraph checkpoint 与人工审批中断。"""

from __future__ import annotations

from typing import TypedDict


class State(TypedDict):
    # request：需要审批的业务动作。
    request: str
    # approved：人工审批结果。
    approved: bool
    # result：工作流最终状态。
    result: str


def main() -> None:
    try:
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Command, interrupt
    except ImportError:
        print("缺少 langgraph，请按阶段 README 安装依赖。")
        return

    def approval_node(state: State) -> dict[str, bool]:
        # interrupt 的 payload 必须可 JSON 序列化，调用方会看到这段审批信息。
        approved = interrupt({"action": state["request"], "risk": "high"})
        return {"approved": bool(approved)}

    def execute_node(state: State) -> dict[str, str]:
        result = "已执行" if state["approved"] else "已拒绝"
        return {"result": result}

    builder = StateGraph(State)
    builder.add_node("approval", approval_node)
    builder.add_node("execute", execute_node)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", "execute")
    builder.add_edge("execute", END)
    graph = builder.compile(checkpointer=InMemorySaver())

    # thread_id 是 checkpoint 的游标；恢复执行时必须复用同一个值。
    config = {"configurable": {"thread_id": "approval-demo-001"}}
    paused = graph.invoke({"request": "导出客户数据", "approved": False, "result": ""}, config)
    print("暂停结果：", paused)
    resumed = graph.invoke(Command(resume=True), config)
    print("恢复结果：", resumed)


if __name__ == "__main__":
    main()
