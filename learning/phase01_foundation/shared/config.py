"""统一读取仓库根目录 dev.json，不在课程代码中硬编码密钥。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PHASE_ROOT = Path(__file__).resolve().parent.parent
LEARNING_ROOT = PHASE_ROOT.parent
REPO_ROOT = LEARNING_ROOT.parent
CONFIG_PATH = REPO_ROOT / "dev.json"


class ConfigError(RuntimeError):
    """配置缺失或格式错误。"""


@dataclass(frozen=True)
class OpenAISettings:
    """OpenAI 或 OpenAI 兼容服务所需的最小配置。"""

    # 服务端鉴权密钥。只能从本地 dev.json 读取，不能提交到 Git。
    api_key: str
    # API 根地址，例如 https://api.openai.com/v1；不要写完整的 /responses 路径。
    base_url: str
    # 文本生成模型 ID，由当前服务商实际支持的模型列表决定。
    model: str
    # 向量化模型 ID。部分兼容服务不提供 embeddings 端点。
    embedding_model: str = "text-embedding-3-small"


@dataclass(frozen=True)
class AnthropicSettings:
    """Anthropic 原生 Messages API 所需配置。"""

    # Anthropic 凭据与 OpenAI 凭据相互独立。
    api_key: str
    # Claude 模型 ID，应以 Anthropic 控制台可用模型为准。
    model: str
    # 可选的 API 根地址；不填写时使用 Anthropic SDK 默认地址。
    base_url: str | None = None


def load_dev_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"缺少配置文件：{path}。请从 dev.example.json 创建。")

    try:
        with path.open("r", encoding="utf-8") as config_file:
            data = json.load(config_file)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"dev.json 不是合法 JSON：{exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("dev.json 顶层必须是 JSON object。")
    return data


def get_openai_settings(config: dict[str, Any] | None = None) -> OpenAISettings:
    # 只有调用方没有传入配置时才读取文件。空字典也应按“配置缺失”处理。
    data = config if config is not None else load_dev_config()
    section = data.get("openai", {})
    api_key = str(section.get("api_key", "")).strip()
    base_url = str(section.get("base_url", "")).strip().rstrip("/")
    model = str(section.get("model", "")).strip()
    embedding_model = str(
        section.get("embedding_model", "text-embedding-3-small")
    ).strip()

    if not api_key or api_key == "your-api-key":
        raise ConfigError("请在 dev.json 中设置 openai.api_key。")
    if not base_url:
        raise ConfigError("请在 dev.json 中设置 openai.base_url。")
    if not model:
        raise ConfigError("请在 dev.json 中设置 openai.model。")
    if not embedding_model:
        raise ConfigError("请在 dev.json 中设置 openai.embedding_model。")

    return OpenAISettings(
        api_key=api_key,
        base_url=base_url,
        model=model,
        embedding_model=embedding_model,
    )


def get_anthropic_settings(
    config: dict[str, Any] | None = None,
) -> AnthropicSettings:
    data = config if config is not None else load_dev_config()
    section = data.get("anthropic", {})
    api_key = str(section.get("api_key", "")).strip()
    model = str(section.get("model", "")).strip()
    base_url = str(section.get("base_url", "")).strip() or None

    if not api_key or api_key == "your-anthropic-api-key":
        raise ConfigError(
            "Claude 示例需要 dev.json 中的 anthropic.api_key。"
            "这与 OpenAI 兼容配置是两套独立凭据。"
        )
    if not model:
        raise ConfigError("Claude 示例需要 dev.json 中的 anthropic.model。")

    return AnthropicSettings(api_key=api_key, model=model, base_url=base_url)
