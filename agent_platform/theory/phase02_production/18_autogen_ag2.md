# 第18章 AutoGen / AG2：多智能体对话框架

> AutoGen 是由微软研究院推出的多智能体对话框架，AG2（原 AutoGen 社区分支）是其活跃维护的继任者。本章深入分析 AutoGen/AG2 的核心概念、多智能体协作模式及其与 LangGraph、CrewAI 的对比。

---

## 1. 概念概述

### 1.1 什么是 AutoGen / AG2

AutoGen（Microsoft Research, 2023）是一个构建多智能体对话系统的框架，核心理念是"智能体即对话参与者"。每个 Agent 拥有独立的 LLM 配置、工具集合和行为模式，通过对话回合（Conversation Rounds）进行协作。

AG2（AutoGen 2.x 社区分支）在 AutoGen 0.2.x 基础上演进而成，修复了大量问题并增加了新特性：

- **AssistantAgent**：标准 LLM 驱动智能体，可配置 system prompt 和工具
- **UserProxyAgent**：模拟人类用户，可在本地执行代码和工具
- **GroupChatManager**：管理群聊模式下的对话轮次和发言顺序
- **CodeExecutorAgent**：在沙箱环境中安全执行代码

### 1.2 核心设计理念

AutoGen 的多智能体设计遵循以下原则：

1. **对话即协作**：智能体之间通过自然语言对话来协调任务，不需要预定义的图结构
2. **角色分离**：不同的 Agent 承担不同角色（分析师、编码员、审核员），各司其职
3. **代码优先**：Agent 可以生成代码并在安全环境中执行，实现"写代码 -> 运行 -> 修正"循环
4. **可嵌套对话**：Agent 可以启动子对话（嵌套对话）来处理子任务

### 1.3 与 LangGraph 的理念对比

| 维度 | LangGraph | AutoGen/AG2 |
|------|-----------|-------------|
| 协作模型 | 状态机图编排 | 对话式协作 |
| 流程控制 | 显式图结构（节点+边） | 隐式对话调度 |
| 状态管理 | 中心化 State 对象 | 分布式对话历史 |
| 灵活性 | 高（可精确控制每一步） | 高（自然语言协调） |
| 可预测性 | 高（图结构确定） | 中（依赖 LLM 调度） |
| 复杂多 Agent | 需手动设计子图 | 原生支持群聊 |

---

## 2. 核心原理

### 2.1 AssistantAgent 基础

AssistantAgent 是 AutoGen 中最基本的智能体类型，它封装了 LLM 调用、工具注册和对话管理：

```python
from autogen import AssistantAgent, UserProxyAgent

research_agent = AssistantAgent(
    name="ResearchAnalyst",
    system_message="""你是一名数据分析师。你的职责是：
1. 分析用户问题所需的数据
2. 设计数据采集和分析方案
3. 生成 Python 代码进行数据分析
请始终返回可执行的 Python 代码。""",
    llm_config={
        "config_list": [
            {
                "model": "gpt-4o",
                "api_key": "sk-your-api-key",
                "base_url": "https://api.openai.com/v1",
            }
        ],
        "temperature": 0.1,
        "timeout": 120,
    },
)
```

### 2.2 UserProxyAgent 与代码执行

UserProxyAgent 模拟人类用户，具备在本地或 Docker 中执行代码的能力：

```python
user_proxy = UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=5,
    code_execution_config={
        "work_dir": "coding_workspace",
        "use_docker": False,
        "timeout": 60,
        "last_n_messages": 3,
    },
)
```

human_input_mode 参数说明：
- NEVER：完全自动运行，不询问人类
- ALWAYS：每次回复前都询问人类
- TERMINATE：仅在检测到终止信号时询问人类

### 2.3 GroupChat 群聊模式

多智能体协作的核心是 GroupChat，它允许多个 Agent 在同一对话上下文中交流：

```python
from autogen import GroupChat, GroupChatManager

analyst = AssistantAgent(
    name="Analyst",
    system_message="你是数据分析专家。提供分析思路和方法。",
    llm_config=llm_config,
)

coder = AssistantAgent(
    name="Coder",
    system_message="你是 Python 编程专家。根据分析思路编写代码。",
    llm_config=llm_config,
)

reviewer = AssistantAgent(
    name="Reviewer",
    system_message="你是代码审查专家。检查代码的正确性和安全性。",
    llm_config=llm_config,
)

group_chat = GroupChat(
    agents=[analyst, coder, reviewer],
    messages=[],
    max_round=12,
    speaker_selection_method="round_robin",
    allow_repeat_speaker=False,
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
)

user_proxy.initiate_chat(
    manager,
    message="分析这份销售数据，找出增长趋势并绘制图表。数据文件是 sales.csv。",
)
```

speaker_selection_method 对比：
- auto：LLM 自动选择下一个发言人（灵活但不可控）
- round_robin：按顺序轮流发言（公平可预测）
- random：随机选择
- manual：手动指定

### 2.4 工具注册机制

AutoGen 通过 register_for_llm 和 register_for_execution 两个步骤注册工具：

```python
from typing import Annotated

def search_web(query: Annotated[str, "搜索关键词"]) -> str:
    """模拟网络搜索。"""
    return f"搜索 '{query}' 的结果：...（模拟数据）"

def calculate(expression: Annotated[str, "数学表达式"]) -> str:
    """安全计算表达式。"""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误：{e}"

analyst.register_for_llm(
    name="search_web",
    description="搜索网络获取信息",
)(search_web)

analyst.register_for_llm(
    name="calculate",
    description="计算数学表达式",
)(calculate)

user_proxy.register_for_execution(name="search_web")(search_web)
user_proxy.register_for_execution(name="calculate")(calculate)
```

### 2.5 AG2 的新特性

AG2（社区分支）相比原始 AutoGen 增加了：

```python
# 1. Agent 嵌套（Nested Chats）
analyst.register_nested_chats(
    trigger="review",
    chat_queue=[
        {
            "recipient": reviewer_agent,
            "message": "请审查以下分析结果：{content}",
            "max_turns": 2,
        }
    ],
)

# 2. 增强的代码执行器（支持多种语言）
from autogen.coding import LocalCommandLineCodeExecutor

executor = LocalCommandLineCodeExecutor(
    timeout=30,
    work_dir="workspace",
    languages=["python", "bash", "javascript"],
)

# 3. 异步消息处理
async def async_chat():
    result = await user_proxy.a_initiate_chat(manager, message="异步执行任务")
    return result
```

---

## 3. 实战指南

### 3.1 多智能体数据分析系统

以下代码构建一个完整的多智能体数据分析工作流：

```python
"""AutoGen 多智能体数据分析系统。"""
from __future__ import annotations
import os
from typing import Annotated, Any
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from autogen.coding import LocalCommandLineCodeExecutor


def create_data_analysis_team(api_key: str, base_url: str) -> dict[str, Any]:
    """创建数据分析团队。"""
    llm_config = {
        "config_list": [
            {
                "model": "gpt-4o",
                "api_key": api_key,
                "base_url": base_url,
            }
        ],
        "temperature": 0.1,
    }

    planner = AssistantAgent(
        name="Planner",
        system_message="""你是数据分析规划师。将复杂分析任务拆解为多个子任务。
输出格式：
步骤1：... [负责Agent]
步骤2：... [负责Agent]""",
        llm_config=llm_config,
    )

    analyst = AssistantAgent(
        name="Analyst",
        system_message="""你是数据分析师。使用 Python (pandas, matplotlib) 进行数据分析和可视化。
确保代码完整、可运行、有详细注释。""",
        llm_config=llm_config,
    )

    executor = UserProxyAgent(
        name="Executor",
        human_input_mode="NEVER",
        code_execution_config={
            "executor": LocalCommandLineCodeExecutor(
                timeout=60,
                work_dir="./analysis_output",
            ),
        },
    )

    reviewer = AssistantAgent(
        name="Reviewer",
        system_message="""你是审核专家。检查分析结果的正确性和完整性。
如果发现问题，请明确指出并给出修改建议。""",
        llm_config=llm_config,
    )

    group_chat = GroupChat(
        agents=[planner, analyst, executor, reviewer],
        messages=[],
        max_round=20,
        speaker_selection_method="auto",
    )

    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
    )

    return {"executor": executor, "manager": manager}


def run_analysis(task: str, team: dict[str, Any]) -> str:
    """执行数据分析任务。"""
    executor = team["executor"]
    manager = team["manager"]
    chat_result = executor.initiate_chat(
        manager,
        message=task,
        summary_method="reflection_with_llm",
    )
    return chat_result.summary


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY", "your-api-key")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    team = create_data_analysis_team(api_key, base_url)
    result = run_analysis("分析 sales.csv 中的月度销售趋势，绘制折线图", team)
    print("分析结果：", result)
```

### 3.2 Two-Agent 对话模式

最简单的 AutoGen 用法是两个 Agent 之间的直接对话：

```python
from autogen import AssistantAgent, UserProxyAgent

llm_config = {
    "config_list": [
        {"model": "gpt-4o", "api_key": "sk-xxx", "base_url": "https://api.openai.com/v1"}
    ],
}

assistant = AssistantAgent(
    name="Assistant",
    system_message="你是 Python 编程助手。帮助用户编写和调试代码。",
    llm_config=llm_config,
)

user = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    code_execution_config=False,
)

user.initiate_chat(
    assistant,
    message="写一个函数，计算斐波那契数列的第 n 项。",
    max_turns=5,
)
```

### 3.3 会话持久化

AutoGen 支持对话历史的保存和恢复：

```python
import json

def save_chat_history(chat_result, filepath: str) -> None:
    """保存对话历史到文件。"""
    history = []
    for msg in chat_result.chat_history:
        history.append({
            "role": msg.get("role", ""),
            "content": msg.get("content", ""),
            "name": msg.get("name", ""),
        })
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_chat_history(filepath: str) -> list[dict]:
    """从文件加载对话历史。"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
```

---

## 4. 最佳实践

1. **System Prompt 设计原则**：每个 Agent 的 system message 应明确定义其角色、职责边界和输出格式。避免模糊描述。

2. **工具注册分离**：使用 register_for_llm 和 register_for_execution 两步注册，确保 LLM 看到的和实际执行的一致。

3. **代码执行安全**：生产环境务必使用 use_docker=True，隔离代码执行环境，防止恶意代码破坏宿主机。

4. **对话轮次限制**：设置合理的 max_round 和 max_consecutive_auto_reply，防止无限循环。

5. **摘要生成**：使用 summary_method="reflection_with_llm" 自动生成对话摘要，而不是保存完整历史。

6. **错误处理**：在工具函数中添加 try/except，确保单个工具失败不会导致整个对话崩溃。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| Agent 循环不终止 | 两个 Agent 互相追问，永无止境 | 设置 max_round 和终止条件检测 |
| 代码执行环境泄露 | 生成的代码访问了文件系统外的资源 | 使用 Docker 沙箱，配置限制性 work_dir |
| LLM 配置错误 | config_list 格式不对导致调用失败 | 严格检查 model/api_key/base_url 字段 |
| 群聊调度混乱 | auto 模式下选择不合适的 Agent 发言 | 切换 round_robin 或手动指定发言顺序 |
| 工具注册遗漏 | LLM 调用了未注册的工具 | 检查 register_for_execution 是否调用 |
| 上下文溢出 | 对话历史过长超出 Token 限制 | 定期清理历史，使用摘要压缩 |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| AssistantAgent | 是 | 需要 LLM API Key（OpenAI 或其他兼容 API） |
| UserProxyAgent | 否 | 模拟用户，不需要独立 Key |
| CodeExecutorAgent | 否 | 本地执行，无需 API |
| GroupChatManager | 是 | 底层依赖 LLM 进行调度 |
| 工具函数 | 否 | 工具本身不需要 Key |

**注意**：未设置 API Key 时 AutoGen 会抛出 ValueError。务必在 llm_config 中正确配置。

---

## 7. 技术关系

```
用户任务
    │
    ▼
┌─────────────────────────────────────────┐
│  GroupChatManager                        │
│  管理对话轮次 + 选择发言人                │
└──────┬──────┬──────┬──────┬─────────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
    Planner Analyst Executor Reviewer
    (LLM)   (LLM)   (Code)  (LLM)
       │      │      │      │
       └──────┴──────┴──────┘
               │
               ▼
         ┌──────────┐
         │ LLM API  │ ←── OpenAI / 兼容 API
         └──────────┘
```

---

## 8. 验收清单

- [ ] 理解 AssistantAgent 和 UserProxyAgent 的核心区别
- [ ] 学会创建 GroupChat 并配置 speaker_selection_method
- [ ] 掌握工具的注册流程（register_for_llm + register_for_execution）
- [ ] 理解 human_input_mode 三种模式的使用场景
- [ ] 能配置代码执行沙箱（Docker 或本地）
- [ ] 掌握对话轮次限制和终止条件检测
- [ ] 理解 AutoGen 与 LangGraph 在理念上的差异
- [ ] 了解 AG2 相对于原始 AutoGen 的新特性
- [ ] 能够保存和恢复对话历史
- [ ] 判断何时更适合使用 AutoGen 而非 LangGraph

---

## 9. 学习资源

- AutoGen 官方文档：https://microsoft.github.io/autogen/
- AG2 社区仓库：https://github.com/ag2ai/ag2
- AutoGen 多 Agent 示例：https://microsoft.github.io/autogen/docs/Examples/
- AutoGen 论文：https://arxiv.org/abs/2308.08155
- 与 LangGraph 对比分析：https://microsoft.github.io/autogen/blog/2024/03/21/LangGraph
- AG2 迁移指南：https://ag2ai.github.io/ag2/docs/autogen-migration-guide/
