# 32. 开源模型：Llama / Qwen / Mistral

## 学习目标

- 理解开源权重模型和托管 API 的差异。
- 会按任务选择 Ollama、vLLM 或托管端点。
- 知道模型许可证、显存、量化和上下文长度都会影响部署决策。

## 核心概念

开源模型的“开放程度”不同：有些提供权重，有些还提供训练代码和数据说明。选型时至少检查：

| 维度 | 要问的问题 |
| --- | --- |
| 能力 | 是否满足文本、多模态、工具调用和语言需求 |
| 许可证 | 是否允许目标商业场景 |
| 资源 | 显存、并发、量化后精度是否可接受 |
| 服务层 | 是否使用 Ollama、vLLM 或云服务 |
| 运维 | 谁负责升级、监控和容量规划 |

本地学习可从 Ollama 开始。需要 OpenAI 兼容 API 和更高吞吐时，可以评估 vLLM。生产平台不应把“模型名称”与“服务地址”写死在业务代码中。

## 示例说明

`demo.py` 将模型名称、提供方、端点和上下文长度放入配置对象，并按场景选择端点。

## 运行

```powershell
python .\learning\phase03_platform\32_open_source_models\demo.py
```

## 延伸阅读

- [Meta Llama 官方站点](https://www.llama.com/)
- [Qwen 官方仓库](https://github.com/QwenLM/Qwen)
- [Mistral AI 官方文档](https://docs.mistral.ai/)
- [vLLM 官方文档](https://docs.vllm.ai/)
- [Ollama 官方文档](https://docs.ollama.com/)
