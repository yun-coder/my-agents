# 11 LlamaIndex

## 学习目标

- 理解 LlamaIndex 聚焦数据摄取、索引和查询。
- 掌握 Reader、Document、Node、Index、Query Engine 的关系。
- 知道它与手写 RAG 的对应关系。

## 核心流程

```text
Reader -> Documents -> Nodes -> VectorStoreIndex -> Query Engine
```

`SimpleDirectoryReader` 适合快速开始。生产系统通常需要更精细的解析器、切分器、元数据和持久化向量库。

## 与 LangChain 的区别

两者能力存在重叠，但关注点不同：

- LlamaIndex 更偏数据摄取、索引和查询。
- LangChain 更偏组件组合、Agent 与工具生态。
- LangGraph 更偏状态流和持久化执行。

## 本章设计

默认打印即将执行的流程。传入 `--online` 后，读取本章 `data` 目录并构建索引。
示例会显式设置 `Settings.llm` 与 `Settings.embed_model`，并把本地 `dev.json`
中的模型 ID、Embedding 模型 ID、密钥和 OpenAI 兼容根地址交给对应适配器。
对于第三方自定义 Embedding 模型 ID，示例使用 `OpenAIEmbedding(model_name=...)`，
避免被 LlamaIndex 的标准 OpenAI 模型枚举拒绝。如果第三方服务没有实现
embeddings 端点，索引构建仍会失败。

## 参考资料

- [LlamaIndex Documentation](https://docs.llamaindex.ai/en/stable/)
- [SimpleDirectoryReader](https://docs.llamaindex.ai/en/stable/module_guides/loading/simpledirectoryreader/)
- [Loading Data](https://docs.llamaindex.ai/en/stable/understanding/loading/loading/)

## 验收清单

- 能解释 Document 与 Node。
- 能运行目录加载、索引和查询。
- 能指出何时替换默认内存索引。
