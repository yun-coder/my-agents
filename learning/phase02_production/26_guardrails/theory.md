# 26. Guardrails：安全护栏

## 学习目标

- 理解输入、检索、输出、工具和执行五类护栏。
- 知道护栏不是一个正则表达式，而是一组分层控制。
- 会为工具调用建立最小权限白名单。

## 核心概念

护栏可以放在 Agent 链路的不同位置：

| 护栏 | 示例 |
| --- | --- |
| 输入护栏 | 拦截敏感指令、限制请求大小 |
| 检索护栏 | 标记外部内容为不可信数据 |
| 输出护栏 | 脱敏、结构校验、内容策略检查 |
| 工具护栏 | 工具白名单、参数校验、审批 |
| 执行护栏 | 沙箱、超时、网络和文件系统限制 |

NeMo Guardrails 将 rails 划分为 input、retrieval、dialog、execution 和 output 等类型。工程上应把不同风险放在相应位置处理，而不是让一条系统提示词承担所有安全职责。

## 示例说明

`demo.py` 演示：

- 对邮箱和手机号进行脱敏。
- 根据白名单判断工具是否允许调用。
- 高风险工具必须进入人工审批。

## 运行

```powershell
python .\learning\phase02_production\26_guardrails\demo.py
```

## 延伸阅读

- [NeMo Guardrails 官方文档](https://docs.nvidia.com/nemo/guardrails/latest/about/rails.html)
- [OWASP LLM 应用风险列表](https://genai.owasp.org/llm-top-10/)
