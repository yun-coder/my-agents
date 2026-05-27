"""
共享的初始化辅助模块，供各个 Langfuse 演示脚本使用。

每个演示文件都刻意保持短小，专注于一个 Langfuse 功能点。
它们都通过本模块获取客户端，使示例代码可读性强，同时都能
针对同一个本地或云端 Langfuse 项目运行。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from langfuse import get_client

# 默认的本地 Langfuse 服务地址
DEFAULT_LANGFUSE_HOST = "http://localhost:3000"


def _candidate_config_paths() -> list[Path]:
    """返回匹配现有仓库布局的配置文件候选路径。

    本目录树中的演示脚本通常读取 ../dev.json，而某些用户
    偏好将 dev.json 放在演示目录旁边。同时支持两者，使文件易于移动。
    """

    here = Path(__file__).resolve()
    return [
        here.parent / "dev.json",             # 与演示目录同级
        here.parent.parent / "dev.json",       # 上级目录
        here.parent.parent.parent / "dev.json", # 上上级目录
    ]


def load_dev_config() -> dict[str, Any]:
    """从 dev.json 加载 Langfuse 凭据配置。

    期望的 JSON 结构：
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
    raise FileNotFoundError(f"缺少 dev.json 文件。已搜索以下路径: {searched}")


def configure_langfuse_from_dev_json() -> None:
    """将 dev.json 中的 Langfuse 凭据注入环境变量，供 SDK 使用。

    Langfuse SDK v3 在 get_client() 初始化单例客户端时读取这些环境变量。
    LANGFUSE_BASE_URL 是当前文档中使用的变量名；
    同时设置 LANGFUSE_HOST 以兼容旧版示例。
    """

    config = load_dev_config()
    langfuse_config = config.get("langfuse", {})

    # 读取并清理 host URL（去掉末尾斜杠）
    host = str(langfuse_config.get("host", DEFAULT_LANGFUSE_HOST)).rstrip("/")
    public_key = langfuse_config.get("public_key")
    secret_key = langfuse_config.get("secret_key")

    # 校验 API 密钥是否已配置（不能使用占位符值）
    if not public_key or public_key == "pk-lf-...":
        raise ValueError("请在 dev.json 中设置 langfuse.public_key。")
    if not secret_key or secret_key == "sk-lf-...":
        raise ValueError("请在 dev.json 中设置 langfuse.secret_key。")

    # 将凭据写入环境变量，供 SDK 自动读取
    os.environ["LANGFUSE_BASE_URL"] = host
    os.environ["LANGFUSE_HOST"] = host
    os.environ["LANGFUSE_PUBLIC_KEY"] = str(public_key)
    os.environ["LANGFUSE_SECRET_KEY"] = str(secret_key)

    if "debug" in langfuse_config:
        os.environ["LANGFUSE_DEBUG"] = str(langfuse_config["debug"])


def get_configured_langfuse(auth_check: bool = False):
    """配置并返回一个 Langfuse 客户端。

    auth_check 参数是可选的，因为许多演示脚本是作为代码示例阅读的，
    不一定总有一个正在运行的 Langfuse 服务器。
    当你需要提前验证凭据和连通性时，请设置 auth_check=True。
    """

    configure_langfuse_from_dev_json()
    langfuse = get_client()
    if auth_check and not langfuse.auth_check():
        raise RuntimeError("Langfuse auth_check 认证失败。请检查 host 和 API 密钥。")
    return langfuse


def flush_and_print(langfuse, trace_hint: str) -> None:
    """刷新缓冲区中的遥测数据，并打印一致的完成提示信息。"""

    langfuse.flush()
    print(f"已发送演示 trace: {trace_hint}")
    print(f"Langfuse 服务地址: {os.environ.get('LANGFUSE_BASE_URL', DEFAULT_LANGFUSE_HOST)}")
