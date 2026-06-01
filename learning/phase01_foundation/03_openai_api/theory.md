# 03 OpenAI API

## 学习目标

- 使用 OpenAI Python SDK 创建客户端。
- 掌握 Responses API 的文本生成与流式输出。
- 知道何时使用 `instructions`、`input`、`response.output_text`。

## Responses API

Responses API 适合构建多模态、可调用工具，并可显式串联上下文的应用。
但单次 `responses.create` 请求不会自动记住此前所有对话。需要连续上下文时，
应用应显式使用 `previous_response_id` 或 Conversation 等状态管理方式。
阶段一先学习最小文本链路：

```text
配置 -> OpenAI 客户端 -> responses.create -> output_text
```

之后再叠加：

- 结构化输出
- 图片与文件输入
- 函数调用
- Hosted tools
- 多轮状态

## 配置原则

本仓库使用 `dev.json`：

```json
{
  "openai": {
    "api_key": "本地密钥",
    "base_url": "OpenAI 或兼容接口根地址",
    "model": "模型名称"
  }
}
```

`base_url` 必须是 API 根地址，不应写成 `/responses` 完整端点。

## 兼容接口提醒

第三方兼容接口经常只实现部分 API。文本生成成功，不代表文件上传、结构化输出、Hosted tools 或 MCP 一定可用。

## 参考资料

- [OpenAI API Docs](https://developers.openai.com/api/docs)
- [OpenAI Models](https://developers.openai.com/api/docs/models)
- [OpenAI Python SDK](https://github.com/openai/openai-python)

## 验收清单

- 能从 `dev.json` 创建客户端并完成一次文本请求。
- 能解释流式输出适用于什么用户体验。
- 能区分客户端配置错误、网络错误、鉴权错误和兼容能力缺失。
