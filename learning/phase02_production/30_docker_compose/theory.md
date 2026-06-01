# 30. Docker / Docker Compose

## 学习目标

- 理解镜像、容器、端口、卷和环境变量。
- 知道 Docker Compose 适合描述多服务本地开发环境。
- 会检查服务是否使用固定镜像版本、健康检查和最小端口暴露。

## 核心概念

Dockerfile 描述如何构建单个镜像。Compose 文件描述多个服务如何一起运行。Agent 服务常见组合包括 API、数据库、Redis 和可观测性服务。

| 字段 | 作用 |
| --- | --- |
| `image` | 使用的镜像和版本 |
| `build` | 本地镜像构建方式 |
| `ports` | 宿主机到容器端口映射 |
| `environment` | 非敏感配置 |
| `env_file` | 从文件读取配置；敏感值不要提交到仓库 |
| `volumes` | 持久化数据或挂载代码 |
| `healthcheck` | 判断服务是否已经可用 |

镜像标签应尽量固定到明确版本。`latest` 方便试验，但会让相同配置在不同时间得到不同结果。

## 示例说明

`demo.py` 校验一个简化 Compose 风格配置，检查：

- 是否使用 `latest`。
- 是否存在健康检查。
- 是否暴露了不必要端口。

## 运行

```powershell
python .\learning\phase02_production\30_docker_compose\demo.py
```

## 延伸阅读

- [Dockerfile 官方文档](https://docs.docker.com/reference/dockerfile/)
- [Docker Compose 官方文档](https://docs.docker.com/compose/)
