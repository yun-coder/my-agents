# 阶段三：平台化与扩展

阶段三关注多租户 Agent 平台需要的类型约束、部署、消息队列、权限、优化与成本治理。

| 编号 | 知识点 | 默认 Demo |
| --- | --- | --- |
| 31 | Pydantic AI | 结构化工单校验 |
| 32 | 开源模型：Llama / Qwen / Mistral | 模型端点配置选择 |
| 33 | Agent 托管平台 | 部署规格检查 |
| 34 | 消息队列 | 带重试的内存任务队列 |
| 35 | Kubernetes | Deployment / Service 配置生成 |
| 36 | 多租户权限隔离 | Tenant + RBAC 查询 |
| 37 | DSPy | 基于样本的提示词候选优化 |
| 38 | 成本控制与限流 | Token 预算与滑动窗口限流 |

## 运行单个 Demo

```powershell
python .\learning\phase03_platform\31_pydantic_ai\demo.py
```

## 运行阶段测试

```powershell
python -m unittest discover -s .\learning\phase03_platform\tests -v
```

综合项目见 `projects/multi_tenant_platform`。
