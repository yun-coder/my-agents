# 06 Embedding 模型
# Vector embeddings   向量嵌入

## 学习目标

- 理解 Embedding 是文本语义的数值表示。
- 使用余弦相似度衡量文本相关性。
- 知道离线稀疏词法向量与真实语义 Embedding 的差异。

## 核心流程

```text
文本 -> Embedding 模型 -> 向量
查询 -> Embedding 模型 -> 查询向量
查询向量与文档向量计算相似度 -> 排序
```

## 关键指标

- 召回准确率
- Top-k 命中率
- 延迟
- 向量维度
- 存储成本
- 多语言效果

## 本章设计

`demo.py` 默认使用离线稀疏词法向量，便于理解余弦相似度。为了适配没有空格的中文，
示例会提取英文单词，并把连续中文拆成单字和双字组合。加 `--online` 后调用 OpenAI
兼容 embeddings 端点。离线实现仍然不理解同义词和上下文，不适合生产语义检索。

如果在线请求返回 `404` 或 `400`，需要分别确认兼容端点是否实现 `/embeddings`，
以及 `dev.json` 中的 `openai.embedding_model` 是否是该服务实际支持的向量化模型。

## 参考资料

- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [OpenAI text-embedding-3-large](https://developers.openai.com/api/docs/models/text-embedding-3-large)
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)

## 验收清单

- 能解释向量与余弦相似度。
- 能比较至少三个查询的排序结果。
- 能说明为什么生产 RAG 需要真实 Embedding 模型。
