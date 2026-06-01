"""GUI Agent 动作分级与审批策略。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from urllib.parse import urlparse


ALLOWED_DOMAINS = {"example.com", "docs.python.org"}
HIGH_RISK_ACTIONS = {"submit", "purchase", "delete", "type_password"}


@dataclass(frozen=True)
class GuiAction:
    """GUI Agent 提议执行的单个动作。"""

    kind: str  # 动作类型，例如 read、click、submit。
    target_url: str  # 当前动作所在页面地址。
    target_label: str  # 目标元素的人类可读标签。
    value_summary: str = ""  # 输入内容摘要，避免记录敏感原文。


@dataclass(frozen=True)
class ActionDecision:
    """策略层对 GUI 动作的判断。"""

    allowed: bool  # 是否允许进入下一步。
    needs_approval: bool  # 是否需要用户确认后才能执行。
    reason: str  # 策略判断原因。


def review(action: GuiAction) -> ActionDecision:
    """检查域名和动作风险等级。"""

    domain = urlparse(action.target_url).hostname
    if domain not in ALLOWED_DOMAINS:
        return ActionDecision(False, False, "目标域名不在白名单中")
    if action.kind in HIGH_RISK_ACTIONS:
        return ActionDecision(True, True, "高风险 GUI 动作需要人工确认")
    return ActionDecision(True, False, "低风险白名单动作可执行")


def main() -> None:
    actions = (
        GuiAction("read", "https://example.com/docs", "课程说明"),
        GuiAction("submit", "https://example.com/publish", "发布按钮", "提交课程草稿"),
    )
    print(json.dumps([{"action": asdict(item), "decision": asdict(review(item))} for item in actions], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
