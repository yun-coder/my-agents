"""Agent 工具定义：可供 LLM 调用的本地函数集合。

每个工具包含：
- 名称和描述（供 LLM 理解）
- JSON Schema 参数定义
- Python 实现函数
"""

from __future__ import annotations

import ast
import operator
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# ---- 工具实现 ----


def _search_files(directory: str, pattern: str) -> str:
    """在指定目录中搜索匹配模式的文件。"""
    p = Path(directory)
    if not p.exists():
        return f"目录 {directory} 不存在。"
    results = []
    for f in p.rglob(pattern):
        if f.is_file():
            results.append(str(f))
    if not results:
        return f"未找到匹配 {pattern} 的文件。"
    return "\n".join(results[:20])


def _get_current_time(_: str = "") -> str:
    """获取当前日期时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def _read_file(path: str) -> str:
    """安全读取文件内容（仅限文本文件，最大 50KB）。"""
    p = Path(path)
    if not p.exists():
        return f"文件 {path} 不存在。"
    if p.stat().st_size > 50 * 1024:
        return f"文件过大（>{50 * 1024}字节），无法读取。"
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "文件不是有效的 UTF-8 文本。"
    except PermissionError:
        return "没有读取权限。"


def _calculate(expression: str) -> str:
    """安全计算算术表达式。"""
    allowed_ops: dict[type, Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](_eval(node.operand))
        raise ValueError("不支持的表达式")

    try:
        result = _eval(ast.parse(expression.strip(), mode="eval").body)
        return str(result)
    except Exception as e:
        return f"计算错误：{e}"


def _get_env_var(name: str) -> str:
    """获取环境变量值（仅限非敏感变量）。"""
    safe_prefixes = ("PATH", "HOME", "USER", "LANG", "PYTHON", "LOG_", "CHROMA_")
    if not any(name.upper().startswith(p) for p in safe_prefixes):
        return "出于安全考虑，不允许读取该环境变量。"
    return os.getenv(name, f"环境变量 {name} 未设置。")


# ---- 工具描述（OpenAI Function Calling 格式）----

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "在指定目录中搜索匹配模式的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "搜索目录路径"},
                    "pattern": {"type": "string", "description": "文件匹配模式，如 *.py"},
                },
                "required": ["directory", "pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文本文件内容（最大 50KB）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "安全计算算术表达式，支持 + - * / 和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "算术表达式，如 (3+5)*2"},
                },
                "required": ["expression"],
            },
        },
    },
]

# 工具名 -> 实现函数的映射
TOOL_EXECUTORS: dict[str, Callable[..., str]] = {
    "search_files": _search_files,
    "get_current_time": _get_current_time,
    "read_file": _read_file,
    "calculate": _calculate,
}
