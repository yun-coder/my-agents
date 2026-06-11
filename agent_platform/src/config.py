"""配置管理：从 dev.json 和环境变量加载配置，不硬编码密钥。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / 'dev.json'


class ConfigError(RuntimeError):
    """配置缺失或格式错误。"""


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class EmbeddingSettings:
    provider: str
    model_name: str
    device: str = 'cpu'


@dataclass(frozen=True)
class LangFuseSettings:
    enabled: bool = True
    host: str = ""
    public_key: str = ""
    secret_key: str = ""


@dataclass(frozen=True)
class AppConfig:
    llm: LLMSettings
    embedding: EmbeddingSettings = field(
        default_factory=lambda: EmbeddingSettings('local_bge', 'BAAI/bge-small-zh-v1.5')
    )
    langfuse: LangFuseSettings | None = None
    chroma_persist_dir: str = './data/chroma'
    max_memory_messages: int = 20
    log_level: str = 'INFO'


def _load_dev_json() -> dict[str, Any]:
    # 优先级: dev.local.json > dev.json（local 不入库，放真密钥）
    for name in ("dev.local.json", "dev.json"):
        p = REPO_ROOT / name
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
    raise ConfigError(
        f'缺少配置文件：{REPO_ROOT / "dev.json"}。请从 dev.example.json 创建。'
    )


def load_config() -> AppConfig:
    dev = _load_dev_json()
    openai_section = dev.get('openai', {})
    llm = LLMSettings(
        api_key=os.getenv('OPENAI_API_KEY', str(openai_section.get('api_key', ''))),
        base_url=os.getenv('OPENAI_BASE_URL', str(openai_section.get('base_url', ''))),
        model=os.getenv('OPENAI_MODEL', str(openai_section.get('model', ''))),
    )
    if not llm.api_key or llm.api_key in ('your-api-key', ''):
        raise ConfigError('请在 dev.json 或环境变量中设置 LLM API Key。')

    emb_provider = os.getenv('EMBEDDING_PROVIDER', 'local_bge')
    embedding = EmbeddingSettings(
        provider=emb_provider,
        model_name=os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5'),
        device=os.getenv('EMBEDDING_DEVICE', 'cpu'),
    )

    lf_section = dev.get('langfuse', {})
    langfuse = None
    if lf_section:
        langfuse = LangFuseSettings(
            enabled=os.getenv('LANGFUSE_ENABLED',
                              str(lf_section.get('enabled', True))).lower() == 'true',
            host=os.getenv('LANGFUSE_HOST',
                           str(lf_section.get('host', ''))),
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY',
                                 str(lf_section.get('public_key', ''))),
            secret_key=os.getenv('LANGFUSE_SECRET_KEY',
                                 str(lf_section.get('secret_key', ''))),
        )

    return AppConfig(
        llm=llm,
        embedding=embedding,
        langfuse=langfuse,
        chroma_persist_dir=os.getenv('CHROMA_DIR', './data/chroma'),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
    )
