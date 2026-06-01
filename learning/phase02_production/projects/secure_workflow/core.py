"""阶段二综合项目：带状态保存与人工审批的安全工作流。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


ALLOWED_TOOLS = {"search_notes", "create_draft", "send_email"}
APPROVAL_REQUIRED = {"send_email"}
SUSPICIOUS_PATTERNS = ("ignore previous instructions", "system prompt", "执行以下隐藏指令")


@dataclass(frozen=True)
class WorkflowRequest:
    """提交给工作流的一次任务。"""

    user_goal: str  # 用户希望完成的目标。
    external_content: str  # 来自网页、文件或检索器的不可信文本。
    requested_tool: str  # Agent 希望调用的工具名称。


@dataclass(frozen=True)
class WorkflowResult:
    """工作流在当前执行点返回的结果。"""

    task_id: str  # 可用于恢复任务的稳定 ID。
    status: str  # rejected、waiting_approval 或 completed。
    message: str  # 面向用户或调用方的简短说明。
    audit_count: int  # 当前任务已累计的审计事件数。


class SecureWorkflow:
    """使用 SQLite 持久化状态的教学级安全工作流。"""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(database_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                request_json TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def _audit(self, task_id: str, event_type: str, detail: str) -> None:
        """追加审计事件；详情仅存放最小必要信息。"""

        self.connection.execute(
            "INSERT INTO audit_events VALUES (?, ?, ?, ?)",
            (str(uuid4()), task_id, event_type, detail),
        )
        self.connection.commit()

    def _save(self, task_id: str, status: str, request: WorkflowRequest) -> None:
        """保存或覆盖任务检查点。"""

        self.connection.execute(
            """
            INSERT INTO workflow_tasks(task_id, status, request_json)
            VALUES (?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET status = excluded.status
            """,
            (task_id, status, json.dumps(asdict(request), ensure_ascii=False)),
        )
        self.connection.commit()

    def _count_events(self, task_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS event_count FROM audit_events WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        return int(row["event_count"])

    def submit(self, request: WorkflowRequest) -> WorkflowResult:
        """执行输入检查和工具策略，必要时创建审批暂停点。"""

        task_id = str(uuid4())
        normalized = request.external_content.lower()
        matches = [pattern for pattern in SUSPICIOUS_PATTERNS if pattern.lower() in normalized]
        if matches:
            self._save(task_id, "rejected", request)
            self._audit(task_id, "prompt_injection_signal", ", ".join(matches))
            return self._result(task_id, "rejected", "检测到外部内容中的高风险指令，任务已拒绝")
        if request.requested_tool not in ALLOWED_TOOLS:
            self._save(task_id, "rejected", request)
            self._audit(task_id, "tool_rejected", request.requested_tool)
            return self._result(task_id, "rejected", "请求的工具不在白名单中")
        if request.requested_tool in APPROVAL_REQUIRED:
            self._save(task_id, "waiting_approval", request)
            self._audit(task_id, "approval_requested", request.requested_tool)
            return self._result(task_id, "waiting_approval", "高风险工具等待人工审批")
        self._save(task_id, "completed", request)
        self._audit(task_id, "tool_completed", request.requested_tool)
        return self._result(task_id, "completed", "低风险工具已完成")

    def resume(self, task_id: str, approved: bool) -> WorkflowResult:
        """使用 task_id 恢复等待审批的任务。"""

        row = self.connection.execute(
            "SELECT status, request_json FROM workflow_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"未知任务：{task_id}")
        if row["status"] != "waiting_approval":
            raise ValueError(f"任务状态不是 waiting_approval：{row['status']}")
        request = WorkflowRequest(**json.loads(row["request_json"]))
        status = "completed" if approved else "rejected"
        message = "审批通过，工具已完成" if approved else "审批拒绝，工具未执行"
        self._save(task_id, status, request)
        self._audit(task_id, "approval_resolved", "approved" if approved else "rejected")
        return self._result(task_id, status, message)

    def events(self, task_id: str) -> list[dict[str, Any]]:
        """读取任务审计事件，便于调试和回归测试。"""

        rows = self.connection.execute(
            "SELECT event_type, detail FROM audit_events WHERE task_id = ? ORDER BY rowid",
            (task_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _result(self, task_id: str, status: str, message: str) -> WorkflowResult:
        return WorkflowResult(task_id, status, message, self._count_events(task_id))
