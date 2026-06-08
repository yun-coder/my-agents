# AI Agent 基础知识

## 什么是 AI Agent

AI Agent（人工智能代理）是一种能够自主感知环境、做出决策并执行行动的智能系统。一个完整的 Agent 通常包含以下核心组件：

- **模型 (Model)**：大语言模型（LLM）作为 Agent 的大脑，负责理解和生成文本。
- **提示词 (Prompt)**：定义 Agent 的行为规范、角色设定和工作流程。
- **工具 (Tools)**：Agent 可以调用的外部功能，如搜索、计算、API 调用等。
- **记忆 (Memory)**：存储和检索对话历史、用户偏好和知识信息。
- **控制流程 (Control Flow)**：编排 Agent 的决策循环，决定何时调用工具、何时生成回答。

## Agent 的工作原理

Agent 的典型工作流程是 ReAct（Reasoning + Acting）模式：

1. 思考（Reasoning）：分析用户输入，判断需要调用哪些工具或知识。
2. 行动（Acting）：执行工具调用，获取外部信息。
3. 观察（Observation）：接收工具返回的结果。
4. 重复：根据观察结果继续思考，直到生成最终回答。

## 常见 Agent 类型

### 单 Agent 系统
最简单的 Agent 形式，一个模型驱动一个 Agent 完成特定任务。

### 多 Agent 系统
多个 Agent 协同工作，每个 Agent 承担不同的角色和职责。例如：
- 一个 Agent 负责信息检索
- 一个 Agent 负责分析推理
- 一个 Agent 负责生成最终输出

### 工作流 Agent
通过预定义的状态图来编排 Agent 的执行流程，支持条件分支、循环和人工审核节点。
