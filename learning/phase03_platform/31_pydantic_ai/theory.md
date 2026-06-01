# 31. Pydantic AI

## 学习目标

- 理解 Pydantic AI 如何用类型描述 Agent 输入输出和依赖。
- 会先用 Pydantic 建立数据边界。
- 知道结构化输出仍需做业务校验。

## 核心概念

Pydantic AI 是面向 Python 的 Agent 框架。它沿用 Pydantic 模型表达结构化数据，并提供 Agent、工具、依赖注入、结构化输出等能力。

类型模型适合放在系统边界：

| 边界 | 示例 |
| --- | --- |
| 用户输入 | 工单标题、优先级、租户 ID |
| 模型输出 | 分类结果、置信度、建议动作 |
| 工具参数 | 查询条件、分页大小 |
| API 响应 | 稳定的 JSON 数据结构 |

类型校验可以发现字段缺失、范围错误和格式错误，但无法保证内容事实正确。业务规则和安全策略仍然需要独立检查。

## 示例说明

`demo.py` 使用 Pydantic 校验客服工单分类结果。示例不调用模型，因此可以稳定离线运行。

## 运行

```powershell
python .\learning\phase03_platform\31_pydantic_ai\demo.py
```

## 延伸阅读

- [Pydantic AI 官方文档](https://ai.pydantic.dev/)
- [Pydantic Models 官方文档](https://docs.pydantic.dev/latest/concepts/models/)
