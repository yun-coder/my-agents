"""默认打印 MCP 能力；传入 --serve 启动 FastMCP stdio 服务。"""

from __future__ import annotations

import argparse


def add(left: int, right: int) -> int:
    """返回两个整数之和。"""

    return left + right


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="启动 MCP stdio 服务。")
    args = parser.parse_args()
    if not args.serve:
        print({"tool": "add", "fields": {"left": "整数", "right": "整数"}})
        return

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("缺少 mcp，请按阶段 README 安装依赖。")
        return

    mcp = FastMCP("phase02-demo")
    # tool 装饰器会根据函数签名和 docstring 生成工具 Schema。
    mcp.tool()(add)
    # stdio 适合由本地 MCP 客户端启动和管理子进程。
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
