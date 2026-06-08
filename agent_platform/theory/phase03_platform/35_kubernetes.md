# 35 Kubernetes — Agent 容器编排与生产部署

## 1. 概念概述

### 1.1 为什么 Agent 需要 Kubernetes

Kubernetes（K8s）是当前业界标准的容器编排平台。对于 AI Agent 的生产部署，K8s 提供了其他方案难以替代的能力：

- **声明式部署**：描述期望状态，K8s 自动维持
- **自动扩缩容**：HPA 根据 CPU/内存/自定义指标自动调整副本数
- **自愈能力**：容器崩溃后自动重启，节点故障时重新调度
- **服务发现**：Agent 内部组件间通过 DNS 名称互相发现
- **滚动更新**：零宕机更新 Agent 版本
- **资源隔离**：每个 Agent 实例有独立的资源限制

### 1.2 核心组件

| 组件 | 作用 | 类比 |
|------|------|------|
| Pod | 最小的部署单元，包含一个或多个容器 | 虚拟机实例 |
| Deployment | 管理 Pod 的声明式更新 | 自动修复组 |
| Service | 提供稳定的网络入口 | 负载均衡器 |
| Ingress | HTTP/HTTPS 路由到 Service | 反向代理 |
| ConfigMap | 非敏感配置管理 | 配置文件 |
| Secret | 敏感信息管理（API Key 等） | 加密存储 |
| HPA | 自动扩缩容 | 自动缩放器 |
| Namespace | 虚拟集群隔离 | 租户/环境隔离 |

### 1.3 Agent 在 K8s 上的典型架构

```
用户请求 -> Ingress -> Service -> Agent Pod (多个副本)
                                           |
                                    +------+------+
                                    |             |
                              Agent Worker    Agent Worker
                                    |             |
                              +-----+      +-----+
                              |                 |
                         LLM API            Knowledge Base
```

### 1.4 与托管平台对比

| 维度 | K8s 自托管 | 托管平台 (Modal) | LangGraph Platform |
|------|-----------|-----------------|-------------------|
| 控制力 | 完全控制 | 有限 | 有限 |
| 运维成本 | 高 | 低 | 低 |
| 成本 (1K req/day) | ~$50 | ~$100 | $99+ |
| GPU 调度 | 支持 | 有限 | 不支持 |
| 学习曲线 | 陡峭 | 平缓 | 中等 |
| 可移植性 | 高（标准 API） | 中等 | 低 |

## 2. 核心原理

### 2.1 Pod 与容器生命周期

Pod 是 K8s 中调度的基本单位。Agent 应用以容器方式运行在 Pod 中：

```
Pod 状态机：
Pending -> Running -> Succeeded/Failed
    |          |
    |          +-> CrashLoopBackOff (反复崩溃)
    +-> ImagePullBackOff (镜像拉取失败)
```

每个 Pod 有独立的 IP 地址和资源限制（CPU/Memory）。

### 2.2 Deployment 的滚动更新

Deployment 通过 ReplicaSet 管理 Pod 的版本和数量。滚动更新策略：

```
v1 Pod * 5 -> 创建 v2 Pod * 1 -> 销毁 v1 Pod * 1 -> 创建 v2 Pod * 1 ...
```

滚动更新参数：
- **maxSurge**：更新期间可以超出期望副本数的比例
- **maxUnavailable**：更新期间可以不可用的最大副本数

### 2.3 Service 与网络模型

Service 实现了 Pod 的负载均衡和服务发现：

- **ClusterIP**：集群内访问（默认）
- **NodePort**：节点端口映射
- **LoadBalancer**：云厂商负载均衡器

### 2.4 HPA 自动扩缩容

水平 Pod 自动扩缩容（HPA）基于指标调整副本数：

```
期望副本数 = 当前副本数 * (当前指标值 / 目标指标值)
```

常用的扩缩容指标：
- CPU 使用率
- 内存使用率
- 自定义指标（请求数/秒、队列深度、Token 消耗速度）

## 3. 实战指南

### 3.1 Minikube 本地开发环境

```bash
# 安装 Minikube
# Windows: 从 https://minikube.sigs.k8s.io/docs/start/ 下载
# Linux:
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动 Minikube 集群
minikube start --cpus=4 --memory=8g --driver=docker

# 启用 Ingress 插件
minikube addons enable ingress

# 查看集群状态
kubectl cluster-info
kubectl get nodes

# 打开 Dashboard
minikube dashboard
```

### 3.2 容器化 Agent 应用

```dockerfile
# Dockerfile — Agent 容器镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量默认值
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import http.client; conn=http.client.HTTPConnection('localhost:8000'); conn.request('GET','/health'); resp=conn.getresponse(); exit(0) if resp.status==200 else exit(1)"

# 启动 Agent 服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-ai==0.0.10
openai==1.50.0
redis==5.1.0
httpx==0.27.0
```

### 3.3 Kubernetes 资源清单

```yaml
# agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-deployment
  namespace: agent-system
  labels:
    app: ai-agent
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agent
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # 零宕机更新
  template:
    metadata:
      labels:
        app: ai-agent
    spec:
      containers:
      - name: agent
        image: myregistry/ai-agent:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          protocol: TCP
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: openai-api-key
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: redis-url
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 3
---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
  namespace: agent-system
spec:
  selector:
    app: ai-agent
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-ingress
  namespace: agent-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  ingressClassName: nginx
  rules:
  - host: agent.mycompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agent-service
            port:
              number: 80
```

### 3.4 ConfigMap 与 Secret 管理

```yaml
# agent-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-config
  namespace: agent-system
data:
  redis-url: "redis://redis-service:6379/0"
  log-level: "INFO"
  max-tokens: "4096"
  temperature: "0.7"
  model-name: "gpt-4o-mini"

---
apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
  namespace: agent-system
type: Opaque
stringData:
  openai-api-key: "sk-your-key-here"
  redis-password: "your-redis-password"
  webhook-secret: "your-webhook-secret"
```

### 3.5 HPA 自动扩缩容配置

```yaml
# agent-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-hpa
  namespace: agent-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-deployment
  minReplicas: 2          # 最小副本数
  maxReplicas: 10         # 最大副本数
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # CPU 使用率 > 70% 时扩容
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # 内存使用率 > 80% 时扩容
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # 缩容等待 5 分钟
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### 3.6 Helm Chart 打包

```yaml
# Chart.yaml
apiVersion: v2
name: ai-agent
description: AI Agent Helm Chart
type: application
version: 0.1.0
appVersion: "1.0.0"
```

```yaml
# values.yaml — Helm 配置值
replicaCount: 3

image:
  repository: myregistry/ai-agent
  tag: latest
  pullPolicy: Always

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  host: agent.mycompany.com

resources:
  requests:
    memory: 512Mi
    cpu: 500m
  limits:
    memory: 2Gi
    cpu: 2

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

config:
  redisUrl: "redis://redis-service:6379/0"
  logLevel: "INFO"
  modelName: "gpt-4o-mini"
  maxTokens: 4096
  temperature: 0.7
```

```bash
# 部署 Helm Chart
helm install ai-agent ./ai-agent-chart \
    --namespace agent-system \
    --create-namespace \
    --set image.tag=v1.0.0 \
    --set replicaCount=5

# 更新部署
helm upgrade ai-agent ./ai-agent-chart \
    --set image.tag=v1.1.0

# 回滚
helm rollback ai-agent 1
```

### 3.7 部署与运维命令

```bash
# 部署到 K8s
kubectl apply -f agent-deployment.yaml
kubectl apply -f agent-config.yaml

# 查看状态
kubectl get pods -n agent-system -w
kubectl get deployments -n agent-system
kubectl get services -n agent-system
kubectl get hpa -n agent-system

# 查看日志
kubectl logs -f deployment/agent-deployment -n agent-system

# 进入容器调试
kubectl exec -it deployment/agent-deployment -n agent-system -- /bin/bash

# 扩缩容
kubectl scale deployment/agent-deployment --replicas=5 -n agent-system

# 滚动更新状态
kubectl rollout status deployment/agent-deployment -n agent-system

# 查看 Pod 资源使用
kubectl top pods -n agent-system
```

### 3.8 Agent 健康检查端点

```python
# health.py — 健康检查端点
from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title="AI Agent API")

START_TIME = time.time()

class HealthStatus(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    active_connections: int

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """存活检查：检查服务是否运行。"""
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        uptime_seconds=time.time() - START_TIME,
        active_connections=0,
    )

@app.get("/ready")
async def readiness_check():
    """就绪检查：检查服务是否可以接收流量。"""
    # 检查数据库连接
    try:
        # await db.ping()
        return {"status": "ready"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "database unavailable"},
        )

@app.get("/chat")
async def chat(prompt: str):
    """Agent 聊天接口。"""
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    import os

    model = OpenAIModel(
        "gpt-4o-mini",
        api_key=os.environ["OPENAI_API_KEY"],
    )
    agent = Agent(model=model)
    result = await agent.run(prompt)
    return {"response": result.data}
```

## 4. 最佳实践

### 4.1 资源管理

1. **设定资源请求和限制**：每个容器必须设定 requests 和 limits
2. **使用 LimitRange**：为 Namespace 设定默认资源限制
3. **监控实际使用**：通过 `kubectl top` 和 Prometheus 监控
4. **避免过度申请**：requests 按实际使用设置，limits 设置安全上限

### 4.2 配置管理

1. **ConfigMap 存配置**：非敏感配置使用 ConfigMap
2. **Secret 存密钥**：API Key、密码使用 Secret 并启用加密
3. **环境变量注入**：应用从环境变量读取配置
4. **版本化管理**：配置变更与代码变更同等对待

### 4.3 高可用部署

1. **多副本部署**：至少 2 个副本
2. **反亲和性**：避免同一节点运行多个副本
3. **PodDisruptionBudget**：确保至少 N 个副本可用
4. **多可用区**：跨可用区部署节点

### 4.4 日志与监控

1. **结构化日志**：JSON 格式日志便于采集
2. **集中式日志**：使用 EFK/ELK 或 Loki 收集
3. **指标暴露**：Prometheus 格式指标端点
4. **告警规则**：配置关键指标告警

## 5. 常见陷阱

### 5.1 容器镜像过大

Python 镜像 + 依赖可能超过 1GB，导致拉取慢。解决方案：
- 使用 slim 或 alpine 基础镜像
- 多阶段构建减少最终镜像大小
- 使用临时存储（emptyDir）缓存 pip 包

### 5.2 CPU 限制导致延迟

```yaml
# 错误：设置过低的 CPU 限制
limits:
  cpu: "500m"  # Python 多线程可能被限流

# 正确：根据实际情况设置
limits:
  cpu: "2"  # 允许使用 2 个核心
```

### 5.3 就绪检查延迟过高

Agent 初始化时需要加载模型和建立连接，就绪检查的成功与否直接影响流量路由。

### 5.4 忽视存储持久化

Agent 的 Session 数据存储在内存中，Pod 重启后丢失。必须使用外部存储。

### 5.5 滚动更新中断长连接

Agent 的流式长连接在滚动更新时会被中断。使用 preStop hook 优雅关闭。

## 6. API Key 依赖

| 功能 | 需要 Key | 说明 |
|------|---------|------|
| Minikube | 不需要 | 本地开发 |
| 云 K8s 服务 (AKS/EKS/GKE) | 需要 | 云账号 |
| Docker Registry | 可能需要 | 私有镜像仓库 |
| LLM API | 需要 | Agent 推理 |
| Prometheus/Grafana | 不需要 | 开源监控 |

## 7. 技术关系

- **上层**：Helm Chart -> 应用打包
- **本层**：Kubernetes -> 容器编排
- **下层**：Docker -> 容器运行时
- **监控**：Prometheus + Grafana -> 指标收集和可视化
- **日志**：Loki / ELK -> 日志聚合
- **CI/CD**：GitHub Actions / GitLab CI -> 自动部署

## 8. 验收清单

- [ ] 理解 Pod、Deployment、Service、Ingress 的核心概念
- [ ] 掌握 Minikube 本地集群的搭建和使用
- [ ] 能够为 Agent 应用编写 Dockerfile
- [ ] 掌握 Kubernetes 资源清单文件的编写
- [ ] 理解 ConfigMap 和 Secret 的区别和使用方法
- [ ] 配置 HPA 自动扩缩容
- [ ] 实现健康检查端点（liveness + readiness）
- [ ] 掌握 Helm Chart 的打包和部署
- [ ] 理解滚动更新策略
- [ ] 了解 K8s 网络模型和服务发现机制

## 9. 学习资源

- Kubernetes 官方文档：https://kubernetes.io/docs
- Minikube 文档：https://minikube.sigs.k8s.io
- Helm 文档：https://helm.sh/docs
- Kubectl 速查表：https://kubernetes.io/docs/reference/kubectl/cheatsheet
- Kubernetes 交互式教程：https://killercoda.com/kubernetes
- 《Kubernetes in Action》第 2 版
- CKAD 考试指南：https://www.cncf.io/certification/ckad/
