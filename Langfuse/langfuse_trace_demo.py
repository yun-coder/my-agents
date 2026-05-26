"""
Create a minimal Langfuse trace against a local self-hosted Langfuse server.

Before running:
1. Open http://localhost:3000
2. Create a project and generate API keys
3. Copy dev.example.json to dev.json and fill in the keys
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
            f"Missing config file: {CONFIG_PATH.name}. "
            "Please create it from dev.example.json."
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

    os.environ["LANGFUSE_HOST"] = str(host).rstrip("/")
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key

    if "debug" in langfuse_config:
        os.environ["LANGFUSE_DEBUG"] = str(langfuse_config["debug"])


@observe(name="Generate local demo answer")
def generate_demo_answer(input_text: str) -> str:
    langfuse = get_client()

    with propagate_attributes(
        user_id="local-demo-user",
        session_id="local-demo-session",
        tags=["local", "demo", "trace"],
        metadata={"source": "langfuse_trace_demo.py"},
    ):
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="Mock LLM generation",
        ) as generation:
            output = f"Langfuse local trace demo received: {input_text}"
            generation.update(
                input=input_text,
                output=output,
                model="mock-local-model",
                metadata={"provider": "local-demo"},
            )

    return output


def main() -> None:
    try:
        config = load_dev_config()
        configure_langfuse(config)

        langfuse = get_client()
        langfuse.auth_check()

        result = generate_demo_answer("Hello, Langfuse.")
        langfuse.flush()

        print(result)
        print(f"Trace sent to: {os.environ['LANGFUSE_HOST']}")
        print("Open Langfuse UI, then check the Traces page in your project.")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print("Local config error.")
        print(f"Original error: {exc}")
    except Exception as exc:
        print("Langfuse trace demo failed.")
        print(f"Original error: {exc}")


if __name__ == "__main__":
    main()
