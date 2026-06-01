# 28. 浏览器自动化：Playwright / Browser Use

## 学习目标

- 理解浏览器自动化与普通 HTTP 请求的差异。
- 会用 Playwright 打开页面、读取标题并关闭浏览器。
- 知道登录态、下载、表单提交等动作需要额外安全控制。

## 核心概念

浏览器自动化适合处理依赖 JavaScript 渲染、需要点击或填写表单的网页。Playwright 提供浏览器、上下文和页面三个层级：

| 对象 | 作用 |
| --- | --- |
| `browser` | 浏览器进程 |
| `context` | 隔离的会话环境，可拥有独立 Cookie |
| `page` | 具体标签页 |

Agent 控制浏览器时，应限制可访问域名、下载目录和可执行动作。付款、发布、发送等不可逆动作应先让用户确认。Browser Use 等上层工具可以把页面操作包装为 Agent 工具，但不会自动消除这些风险。

## 示例说明

`demo.py` 默认只打印执行计划。加上 `--run` 后才会启动 Playwright 并访问 `https://example.com`。

## 运行

```powershell
python .\learning\phase02_production\28_browser_automation\demo.py
python .\learning\phase02_production\28_browser_automation\demo.py --run
```

## 延伸阅读

- [Playwright Python 官方文档](https://playwright.dev/python/docs/intro)
- [Browser Use 官方文档](https://docs.browser-use.com/)
