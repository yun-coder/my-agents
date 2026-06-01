"""输入脱敏、工具白名单与审批策略的离线示例。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re


ALLOWED_TOOLS = {"search_notes", "create_draft", "send_email"}
APPROVAL_REQUIRED = {"send_email"}


@dataclass(frozen=True)
class ToolDecision:
    """护栏对一次工具调用做出的决定。"""

    tool_name: str  # Agent 希望调用的工具名称。
    allowed: bool  # 工具是否位于白名单中。
    needs_approval: bool  # 即使允许调用，是否仍需人工审批。
    reason: str  # 面向日志和用户的决策原因。


def redact_pii(text: str) -> str:
    """隐藏常见邮箱和中国大陆手机号。"""

    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    return re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[REDACTED_PHONE]", text)


def decide_tool(tool_name: str) -> ToolDecision:
    """按最小权限原则判断工具是否可以执行。"""

    if tool_name not in ALLOWED_TOOLS:
        return ToolDecision(tool_name, False, False, "工具不在白名单中")
    if tool_name in APPROVAL_REQUIRED:
        return ToolDecision(tool_name, True, True, "高风险操作需要人工审批")
    return ToolDecision(tool_name, True, False, "低风险白名单工具可直接执行")


def main() -> None:
    raw_text = "请联系 learner@example.com，电话 13800138000。"
    decisions = [decide_tool("search_notes"), decide_tool("send_email"), decide_tool("delete_database")]
    print(json.dumps({"redacted": redact_pii(raw_text), "decisions": [asdict(item) for item in decisions]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
