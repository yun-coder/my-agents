# 05 Function Calling / Tool Use

## 学习目标

- 理解模型不会真正执行函数，它只会提出工具调用请求。
- 掌握工具 Schema、参数校验、执行、结果回传和再次生成。
- 理解工具权限边界比 Prompt 更重要。

## 完整链路

```text
用户问题
-> 把工具定义交给模型
-> 模型返回 function_call
-> 应用校验参数并执行本地函数
-> 应用回传 function_call_output
-> 模型基于工具结果生成答案
```

回传工具结果时有两类上下文串联方式：

- 使用 `previous_response_id` 引用此前响应，依赖服务端保存该响应状态。
- 由应用显式维护输入列表，把模型返回的 `function_call` 和应用生成的
  `function_call_output` 一起追加到下一轮输入。

本章 Demo 使用第二种方式，便于兼容未持久化响应状态的第三方 OpenAI 兼容端点。

## 工程实践

- 工具名称和描述要明确。
- 参数使用 JSON Schema，并关闭额外字段。
- 高风险工具增加鉴权、白名单、审批和审计。
- 网络请求、数据库写入和文件操作设置超时。
- 工具结果视为外部数据，不视为系统指令。

## 参考资料

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)

## 验收清单

- 能画出一次工具调用循环。
- 能解释为什么模型返回工具参数后还不能直接执行高风险操作。
- 能实现工具参数校验与错误处理。
