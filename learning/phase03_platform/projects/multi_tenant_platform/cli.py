"""运行阶段三多租户 SaaS Agent 平台原型。"""

from __future__ import annotations

from dataclasses import asdict
import json

from core import Document, TenantPlatform, UserContext


def main() -> None:
    platform = TenantPlatform(request_limit=2, window_seconds=60)
    platform.set_budget("tenant-a", 0.02)
    platform.add_document(Document("doc-a", "tenant-a", "A 租户运行手册"))
    platform.add_document(Document("doc-b", "tenant-b", "B 租户私有文档"))

    viewer = UserContext("user-001", "tenant-a", "viewer")
    decisions = (
        platform.authorize(viewer, "read", estimated_cost=0.005, now=0.0),
        platform.authorize(viewer, "draft", estimated_cost=0.005, now=1.0),
    )
    print(
        json.dumps(
            {
                "visible_documents": [asdict(item) for item in platform.list_documents(viewer)],
                "decisions": [asdict(item) for item in decisions],
                "audit_log": platform.audit_log,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
