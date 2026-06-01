"""使用现有 OpenAI 配置：Responses API 文本生成与流式输出。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import get_openai_settings  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402


def run_once(prompt: str) -> None:
    settings = get_openai_settings()
    client = create_openai_client(settings)
    response = client.responses.create(
        # model：dev.json 中的文本生成模型 ID。
        model=settings.model,
        # instructions：应用层规则。本次请求中，它的优先级高于普通用户输入。
        instructions="你是 Python 入门老师。回答简洁，并给出一个小例子。",
        # input：用户本轮问题。这里只发送单轮文本，不会自动附带历史消息。
        input=prompt,
    )
    print(response.output_text)


def run_stream(prompt: str) -> None:
    settings = get_openai_settings()
    client = create_openai_client(settings)
    stream = client.responses.create(
        # model：与非流式请求使用同一个模型。
        model=settings.model,
        # input：用户输入文本。
        input=prompt,
        # stream=True：让服务端逐步返回事件，而不是等待完整答案后一次返回。
        stream=True,
    )
    for event in stream:
        # 文本增量事件只包含新增片段；其他事件可用于处理状态、错误或工具调用。
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", action="store_true", help="启用流式输出")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="请解释 Python 列表推导式。",
    )
    args = parser.parse_args()
    (run_stream if args.stream else run_once)(args.prompt)


if __name__ == "__main__":
    main()
