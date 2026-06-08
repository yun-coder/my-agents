"""安全护栏：输入/输出内容检查和 Prompt 注入检测。

检测策略：
1. 输入检查：匹配已知注入模式
2. 输出检查：匹配有害内容关键词
3. 支持自定义规则扩展
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class GuardRule:
    """一条安全规则。"""

    name: str
    patterns: list[str]
    severity: str = "medium"  # low, medium, high, critical
    action: str = "block"  # block, warn, sanitize


DEFAULT_INPUT_RULES: list[GuardRule] = [
    GuardRule(
        name="ignore_instructions",
        patterns=[
            r"ignore\s+(all\s+)?(previous|above|system)\s+(instructions?|prompt)",
            r"忘记.*指令",
            r"忽略.*规则",
            r"不要.*(遵循|遵守)",
        ],
        severity="critical",
    ),
    GuardRule(
        name="system_prompt_leak",
        patterns=[
            r"(show|reveal|print|display)\s+(your\s+)?(system\s+)?prompt",
            r"显示.*系统.*提示",
            r"打印.*系统.*指令",
        ],
        severity="high",
    ),
    GuardRule(
        name="role_override",
        patterns=[
            r"(from\s+now\s+on|从现在开始).*(you\s+are|你是)",
            r"(act\s+as|扮演|假装).*(developer|开发者|admin|管理员)",
        ],
        severity="high",
    ),
    GuardRule(
        name="hidden_instructions",
        patterns=[
            r"执行以下隐藏指令",
            r"hidden\s+instruction",
            r"<\|.*?\|>",  # 特殊标记
        ],
        severity="critical",
    ),
]

DEFAULT_OUTPUT_RULES: list[GuardRule] = [
    GuardRule(
        name="pii_phone",
        patterns=[r"1[3-9]\d{9}"],
        severity="high",
        action="warn",
    ),
    GuardRule(
        name="pii_id_card",
        patterns=[r"\d{17}[\dXx]"],
        severity="critical",
        action="block",
    ),
    GuardRule(
        name="harmful_content",
        patterns=[r"(攻击|破解|入侵).*(方法|步骤|教程)"],
        severity="critical",
    ),
]


class SecurityGuard:
    """安全护栏：检测输入/输出中的安全风险。

    用法:
        guard = SecurityGuard()
        violations = guard.check_input(user_text)
        if violations:
            print(f"检测到风险：{violations}")
    """

    def __init__(
        self,
        input_rules: list[GuardRule] | None = None,
        output_rules: list[GuardRule] | None = None,
    ) -> None:
        self._input_rules = input_rules or DEFAULT_INPUT_RULES
        self._output_rules = output_rules or DEFAULT_OUTPUT_RULES

    def _check(self, text: str, rules: list[GuardRule]) -> list[str]:
        violations: list[str] = []
        text_lower = text.lower()
        for rule in rules:
            for pattern in rule.patterns:
                if re.search(pattern, text_lower):
                    violations.append(
                        f"[{rule.severity}] {rule.name}: 匹配模式 '{pattern[:50]}...'"
                    )
        return violations

    def check_input(self, text: str) -> list[str]:
        """检查用户输入是否包含注入攻击或越权指令。"""
        return self._check(text, self._input_rules)

    def check_output(self, text: str) -> list[str]:
        """检查模型输出是否包含 PII 或有害内容。"""
        return self._check(text, self._output_rules)

    def is_safe(self, text: str) -> bool:
        """快速安全检查：输入是否可以通过基础护栏。"""
        return len(self.check_input(text)) == 0
