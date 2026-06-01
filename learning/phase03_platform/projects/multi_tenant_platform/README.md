# 阶段三综合项目：多租户 SaaS Agent 平台原型

这个原型聚焦平台层的请求准入，不调用外部模型：

1. 根据角色判断动作权限。
2. 强制按 `tenant_id` 返回知识库文档。
3. 对每个租户做滑动窗口限流。
4. 在模型调用前检查租户预算。
5. 记录准入、拒绝和 Token 费用审计事件。

## 运行

```powershell
python .\learning\phase03_platform\projects\multi_tenant_platform\cli.py
```

## 设计边界

- 内存存储仅用于学习。生产环境需要数据库、Redis 或策略服务。
- 预算和价格应由平台配置中心管理。
- 权限校验必须在服务端执行，不能交给模型自行决定。
