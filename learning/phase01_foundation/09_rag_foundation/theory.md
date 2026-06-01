# 09 RAG 基础

## 学习目标

- 理解 RAG 的五个步骤：解析、切分、向量化、召回、生成。
- 能区分检索问题与生成问题。
- 能在答案中保留来源。

## 基础架构

```text
文档 -> 解析 -> chunks -> Embedding -> 向量库
用户问题 -> Embedding -> 过滤低相关结果并取 Top-k -> 组装上下文 -> LLM 答案
```

## 为什么要保留来源

RAG 的价值不只是“回答得像真的”，而是让答案可追溯。每个 chunk 至少保留：

- 文档名
- 页码或章节
- chunk ID
- 原始文本定位

## 调试顺序

1. 先看正确文档是否被召回。
2. 再看 chunk 是否包含足够上下文。
3. 再检查 Prompt 是否要求基于资料回答。
4. 最后才考虑换模型。

## 本章设计

默认离线演示词法召回和上下文组装。传入 `--online` 后，将召回上下文提交给现有
OpenAI 兼容模型。离线实现用于理解流程，不代表生产级语义检索质量。

## 参考资料

- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [LlamaIndex RAG](https://docs.llamaindex.ai/en/stable/understanding/rag/)
- [OpenAI Cookbook](https://cookbook.openai.com/)

## 验收清单

- 能画出 RAG 数据流。
- 能输出 Top-k chunk 与来源。
- 能区分召回失败、上下文不足和生成幻觉。
