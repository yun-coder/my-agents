"""离线可运行：SQLite 模拟任务 checkpoint 保存与恢复。"""

from __future__ import annotations

import json
import sqlite3


def main() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE checkpoint (task_id TEXT PRIMARY KEY, step TEXT, state_json TEXT)"
    )
    state = {"tenant_id": "tenant-a", "processed": 3, "remaining": 2}
    # state_json：把可恢复的业务状态序列化保存。
    connection.execute(
        "INSERT INTO checkpoint VALUES (?, ?, ?)",
        ("task-001", "parse_documents", json.dumps(state, ensure_ascii=False)),
    )
    task_id, step, state_json = connection.execute("SELECT * FROM checkpoint").fetchone()
    print({"task_id": task_id, "step": step, "state": json.loads(state_json)})


if __name__ == "__main__":
    main()
