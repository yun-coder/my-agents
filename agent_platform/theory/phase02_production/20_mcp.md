# 第20章 MCP（Model Context Protocol）：模型上下文协议

> MCP（Model Context Protocol）是由 Anthropic 推出的开放协议，旨在标准化 LLM 应用与外部数据源和工具之间的通信方式。MCP 提供了类似"USB-C 接口"的标准化连接方案，让 AI 应用能够统一接入各种数据源和工具。

---

## 1. 概念概述

### 1.1 什么是 MCP

MCP（Model Context Protocol）是一个开放的、基于 JSON-RPC 2.0 的协议，定义了 LLM 主机（Host）与 MCP 服务器（Server）之间的通信标准。它解决的核心问题是：每个 AI 应用都需要自定义集成各种数据源和工具，导致重复开发和维护困难。

MCP 的核心角色：

- **MCP Host**：发起请求的 LLM 应用（如 Claude Desktop、自定义 Agent 平台）
- **MCP Server**：提供数据访问或工具执行的轻量级服务
- **MCP Client**：Host 内部用于与 Server 通信的协议客户端
- **Transport**：Host 与 Server 之间的通信层（stdio 或 SSE）

### 1.2 MCP 的设计目标

1. **标准化**：统一的工具、资源和提示词接口定义
2. **解耦**：AI 应用逻辑与工具实现分离
3. **可发现**：Server 动态暴露可用能力，Host 运行时发现
4. **安全**：Host 控制权限，Server 运行在隔离环境

### 1.3 MCP 解决的问题

在传统 AI 应用中，集成外部工具的常见问题：

- 每个工具需要自定义 API 封装
- 工具列表硬编码在应用代码中
- 新增工具需要修改应用逻辑
- 缺乏统一的认证和安全机制

MCP 通过标准化的协议层解决这些问题，让工具集成变为"即插即用"。

---

## 2. 核心原理

### 2.1 协议架构

MCP 基于 JSON-RPC 2.0 协议，定义了三种核心能力类型：

**工具（Tools）：** 可被 LLM 调用的函数，类似 OpenAI Function Calling。
- 包含名称、描述和参数 Schema
- 执行后返回结果给 LLM

**资源（Resources）：** 可被 LLM 读取的数据。
- 类似 REST API 的 GET 端点
- 返回结构化数据

**提示词（Prompts）：** 预定义的提示词模板。
- 可包含动态参数
- 帮助 LLM 更好地处理特定场景

```python
# JSON-RPC 2.0 调用示例
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "search_files",
        "arguments": {
            "directory": "/data",
            "pattern": "*.csv"
        }
    },
    "id": "req-001"
}
```

### 2.2 Transport 层

MCP 支持两种传输方式：

**stdio 传输：**
Host 启动 Server 子进程，通过标准输入/输出进行通信。适用于本地部署：

```
Host ──启动子进程──→ MCP Server
       ←──stdin/stdout──→
```

- 低延迟，无网络开销
- 安全性高，进程隔离
- 适合本地开发和生产部署

**SSE 传输（Server-Sent Events）：**
通过 HTTP 连接进行通信，Server 运行在独立进程中：

```
Host ←──SSE 事件流── MCP Server (HTTP)
Host ───HTTP POST──→ MCP Server
```

- 支持远程部署
- 适合微服务架构
- 需要处理认证和网络安全

### 2.3 标准 MCP 服务器实现

以下是一个完整的 MCP 服务器实现示例：

```python
"""标准 MCP 服务器实现：提供文件搜索和数据分析工具。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
    ListResourcesResult,
    Resource,
)

logger = logging.getLogger(__name__)


class DataAnalysisServer:
    """数据分析 MCP 服务器。"""

    def __init__(self, name: str = "data-analysis-server"):
        self._server = Server(name)
        self._register_handlers()

    def _register_handlers(self) -> None:
        """注册 MCP 处理器。"""

        @self._server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出所有可用工具。"""
            return [
                Tool(
                    name="search_files",
                    description="在指定目录中搜索文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "搜索目录",
                            },
                            "pattern": {
                                "type": "string",
                                "description": "文件匹配模式，如 *.csv",
                            },
                        },
                        "required": ["directory", "pattern"],
                    },
                ),
                Tool(
                    name="read_file",
                    description="读取文件内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径",
                            }
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="analyze_csv",
                    description="分析 CSV 文件的基本统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "CSV 文件路径",
                            }
                        },
                        "required": ["filepath"],
                    },
                ),
            ]

        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """执行工具调用。"""
            if name == "search_files":
                directory = arguments["directory"]
                pattern = arguments["pattern"]
                p = Path(directory)
                results = [str(f) for f in p.rglob(pattern) if f.is_file()]
                return [TextContent(
                    type="text",
                    text="\n".join(results[:50]) if results else "未找到文件",
                )]

            elif name == "read_file":
                path = arguments["path"]
                p = Path(path)
                if not p.exists():
                    return [TextContent(type="text", text=f"文件不存在：{path}")]
                content = p.read_text(encoding="utf-8")
                return [TextContent(type="text", text=content[:10000])]

            elif name == "analyze_csv":
                import pandas as pd
                filepath = arguments["filepath"]
                df = pd.read_csv(filepath)
                info = {
                    "rows": df.shape[0],
                    "columns": df.shape[1],
                    "dtypes": {c: str(d) for c, d in df.dtypes.items()},
                    "missing": {c: int(v) for c, v in df.isnull().sum().items()},
                }
                return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False, indent=2))]

            else:
                raise ValueError(f"未知工具：{name}")

        @self._server.list_resources()
        async def list_resources() -> list[Resource]:
            """列出可用资源。"""
            return [
                Resource(
                    uri="data://config/analysis",
                    name="分析配置",
                    description="数据分析的默认配置参数",
                    mimeType="application/json",
                ),
            ]

        @self._server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            """列出可用提示词模板。"""
            return [
                Prompt(
                    name="analyze_data",
                    description="数据分析提示词模板",
                    arguments=[
                        PromptArgument(
                            name="task",
                            description="分析任务描述",
                            required=True,
                        ),
                    ],
                ),
            ]

        @self._server.get_prompt()
        async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
            """获取提示词模板内容。"""
            if name == "analyze_data":
                task = arguments.get("task", "") if arguments else ""
                return GetPromptResult(
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"请执行以下数据分析任务：{task}\n"
                                     "步骤：\n"
                                     "1. 首先使用 search_files 查找数据文件\n"
                                     "2. 使用 analyze_csv 分析文件内容\n"
                                     "3. 基于分析结果撰写报告",
                            ),
                        ),
                    ],
                )
            raise ValueError(f"未知提示词：{name}")

    async def run_stdio(self) -> None:
        """通过 stdio 启动服务器。"""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="data-analysis-server",
                    server_version="1.0.0",
                ),
            )

    async def run_sse(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """通过 SSE 启动服务器。"""
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await self._server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="data-analysis-server",
                        server_version="1.0.0",
                    ),
                )

        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages/", endpoint=sse.handle_post_message),
            ],
        )

        import uvicorn
        await uvicorn.run(app, host=host, port=port)
```

### 2.4 MCP 客户端实现

Host 端的 MCP Client 负责连接 Server 并发现能力：

```python
"""MCP 客户端：连接远程 MCP 服务器并调用工具。"""

from __future__ import annotations

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client


class MCPClient:
    """MCP 协议客户端。"""

    async def connect_stdio(self, command: str, args: list[str]) -> None:
        """通过 stdio 连接到 MCP Server。"""
        server_params = StdioServerParameters(
            command=command,
            args=args,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 发现服务器能力
                tools = await session.list_tools()
                print(f"可用工具：{[t.name for t in tools.tools]}")
                # 调用工具
                result = await session.call_tool(
                    "search_files",
                    {"directory": "/data", "pattern": "*.csv"},
                )
                print(f"工具结果：{result.content}")

    async def connect_sse(self, url: str) -> None:
        """通过 SSE 连接到 MCP Server。"""
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                resources = await session.list_resources()
                print(f"可用资源：{[r.name for r in resources.resources]}")
```

---

## 3. 实战指南

### 3.1 构建自定义 MCP 服务器

以下代码构建一个完整的 MCP 服务器，封装文件搜索和时间查询工具：

```python
"""自定义 MCP 服务器：为 Agent 提供文件和系统工具。"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent


class AgentToolsServer:
    """Agent 工具 MCP 服务器。"""

    def __init__(self):
        self._server = Server("agent-tools-server")
        self._setup_handlers()

    def _setup_handlers(self):
        @self._server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="get_current_time",
                    description="获取当前日期和时间",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="calculate",
                    description="安全计算算术表达式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "算术表达式，如 (3+5)*2",
                            }
                        },
                        "required": ["expression"],
                    },
                ),
                Tool(
                    name="list_directory",
                    description="列出目录内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "目录路径",
                            }
                        },
                        "required": ["path"],
                    },
                ),
            ]

        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "get_current_time":
                return [TextContent(
                    type="text",
                    text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )]
            elif name == "calculate":
                expression = arguments["expression"]
                try:
                    result = eval(expression, {"__builtins__": {}}, {})
                    return [TextContent(type="text", text=str(result))]
                except Exception as e:
                    return [TextContent(type="text", text=f"计算错误：{e}")]
            elif name == "list_directory":
                path = arguments["path"]
                p = Path(path)
                if not p.exists() or not p.is_dir():
                    return [TextContent(type="text", text=f"目录不存在：{path}")]
                items = []
                for entry in p.iterdir():
                    typ = "目录" if entry.is_dir() else "文件"
                    items.append(f"[{typ}] {entry.name}")
                return [TextContent(type="text", text="\n".join(items))]
            raise ValueError(f"未知工具：{name}")

    async def run(self):
        async with stdio_server() as (read, write):
            await self._server.run(
                read, write,
                InitializationOptions(
                    server_name="agent-tools-server",
                    server_version="0.1.0",
                ),
            )


if __name__ == "__main__":
    import asyncio
    server = AgentToolsServer()
    asyncio.run(server.run())
```

### 3.2 在 Agent 中集成 MCP 客户端

```python
"""使用 MCP 工具增强 Agent 能力。"""

from __future__ import annotations
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


class MCPAgent:
    """集成 MCP 工具的 Agent。"""

    def __init__(self, server_command: str, server_args: list[str] | None = None):
        self._server_params = StdioServerParameters(
            command=server_command,
            args=server_args or [],
        )
        self._tools = []

    async def initialize(self) -> None:
        """连接 MCP 服务器并发现工具。"""
        async with stdio_client(self._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                self._tools = tools_response.tools
                print(f"已发现 {len(self._tools)} 个工具：")
                for tool in self._tools:
                    print(f"  - {tool.name}: {tool.description}")

    async def call_tool(self, name: str, arguments: dict) -> str:
        """调用远程 MCP 工具。"""
        async with stdio_client(self._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                return result.content[0].text if result.content else ""


async def main():
    agent = MCPAgent("python", ["-m", "agent_tools_server"])
    await agent.initialize()
    result = await agent.call_tool("get_current_time", {})
    print(f"当前时间：{result}")

    result = await agent.call_tool("calculate", {"expression": "(3+5)*2"})
    print(f"计算结果：{result}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. 最佳实践

1. **优先使用 stdio 传输**：对于本地部署，stdio 延迟最低且最安全。仅在需要跨越网络边界时使用 SSE。

2. **工具设计原则**：每个工具应聚焦于一个操作，参数尽量简单。复杂的业务逻辑拆分为多个工具。

3. **错误处理**：工具函数应捕获所有异常并返回友好的错误信息，而不是让 MCP 连接断开。

4. **资源清单优化**：资源 URI 使用标准化的命名规则，方便 Host 端缓存和发现。

5. **提示词模板复用**：将常用的 Agent 指令封装为 Prompt，减少重复的 System Prompt 编写。

6. **安全性考虑**：MCP Server 运行在 Host 子进程中，但文件系统访问应限制在特定目录。

7. **版本管理**：Server 在初始化时声明版本号，Host 可以据此做兼容性检查。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| JSON-RPC 格式错误 | 请求或响应不符合 JSON-RPC 2.0 规范 | 严格遵循 id/method/params/result/error 格式 |
| 工具名冲突 | 多个 Server 提供了同名工具 | 在工具名前添加命名空间前缀 |
| SSE 连接断开 | 长时间未活动导致 SSE 连接超时 | 实现心跳机制或断线重连逻辑 |
| 初始化顺序错误 | 在 initialize 完成前调用工具 | 始终先 await session.initialize() |
| 资源泄露 | 未正确关闭 Server 子进程 | 使用 async with 上下文管理器确保清理 |
| 参数校验缺失 | LLM 生成了不符合 Schema 的参数 | Server 端做二次校验，返回明确错误 |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| MCP 协议核心 | 否 | 完全开源、开放协议 |
| MCP Python SDK | 否 | MIT 许可证，无需 Key |
| MCP Server 实现 | 否 | 自定义 Server 无需 Key |
| MCP Host 应用 | 视情况而定 | 如果 Host 需要 LLM 则需要 API Key |
| 第三方 MCP Servers | 视情况而定 | 某些 Server 可能依赖付费 API |

**MCP 是免费开放协议**，所有 SDK 和协议规范均开源。但 MCP Server 内部调用的服务可能需要 API Key。

---

## 7. 技术关系

```
┌─────────────────────────────────────────────────┐
│  MCP Host（AI 应用）                              │
│                                                    │
│  ┌──────────────┐    ┌──────────────────┐        │
│  │  LLM 引擎    │◄───│  MCP Client       │        │
│  │ (Agent 决策) │    │ (JSON-RPC 调用)   │        │
│  └──────────────┘    └────────┬─────────┘        │
└──────────────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │ stdio              │ SSE                │
          ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│  MCP Server A    │  │  MCP Server B    │
│  本地文件工具     │  │  远程数据 API    │
│  Transport: stdio│  │  Transport: SSE  │
└──────────────────┘  └──────────────────┘
```

---

## 8. 验收清单

- [ ] 理解 MCP 的三层模型：Host / Server / Transport
- [ ] 掌握 Tool、Resource、Prompt 三种能力类型
- [ ] 理解 stdio 和 SSE 两种传输方式的适用场景
- [ ] 学会构建一个基本的 MCP Server
- [ ] 学会在 Agent 中集成 MCP Client
- [ ] 理解 JSON-RPC 2.0 在 MCP 中的应用
- [ ] 了解 MCP 的初始化流程（initialize -> list -> call）
- [ ] 掌握工具发现的动态机制
- [ ] 理解 MCP 与 Function Calling 的关系
- [ ] 能够将现有工具封装为 MCP 标准服务

---

## 9. 学习资源

- MCP 官方文档：https://modelcontextprotocol.io/
- MCP 规范（GitHub）：https://github.com/modelcontextprotocol/specification
- MCP Python SDK：https://github.com/modelcontextprotocol/python-sdk
- MCP 快速入门：https://modelcontextprotocol.io/quickstart
- MCP 服务器教程：https://modelcontextprotocol.io/tutorials/building-a-server
- MCP 生态（Smithery）：https://smithery.ai/
- MCP 传输对比：https://modelcontextprotocol.io/docs/concepts/transports
