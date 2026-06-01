"""需要额外 Anthropic 配置：最小 Messages API 调用。"""

from __future__ import annotations

import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from anthropic import Anthropic  # noqa: E402

from shared.config import ConfigError, get_anthropic_settings  # noqa: E402


def main() -> None:
    try:
        settings = get_anthropic_settings()
    except ConfigError as exc:
        print(f"Claude 示例暂未运行：{exc}")
        return

    client = Anthropic(api_key=settings.api_key, base_url=settings.base_url)
    message = client.messages.create(
        # model：dev.json 中配置的 Claude 模型 ID。
        model=settings.model,
        # max_tokens：本次最多生成多少输出 token，不是上下文窗口大小。
        max_tokens=300,
        # system：顶层系统提示词。Anthropic Messages API 不使用 system role 消息。
        system="你是 Python 入门老师，请使用简洁中文回答。",
        # messages：由应用显式提交的对话历史；本例只有一轮用户问题。
        messages=[
            {"role": "user", "content": "什么是 Python 装饰器？"},
        ],
    )
    # content 是内容块列表。最小文本示例中第一个块是 TextBlock。
    print(message.content[0].text)


if __name__ == "__main__":
    main()
