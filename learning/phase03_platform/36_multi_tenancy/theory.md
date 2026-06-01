# 36. 多租户权限隔离

## 学习目标

- 理解租户隔离和角色权限是两件不同的事。
- 会在数据查询中强制加入 `tenant_id`。
- 知道仅在提示词中声明租户边界不具备安全性。

## 核心概念

多租户 Agent 平台需要同时控制“谁可以访问”和“可以访问哪些租户数据”：

| 控制 | 作用 |
| --- | --- |
| 身份认证 | 确认调用者是谁 |
| 租户上下文 | 确认调用者当前属于哪个租户 |
| RBAC / ABAC | 判断角色或属性是否允许执行动作 |
| 数据过滤 | 每次查询强制使用 `tenant_id` |
| 审计日志 | 记录谁在何时访问了什么资源 |

不要让模型自由拼接 SQL，也不要相信模型会主动遵守租户边界。边界必须由服务端代码、数据库策略或独立权限服务执行。

## 示例说明

`demo.py` 使用 SQLite 演示：

- 文档写入时携带 `tenant_id`。
- 查询方法始终要求传入租户。
- 角色权限使用显式白名单判断。

## 运行

```powershell
python .\learning\phase03_platform\36_multi_tenancy\demo.py
```

## 延伸阅读

- [Casbin RBAC 官方文档](https://casbin.org/docs/rbac)
- [PostgreSQL Row Security 官方文档](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
