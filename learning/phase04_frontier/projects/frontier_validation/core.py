"""阶段四综合项目：前沿能力验证集。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


ALLOWED_RISK_LEVELS = {"low", "medium", "high"}


@dataclass(frozen=True)
class CapabilityCase:
    """一项前沿能力的验证记录。"""

    capability: str  # 被验证的能力名称。
    risk_level: str  # low、medium 或 high。
    score: float  # 当前验证分数，范围 0 到 1。
    pass_threshold: float  # 进入下一阶段所需分数。
    evidence: tuple[str, ...]  # 可追溯的测试证据。


@dataclass(frozen=True)
class CapabilityDecision:
    """验证集根据门槛生成的阶段决策。"""

    capability: str  # 被验证的能力名称。
    status: str  # experiment 或 candidate。
    reason: str  # 保持实验状态或进入候选状态的原因。


def load_cases(path: Path) -> list[CapabilityCase]:
    """从 JSON 文件加载并校验能力验证记录。"""

    raw_cases: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    cases = [CapabilityCase(**{**item, "evidence": tuple(item["evidence"])}) for item in raw_cases]
    for case in cases:
        if case.risk_level not in ALLOWED_RISK_LEVELS:
            raise ValueError(f"未知风险等级：{case.risk_level}")
        if not 0 <= case.score <= 1 or not 0 <= case.pass_threshold <= 1:
            raise ValueError("score 和 pass_threshold 必须在 0 到 1 之间")
        if not case.evidence:
            raise ValueError("每项能力至少需要一条证据")
    return cases


def decide(case: CapabilityCase) -> CapabilityDecision:
    """根据验证分数生成阶段决策；高风险能力仍需额外安全评审。"""

    if case.score < case.pass_threshold:
        return CapabilityDecision(case.capability, "experiment", "分数尚未达到候选门槛")
    if case.risk_level == "high":
        return CapabilityDecision(case.capability, "candidate", "达到门槛，但仍需安全评审和人工确认策略")
    return CapabilityDecision(case.capability, "candidate", "达到候选门槛")


def report(path: Path) -> list[dict[str, object]]:
    return [{"case": asdict(case), "decision": asdict(decide(case))} for case in load_cases(path)]
