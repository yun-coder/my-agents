"""LangGraph Agent 工作流：状态图编排 + Tool Calling 循环。

工作流结构：
    START -> agent_node -> [有 tool_calls?] -> tool_node -> agent_node -> ... -> END
                                     \-> [无 tool_calls] -> END

支持：
- 多轮 Tool Calling 循环（最多 5 轮）
- 状态持久化（Checkpoint，可选）
- 条件分支（根据 tools 调用结果走不同路径）
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from ..llm.client import get_llm_client
from ..rag.generator import RAGGenerator
from .tools import TOOL_DEFINITIONS, TOOL_EXECUTORS
from .memory import ConversationMemory

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5


class AgentState(TypedDict, total=False):
    """LangGraph 共享状态。"""

    messages: list[dict[str, Any]]
    query: str
    session_id: str
    iteration_count: int
    final_answer: str
    tool_log: list[str]
    error: str


class AgentWorkflow:
    """基于 LangGraph 的 Agent 工作流。

    用法:
        wf = AgentWorkflow(rag_generator=generator)
        result = wf.run("帮我搜索 Python 文件并计算 3*5")
        print(result["final_answer"])
        print(result["tool_log"])
    """

    def __init__(
        self,
        rag_generator: RAGGenerator | None = None,
        *,
        memory: ConversationMemory | None = None,
        enable_checkpoint: bool = False,
    ):
        self._llm = get_llm_client()
        self._rag = rag_generator
        self._memory = memory or ConversationMemory()

        builder = StateGraph(AgentState)

        builder.add_node("agent", self._agent_node)
        builder.add_node("tools", self._tool_node)
        builder.add_node("rag", self._rag_node)

        builder.set_entry_point("agent")

        builder.add_conditional_edges(
            "agent",
            self._router,
            {
                "tools": "tools",
                "rag": "rag",
                "end": END,
            },
        )
        builder.add_edge("tools", "agent")
        builder.add_edge("rag", "agent")

        if enable_checkpoint:
            self._checkpointer = MemorySaver()
            self._graph = builder.compile(checkpointer=self._checkpointer)
        else:
            self._graph = builder.compile()

    def run(self, query: str, session_id: str = "default") -> AgentState:
        """执行 Agent 工作流，返回最终状态。"""
        from ..observability import init_tracing, traced_operation
        init_tracing()   # 兜底：万一 get_llm_client 还没被调用
        initial_state: AgentState = {
            "messages": self._memory.get_messages(),
            "query": query,
            "session_id": session_id,
            "iteration_count": 0,
            "final_answer": "",
            "tool_log": [],
            "error": "",
        }
        with traced_operation(
            "agent.run",
            input={"query": query, "session_id": session_id},
        ) as op:
            result = self._graph.invoke(initial_state)
            op.update(
                output=result.get("final_answer", ""),
                metadata={
                    "iterations": result.get("iteration_count", 0),
                    "tools_used": len(result.get("tool_log", [])),
                },
            )
        if result.get("final_answer"):
            self._memory.add("user", query)
            self._memory.add("assistant", result["final_answer"])
        return result

    def stream(self, query: str, session_id: str = "default"):
        """流式执行 Agent 工作流。"""
        initial_state: AgentState = {
            "messages": [],
            "query": query,
            "session_id": session_id,
            "iteration_count": 0,
            "final_answer": "",
            "tool_log": [],
            "error": "",
        }
        for event in self._graph.stream(initial_state):
            yield event

    # ---- 内部节点 ----

    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent 决策节点：决定调用工具、搜索RAG还是直接回答。"""
        iteration = state.get("iteration_count", 0)

        if iteration >= MAX_TOOL_ITERATIONS:
            state["final_answer"] = "已达到最大工具调用次数，请简化你的问题。"
            return state

        system_prompt = """你是一个智能助手。你可以：
1. 调用工具（search_files, get_current_time, read_file, calculate）获取信息
2. 如果问题需要搜索知识库，在回答中说"需要搜索知识库：<关键词>"
3. 如果可以直接回答，直接给出答案

使用中文回答。"""

        messages = [{"role": "system", "content": system_prompt}]
        history = state.get("messages", [])
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": state["query"]})

        try:
            response = self._llm.chat_with_tools(messages, TOOL_DEFINITIONS)
            choice = response.choices[0]

            if choice.message.tool_calls:
                state["messages"] = messages + [choice.message.model_dump()]
                state["iteration_count"] = iteration + 1
            elif choice.message.content:
                content = choice.message.content
                if "需要搜索知识库" in content:
                    state["iteration_count"] = iteration + 1
                else:
                    state["final_answer"] = content
            else:
                state["final_answer"] = "无法理解你的问题，请换一种方式描述。"
        except Exception as e:
            logger.error("Agent 节点错误：%s", e)
            state["error"] = str(e)
            state["final_answer"] = f"处理请求时出错：{e}"

        return state

    def _tool_node(self, state: AgentState) -> AgentState:
        """工具执行节点：执行 LLM 请求的工具调用。"""
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1]
        tool_calls = last_message.get("tool_calls", [])

        tool_results: list[dict[str, Any]] = []
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            func_args = json.loads(tc["function"]["arguments"])

            executor = TOOL_EXECUTORS.get(func_name)
            if executor:
                args_list = list(func_args.values())
                result = executor(*args_list) if args_list else executor()
                log_entry = f"[{func_name}] {' '.join(str(v) for v in func_args.values())} -> {result[:100]}"
                state.setdefault("tool_log", []).append(log_entry)
                logger.info(log_entry)
            else:
                result = f"未知工具：{func_name}"

            tool_results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        state["messages"] = messages + tool_results
        return state

    def _rag_node(self, state: AgentState) -> AgentState:
        """RAG 检索节点：搜索知识库。"""
        query = state.get("query", "")

        if "需要搜索知识库" in query:
            search_query = query.split("需要搜索知识库：", 1)[-1].strip()
        else:
            search_query = query

        if self._rag:
            answer = self._rag.generate(search_query)
            state["messages"] = state.get("messages", []) + [
                {"role": "system", "content": f"知识库检索结果来源：{', '.join(answer.sources)}"}
            ]
            state["query"] = f"基于以下知识库资料回答问题：\n{chr(10).join(answer.context_docs)}\n\n原问题：{search_query}"
        else:
            state["messages"] = state.get("messages", []) + [
                {"role": "system", "content": "知识库未配置，请直接回答。"}
            ]

        return state

    def _router(
        self, state: AgentState
    ) -> Literal["tools", "rag", "end"]:
        """条件路由：根据 Agent 节点输出决定下一步。"""
        if state.get("final_answer"):
            return "end"
        if state.get("error"):
            return "end"

        messages = state.get("messages", [])
        if messages:
            last = messages[-1]
            if last.get("tool_calls"):
                return "tools"
            if last.get("role") == "system" and "知识库检索结果来源" in last.get("content", ""):
                return "rag"
            content = last.get("content", "")
            if isinstance(content, str) and "需要搜索知识库" in content:
                return "rag"
        return "end"

    @property
    def graph(self) -> StateGraph:
        return self._graph
