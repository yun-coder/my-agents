"""
Test the OpenAI Responses API with LangSmith tracing.
"""

import json
import os
from pathlib import Path
from typing import Any

from openai import (
    APIConnectionError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from langsmith import traceable
from langsmith.wrappers import wrap_openai

CONFIG_PATH = Path(__file__).with_name("dev.json")
DEFAULT_MODEL = "gpt-5.4-mini"


def load_dev_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing config file: {CONFIG_PATH.name}. "
            "Please create it from dev.example.json."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def configure_langsmith(config: dict[str, Any]) -> None:
    langsmith_config = config.get("langsmith", {})

    if "tracing" in langsmith_config:
        os.environ["LANGSMITH_TRACING"] = str(langsmith_config["tracing"]).lower()
    if langsmith_config.get("api_key"):
        os.environ["LANGSMITH_API_KEY"] = langsmith_config["api_key"]
    if langsmith_config.get("project"):
        os.environ["LANGSMITH_PROJECT"] = langsmith_config["project"]


def create_openai_client(config: dict[str, Any]) -> OpenAI:
    openai_config = config.get("openai", {})
    api_key = openai_config.get("api_key")
    base_url = str(openai_config.get("base_url", "")).rstrip("/")

    if not api_key or api_key == "your-api-key":
        raise ValueError("Please set openai.api_key in dev.json.")
    if not base_url or base_url == "https://your-api-provider.example.com/v1":
        raise ValueError("Please set openai.base_url in dev.json.")
    if "apifox.newapi.ai" in base_url:
        raise ValueError(
            "openai.base_url points to the NewAPI Apifox documentation page. "
            "Copy the API Base URL from your NewAPI platform homepage instead; "
            "it should look like https://your-platform.com/v1."
        )
    if "docs." in base_url:
        raise ValueError(
            "openai.base_url points to a documentation site. "
            "Set it to the API root URL, for example https://api.openai.com/v1."
        )
    if base_url.endswith(("/chat/completions", "/responses")):
        raise ValueError(
            "openai.base_url must be an API root URL, not a full endpoint. "
            "Use a value like https://api.openai.com/v1 instead of a path ending "
            "in /chat/completions or /responses."
        )

    return wrap_openai(
        OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    )


@traceable(
    name="Generate bedtime story",
    run_type="chain",
    tags=["openai", "responses-api"],
)
def generate_bedtime_story(client: OpenAI, model: str, input_text: str) -> str:
    response = client.responses.create(
        model=model,
        input=f"{input_text}\n\n请使用中文输出。",
    )

    return response.output_text


def main() -> None:
    try:
        config = load_dev_config()
        configure_langsmith(config)
        client = create_openai_client(config)
        model = config.get("openai", {}).get("model", DEFAULT_MODEL)

        story = generate_bedtime_story(
            client, model, "Write a one-sentence bedtime story about a unicorn."
        )
        print(story)
    except AuthenticationError:
        print("OpenAI authentication failed. Please check openai.api_key in dev.json.")
    except RateLimitError as exc:
        print(
            "OpenAI request failed: quota is insufficient or the rate limit was reached."
        )
        print("Please check your OpenAI billing, plan, and usage limits.")
        print(f"Original error: {exc}")
    except APIConnectionError as exc:
        print("OpenAI request failed: could not connect to the API.")
        print(f"Original error: {exc}")
    except OpenAIError as exc:
        print("OpenAI request failed.")
        print(f"Original error: {exc}")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print("Local config error.")
        print(f"Original error: {exc}")


if __name__ == "__main__":
    main()
