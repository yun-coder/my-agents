# 25. LLM 可观测性：Langfuse / Phoenix / Helicone

## 学习目标

- 区分 trace、span、observation 和 event。
- 理解为什么 Agent 调试需要记录模型、工具、检索和审批过程。
- 会在不泄露敏感信息的前提下记录延迟、Token 和结果状态。

## 核心概念

普通 Web 服务常按一次 HTTP 请求记录 trace。Agent 的一次请求可能经历多轮推理、工具调用、检索和人工审批，因此需要更细粒度的 observation。

| 字段 | 用途 |
| --- | --- |
| `trace_id` | 串联一次用户任务 |
| `observation_id` | 标识一个模型、工具或检索步骤 |
| `kind` | 区分 `llm`、`tool`、`retrieval`、`approval` |
| `latency_ms` | 定位慢步骤 |
| `input_tokens` / `output_tokens` | 估算成本 |
| `status` | 区分成功、拒绝和失败 |

日志中不应直接写入 API Key、完整身份证号、密码或未经处理的用户隐私。对于输入输出正文，可以只记录摘要、哈希或经过脱敏的副本。

## 示例说明

`demo.py` 使用标准库构造一个 trace，记录检索和模型步骤。真实项目中可以将同样的字段映射到 Langfuse、Phoenix 或 Helicone。

## 运行

```powershell
python .\learning\phase02_production\25_observability\demo.py
```

## 延伸阅读

- [Langfuse Observability 官方文档](https://langfuse.com/docs/observability/overview)
- [Arize Phoenix Tracing 官方文档](https://arize.com/docs/phoenix/tracing)
- [Helicone Observability 官方文档](https://docs.helicone.ai/features/advanced-usage/observability)
