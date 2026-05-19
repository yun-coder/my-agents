"""
Basic prompt API call using the local dev.json config.
"""

import json
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI


CONFIG_PATH = Path(__file__).with_name("dev.json")
DEFAULT_PROMPT = "请用一句话介绍 Python。"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def create_client(config: dict[str, Any]) -> OpenAI:
    openai_config = config["openai"]
    return OpenAI(
        api_key=openai_config["api_key"],
        base_url=openai_config["base_url"],
    )


def send_prompt(client: OpenAI, model: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content or ""


def main() -> None:
    config = load_config()
    client = create_client(config)
    model = config["openai"]["model"]
    prompt = " ".join(sys.argv[1:]).strip() or DEFAULT_PROMPT

    answer = send_prompt(client, model, prompt)
    print(answer)


if __name__ == "__main__":
    main()
