"""
Send a minimal Langfuse trace with token usage and cost data.

Before running:
1. Open http://localhost:3000
2. Create a project and generate API keys
3. Copy D:/学习院/my-agents/dev.example.json to dev.json and fill in langfuse keys

This demo does not call a real LLM. In a real application, replace the mocked
token counts with values returned by the model provider, such as response.usage.
"""

import json
import os
from pathlib import Path
from typing import Any

from langfuse import get_client, observe, propagate_attributes

CONFIG_PATH = Path(__file__).resolve().parent.parent / "dev.json"
DEFAULT_LANGFUSE_HOST = "http://localhost:3000"


def load_dev_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing config file: {CONFIG_PATH}. "
            "Please create it from D:\\学习院\\my-agents\\dev.example.json."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def configure_langfuse(config: dict[str, Any]) -> None:
    langfuse_config = config.get("langfuse", {})

    host = langfuse_config.get("host", DEFAULT_LANGFUSE_HOST)
    public_key = langfuse_config.get("public_key")
    secret_key = langfuse_config.get("secret_key")

    if not public_key or public_key == "pk-lf-...":
        raise ValueError("Please set langfuse.public_key in dev.json.")
    if not secret_key or secret_key == "sk-lf-...":
        raise ValueError("Please set langfuse.secret_key in dev.json.")

    base_url = str(host).rstrip("/")
    os.environ["LANGFUSE_BASE_URL"] = base_url
    os.environ["LANGFUSE_HOST"] = base_url
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key

    if "debug" in langfuse_config:
        os.environ["LANGFUSE_DEBUG"] = str(langfuse_config["debug"])


@observe(name="Token usage tracking demo")
def run_token_usage_demo() -> str:
    langfuse = get_client()

    with propagate_attributes(
        user_id="local-demo-user",
        session_id="local-token-usage-session",
        tags=["local", "demo", "token-usage"],
        metadata={"source": "langfuse_token_usage_demo.py"},
    ):
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="manual-token-usage",
            model="mock-local-model",
            input=[
                {
                    "role": "user",
                    "content": "Explain how Langfuse tracks token usage.",
                }
            ],
        ) as generation:
            output = "Langfuse records token usage on generation observations."
            generation.update(
                output=output,
                usage_details={
                    "input": 18,
                    "output": 32,
                    "cache_read_input_tokens": 5,
                    "total": 55,
                },
                cost_details={
                    "input": 0.000009,
                    "output": 0.000048,
                    "cache_read_input_tokens": 0.000001,
                    "total": 0.000058,
                },
                metadata={
                    "note": "Replace these mocked numbers with provider response.usage values."
                },
            )

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="openai-style-token-usage",
            model="gpt-4o-mini",
            input=[{"role": "user", "content": "Give me a short demo."}],
        ) as generation:
            generation.update(
                output="This generation uses the OpenAI-compatible usage schema.",
                usage_details={
                    "prompt_tokens": 23,
                    "completion_tokens": 41,
                    "total_tokens": 64,
                    "prompt_tokens_details": {"cached_tokens": 4},
                    "completion_tokens_details": {"reasoning_tokens": 12},
                },
                metadata={
                    "note": "Langfuse maps prompt_tokens to input and completion_tokens to output."
                },
            )

    return "Sent token usage demo trace to Langfuse."


def main() -> None:
    try:
        config = load_dev_config()
        configure_langfuse(config)

        langfuse = get_client()
        langfuse.auth_check()

        result = run_token_usage_demo()
        langfuse.flush()

        print(result)
        print(f"Trace sent to: {os.environ['LANGFUSE_BASE_URL']}")
        print("Open Langfuse UI, then check Traces -> Token usage tracking demo.")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print("Local config error.")
        print(f"Original error: {exc}")
    except Exception as exc:
        print("Langfuse token usage demo failed.")
        print(f"Original error: {exc}")


if __name__ == "__main__":
    main()
