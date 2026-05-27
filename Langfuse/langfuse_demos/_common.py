"""
Shared setup helpers for the Langfuse demo files.

The demos are intentionally small and focused on one Langfuse capability each.
They all use this helper so the examples stay readable while still being
runnable against the same local or cloud Langfuse project.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from langfuse import get_client


DEFAULT_LANGFUSE_HOST = "http://localhost:3000"


def _candidate_config_paths() -> list[Path]:
    """Return config locations that match the existing repo layout.

    Existing demos in this directory tree read ../dev.json, while some users
    prefer keeping a dev.json next to the demo folder. Supporting both keeps
    these files easy to move.
    """

    here = Path(__file__).resolve()
    return [
        here.parent / "dev.json",
        here.parent.parent / "dev.json",
        here.parent.parent.parent / "dev.json",
    ]


def load_dev_config() -> dict[str, Any]:
    """Load Langfuse credentials from dev.json.

    Expected shape:
        {
          "langfuse": {
            "host": "http://localhost:3000",
            "public_key": "pk-lf-...",
            "secret_key": "sk-lf-...",
            "debug": true
          }
        }
    """

    for config_path in _candidate_config_paths():
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as config_file:
                return json.load(config_file)

    searched = ", ".join(str(path) for path in _candidate_config_paths())
    raise FileNotFoundError(f"Missing dev.json. Searched: {searched}")


def configure_langfuse_from_dev_json() -> None:
    """Put Langfuse credentials into the environment for the SDK.

    Langfuse SDK v3 reads these variables when get_client() initializes the
    singleton client. LANGFUSE_BASE_URL is the current name used in the docs;
    LANGFUSE_HOST is also set for compatibility with older examples.
    """

    config = load_dev_config()
    langfuse_config = config.get("langfuse", {})

    host = str(langfuse_config.get("host", DEFAULT_LANGFUSE_HOST)).rstrip("/")
    public_key = langfuse_config.get("public_key")
    secret_key = langfuse_config.get("secret_key")

    if not public_key or public_key == "pk-lf-...":
        raise ValueError("Please set langfuse.public_key in dev.json.")
    if not secret_key or secret_key == "sk-lf-...":
        raise ValueError("Please set langfuse.secret_key in dev.json.")

    os.environ["LANGFUSE_BASE_URL"] = host
    os.environ["LANGFUSE_HOST"] = host
    os.environ["LANGFUSE_PUBLIC_KEY"] = str(public_key)
    os.environ["LANGFUSE_SECRET_KEY"] = str(secret_key)

    if "debug" in langfuse_config:
        os.environ["LANGFUSE_DEBUG"] = str(langfuse_config["debug"])


def get_configured_langfuse(auth_check: bool = False):
    """Configure and return a Langfuse client.

    auth_check is optional because many demos are read as code examples before
    a local Langfuse server is running. Set auth_check=True when you want an
    early, explicit credentials and connectivity check.
    """

    configure_langfuse_from_dev_json()
    langfuse = get_client()
    if auth_check and not langfuse.auth_check():
        raise RuntimeError("Langfuse auth_check failed. Check host and API keys.")
    return langfuse


def flush_and_print(langfuse, trace_hint: str) -> None:
    """Flush buffered telemetry and print a consistent completion message."""

    langfuse.flush()
    print(f"Sent demo trace: {trace_hint}")
    print(f"Langfuse host: {os.environ.get('LANGFUSE_BASE_URL', DEFAULT_LANGFUSE_HOST)}")
