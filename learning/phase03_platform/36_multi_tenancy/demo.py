"""SQLite 多租户数据过滤与 RBAC 示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import sqlite3


ROLE_ACTIONS = {
    "viewer": {"read"},
    "editor": {"read", "write"},
    "admin": {"read", "write", "manage_members"},
}


@dataclass(frozen=True)
class Document:
    """属于单一租户的文档。"""

    document_id: str  # 文档唯一 ID。
    tenant_id: str  # 数据归属租户，查询时必须过滤。
    title: str  # 文档标题。


class TenantDocuments:
    """强制使用 tenant_id 查询的文档仓库。"""

    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            "CREATE TABLE documents(document_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL)"
        )

    def add(self, document: Document) -> None:
        self.connection.execute("INSERT INTO documents VALUES (?, ?, ?)", tuple(asdict(document).values()))
        self.connection.commit()

    def list_for_tenant(self, tenant_id: str) -> list[Document]:
        rows = self.connection.execute(
            "SELECT document_id, tenant_id, title FROM documents WHERE tenant_id = ? ORDER BY document_id",
            (tenant_id,),
        ).fetchall()
        return [Document(**dict(row)) for row in rows]


def is_allowed(role: str, action: str) -> bool:
    """使用服务端权限表判断角色是否允许执行动作。"""

    return action in ROLE_ACTIONS.get(role, set())


def main() -> None:
    repository = TenantDocuments()
    repository.add(Document("doc-001", "tenant-a", "A 租户知识库"))
    repository.add(Document("doc-002", "tenant-b", "B 租户私有文档"))
    print(json.dumps({"documents": [asdict(item) for item in repository.list_for_tenant("tenant-a")], "viewer_can_write": is_allowed("viewer", "write")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
