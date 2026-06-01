"""离线可运行：用标准库理解 CrewAI 的 Agent、Task 与顺序流程。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    # role：Agent 在团队中的职责。
    role: str
    # goal：Agent 本次工作目标。
    goal: str


@dataclass(frozen=True)
class Task:
    # description：需要执行的任务。
    description: str
    # expected_output：验收输出格式。
    expected_output: str
    # agent：负责执行任务的角色。
    agent: Agent


def main() -> None:
    researcher = Agent("researcher", "收集可靠资料")
    writer = Agent("writer", "把资料整理成摘要")
    tasks = [
        Task("收集 RAG 的定义", "三条要点", researcher),
        Task("整理成学习笔记", "一段摘要", writer),
    ]
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task.agent.role}: {task.description} -> {task.expected_output}")


if __name__ == "__main__":
    main()
