"""生成 Agent API 的最小 Kubernetes Deployment 与 Service。"""

from __future__ import annotations

import json


def build_manifests(image: str) -> list[dict[str, object]]:
    """构造固定镜像版本、健康检查和资源限制。"""

    labels = {"app": "tenant-agent-api"}
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "tenant-agent-api"},  # Deployment 名称。
        "spec": {
            "replicas": 2,  # API Pod 副本数量。
            "selector": {"matchLabels": labels},
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "containers": [
                        {
                            "name": "api",  # 容器名称。
                            "image": image,  # 必须使用固定镜像版本。
                            "ports": [{"containerPort": 8000}],
                            "readinessProbe": {"httpGet": {"path": "/health", "port": 8000}},
                            "resources": {
                                "requests": {"cpu": "250m", "memory": "256Mi"},
                                "limits": {"cpu": "1", "memory": "1Gi"},
                            },
                        }
                    ]
                },
            },
        },
    }
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "tenant-agent-api"},
        "spec": {"selector": labels, "ports": [{"port": 80, "targetPort": 8000}]},
    }
    return [deployment, service]


def main() -> None:
    print(json.dumps(build_manifests("tenant-agent-api:1.0.0"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
