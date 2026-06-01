# 33. Agent 托管平台：LangGraph Platform / Modal / Vertex AI

## 学习目标

- 理解托管平台解决的部署问题。
- 会描述最小部署规格。
- 知道平台选型取决于状态、运行时、网络和治理要求。

## 核心概念

Agent 从 Demo 进入生产后，需要持续处理部署、扩缩容、状态、队列、密钥、日志和版本回滚。托管平台可以减少基础设施工作，但不同平台的抽象层次不同。

| 平台方向 | 适合关注 |
| --- | --- |
| LangGraph Platform / LangSmith Deployment | LangGraph 应用部署、线程与运行管理 |
| Modal | Python 函数、容器和按需计算 |
| Vertex AI Agent Engine | Google Cloud 体系内的托管 Agent 运行 |

部署配置应显式记录镜像版本、运行区域、并发上限、CPU、内存和密钥引用。密钥本身不应写入配置文件。

## 示例说明

`demo.py` 检查一份部署规格是否固定镜像版本、限制并发并只引用密钥名称。

## 运行

```powershell
python .\learning\phase03_platform\33_managed_platforms\demo.py
```

## 延伸阅读

- [LangSmith Deployment 官方文档](https://docs.langchain.com/langsmith/deployment-quickstart)
- [Modal 官方文档](https://modal.com/docs)
- [Vertex AI Agent Engine 官方文档](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
