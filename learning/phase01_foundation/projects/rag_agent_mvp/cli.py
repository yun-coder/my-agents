"""阶段一 RAG Agent MVP 命令行入口。"""

from __future__ import annotations

import argparse
from pathlib import Path

from core import KnowledgeAgent, KnowledgeBase


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--online",
        action="store_true",
        help="启用 dev.json 中配置的在线模型生成。",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="RAG 是什么？",
        help="用户问题；不填写时使用默认 RAG 问题。",
    )
    args = parser.parse_args()

    knowledge_base = KnowledgeBase.from_markdown_directory(Path(__file__).with_name("data"))
    result = KnowledgeAgent(knowledge_base).ask(args.question, online=args.online)
    print(result.answer)
    if result.tool_name:
        print(f"\n工具：{result.tool_name}")
    if result.sources:
        print("\n来源：")
        for source in result.sources:
            print(f"- {source}")


if __name__ == "__main__":
    main()
