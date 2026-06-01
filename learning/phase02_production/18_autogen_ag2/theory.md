# 18 AutoGen / AG2

## 核心概念

AutoGen 的新版主线是 AgentChat：`AssistantAgent` 表示单个智能体，团队可使用 `RoundRobinGroupChat` 等方式协作。AG2 与 AutoGen 生态存在历史关系，学习时不要把旧版 `pyautogen` 示例直接当作当前 API。

## 本章重点

- 明确 Agent 角色与职责。
- 限制协作轮次，避免无限对话。
- 高风险动作仍由确定性代码和审批节点控制。

本章默认 Demo 使用标准库模拟多角色消息流，先理解协议；接入框架时再替换为 AgentChat。

## 参考资料

- [AutoGen AgentChat Tutorial](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/index.html)
- [AutoGen API Reference](https://microsoft.github.io/autogen/stable/reference/index.html)
