"""带重试与幂等记录的内存任务队列。"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
import json


@dataclass(frozen=True)
class Task:
    """排队等待 worker 执行的任务。"""

    task_id: str  # 稳定 ID，用于幂等去重。
    payload: str  # 任务输入摘要。
    attempt: int = 0  # 当前已经尝试的次数。
    max_attempts: int = 3  # 允许执行的最大次数。


def process_queue(tasks: deque[Task]) -> list[dict[str, object]]:
    """模拟 worker：第一次失败，第二次成功，重复任务跳过。"""

    completed: set[str] = set()
    events: list[dict[str, object]] = []
    while tasks:
        task = tasks.popleft()
        if task.task_id in completed:
            events.append({"task_id": task.task_id, "status": "duplicate-skipped"})
            continue
        next_attempt = task.attempt + 1
        if next_attempt == 1 and next_attempt < task.max_attempts:
            tasks.append(replace(task, attempt=next_attempt))
            events.append({"task_id": task.task_id, "status": "retrying", "attempt": next_attempt})
            continue
        completed.add(task.task_id)
        events.append({"task": asdict(replace(task, attempt=next_attempt)), "status": "completed"})
    return events


def main() -> None:
    tasks = deque((Task("task-001", "生成租户报表"), Task("task-001", "重复投递")))
    print(json.dumps(process_queue(tasks), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
