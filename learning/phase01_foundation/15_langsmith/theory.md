# 15 LangSmith 调试追踪

## 学习目标

- 理解 Trace、Run、标签和项目。
- 追踪一次模型调用的输入、输出、耗时和错误。
- 知道可观测性不等于业务评估。

## 核心概念

| 概念 | 说明 |
|---|---|
| Trace | 一次完整用户请求 |
| Run | Trace 中的一步，例如模型、工具或检索 |
| Project | Trace 的逻辑分组 |
| Evaluation | 对输出质量做离线或在线评估 |

## 本仓库配置

根目录 `ResponsesAPI.py` 已使用：

- `LANGSMITH_TRACING`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `wrap_openai`
- `@traceable`

本章示例缩小到一个最小调用，便于理解。

## 参考资料

- [LangSmith Documentation](https://docs.langchain.com/langsmith/home)
- [Trace LangChain Applications](https://docs.langchain.com/langsmith/trace-with-langchain)

## 验收清单

- 能解释 Trace 与 Run。
- 能在 LangSmith 中找到一次调用。
- 能说明 Trace 数据为什么可能包含敏感信息。
