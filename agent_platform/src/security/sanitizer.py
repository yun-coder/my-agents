"""输入净化器：清理用户输入中的潜在攻击向量。"""

from __future__ import annotations

import re


class InputSanitizer:
    """清理用户输入，移除危险字符和模式。"""

    MAX_LENGTH = 5000
    DANGEROUS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript\s*:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
    ]

    def sanitize(self, text: str) -> str:
        """清理输入文本，去除 HTML 标签和危险模式。"""
        clean = text.strip()[: self.MAX_LENGTH]
        for pattern in self.DANGEROUS_PATTERNS:
            clean = pattern.sub("[已过滤]", clean)
        return clean
