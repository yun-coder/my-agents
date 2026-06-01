# 01 Prompt Engineering

## 学习目标

- 区分系统指令、用户输入、上下文和示例。
- 掌握角色设定、任务约束、分隔符、Few-shot、输出格式和失败兜底。
- 理解 Prompt 不是一句“魔法咒语”，而是可测试、可版本化的接口设计。

## 核心结构

一个稳定的 Prompt 通常包含：

1. **角色与目标**：模型在当前任务中扮演什么角色，要完成什么结果。
2. **边界**：不能做什么，信息不足时如何处理。
3. **输入数据**：用 XML、Markdown 标题或其他分隔符包裹外部内容。
4. **输出契约**：需要哪些字段、格式、语言和长度。
5. **示例**：用少量高质量样例表达判断标准。

## 常见误区

- 把外部文档和系统指令混在一起，增加提示注入风险。
- 只描述理想输出，不说明信息不足时如何返回。
- Prompt 修改后不做固定样例回归测试。
- 把业务规则全部塞进 Prompt，而不在代码中做确定性校验。

## 工程实践

- Prompt 放入独立文件或常量，建立版本号。
- 建立小型测试集，至少包含正常、边界、缺失信息和恶意输入。
- 对可验证的结果使用结构化输出和代码校验。
- 对长上下文优先保留稳定前缀，有利于缓存和复用。

## 参考资料

- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

## 验收清单

- 能解释 `instruction`、`context`、`examples`、`output contract` 的作用。
- 为同一任务写出基础版与增强版 Prompt。
- 能指出用户输入为什么必须与系统规则隔离。
