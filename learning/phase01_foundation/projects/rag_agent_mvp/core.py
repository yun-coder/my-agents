"""阶段一综合项目：轻量、可解释、默认离线的 RAG Agent。"""

from __future__ import annotations

import ast
import operator
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PHASE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import get_openai_settings  # noqa: E402
from shared.offline_embeddings import bag_of_words, cosine_similarity  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402


@dataclass(frozen=True)
class Chunk:
    # source：原文定位，例如文件名与分块编号。
    source: str
    # text：参与检索、上下文组装和最终生成的文本块。
    text: str


@dataclass(frozen=True)
class AgentAnswer:
    # answer：返回给用户的回答文本。
    answer: str
    # sources：回答依据的知识库分块；工具直答时为空列表。
    sources: list[str]
    # tool_name：命中本地工具时记录工具名，否则为 None。
    tool_name: str | None = None


class SessionMemory:
    def __init__(self, max_messages: int = 6) -> None:
        # 进程内 deque 只适合教学。生产环境应换成 Redis 或数据库。
        self._messages: dict[str, deque[str]] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )

    def add(self, session_id: str, message: str) -> None:
        self._messages[session_id].append(message)

    def get(self, session_id: str) -> list[str]:
        return list(self._messages[session_id])


class KnowledgeBase:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks

    @classmethod
    def from_markdown_directory(cls, directory: Path) -> "KnowledgeBase":
        chunks = []
        for path in sorted(directory.glob("*.md")):
            for index, paragraph in enumerate(path.read_text(encoding="utf-8").split("\n\n")):
                text = paragraph.strip()
                if text:
                    chunks.append(Chunk(f"{path.name}#chunk-{index + 1}", text))
        return cls(chunks)

    def search(self, question: str, top_k: int = 2) -> list[Chunk]:
        vector = bag_of_words(question)
        scored = [
            (cosine_similarity(vector, bag_of_words(chunk.text)), chunk)
            for chunk in self.chunks
        ]
        # 零相关文本不应被送入模型，否则会制造“有来源但与问题无关”的假象。
        relevant = [item for item in scored if item[0] > 0]
        return [
            chunk
            for _, chunk in sorted(relevant, key=lambda item: item[0], reverse=True)[:top_k]
        ]

    def sources(self) -> list[str]:
        return sorted({chunk.source.split("#", maxsplit=1)[0] for chunk in self.chunks})


def get_weather(city: str) -> str:
    """返回固定演示数据，不访问真实天气服务。"""

    data = {"北京": "晴，26 摄氏度", "上海": "多云，24 摄氏度"}
    return data.get(city, "暂无演示天气数据")


ALLOWED_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
ALLOWED_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def calculate(expression: str) -> float:
    """安全计算有限的算术表达式，避免直接使用 eval。"""

    def evaluate(node: ast.AST) -> float:
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        ):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINARY_OPERATORS:
            return ALLOWED_BINARY_OPERATORS[type(node.op)](
                evaluate(node.left), evaluate(node.right)
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY_OPERATORS:
            return ALLOWED_UNARY_OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("计算器只支持数字、括号和 + - * /。")

    return evaluate(ast.parse(expression, mode="eval").body)


class KnowledgeAgent:
    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base = knowledge_base
        self.memory = SessionMemory()

    def ask(self, question: str, session_id: str = "default", online: bool = False) -> AgentAnswer:
        """先尝试只读工具，再检索知识库，最后按需调用在线模型。"""

        self.memory.add(session_id, f"user: {question}")
        tool_answer = self._try_tool(question)
        if tool_answer:
            self.memory.add(session_id, f"assistant: {tool_answer.answer}")
            return tool_answer

        chunks = self.knowledge_base.search(question)
        sources = [chunk.source for chunk in chunks]
        if not chunks:
            answer = "未找到相关资料，无法基于知识库回答。"
        elif online:
            answer = self._generate_online(question, chunks, session_id)
        else:
            context = "\n".join(f"- {chunk.text}" for chunk in chunks)
            answer = f"离线模式已召回以下资料：\n{context}"
        self.memory.add(session_id, f"assistant: {answer}")
        return AgentAnswer(answer=answer, sources=sources)

    def _try_tool(self, question: str) -> AgentAnswer | None:
        if "天气" in question:
            city = next((name for name in ("北京", "上海") if name in question), None)
            if city is None:
                return AgentAnswer("演示天气工具目前只支持北京和上海。", [], "get_weather")
            return AgentAnswer(get_weather(city), [], "get_weather")
        if question.startswith("计算 "):
            expression = question.removeprefix("计算 ").strip()
            return AgentAnswer(str(calculate(expression)), [], "calculate")
        if "来源" in question or "文档列表" in question:
            return AgentAnswer("\n".join(self.knowledge_base.sources()), [], "list_sources")
        return None

    def _generate_online(self, question: str, chunks: list[Chunk], session_id: str) -> str:
        settings = get_openai_settings()
        client = create_openai_client(settings)
        context = "\n".join(f"[{chunk.source}] {chunk.text}" for chunk in chunks)
        history = "\n".join(self.memory.get(session_id)[-4:])
        prompt = (
            "只根据资料回答问题；资料不足时明确说明。回答末尾列出来源。\n\n"
            f"<history>\n{history}\n</history>\n"
            f"<context>\n{context}\n</context>\n"
            f"问题：{question}"
        )
        # 在线模式只提交已召回上下文，不允许模型自行读取本地文件。
        return client.responses.create(model=settings.model, input=prompt).output_text
