# 第19章 CrewAI：角色化多智能体协作框架

> CrewAI 是一个专注于"角色驱动"的多智能体框架，其设计灵感来源于电影《碟中谍》的团队协作模式。每个 Agent 拥有明确的角色（Role）、目标（Goal）和背景故事（Backstory），通过任务分解和委派完成复杂工作。

---

## 1. 概念概述

### 1.1 什么是 CrewAI

CrewAI 是一个轻量级的多智能体编排框架，核心理念是"为每个 Agent 定义角色，让 Agent 像人类团队一样协作"。与 AutoGen 的对话模式不同，CrewAI 采用"任务委派"模式：一个高级 Agent（如管理者）可以将子任务委派给其他 Agent 执行。

### 1.2 三大核心抽象

CrewAI 围绕三个核心抽象构建：

- **Agent**：一个智能体角色，拥有 role、goal、backstory、llm 配置和工具
- **Task**：一个具体任务，描述任务描述、期望输出、负责 Agent 和可用工具
- **Crew**：Agent 和 Task 的集合，定义执行流程（顺序或层级）

### 1.3 与 AutoGen 的核心差异

| 维度 | CrewAI | AutoGen/AG2 |
|------|--------|-------------|
| 协作模式 | 任务委派（Manager -> Worker） | 对话式协作 |
| 流程控制 | 预定义 Process（sequential/hierarchical） | 对话驱动，动态调度 |
| 角色定义 | Role/Goal/Backstory 强角色绑定 | System Message 自由定义 |
| 任务定义 | 显式的 Task 对象 | 隐式对话目标 |
| 代码执行 | 需自行集成 | 内置 CodeExecutorAgent |
| 学习曲线 | 较低，API 简洁 | 中等，概念较多 |

---

## 2. 核心原理

### 2.1 Agent 定义

CrewAI 的 Agent 通过角色、目标和背景故事三个维度来定义行为：

```python
from crewai import Agent

analyst = Agent(
    role="高级数据分析师",
    goal="从原始数据中提取有价值的商业洞察",
    backstory="""你是一名拥有十年经验的高级数据分析师，擅长使用 Python 和 SQL
进行数据清洗、分析和可视化。你的报告总是数据驱动、洞察深刻。""",
    verbose=True,
    allow_delegation=False,
    max_iter=15,
    max_rpm=5,
    llm_config={
        "model": "gpt-4o",
        "api_key": "sk-your-api-key",
        "temperature": 0.3,
    },
)
```

### 2.2 Task 定义

Task 是 CrewAI 中的工作单元，包含明确的目标描述和期望输出：

```python
from crewai import Task

cleaning_task = Task(
    description="""对 sales_data.csv 进行数据清洗：
1. 检查并处理缺失值
2. 去除重复记录
3. 标准化日期格式
4. 检测并处理异常值
将清洗后的数据保存为 cleaned_sales.csv。""",
    expected_output="清洗后的数据文件 cleaned_sales.csv 和数据质量报告",
    agent=analyst,
    tools=[],
    context=[],
)
```

### 2.3 Crew 与 Process

Crew 将 Agent 和 Task 组合在一起，定义执行流程：

**顺序执行（Sequential Process）：**

```python
from crewai import Crew, Process

crew = Crew(
    agents=[analyst, visualizer, reporter],
    tasks=[cleaning_task, analysis_task, visualization_task, report_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()
```

**层级执行（Hierarchical Process）：**

在层级模式下，CrewAI 会自动创建一个"管理者"Agent，负责将任务分派给其他 Agent：

```python
manager = Agent(
    role="项目管理者",
    goal="协调团队成员高效完成任务",
    backstory="你是一名经验丰富的项目经理，擅长任务分配和质量把控。",
    allow_delegation=True,
    llm_config={"model": "gpt-4o", "api_key": "sk-xxx"},
)

hierarchical_crew = Crew(
    agents=[analyst, visualizer, reporter],
    tasks=[analysis_project_task],
    process=Process.hierarchical,
    manager_agent=manager,
    verbose=True,
)

result = hierarchical_crew.kickoff()
```

### 2.4 工具集成

CrewAI 支持通过 @tool 装饰器自定义工具：

```python
from crewai.tools import tool
import pandas as pd

@tool("数据加载工具")
def load_data(filepath: str) -> str:
    """加载 CSV 或 Excel 数据文件。"""
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    elif filepath.endswith(".xlsx"):
        df = pd.read_excel(filepath)
    else:
        return "不支持的文件格式"
    return f"数据加载成功：{df.shape[0]} 行, {df.shape[1]} 列\n列名：{list(df.columns)}"

@tool("数据统计工具")
def describe_data(filepath: str) -> str:
    """生成数据集的描述性统计。"""
    df = pd.read_csv(filepath)
    desc = df.describe().to_string()
    missing = df.isnull().sum().to_dict()
    return f"描述性统计：\n{desc}\n\n缺失值：{missing}"

analyst_with_tools = Agent(
    role="数据分析师",
    goal="分析数据并生成统计报告",
    backstory="你擅长使用数据分析工具。",
    tools=[load_data, describe_data],
)
```

### 2.5 任务委派机制

在层级模式中，CrewAI 的任务委派流程如下：

- 管理者 Agent 分析总体任务，拆解子任务
- 根据各 Agent 的 role 和 goal 匹配最合适的执行者
- 发送委派消息给对应 Agent
- 收集结果，汇总成最终报告

```python
senior_analyst = Agent(
    role="高级分析师",
    goal="领导分析团队完成项目",
    backstory="你是团队负责人，可以委派任务给初级分析师。",
    allow_delegation=True,
)

junior_analyst = Agent(
    role="初级分析师",
    goal="执行分配的分析任务",
    backstory="你是团队中的初级成员，听从高级分析师的指导。",
    allow_delegation=False,
)
```

---

## 3. 实战指南

### 3.1 完整的数据分析团队

以下代码构建一个完整的 CrewAI 数据分析工作流：

```python
"""CrewAI 数据分析团队：从数据采集到报告生成的全流程。"""
from __future__ import annotations
import os
from typing import Any
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool


# ---- 工具定义 ----

@tool("文件搜索工具")
def search_files(directory: str, pattern: str) -> str:
    """在指定目录中搜索匹配模式的数据文件。"""
    from pathlib import Path
    p = Path(directory)
    results = [str(f) for f in p.rglob(pattern) if f.is_file()]
    if not results:
        return f"未找到匹配 {pattern} 的文件"
    return "\n".join(results[:20])


@tool("数据分析工具")
def analyze_data(filepath: str) -> str:
    """对 CSV 数据文件进行基本统计分析。"""
    import pandas as pd
    try:
        df = pd.read_csv(filepath)
        info = {
            "行数": df.shape[0],
            "列数": df.shape[1],
            "列名": list(df.columns),
            "数据类型": {c: str(d) for c, d in df.dtypes.items()},
            "缺失值": {c: int(v) for c, v in df.isnull().sum().items()},
        }
        return f"数据分析结果：\n{info}"
    except Exception as e:
        return f"分析失败：{e}"


@tool("报告生成工具")
def generate_report(analysis: str, chart_path: str | None = None) -> str:
    """生成格式化的 Markdown 报告。"""
    report_parts = [
        "# 数据分析报告\n",
        f"## 分析摘要\n{analysis}\n",
    ]
    if chart_path:
        report_parts.append(f"![图表]({chart_path})\n")
    report_parts.append("---\n*报告由 AI 自动生成*")
    return "\n".join(report_parts)


# ---- Agent 定义 ----

def create_analyst_team(api_key: str, base_url: str) -> list[Agent]:
    """创建数据分析团队。"""
    llm_config = {
        "model": "gpt-4o",
        "api_key": api_key,
        "base_url": base_url,
        "temperature": 0.3,
    }

    data_engineer = Agent(
        role="数据工程师",
        goal="从指定位置找到并加载数据文件",
        backstory="""你擅长在文件系统中查找数据，并能处理各种格式的数据文件。
确保文件存在且格式正确后再交给数据分析师。""",
        tools=[search_files],
        llm_config=llm_config,
        verbose=True,
    )

    data_analyst = Agent(
        role="数据分析师",
        goal="对数据进行深入分析，提取关键洞察",
        backstory="""你是一名资深数据分析师，精通统计学和数据分析方法。
你总是能发现数据中的重要模式和趋势。""",
        tools=[analyze_data],
        llm_config=llm_config,
        verbose=True,
    )

    report_writer = Agent(
        role="报告撰写人",
        goal="撰写清晰、专业的数据分析报告",
        backstory="""你是一名技术写作专家，擅长将复杂分析结果转化为
通俗易懂的报告。你的报告结构清晰、数据准确。""",
        tools=[generate_report],
        llm_config=llm_config,
        verbose=True,
    )

    return [data_engineer, data_analyst, report_writer]


# ---- Task 定义 ----

def create_analysis_tasks() -> list[Task]:
    """创建数据分析任务链。"""
    search_task = Task(
        description="""在 ./data 目录中查找所有 CSV 和 Excel 文件。
列出找到的所有数据文件路径和文件大小。""",
        expected_output="数据文件列表，包含路径和大小信息",
    )

    analysis_task = Task(
        description="""对找到的数据文件进行完整分析，包括：
1. 数据基本结构（行数、列数、数据类型）
2. 数据质量检查（缺失值、异常值）
3. 基本统计信息（均值、中位数、标准差）
4. 初步趋势分析""",
        expected_output="完整的数据分析结果，包含统计指标和质量报告",
    )

    report_task = Task(
        description="""基于分析结果撰写专业的 Markdown 数据分析报告。
报告应包含：
1. 执行摘要
2. 数据概况
3. 关键发现
4. 结论与建议""",
        expected_output="格式规范的 Markdown 报告文件",
    )

    return [search_task, analysis_task, report_task]


# ---- 执行 ----

def run_crew_analysis(
    api_key: str,
    base_url: str,
    *,
    process: Process = Process.sequential,
) -> dict[str, Any]:
    """运行数据分析 Crew。"""
    agents = create_analyst_team(api_key, base_url)
    tasks = create_analysis_tasks()

    for i, task in enumerate(tasks):
        task.agent = agents[i]

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=process,
        verbose=True,
        max_rpm=30,
    )

    result = crew.kickoff()
    return {"result": result, "tasks_output": [t.output for t in tasks]}


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY", "your-api-key")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    output = run_crew_analysis(api_key, base_url)
    print("最终报告：", output["result"])
```

### 3.2 层级流程中的管理者模式

使用层级流程时，CrewAI 自动创建管理者 Agent：

```python
manager_llm_config = {
    "model": "gpt-4o",
    "api_key": "sk-xxx",
    "temperature": 0.1,
}

hierarchical_crew = Crew(
    agents=[data_engineer, data_analyst, report_writer],
    tasks=[main_task],
    process=Process.hierarchical,
    manager_llm=manager_llm_config,
    verbose=True,
    memory=True,
)
```

---

## 4. 最佳实践

1. **角色设计要具体**：Role 和 Goal 应该具体清晰，避免泛泛而谈。"数据分析师"不如"电商销售数据分析师"有效。

2. **Backstory 提供行为锚定**：背景故事应该暗示 Agent 的行为风格和工作方法，而不仅仅是背景介绍。

3. **任务粒度适中**：Task 太大则 Agent 无法聚焦，太小则管理开销过大。一个 Task 对应一个可独立验证的输出。

4. **顺序流程适合确定性场景**：当任务步骤明确、依赖关系清晰时，sequential process 更高效。

5. **层级流程适合复杂场景**：当任务需要动态拆解和适配时，hierarchical process 更灵活。

6. **工具的 description 要详细**：CrewAI 的 LLM 根据工具的 description 决定何时使用，描述越清晰越准确。

7. **限制 API 调用频率**：使用 max_rpm 控制请求频率，避免触发 API 限流。

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| 角色冲突 | 多个 Agent 的 role 定义相似，导致任务分配混乱 | 确保每个 Agent 有明确的职责边界 |
| 任务歧义 | Task description 不够具体，Agent 理解偏差 | 使用 bullet point 列出具体步骤 |
| 层级模式 LLM 消耗大 | Manager Agent 每次任务分配都调用 LLM | 顺序流程能完成的场景不用层级模式 |
| 工具调用失败 | Agent 使用了错误参数或在不存在的路径上操作 | 工具函数要有完善的错误处理 |
| 循环委派 | Agent 之间互相委派任务，形成死循环 | ensure allow_delegation 只对必要 Agent 开启 |
| 输出格式不一致 | Task 的 expected_output 不明确导致输出格式混乱 | 在 expected_output 中给出格式示例 |

---

## 6. API Key 依赖

| 组件 | 是否需要 API Key | 说明 |
|------|-----------------|------|
| Agent | 是 | 每个 Agent 需要 LLM API Key |
| Crew（顺序流程） | 是 | 所有 Agent 都需要 LLM 调用 |
| Crew（层级流程） | 是 | 额外需要 Manager Agent 的 LLM |
| 工具函数 | 否 | 工具本身不需要 API Key |
| CrewAI 框架 | 否 | 开源框架，无需 Key（但无 LLM 则无法运行） |

**关键提示**：CrewAI 所有 Agent 都需要 LLM 配置，未配置时将报错：ValueError: LLM configuration is required for Agent。

---

## 7. 技术关系

```
┌─────────────────────────────────────────────────┐
│                     Crew                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Agent 1 │  │  Agent 2 │  │  Agent 3 │       │
│  │ (角色 A) │  │ (角色 B) │  │ (角色 C) │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │              │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐       │
│  │  Task 1  │→ │  Task 2  │→ │  Task 3  │ (Seq)│
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                  │
│  ┌──────────────────────────── 层级模式 ──────┐  │
│  │         Manager Agent                       │  │
│  │    ┌──────┐  ┌──────┐  ┌──────┐            │  │
│  │    │Agent1│  │Agent2│  │Agent3│            │  │
│  │    └──────┘  └──────┘  └──────┘            │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         │
         ▼
    ┌──────────┐
    │ LLM API  │ ←── 所有 Agent 共享或独立配置
    └──────────┘
```

---

## 8. 验收清单

- [ ] 理解 Agent 的 role / goal / backstory 三个核心属性
- [ ] 掌握 Task 的定义方式和 expected_output 的重要性
- [ ] 理解 sequential 和 hierarchical 两种 Process 的区别
- [ ] 学会使用 @tool 装饰器自定义工具
- [ ] 理解层级流程中的任务委派机制
- [ ] 能配置 Crew 级别的记忆功能
- [ ] 理解 CrewAI 和 AutoGen 在理念上的根本差异
- [ ] 判断何时使用 CrewAI 而非 AutoGen 或 LangGraph
- [ ] 掌握 max_rpm 和 max_iter 等资源控制参数
- [ ] 能够通过 crew.kickoff() 启动并获取执行结果

---

## 9. 学习资源

- CrewAI 官方文档：https://docs.crewai.com/
- CrewAI 示例仓库：https://github.com/crewAIInc/crewAI-examples
- CrewAI 核心概念：https://docs.crewai.com/core-concepts/Agents/
- CrewAI Process 对比：https://docs.crewai.com/core-concepts/Processes/
- CrewAI vs AutoGen 分析：https://docs.crewai.com/migration-guide/autogen/
- Agents 最佳实践：https://docs.crewai.com/how-to/LLM-Connections/
