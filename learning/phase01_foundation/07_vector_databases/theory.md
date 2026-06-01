# 07 向量数据库

## 学习目标

- 理解向量库负责存储、过滤、检索和集合管理。
- 区分向量数据库与 Embedding 模型。
- 用最小内存实现理解 `add` 与 `query`。

## 常见选择

| 方案 | 适合场景 |
|---|---|
| Chroma | 本地学习、小型原型 |
| Qdrant | 自部署、过滤与工程能力 |
| Pinecone | 托管服务、快速上线 |
| Weaviate | 向量检索与扩展能力 |

## 数据模型

每条记录至少包括：

- 唯一 ID
- 文本或原文定位
- 向量
- 元数据，例如来源、租户、文档类型

生产环境查询通常不是只算相似度，还会叠加租户过滤、权限过滤、时间范围和业务标签。

## 本章设计

`demo.py` 是教学用内存向量库：写入时生成并保存离线稀疏向量，查询时生成查询向量，
再执行元数据过滤、相似度排序和零相关结果过滤。理解接口后，再将内部存储替换为
Chroma 或 Qdrant 客户端。

## 参考资料

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)

## 验收清单

- 能解释向量库和 Embedding 模型的分工。
- 能按元数据过滤查询结果。
- 能指出生产系统为什么必须做租户隔离。
