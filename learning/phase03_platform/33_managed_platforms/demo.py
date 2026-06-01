"""Agent 部署规格的离线检查示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class DeploymentSpec:
    """提交给托管平台的最小部署规格。"""

    service_name: str  # 服务名称。
    image: str  # 带固定版本的容器镜像。
    region: str  # 部署区域。
    cpu: float  # 每个实例申请的 CPU 核数。
    memory_mb: int  # 每个实例申请的内存。
    max_concurrency: int  # 单实例允许的最大并发。
    secret_refs: tuple[str, ...]  # 只保存密钥引用名称，不保存密钥值。


def review(spec: DeploymentSpec) -> list[str]:
    """返回不适合进入生产的配置问题。"""

    issues: list[str] = []
    if ":" not in spec.image or spec.image.endswith(":latest"):
        issues.append("镜像必须使用明确版本")
    if spec.max_concurrency < 1:
        issues.append("max_concurrency 必须大于 0")
    if any("=" in item for item in spec.secret_refs):
        issues.append("secret_refs 只能保存引用名称")
    return issues


def main() -> None:
    spec = DeploymentSpec("tenant-agent-api", "agent-api:1.2.0", "asia-east1", 1.0, 1024, 8, ("OPENAI_API_KEY",))
    print(json.dumps({"spec": asdict(spec), "issues": review(spec)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
