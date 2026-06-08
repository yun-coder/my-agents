# 30 Docker / Docker Compose

## 概念概述

Docker 是一种容器化平台，允许开发者将应用及其依赖打包到一个轻量级、可移植的容器中，确保应用在任何环境中都能一致地运行。Docker Compose 则是用于定义和运行多容器 Docker 应用的工具，通过一个 YAML 文件配置所有服务的依赖关系、网络连接、卷挂载等。

在 AI Agent 应用的生产部署中，Docker 和 Docker Compose 扮演着至关重要的角色。一个典型的 AI Agent 系统通常包含多个服务组件：Agent 服务、LLM 代理、向量数据库、观测平台（如 LangFuse）、数据库等。Docker Compose 可以一站式管理所有这些服务的部署、配置和生命周期。

Dockerfile 定义了如何构建单个服务的镜像，而 compose.yaml 则定义了多个服务如何协同工作。这种"构建 + 编排"的模式使得 AI Agent 应用的部署变得标准化、可重复、可扩展。

## 核心原理

### Dockerfile 关键概念

**镜像层（Layers）**：Dockerfile 中的每条指令都会创建一个新的镜像层。层可以被缓存和复用，合理排序指令可以最大化缓存命中率，加速构建过程。

**多阶段构建（Multi-stage Build）**：在单个 Dockerfile 中使用多个 FROM 语句，前一阶段用于编译和构建，后一阶段只复制必要的产物，最终镜像更小、更安全。

**最佳实践层次结构**：

```
基础镜像选择（slim / alpine）
    ↓
系统依赖安装（合并 RUN 指令）
    ↓
依赖安装（先复制依赖描述文件，后复制源码）
    ↓
应用源码复制
    ↓
运行配置（非 root 用户，健康检查）
    ↓
CMD / ENTRYPOINT
```

### Docker Compose 核心概念

**Service（服务）**：一个容器的配置，包括镜像、端口、环境变量、卷等。

**Volume（卷）**：持久化数据存储，即使容器删除也不会丢失。用于数据库数据、配置文件、日志等。

**Network（网络）**：容器间的通信通道。Compose 自动创建默认网络，所有服务可通过服务名互相访问。

**Healthcheck（健康检查）**：Docker 定期执行的命令，用于判断容器是否正常运行。Compose 中可通过 `depends_on.condition` 控制服务启动顺序。

## 实战指南

### 优化 Dockerfile

以下分析基于本项目的 `Dockerfile`：

```dockerfile
# 原始 Dockerfile（来自项目）
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir openai langgraph langfuse fastapi uvicorn[standard] \
    pydantic instructor chromadb sentence-transformers FlagEmbedding PyMuPDF python-docx httpx

COPY src/ ./src/
RUN mkdir -p /app/data/chroma
EXPOSE 8000
CMD ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

优化后的多阶段构建版本：

```dockerfile
# ========== 阶段一：依赖构建 ==========
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装编译工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先复制 requirements，利用缓存
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ========== 阶段二：运行镜像 ==========
FROM python:3.11-slim

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# 仅从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY src/ ./src/

# 创建数据目录并设置权限
RUN mkdir -p /app/data/chroma && \
    chown -R appuser:appuser /app/data

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# 切换到非 root 用户运行
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

### 使用 requirements.txt 替代直接安装

```dockerfile
# requirements.txt 方式管理依赖
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/

# 创建数据目录
RUN mkdir -p /app/data && \
    mkdir -p /app/data/chroma

EXPOSE 8000

CMD ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

对应的 `requirements.txt`：

```
openai>=1.0.0
langgraph>=0.1.0
langfuse>=2.0.0
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
instructor>=1.0.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
FlagEmbedding>=1.0.0
PyMuPDF>=1.23.0
python-docx>=1.0.0
httpx>=0.25.0
```

### Docker Compose 完整配置

以下分析基于本项目的 `compose.yaml`：

```yaml
# compose.yaml（来自项目）
services:
  agent-platform:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ../dev.json:/app/dev.json:ro
    environment:
      - CHROMA_DIR=/app/data/chroma
      - LOG_LEVEL=INFO
    restart: unless-stopped

  langfuse-server:
    image: ghcr.io/langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@langfuse-db:5432/postgres
      - NEXTAUTH_SECRET=mysecret
      - NEXTAUTH_URL=http://localhost:3000
      - SALT=mysalt
    depends_on:
      langfuse-db:
        condition: service_healthy

  langfuse-db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=postgres
    volumes:
      - langfuse-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  langfuse-db-data:
```

增强版 compose.yaml（添加更多生产特性）：

```yaml
# docker-compose.yml（增强版）
version: "3.9"

services:
  agent-platform:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - BUILD_ENV=production
    ports:
      - "${APP_PORT:-8000}:8000"
    volumes:
      # 持久化数据
      - app-data:/app/data
      # 配置文件只读挂载
      - ./config/prod.json:/app/config.json:ro
    environment:
      - CHROMA_DIR=/app/data/chroma
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - OPENAI_API_KEY=${OPENAI_API_KEY:?请设置 OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.openai.com/v1}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o}
      - LANGFUSE_ENABLED=true
      - LANGFUSE_HOST=http://langfuse-server:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY:-}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY:-}
    depends_on:
      langfuse-server:
        condition: service_started
    restart: unless-stopped
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: "2G"
        reservations:
          cpus: "0.5"
          memory: "512M"
    # 健康检查
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    # 日志配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  langfuse-server:
    image: ghcr.io/langfuse/langfuse:latest
    ports:
      - "${LANGFUSE_PORT:-3000}:3000"
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@langfuse-db:5432/${DB_NAME:-postgres}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET:-change-me-in-production}
      - NEXTAUTH_URL=http://localhost:${LANGFUSE_PORT:-3000}
      - SALT=${LANGFUSE_SALT:-change-me-in-production}
      - LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=false
    depends_on:
      langfuse-db:
        condition: service_healthy
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  langfuse-db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=${DB_USER:-postgres}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-postgres}
      - POSTGRES_DB=${DB_NAME:-postgres}
    volumes:
      - langfuse-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: "512M"

  # 可选：Chroma 向量数据库独立服务
  chroma:
    image: chromadb/chroma:latest
    ports:
      - "${CHROMA_PORT:-8001}:8000"
    volumes:
      - chroma-data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - PERSIST_DIRECTORY=/chroma/chroma
      - ANONYMIZED_TELEMETRY=FALSE
    restart: unless-stopped

volumes:
  app-data:
  langfuse-db-data:
  chroma-data:

networks:
  default:
    name: agent-platform-network
    driver: bridge
```

### .env 配置文件

```bash
# .env 文件：集中管理环境变量
# 应用配置
APP_PORT=8000
LOG_LEVEL=INFO

# LLM 配置
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# LangFuse 配置
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PORT=3000
LANGFUSE_SALT=your-salt-here

# 数据库配置
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres

# Chroma 配置
CHROMA_PORT=8001

# NextAuth
NEXTAUTH_SECRET=your-nextauth-secret
```

### Docker 管理脚本

```bash
#!/usr/bin/env bash
# manage.sh：Docker 环境管理脚本
set -euo pipefail

COMPOSE_FILE="compose.yaml"
ENV_FILE=".env"

usage() {
    echo "用法: $0 {up|down|restart|build|logs|ps|exec|clean}"
    echo ""
    echo "命令:"
    echo "  up        启动所有服务（后台）"
    echo "  down      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  build     重新构建镜像"
    echo "  logs      查看服务日志"
    echo "  ps        查看服务状态"
    echo "  exec      进入容器执行命令"
    echo "  clean     清理所有数据和镜像"
    exit 1
}

cmd_up() {
    echo "启动所有服务..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
    echo "服务已启动。运行 '$0 ps' 查看状态。"
}

cmd_down() {
    echo "停止所有服务..."
    docker compose -f "$COMPOSE_FILE" down
    echo "服务已停止。"
}

cmd_restart() {
    cmd_down
    cmd_up
}

cmd_build() {
    echo "重新构建镜像..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    echo "构建完成。"
}

cmd_logs() {
    local service="${1:-}"
    if [ -n "$service" ]; then
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

cmd_ps() {
    docker compose -f "$COMPOSE_FILE" ps
}

cmd_exec() {
    local service="${1:-agent-platform}"
    shift 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" exec "$service" /bin/bash
}

cmd_clean() {
    echo "警告：这将删除所有数据卷和镜像！"
    read -p "确认继续？(y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        docker compose -f "$COMPOSE_FILE" down -v
        docker system prune -a -f
        echo "清理完成。"
    else
        echo "已取消。"
    fi
}

main() {
    if [ $# -eq 0 ]; then
        usage
    fi

    case "$1" in
        up) cmd_up ;;
        down) cmd_down ;;
        restart) cmd_restart ;;
        build) cmd_build ;;
        logs) cmd_logs "${2:-}" ;;
        ps) cmd_ps ;;
        exec) cmd_exec "${2:-}" ;;
        clean) cmd_clean ;;
        *) usage ;;
    esac
}

main "$@"
```

### 生产环境安全检查

```python
"""Docker 配置安全检查工具。"""
import subprocess
from typing import Any


class DockerSecurityChecker:
    """检查 Docker 配置的安全性。"""

    @staticmethod
    def check_dockerfile(filepath: str) -> list[dict[str, Any]]:
        """检查 Dockerfile 的安全最佳实践。"""
        findings: list[dict[str, Any]] = []

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否使用 root 用户
        if "USER" not in content:
            findings.append({
                "severity": "medium",
                "check": "root_user",
                "detail": "Dockerfile 未指定非 root 用户，容器将以 root 运行",
            })

        # 检查是否设置 HEALTHCHECK
        if "HEALTHCHECK" not in content:
            findings.append({
                "severity": "low",
                "check": "healthcheck",
                "detail": "未设置健康检查",
            })

        # 检查基础镜像
        for line in content.split("\n"):
            if line.startswith("FROM"):
                if "slim" not in line and "alpine" not in line:
                    findings.append({
                        "severity": "low",
                        "check": "base_image",
                        "detail": f"基础镜像不是 slim/alpine 版本: {line}",
                    })
                break

        return findings

    @staticmethod
    def check_compose(filepath: str) -> list[dict[str, Any]]:
        """检查 Docker Compose 的安全最佳实践。"""
        findings: list[dict[str, Any]] = []

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否硬编码密码
        import re

        password_patterns = re.findall(
            r"PASSWORD=\w+|SECRET=\w+|secret=change-me",
            content,
        )
        if password_patterns:
            findings.append({
                "severity": "critical",
                "check": "hardcoded_secrets",
                "detail": f"检测到硬编码密码/密钥: {password_patterns}",
            })

        # 检查是否使用 .env 文件
        if "env_file" not in content and "${" not in content:
            findings.append({
                "severity": "medium",
                "check": "env_management",
                "detail": "未使用 .env 文件或环境变量引用，可能包含硬编码配置",
            })

        # 检查是否设置了重启策略
        if "restart:" not in content:
            findings.append({
                "severity": "low",
                "check": "restart_policy",
                "detail": "未设置重启策略",
            })

        # 检查卷挂载权限
        if ":ro" not in content and "read_only" not in content:
            findings.append({
                "severity": "low",
                "check": "volume_permissions",
                "detail": "配置文件卷应使用 :ro（只读）模式",
            })

        return findings

    @staticmethod
    def check_running_containers() -> list[dict[str, Any]]:
        """检查正在运行的容器的安全状态。"""
        findings: list[dict[str, Any]] = []

        try:
            # 检查是否有容器以 root 运行
            result = subprocess.run(
                ["docker", "ps", "--filter", "status=running", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            for container in result.stdout.strip().split("\n"):
                if not container:
                    continue

                inspect = subprocess.run(
                    ["docker", "inspect", container, "--format", "{{.Config.User}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                user = inspect.stdout.strip()
                if not user or user == "" or user == "0":
                    findings.append({
                        "severity": "medium",
                        "check": "container_root",
                        "detail": f"容器 {container} 以 root 用户运行",
                    })

        except Exception as exc:
            findings.append({
                "severity": "info",
                "check": "docker_access",
                "detail": f"无法访问 Docker 守护进程: {exc}",
            })

        return findings


def check_all() -> None:
    """运行所有安全检查。"""
    print("=" * 60)
    print("Docker 安全配置检查")
    print("=" * 60)

    checker = DockerSecurityChecker()

    dockerfile_findings = checker.check_dockerfile("Dockerfile")
    if dockerfile_findings:
        print(f"\nDockerfile 检查结果 ({len(dockerfile_findings)} 项):")
        for f in dockerfile_findings:
            print(f"  [{f['severity']}] {f['check']}: {f['detail']}")
    else:
        print("\nDockerfile 检查通过")

    compose_findings = checker.check_compose("compose.yaml")
    if compose_findings:
        print(f"\nDocker Compose 检查结果 ({len(compose_findings)} 项):")
        for f in compose_findings:
            print(f"  [{f['severity']}] {f['check']}: {f['detail']}")
    else:
        print("\nDocker Compose 检查通过")

    container_findings = checker.check_running_containers()
    if container_findings:
        print(f"\n运行容器检查结果 ({len(container_findings)} 项):")
        for f in container_findings:
            print(f"  [{f['severity']}] {f['check']}: {f['detail']}")


if __name__ == "__main__":
    check_all()
```

## 最佳实践

1. **多阶段构建**：使用多阶段构建将构建环境和运行环境分离，大幅减小最终镜像体积。对于 Python 项目，可以减小 50% 以上。

2. **层缓存优化**：将不常变化的指令放在 Dockerfile 前面（如系统依赖、pip 安装），将频繁变化的指令放在后面（如源码复制）。

3. **使用 .env 管理环境变量**：不要在 compose.yaml 中硬编码敏感信息。使用 `${VAR_NAME}` 引用 .env 文件中的变量。

4. **非 root 用户运行**：始终在 Dockerfile 中创建并切换到非 root 用户，减少容器逃逸的风险。

5. **健康检查**：为每个服务配置健康检查，确保编排系统可以准确判断服务状态。

6. **资源限制**：使用 `deploy.resources.limits` 设置每个容器的资源上限，防止单个服务耗尽主机资源。

## 常见陷阱

1. **镜像过大**：未使用 slim/alpine 版本的基础镜像，或未清理构建缓存，导致镜像体积过大（GB 级别）。

2. **数据持久化缺失**：没有使用卷挂载存储数据库数据，容器删除后数据丢失。

3. **依赖顺序问题**：没有正确配置 `depends_on.condition`，导致服务启动顺序错误，应用启动时数据库尚未就绪。

4. **敏感信息泄露**：在 Dockerfile 或 compose.yaml 中硬编码 API Key、密码等敏感信息。

5. **root 用户运行**：容器以 root 用户运行，如果攻击者通过应用漏洞获取了容器访问权限，将获得宿主机的 root 权限。

## API Key 依赖

Docker 部署中的 API Key 管理：

- **LLM API Key**（如 OPENAI_API_KEY）：通过 `.env` 文件注入，不在镜像中硬编码
- **LangFuse 密钥**：通过环境变量传递，生产环境使用强随机值
- **推荐方案**：生产环境使用 Docker Secrets 或外部密钥管理服务（如 Vault）

## 技术关系

Docker 和 Docker Compose 是 AI Agent 应用的部署基础设施：

- **[项目 compose.yaml](compose.yaml)**：定义了 Agent 服务、LangFuse、PostgreSQL 的完整部署
- **[项目 Dockerfile](Dockerfile)**：Agent 平台的容器镜像构建定义
- **[代码执行沙箱](../phase02_production/29_code_sandbox.md)**：Docker 是沙箱的底层技术
- **[LLM 可观测性](../phase02_production/25_observability.md)**：LangFuse 服务和数据库通过 Compose 编排
- **CI/CD 流水线**：Docker 镜像构建是持续集成的核心环节

## 验收清单

- [ ] Dockerfile 使用多阶段构建
- [ ] 基础镜像使用 slim 或 alpine 版本
- [ ] 容器以非 root 用户运行
- [ ] 配置了健康检查
- [ ] 设置了资源限制（CPU / 内存）
- [ ] compose.yaml 使用 .env 文件管理配置
- [ ] 敏感信息已从配置文件中移除
- [ ] 数据卷正确配置（持久化 / 只读挂载）
- [ ] 服务启动顺序正确配置
- [ ] 日志管理配置（大小 / 轮转）
- [ ] 网络隔离配置
- [ ] 生产环境密钥使用外部管理

## 学习资源

- [Dockerfile 最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Docker 安全](https://docs.docker.com/engine/security/)
- [多阶段构建](https://docs.docker.com/build/building/multi-stage/)
- [Docker 官方 Python 镜像](https://hub.docker.com/_/python)
