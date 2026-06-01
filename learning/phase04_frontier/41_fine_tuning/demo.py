"""监督微调 JSONL 样本的离线校验。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_ROLES = {"system", "user", "assistant"}


def validate_example(example: dict[str, Any]) -> list[str]:
    """返回一条聊天微调样本中的结构问题。"""

    messages = example.get("messages")
    if not isinstance(messages, list) or not messages:
        return ["messages 必须是非空数组"]
    issues: list[str] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            issues.append(f"messages[{index}] 必须是对象")
            continue
        if message.get("role") not in ALLOWED_ROLES:
            issues.append(f"messages[{index}].role 不合法")
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            issues.append(f"messages[{index}].content 必须是非空字符串")
    return issues


def validate_jsonl(path: Path) -> list[dict[str, object]]:
    """逐行解析 JSONL，并保留行号方便修复数据。"""

    results: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            example = json.loads(raw_line)
            issues = validate_example(example) if isinstance(example, dict) else ["每行必须是 JSON 对象"]
        except json.JSONDecodeError as error:
            issues = [f"JSON 解析失败：{error.msg}"]
        results.append({"line": line_number, "issues": issues})
    return results


def main() -> None:
    data_path = Path(__file__).with_name("data") / "sft_examples.jsonl"
    print(json.dumps(validate_jsonl(data_path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
