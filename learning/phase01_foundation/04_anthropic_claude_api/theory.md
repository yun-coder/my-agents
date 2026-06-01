# 04 Anthropic Claude API

## 学习目标

- 理解 Anthropic Messages API 的请求结构。
- 掌握 `system`、`messages`、`max_tokens` 和内容块。
- 比较 Claude Messages API 与 OpenAI Responses API 的设计差异。

## 关键区别

Anthropic Messages API 是无状态的。多轮对话时，应用程序需要提交本轮所需的历史消息。

系统提示词使用顶层 `system` 参数，不放进 `messages` 的 `system` role。消息主要使用 `user` 与 `assistant` role。

## 为什么单独学习

Claude API 不是 OpenAI 兼容接口。学习 Agent 时，应区分：

- 业务层：Prompt、工具、记忆、RAG 流程。
- 供应商适配层：不同 SDK、请求字段和响应对象。

这样后续才能做模型供应商切换。

## 配置

要运行示例，在本地 `dev.json` 增加：

```json
{
  "anthropic": {
    "api_key": "your-anthropic-api-key",
    "model": "你的 Claude 模型 ID"
  }
}
```

## 参考资料

- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Anthropic Messages Examples](https://docs.anthropic.com/en/api/messages-examples)

## 验收清单

- 能解释 Messages API 为什么要由客户端提交历史。
- 能说明 Claude 的系统提示词放在哪里。
- 能指出 OpenAI 配置不能直接代替 Anthropic 凭据。
