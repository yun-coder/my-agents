"""Docker Compose 风格配置的离线检查示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class Service:
    """一个容器服务的教学级配置。"""

    name: str  # Compose 服务名。
    image: str  # 镜像名与明确版本标签。
    ports: tuple[str, ...]  # 宿主机到容器的端口映射。
    has_healthcheck: bool  # 是否配置健康检查。


def review(service: Service) -> list[str]:
    """返回需要修正的容器配置问题。"""

    issues: list[str] = []
    if service.image.endswith(":latest"):
        issues.append("镜像标签不应使用 latest")
    if not service.has_healthcheck:
        issues.append("应配置 healthcheck")
    if any(port.startswith("0.0.0.0:") for port in service.ports):
        issues.append("开发环境优先绑定 127.0.0.1")
    return issues


def main() -> None:
    services = (
        Service("api", "agent-course-api:1.0.0", ("127.0.0.1:8000:8000",), True),
        Service("redis", "redis:latest", ("0.0.0.0:6379:6379",), False),
    )
    print(json.dumps([{"service": asdict(item), "issues": review(item)} for item in services], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
