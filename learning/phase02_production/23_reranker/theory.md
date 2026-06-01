# 23 Reranker / CrossEncoder

## 核心概念

高质量 RAG 常使用两阶段检索：

```text
快速召回 Top-N -> Reranker 精排 -> 选取 Top-K 上下文
```

Embedding 召回适合大规模候选筛选；CrossEncoder 或 Rerank API 会联合阅读查询与候选文本，通常更准确但成本更高。

## 参考资料

- [Cohere Rerank](https://docs.cohere.com/docs/reranking)
- [Sentence Transformers CrossEncoder](https://www.sbert.net/examples/cross_encoder/applications/README.html)
