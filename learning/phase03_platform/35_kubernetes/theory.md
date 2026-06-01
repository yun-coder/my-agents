# 35. Kubernetes

## 学习目标

- 理解 Pod、Deployment、Service、ConfigMap 和 Secret。
- 会为 Agent API 描述副本数、健康检查和资源限制。
- 知道容器化不等于已经适合生产运行。

## 核心概念

Kubernetes 用声明式资源管理容器工作负载：

| 资源 | 作用 |
| --- | --- |
| `Pod` | 一个或多个共同运行的容器 |
| `Deployment` | 管理无状态 Pod 副本和滚动升级 |
| `Service` | 为一组 Pod 提供稳定访问入口 |
| `ConfigMap` | 保存非敏感配置 |
| `Secret` | 保存敏感配置引用 |

Agent API 通常还需要队列 worker、状态存储和可观测性组件。对 API 设置 readiness probe 可以避免流量进入尚未就绪的实例。资源 requests 和 limits 有助于调度与容量控制。

## 示例说明

`demo.py` 使用 Python 字典生成简化 Deployment 与 Service 清单，便于先理解字段关系。

## 运行

```powershell
python .\learning\phase03_platform\35_kubernetes\demo.py
```

## 延伸阅读

- [Kubernetes Deployments 官方文档](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes Services 官方文档](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes ConfigMap 官方文档](https://kubernetes.io/docs/concepts/configuration/configmap/)
