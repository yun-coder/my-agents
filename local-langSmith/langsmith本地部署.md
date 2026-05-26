# LangSmith 离线自托管部署本机扫描报告

工作目录：`D:\learn-langSmith`

## 结论

这台机器具备用 Docker Desktop + 本机 Kubernetes 做 LangSmith 自托管验证部署的基础条件，但还不具备“完全离线 / air-gapped”安装条件。

当前可以继续做本机验证；如果目标是严格离线部署，还需要准备 LangSmith self-hosted license、offline/air-gapped license、Helm chart 包、完整镜像包或内网 registry、以及 `langsmith_config.yaml`。

## 本机环境

| 检查项 | 当前结果 | 结论 |
| --- | --- | --- |
| OS | Windows 10 Pro / amd64 | 可用 |
| Docker Desktop | 4.74.0 | 可用 |
| Docker Engine | 29.4.3 / linux amd64 | 可用 |
| Docker context | `desktop-linux` | 正确 |
| Docker Compose | v5.1.4 | 可用 |
| Docker 分配资源 | 24 CPU / 23.05 GiB RAM | 可做本机验证，低于生产建议 |
| Kubernetes context | `docker-desktop` | 可用 |
| Kubernetes node | `desktop-control-plane` Ready | 可用 |
| Kubernetes version | v1.34.3 | 可用 |
| Helm | v4.2.0 | 可用 |
| OpenSSL | 3.0.18 | 可生成 secret |
| 磁盘空间 | C: 258.29GB free, D: 227.21GB free, E: 257.35GB free | 充足 |

官方 Kubernetes 部署文档建议至少 16 vCPU / 64GB memory，且如果 ClickHouse 跑在集群内，ClickHouse 默认会请求 4 vCPU / 16GB memory。当前 Docker Desktop 分配 23.05GiB RAM，适合验证，不建议作为生产容量。

## Kubernetes 状态

当前集群核心组件均在运行：

```text
kube-system/coredns: Running
kube-system/etcd-desktop-control-plane: Running
kube-system/kube-apiserver-desktop-control-plane: Running
kube-system/kube-controller-manager-desktop-control-plane: Running
kube-system/kube-proxy: Running
kube-system/kube-scheduler: Running
local-path-storage/local-path-provisioner: Running
```

StorageClass：

```text
hostpath
standard (default)
```

说明：默认 StorageClass 存在，可以支持 Helm chart 创建 PVC。不过它是 Docker Desktop 的本地存储，适合开发验证，不适合生产备份和扩容。

## LangSmith 当前状态

| 项目 | 当前状态 |
| --- | --- |
| `langsmith` namespace | 未创建 |
| Helm release | 未发现 |
| Helm repo | 未配置任何 repo |
| 当前目录配置文件 | 未发现 `langsmith_config.yaml` / values 文件 |
| 离线 chart 包 | 未发现 `.tgz` chart 包 |
| 离线镜像 tar 包 | 未发现 |
| LangSmith 镜像 | 未发现 |
| license 文件 | 未发现 |
| 内网 registry 配置 | 未发现 |

当前 Docker 本地镜像里有 Postgres、Redis、Dify、Nginx、Kind 等镜像，但没有 LangSmith 相关镜像，例如：

```text
langchain/langsmith-backend
langchain/langsmith-frontend
langchain/langsmith-go-backend
langchain/langsmith-playground
langchain/langsmith-ace-backend
langchain/hosted-langserve-backend
langchain/langgraph-operator
clickhouse/clickhouse-server
```

## 官方要求摘录

根据 LangChain 官方文档：

- LangSmith self-hosted 是 Enterprise plan 的 add-on，需要 license key。
- Kubernetes + Helm 是生产部署 LangSmith observability/evaluation 的方式。
- 最低依赖包括 PostgreSQL >= 14、Redis >= 5 或 Valkey 8、Helm >= 3、受支持周期内的 Kubernetes。
- 非 offline 模式需要访问 `https://beacon.langchain.com` 做 license verification 和 usage reporting。
- 完全离线模式需要联系账号团队获取 offline/air-gapped license。
- 离线或私有 registry 环境需要 mirror LangSmith Helm chart 中的镜像，并在 values 配置里指向私有 registry。

参考：

- https://docs.langchain.com/langsmith/kubernetes
- https://docs.langchain.com/langsmith/self-hosted
- https://docs.langchain.com/langsmith/self-host-dependency-versions
- https://docs.langchain.com/langsmith/self-host-egress
- https://docs.langchain.com/langsmith/self-host-mirroring-images

## 离线部署还缺什么

1. LangSmith self-hosted license key。
2. 如果机器最终不能访问 `https://beacon.langchain.com`，还需要 offline/air-gapped license。
3. Helm chart 包，例如 `langsmith-<version>.tgz`。
4. Helm chart 对应版本的全部容器镜像。
5. 内网 registry，或一套 `docker save` / `docker load` 镜像导入方案。
6. `langsmith_config.yaml`，至少包含 license、auth、secret、镜像 registry、存储配置。
7. 若要生产化，需要外部 PostgreSQL、Redis/Valkey、ClickHouse 或更大的 Kubernetes 集群。

## Key 与授权如何获取

LangSmith self-hosted 不是普通 SaaS API key，它需要 self-hosted license key。官方文档说明 self-hosting 是 Enterprise plan 的 add-on；如果要试用或正式部署，需要联系 LangChain / LangSmith 销售或你的 LangChain representative 获取 license。

需要准备的密钥分为三类：

| 名称 | 用途 | 如何获取/生成 |
| --- | --- | --- |
| `langsmithLicenseKey` | LangSmith self-hosted 授权，启动和计费验证需要 | 联系 LangChain 销售/客户代表获取 |
| Offline / air-gapped license | 完全离线部署时使用，避免依赖 `beacon.langchain.com` | 联系账号团队明确申请 offline/air-gapped license |
| `apiKeySalt` | 本地实例生成/校验 LangSmith API key 的盐 | 本机用 `openssl rand -base64 32` 生成 |
| `jwtSecret` | Basic auth 登录 JWT 签名密钥 | 本机用 `openssl rand -base64 32` 生成 |
| `initialOrgAdminPassword` | 首个管理员账号密码 | 自行设置，至少 12 位，包含小写、大写和符号 |

申请 license 时建议把这些信息发给 LangChain：

1. 目标用途：local validation / staging / production。
2. 部署方式：self-hosted LangSmith on Kubernetes with Helm。
3. 是否完全离线：如果不能访问 `https://beacon.langchain.com`，明确写 air-gapped/offline。
4. 部署规模：预计用户数、trace 量、是否只做 Observability/Evaluation，是否需要 Deployment/Fleet/Insights/Polly。
5. 环境信息：Kubernetes 发行版、CPU/内存、是否使用外部 PostgreSQL/Redis/ClickHouse。

填写申请表时，`Work email` 建议使用公司/机构域名邮箱，而不是个人邮箱。国内可用企业微信邮箱、腾讯企业邮箱、阿里企业邮箱、飞书企业邮箱等，只要邮箱后缀是公司或机构自己的域名即可，例如：

```text
name@yourcompany.com
name@yourcompany.cn
name@yourcompany.com.cn
name@yourcompany.ai
name@university.edu.cn
```

不太推荐使用个人邮箱，例如：

```text
name@qq.com
name@163.com
name@126.com
name@gmail.com
name@outlook.com
```

如果暂时没有公司域名邮箱，可以先用常用邮箱提交，并在备注里说明：

```text
We are based in China and currently do not have a company-domain email available. Please contact us through this email for self-hosted LangSmith Enterprise license discussion.
```

官方入口：

- Pricing: https://www.langchain.com/pricing
- Contact Sales: https://www.langchain.com/contact-sales

## 本机验证部署步骤

下面步骤用于“当前机器上先跑通 LangSmith 验证环境”。这个流程默认当前机器可以临时访问公网拉 Helm chart 和镜像，并可以访问 `https://beacon.langchain.com` 做 license 验证。如果机器必须完全断网，请跳到“严格离线部署准备步骤”。

### 0. 确认前置条件

在 PowerShell 中执行：

```powershell
docker version
docker context ls
kubectl config current-context
kubectl get nodes -o wide
kubectl get storageclass
helm version
```

本机当前已确认：

```text
Docker context: desktop-linux
Kubernetes context: docker-desktop
Node: desktop-control-plane Ready
StorageClass: standard (default)
Helm: v4.2.0
```

### 1. 创建工作目录

建议把安装过程文件放在当前目录：

```powershell
Set-Location D:\learn-langSmith
New-Item -ItemType Directory -Force .\install-assets
New-Item -ItemType Directory -Force .\secrets
```

不要把真实 license、salt、密码提交到 Git。

### 2. 生成本地 secret

生成 `apiKeySalt`：

```powershell
openssl rand -base64 32
```

生成 `jwtSecret`：

```powershell
openssl rand -base64 32
```

记录三项敏感值：

```text
LANGSMITH_LICENSE_KEY=<从 LangChain 获取>
API_KEY_SALT=<openssl 生成>
JWT_SECRET=<openssl 生成>
```

管理员密码也要提前准备，例如：

```text
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=<至少12位，包含小写、大写和符号>
```

### 3. 创建 namespace

```powershell
kubectl create namespace langsmith
kubectl get namespace langsmith
```

如果 namespace 已存在，第一条命令会报 AlreadyExists，可以忽略。

### 4. 添加 Helm repo 并选择版本

```powershell
helm repo add langchain https://langchain-ai.github.io/helm
helm repo update
helm search repo langchain/langsmith --versions
```

选择一个 chart 版本，建议先用搜索结果里的最新稳定版本，并把版本记录下来：

```powershell
$env:LANGSMITH_CHART_VERSION="<version>"
```

### 5. 创建最小 `langsmith_config.yaml`

在 `D:\learn-langSmith\langsmith_config.yaml` 创建如下内容，并替换占位符：

```yaml
config:
  langsmithLicenseKey: "<LANGSMITH_LICENSE_KEY>"
  apiKeySalt: "<API_KEY_SALT>"
  authType: mixed
  initialOrgAdminEmail: "admin@example.com"
  basicAuth:
    enabled: true
    initialOrgAdminPassword: "<INITIAL_ADMIN_PASSWORD>"
    jwtSecret: "<JWT_SECRET>"

  telemetry:
    logs: false
    metrics: false
    traces: false

commonEnv:
  - name: PHONE_HOME_USAGE_REPORTING_ENABLED
    value: "false"
```

说明：

1. `telemetry.logs/metrics/traces: false` 只关闭 operational telemetry，不关闭 license verification。
2. `commonEnv` 在 chart 0.14.6 中必须是列表，不能写成 map；`PHONE_HOME_USAGE_REPORTING_ENABLED=false` 关闭 usage telemetry。
3. 非 offline 模式下，billing telemetry / license verification 仍需要访问 `https://beacon.langchain.com`。
4. 这只是本机验证最小配置。生产环境建议使用 Kubernetes Secret 或外部 secret manager，不要把密钥明文放在 values 文件里。

### 6. 安装 LangSmith

```powershell
  helm upgrade -i langsmith langchain/langsmith --values .\langsmith_config.yaml --version 0.14.6 -n langsmith --wait --debug
```

首次安装会拉取多个镜像并初始化 PostgreSQL、Redis、ClickHouse 等组件，可能需要较长时间。当前 Docker Desktop 分配 23.05GiB RAM，如果出现 Pod Pending 或 OOM，需要增加 Docker Desktop 内存或调低 chart 资源请求。

### 7. 查看部署状态

```powershell
helm list -n langsmith
kubectl get pods -n langsmith -o wide
kubectl get services -n langsmith
kubectl get pvc -n langsmith
```

期望看到 LangSmith backend、frontend、queue、playground、PostgreSQL、Redis、ClickHouse 等 Pod 逐步进入 `Running` 或 `Completed`。

如果某些 Pod 没起来，先看事件：

```powershell
kubectl get events -n langsmith --sort-by=.metadata.creationTimestamp
```

再看具体 Pod：

```powershell
kubectl describe pod <pod-name> -n langsmith
kubectl logs <pod-name> -n langsmith --tail=200
```

### 8. 本机访问 UI

优先使用 port-forward，避免 Docker Desktop LoadBalancer 行为差异：

```powershell
kubectl port-forward svc/langsmith-frontend 8080:80 -n langsmith
```

然后浏览器访问：

```text
http://localhost:8080
```

用 `langsmith_config.yaml` 中的 `initialOrgAdminEmail` 和 `initialOrgAdminPassword` 登录。

### 9. 验证 API

另开一个 PowerShell 窗口：

```powershell
Invoke-RestMethod http://localhost:8080/api/tenants
```

如果返回 tenant JSON，说明前端服务和后端 API 基本可用。

### 10. 创建 LangSmith API Key 并验证 tracing

登录 UI 后，在 LangSmith 页面里创建一个 API key。注意这个 API key 和 self-hosted license key 不是一回事：

| Key | 用途 |
| --- | --- |
| Self-hosted license key | 部署 LangSmith 服务本身 |
| LangSmith API key | 应用程序向你的 LangSmith 实例上报 traces |

本机应用使用自托管实例时，环境变量应指向本机 LangSmith：

```powershell
$env:LANGSMITH_TRACING="true"
$env:LANGSMITH_ENDPOINT="http://localhost:8080"
$env:LANGSMITH_API_KEY="<在自托管 UI 中创建的 API key>"
$env:LANGSMITH_PROJECT="local-validation"
```

然后运行一个带 LangSmith tracing 的最小测试脚本或你的应用，确认 UI 中能看到 project 和 traces。

## 严格离线部署准备步骤

严格离线是指目标机器不能访问公网，也不能访问 `https://beacon.langchain.com`。这时不能只执行在线 Helm 安装，需要先在有网机器准备资产。

### 1. 获取 offline/air-gapped license

联系 LangChain 账号团队，明确说明目标环境不能访问公网，要求提供 offline/air-gapped license。普通 self-hosted license 在非 offline 模式下仍需要访问 `https://beacon.langchain.com`。

### 2. 下载固定版本 Helm chart

在有网机器执行：

```powershell
helm repo add langchain https://langchain-ai.github.io/helm
helm repo update
helm search repo langchain/langsmith --versions
helm pull langchain/langsmith --version <version> --destination .\install-assets
```

得到：

```text
install-assets\langsmith-<version>.tgz
```

### 3. 获取 chart 默认 values 并确认镜像列表

```powershell
helm show values langchain/langsmith --version <version> > .\install-assets\values-default.yaml
```

在 `values-default.yaml` 中检查 `images:` 段，确认该 chart 版本实际需要的 image repository 和 tag。镜像清单会随 chart 版本变化，必须以固定 chart 版本的 values 为准。

### 4. Mirror 镜像到内网 registry

如果有内网 registry，例如 `registry.local:5000`，优先用官方 Helm chart repo 中的 mirror 脚本：

```bash
bash mirror_langsmith_images.sh --registry registry.local:5000 --platform linux/amd64 --version <app-version>
```

如果不用脚本，则手动对每个镜像执行：

```powershell
docker pull <source-image>:<tag>
docker tag <source-image>:<tag> registry.local:5000/<target-image>:<tag>
docker push registry.local:5000/<target-image>:<tag>
```

常见需要 mirror 的镜像包括 LangSmith backend、frontend、playground、ACE、platform backend、PostgreSQL、Redis/Valkey、ClickHouse 等；最终以 `values-default.yaml` 为准。

### 5. 没有内网 registry 时，用 tar 包导入

在有网机器：

```powershell
docker pull <image-a>:<tag>
docker pull <image-b>:<tag>
docker save -o langsmith-images.tar <image-a>:<tag> <image-b>:<tag>
```

把 `langsmith-images.tar` 拷贝到目标机器：

```powershell
docker load -i .\langsmith-images.tar
docker images
```

如果 Kubernetes 运行在 Docker Desktop 的 Linux engine 上，`docker load` 后通常可被本机集群使用。更稳妥的方式仍是内网 registry。

### 6. 准备离线 `langsmith_config.yaml`

如果使用内网 registry，在 values 中覆盖镜像仓库，例如：

```yaml
images:
  registry: "registry.local:5000"
  imagePullSecrets: []

config:
  langsmithLicenseKey: "<OFFLINE_OR_AIR_GAPPED_LICENSE>"
  apiKeySalt: "<API_KEY_SALT>"
  authType: mixed
  initialOrgAdminEmail: "admin@example.com"
  basicAuth:
    enabled: true
    initialOrgAdminPassword: "<INITIAL_ADMIN_PASSWORD>"
    jwtSecret: "<JWT_SECRET>"
```

如果使用私有 registry 且需要认证，先创建 pull secret：

```powershell
kubectl create secret docker-registry registry-creds `
  --docker-server=registry.local:5000 `
  --docker-username=<username> `
  --docker-password=<password> `
  -n langsmith
```

然后配置：

```yaml
images:
  imagePullSecrets:
    - name: registry-creds
```

### 7. 使用本地 chart 包安装

```powershell
kubectl create namespace langsmith

helm upgrade -i langsmith .\install-assets\langsmith-<version>.tgz `
  --values .\langsmith_config.yaml `
  -n langsmith `
  --wait `
  --debug
```

### 8. 离线部署验证

```powershell
kubectl get pods -n langsmith -o wide
kubectl get services -n langsmith
kubectl port-forward svc/langsmith-frontend 8080:80 -n langsmith
Invoke-RestMethod http://localhost:8080/api/tenants
```

如果 Pod 出现 `ImagePullBackOff`，说明镜像名、tag、registry 地址、pull secret 或本地导入不匹配。先用下面命令确认：

```powershell
kubectl describe pod <pod-name> -n langsmith
docker images
```

## 卸载验证环境

仅删除 LangSmith release：

```powershell
helm uninstall langsmith -n langsmith
```

如果要删除 namespace 和 PVC 数据：

```powershell
kubectl delete namespace langsmith
```

注意：删除 namespace 会删除本地验证环境里的数据库 PVC 和数据。

## 快速命令清单

在线验证路径：

```powershell
kubectl create namespace langsmith
helm repo add langchain https://langchain-ai.github.io/helm
helm repo update
helm search repo langchain/langsmith --versions
helm upgrade -i langsmith langchain/langsmith --values .\langsmith_config.yaml --version <version> -n langsmith --wait --debug
kubectl port-forward svc/langsmith-frontend 8080:80 -n langsmith
```

离线路径：

```powershell
helm pull langchain/langsmith --version <version> --destination .\install-assets
helm show values langchain/langsmith --version <version> > .\install-assets\values-default.yaml
docker load -i .\langsmith-images.tar
helm upgrade -i langsmith .\install-assets\langsmith-<version>.tgz --values .\langsmith_config.yaml -n langsmith --wait --debug
```

## 风险点

1. 当前 23.05GiB Docker RAM 低于官方生产建议 64GB，完整组件可能有资源压力。
2. Docker Desktop Kubernetes 是单节点开发环境，不建议承载生产 LangSmith。
3. 当前没有任何 LangSmith 离线资产，严格离线部署不能马上开始。
4. 当前没有 license 信息，无法完成 self-hosted 安装。
5. 当前未配置 Helm repo，也没有本地 chart 缓存。
