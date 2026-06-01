# 39. Computer Use / GUI Agent

## 学习目标

- 理解 GUI Agent 与普通工具调用的差异。
- 会为浏览、输入、点击和提交动作分级。
- 知道高风险动作必须保留人工确认点。

## 核心概念

GUI Agent 通过截图、鼠标、键盘和浏览器页面完成任务。它面对的是非结构化界面，因此比调用明确 schema 的 API 更容易出错。

| 风险等级 | 示例 | 默认策略 |
| --- | --- | --- |
| 低 | 滚动、读取公开页面 | 可自动执行并记录 |
| 中 | 搜索、填写普通文本 | 限制域名和输入字段 |
| 高 | 登录、发送、付款、删除 | 执行前要求确认 |

GUI Agent 需要关注页面中的间接 Prompt Injection。网页文本是数据，不应自动升级为系统指令。重要动作应记录截图、目标元素、动作参数和审批结果。

## 示例说明

`demo.py` 对 GUI 动作进行策略判断。它不会真的控制桌面或浏览器。

## 运行

```powershell
python .\learning\phase04_frontier\39_computer_use\demo.py
```

## 延伸阅读

- [Anthropic Computer Use 官方文档](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool)
- [Playwright Python 官方文档](https://playwright.dev/python/docs/intro)
