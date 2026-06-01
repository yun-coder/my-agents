# 38. 成本控制与限流

## 学习目标

- 会按输入输出 Token 估算单次调用成本。
- 理解用户级、租户级和全局限流。
- 会在调用模型前检查预算。

## 核心概念

Agent 可能多轮调用模型和工具，因此成本控制必须贯穿工作流，而不是只在 API 入口检查一次。

| 控制 | 示例 |
| --- | --- |
| 单次上限 | 限制最大输出 Token |
| 用户限流 | 每分钟最多 N 次请求 |
| 租户预算 | 每日或每月最大金额 |
| 模型路由 | 简单任务优先使用成本较低模型 |
| 缓存 | 对稳定问题复用结果 |
| 观测 | 记录每个步骤的 Token 和费用 |

价格会变化，也会因模型和提供商不同而不同。生产配置应把单价放在可更新配置中，不要散落在业务代码里。

## 示例说明

`demo.py` 实现：

- 输入输出 Token 成本估算。
- 每个租户的滑动窗口请求限流。
- 预算不足时拒绝模型调用。

## 运行

```powershell
python .\learning\phase03_platform\38_cost_rate_limit\demo.py
```

## 延伸阅读

- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [Redis Rate Limiting 官方教程](https://redis.io/learn/howtos/ratelimiting/)
