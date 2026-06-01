# 10 LangChain

## 学习目标

- 理解 LangChain 是组件抽象与组合工具，不是模型本身。
- 掌握 Runnable 管道的输入、转换和输出。
- 知道何时使用高层 Agent，何时保留原生 SDK。

## 核心组件

| 组件 | 作用 |
|---|---|
| Model | 对接模型供应商 |
| Prompt | 管理提示模板 |
| Runnable | 可组合的处理步骤 |
| Retriever | 检索上下文 |
| Tool | 暴露可执行能力 |
| Output Parser | 解析输出 |

LangChain v1 的高层 Agent 以 `create_agent` 为入口，底层运行时建立在 LangGraph 上。阶段一先理解 Runnable 组合，再进入 Agent。

## 何时使用

- 多步骤处理需要统一接口时。
- 需要替换模型、Retriever 或 Tool 时。
- 需要与 LangGraph、LangSmith 组合时。

简单的一次模型调用仍可直接使用供应商 SDK。

## 参考资料

- [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Integrations](https://docs.langchain.com/oss/python/integrations/providers/overview)

## 验收清单

- 能解释 Runnable 管道。
- 能指出 LangChain、LangGraph、LangSmith 的不同职责。
- 能判断一个简单功能是否真的需要框架。
