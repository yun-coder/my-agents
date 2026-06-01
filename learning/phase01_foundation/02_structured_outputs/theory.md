# 02 结构化输出 / JSON Schema

## 学习目标

- 区分“看起来像 JSON”和“满足 Schema 的 JSON”。
- 理解 Schema、严格模式、解析、校验和错误处理。
- 用结构化输出把 LLM 接入可靠的数据处理流程。

## 为什么重要

自然语言适合人阅读，但后续程序通常需要稳定字段。结构化输出用于：

- 工单分类
- 合同字段抽取
- 表单填充
- Agent 决策结果
- API 参数生成

## 关键概念

| 概念 | 说明 |
|---|---|
| JSON Schema | 描述字段类型、必填项、枚举值和嵌套结构 |
| strict | 要求模型严格遵守支持的 Schema 子集 |
| 校验 | 模型返回后仍要在应用侧验证 |
| 失败策略 | 记录错误、重试、降级或交给人工 |

OpenAI Responses API 使用 `text.format` 配置 `json_schema`。旧式 JSON mode 只保证 JSON 合法，不保证业务字段满足约束。

## 工程实践

- Schema 尽量小而明确。
- 枚举值固定，不让模型自由创造状态。
- 使用 `additionalProperties: false` 防止意外字段。
- 不要因模型输出了 JSON 就跳过应用侧校验。

## 参考资料

- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Instructor](https://python.useinstructor.com/)

## 验收清单

- 能解释 JSON mode 与 Structured Outputs 的差异。
- 能为业务对象写出 JSON Schema。
- 能处理解析失败和兼容接口不支持该能力的情况。
