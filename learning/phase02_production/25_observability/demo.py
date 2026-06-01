"""Agent observation 的最小离线示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from time import perf_counter, sleep
from typing import Callable, TypeVar
from uuid import uuid4


T = TypeVar("T")


@dataclass(frozen=True)
class Observation:
    """一次可观测步骤的摘要。"""

    trace_id: str  # 一次用户任务的关联 ID。
    observation_id: str  # 当前步骤的唯一 ID。
    kind: str  # 步骤类型，例如 retrieval 或 llm。
    name: str  # 便于检索的步骤名称。
    latency_ms: float  # 当前步骤耗时，单位为毫秒。
    status: str  # 执行结果，例如 ok、rejected 或 error。
    input_tokens: int = 0  # 输入 Token 数；非模型步骤通常为 0。
    output_tokens: int = 0  # 输出 Token 数；非模型步骤通常为 0。


def observe(trace_id: str, kind: str, name: str, action: Callable[[], T]) -> tuple[T, Observation]:
    """执行 action，并返回结果与脱敏后的 observation。"""

    started_at = perf_counter()
    result = action()
    latency_ms = round((perf_counter() - started_at) * 1000, 3)
    observation = Observation(
        trace_id=trace_id,
        observation_id=str(uuid4()),
        kind=kind,
        name=name,
        latency_ms=latency_ms,
        status="ok",
    )
    return result, observation


def main() -> None:
    trace_id = str(uuid4())
    _, retrieval = observe(trace_id, "retrieval", "search-course-notes", lambda: sleep(0.01))
    _, generation = observe(trace_id, "llm", "draft-answer", lambda: sleep(0.01))
    generation = Observation(**{**asdict(generation), "input_tokens": 120, "output_tokens": 48})
    print(json.dumps([asdict(retrieval), asdict(generation)], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
