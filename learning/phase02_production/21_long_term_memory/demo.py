"""离线可运行：SQLite 用户偏好长期记忆。"""

from __future__ import annotations

import sqlite3


def create_connection() -> sqlite3.Connection:
    # :memory: 仅用于演示；生产环境应换成持久化数据库。
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE memory (tenant_id TEXT, user_id TEXT, key TEXT, value TEXT)"
    )
    return connection


def remember(connection: sqlite3.Connection, tenant_id: str, user_id: str, key: str, value: str) -> None:
    # tenant_id 和 user_id 共同限定记忆命名空间。
    connection.execute("INSERT INTO memory VALUES (?, ?, ?, ?)", (tenant_id, user_id, key, value))


def recall(connection: sqlite3.Connection, tenant_id: str, user_id: str) -> list[tuple[str, str]]:
    rows = connection.execute(
        "SELECT key, value FROM memory WHERE tenant_id = ? AND user_id = ?",
        (tenant_id, user_id),
    )
    return list(rows)


def main() -> None:
    connection = create_connection()
    remember(connection, "tenant-a", "user-001", "language", "中文")
    remember(connection, "tenant-a", "user-001", "topic", "AI Agent")
    print(recall(connection, "tenant-a", "user-001"))


if __name__ == "__main__":
    main()
