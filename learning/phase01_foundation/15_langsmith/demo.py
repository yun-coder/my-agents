"""使用现有 OpenAI 与 LangSmith 配置：追踪一次 Responses API 调用。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from langsmith import traceable  # noqa: E402
from langsmith.wrappers import wrap_openai  # noqa: E402
from openai import OpenAI  # noqa: E402

from shared.config import get_openai_settings, load_dev_config  # noqa: E402


def configure_langsmith(config: dict[str, Any]) -> None:
    section = config.get("langsmith", {})
    # LANGSMITH_TRACING：是否启用自动追踪。
    os.environ["LANGSMITH_TRACING"] = str(section.get("tracing", False)).lower()
    if section.get("api_key"):
        # LANGSMITH_API_KEY：向 LangSmith 上报 trace 时使用的凭据。
        os.environ["LANGSMITH_API_KEY"] = str(section["api_key"])
    if section.get("project"):
        # LANGSMITH_PROJECT：本次 trace 在 LangSmith UI 中所属的项目。
        os.environ["LANGSMITH_PROJECT"] = str(section["project"])


@traceable(name="phase01-langsmith-demo", run_type="chain")
def answer_question(client: OpenAI, model: str) -> str:
    return client.responses.create(
        # model：仍然来自 OpenAI 配置；LangSmith 只负责观测，不提供模型。
        model=model,
        # input：这段输入和输出会进入 trace，生产环境要评估脱敏需求。
        input=(
            "请用一句中文改写下面的事实，不要引入其他定义："
            "在 LangSmith 中，Trace 表示一次端到端请求；"
            "Run 表示这次请求中的一个执行步骤，例如模型调用、工具调用或检索。"
        ),
    ).output_text


def main() -> None:
    config = load_dev_config()
    configure_langsmith(config)
    settings = get_openai_settings(config)
    client = wrap_openai(OpenAI(api_key=settings.api_key, base_url=settings.base_url))
    print(answer_question(client, settings.model))


if __name__ == "__main__":
    main()
