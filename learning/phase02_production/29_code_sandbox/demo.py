"""教学级代码执行策略检查，不可替代生产沙箱。"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import json
import subprocess
import sys


FORBIDDEN_NODES = (ast.Import, ast.ImportFrom, ast.Attribute)


@dataclass(frozen=True)
class ExecutionResult:
    """一次受限执行的结果摘要。"""

    accepted: bool  # 代码是否通过教学级静态策略。
    stdout: str  # 子进程标准输出。
    stderr: str  # 子进程错误输出。
    reason: str  # 拒绝或执行结果说明。


def validate(code: str) -> tuple[bool, str]:
    """拒绝导入模块和属性访问，缩小示例可执行范围。"""

    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            return False, f"禁止的语法节点：{type(node).__name__}"
    return True, "策略检查通过"


def run_checked(code: str) -> ExecutionResult:
    """在独立解释器中执行通过策略检查的代码，并设置超时。"""

    accepted, reason = validate(code)
    if not accepted:
        return ExecutionResult(False, "", "", reason)
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        check=False,
        text=True,
        timeout=2,
    )
    return ExecutionResult(completed.returncode == 0, completed.stdout.strip(), completed.stderr.strip(), reason)


def main() -> None:
    examples = ("print(sum([2, 3, 5]))", "import os\nprint(os.listdir('.'))")
    print(json.dumps([asdict(run_checked(code)) for code in examples], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
