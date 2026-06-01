"""默认离线展示 RAG 检索；传入 --online 生成最终答案。"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import get_openai_settings  # noqa: E402
from shared.offline_embeddings import bag_of_words, cosine_similarity  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402


@dataclass(frozen=True)
class Chunk:
    # source：原文定位。生产系统通常还会保存页码、标题和 URL。
    source: str
    # text：本次送入检索与生成步骤的文本块。
    text: str


CHUNKS = [
    Chunk("agent_notes.md#agent", "Agent 通常包含模型、提示词、工具、记忆和控制流程。"),
    Chunk("agent_notes.md#rag", "RAG 会先检索外部资料，再把相关上下文交给模型生成答案。"),
    Chunk("agent_notes.md#tools", "工具调用时，真正执行函数的是应用程序，而不是模型。"),
]


def retrieve(question: str, top_k: int = 2) -> list[Chunk]:
    """按词法相似度召回非零相关的 Top-k 文本块。"""

    query_vector = bag_of_words(question)
    scored = [
        (cosine_similarity(query_vector, bag_of_words(chunk.text)), chunk)
        for chunk in CHUNKS
    ]
    relevant = [item for item in scored if item[0] > 0]
    return [
        chunk
        for _, chunk in sorted(relevant, key=lambda item: item[0], reverse=True)[:top_k]
    ]


def build_prompt(question: str, chunks: list[Chunk]) -> str:
    context = "\n".join(f"[{chunk.source}] {chunk.text}" for chunk in chunks)
    return (
        "只根据资料回答问题。资料不足时明确说不知道。回答后列出来源。\n\n"
        f"<context>\n{context}\n</context>\n\n"
        f"问题：{question}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    parser.add_argument("question", nargs="?", default="RAG 是什么？")
    args = parser.parse_args()

    chunks = retrieve(args.question)
    if not chunks:
        print("未召回到非零相关资料，停止生成。")
        return

    prompt = build_prompt(args.question, chunks)
    if not args.online:
        print(prompt)
        return

    settings = get_openai_settings()
    client = create_openai_client(settings)
    # 将召回资料和用户问题一起提交给模型；模型不会自动读取本地知识库。
    response = client.responses.create(model=settings.model, input=prompt)
    print(response.output_text)


if __name__ == "__main__":
    main()
