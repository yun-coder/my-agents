"""开源模型服务端点的配置选择示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class ModelEndpoint:
    """可由平台配置中心管理的模型端点。"""

    name: str  # 业务侧使用的模型别名。
    provider: str  # 服务实现，例如 ollama 或 vllm。
    base_url: str  # 推理服务地址，不包含密钥。
    context_window: int  # 最大上下文 Token 数。
    supports_tools: bool  # 当前端点是否支持工具调用。


def choose_endpoint(endpoints: tuple[ModelEndpoint, ...], needs_tools: bool) -> ModelEndpoint:
    """选择满足工具调用要求且上下文最长的端点。"""

    candidates = [item for item in endpoints if not needs_tools or item.supports_tools]
    if not candidates:
        raise ValueError("没有满足要求的模型端点")
    return max(candidates, key=lambda item: item.context_window)


def main() -> None:
    endpoints = (
        ModelEndpoint("local-qwen", "ollama", "http://127.0.0.1:11434", 32768, False),
        ModelEndpoint("team-llama", "vllm", "http://127.0.0.1:8001/v1", 65536, True),
    )
    selected = choose_endpoint(endpoints, needs_tools=True)
    print(json.dumps(asdict(selected), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
