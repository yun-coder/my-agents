# Agent Platform — 企业级 AI Agent 集成演示平台

## 概述

本项目是 AI Agent 技术栈学习计划的**核心集成 Demo**，在一个项目中展示了以下技术的生产级集成：

| 模块 | 技术 | Key 依赖 |
|---|---|---|
| LLM 客户端 | OpenAI 兼容 API | 已有（okinto.com） |
| 结构化输出 | Instructor + Pydantic | 免费 pip |
| Embedding | BGE (sentence-transformers) | **免费本地** |
| 向量数据库 | Chroma (持久化) | **免费本地** |
| 文档解析 | PyMuPDF / python-docx | **免费本地** |
| RAG 检索 | 语义检索 + BM25 混合 | **免费本地** |
| Reranker | BGE-Reranker (FlagEmbedding) | **免费本地** |
| Agent 编排 | LangGraph 状态图 | **免费 pip** |
| 工具调用 | 文件搜索 / 计算器 / 时间 | **免费本地** |
| 对话记忆 | 滑动窗口 + 摘要压缩 | **免费本地** |
| API 服务 | FastAPI + SSE 流式 | **免费 pip** |
| 安全护栏 | 注入检测 + 内容过滤 | **免费本地** |
| 可观测性 | LangFuse 自托管 (Docker) | **免费本地** |
| 部署 | Docker Compose 一键启动 | **免费本地** |

## 零额外 Key 原则

本项目设计目标：**在不申请任何新 API Key 的前提下**，完整展示 AI Agent 技术栈。

- **LLM 调用**：复用现有 OpenAI 兼容 API
- **Embedding**：本地 BGE 模型（首次运行自动下载，约 100MB）
- **Reranker**：本地 BGE-Reranker（首次运行自动下载，约 1GB）
- **向量存储**：Chroma 本地持久化
- **可观测性**：LangFuse Docker 自托管（替代 LangSmith）

## 快速开始

### 1. 环境准备

```bash
# Python 3.11+
python --version

# 安装依赖
cd agent_platform
pip install -e ".[dev]"

# 确保 dev.json 存在（仓库根目录）
cat ../dev.json
```

### 2. 导入知识库

```bash
# 创建示例文档目录
mkdir -p data/documents

# 导入文档
python -m src.cli ingest --dir data/documents
```

### 3. 命令行使用

```bash
# RAG 问答（在线模式）
python -m src.cli ask "什么是 RAG？"

# RAG 问答（离线模式，仅检索）
python -m src.cli ask "什么是 RAG？" --offline

# Agent 模式（带工具调用）
python -m src.cli agent "帮我计算 3*5+10"
python -m src.cli agent "搜索当前目录的 Python 文件"
python -m src.cli agent "现在几点了？"
```

### 4. API 服务

```bash
# 启动 API 服务
python -m src.cli serve --port 8000

# 或使用 uvicorn
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

API 文档：http://localhost:8000/docs

**API 端点**：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/rag/ask` | RAG 问答 |
| POST | `/api/v1/rag/stream` | RAG 流式问答 (SSE) |
| POST | `/api/v1/agent/ask` | Agent 对话（含工具调用） |
| POST | `/api/v1/documents/upload` | 批量导入文档 |
| GET | `/api/v1/documents/count` | 知识库文档数 |

```bash
# 测试 API
curl -X POST http://localhost:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是 RAG？"}'
```

### 5. Docker Compose 部署

```bash
docker compose up -d
# API: http://localhost:8000
# LangFuse: http://localhost:3000
```

## 项目结构

```
agent_platform/
├── src/
│   ├── config.py              # 配置管理
│   ├── cli.py                 # CLI 命令行工具
│   ├── llm/
│   │   ├── client.py          # 统一 LLM 客户端
│   │   └── structured.py      # 结构化输出 (Instructor)
│   ├── embeddings/
│   │   └── local_bge.py       # 本地 BGE Embedding
│   ├── parsing/
│   │   └── document.py        # 文档解析 + 分块
│   ├── vectordb/
│   │   └── chroma_store.py    # Chroma 向量存储
│   ├── rag/
│   │   ├── retriever.py       # RAG 检索器
│   │   ├── reranker.py        # 本地 BGE Reranker
│   │   └── generator.py       # RAG 生成器
│   ├── agent/
│   │   ├── graph.py           # LangGraph 工作流
│   │   ├── tools.py           # 工具定义
│   │   └── memory.py          # 对话记忆
│   ├── api/
│   │   ├── app.py             # FastAPI 应用
│   │   ├── routes.py          # API 路由
│   │   └── middleware.py      # 请求追踪中间件
│   ├── security/
│   │   ├── guard.py           # 安全护栏
│   │   └── sanitizer.py       # 输入净化
│   └── observability/
│       └── tracing.py         # LangFuse 追踪
├── tests/
│   └── test_all.py            # 集成测试
├── data/
│   └── documents/             # 知识库文档目录
├── pyproject.toml
├── Dockerfile
├── compose.yaml
├── README.md
└── API_KEY_DEPENDENCY_ANALYSIS.md  # API Key 依赖分析
```

## 安全性

- **输入净化**：自动过滤 XSS、HTML 注入
- **Prompt 注入检测**：检测 "ignore instructions"、"显示系统提示词" 等攻击
- **输出检查**：检测 PII（手机号、身份证）泄漏
- **工具白名单**：只有预定义的工具可被调用
- **Key 隔离**：所有密钥存储在 dev.json（Git 忽略）

## 测试

```bash
cd agent_platform
python -m pytest tests/ -v
```

## 知识点对照

本项目覆盖学习计划中的以下知识点：

**必须优先掌握 ✅**：
1. Prompt Engineering — `src/llm/client.py`（系统提示词设计）
2. 结构化输出 — `src/llm/structured.py`（Instructor + Pydantic）
3. OpenAI API — `src/llm/client.py`（统一客户端）
4. Function Calling / Tool Use — `src/agent/tools.py`
5. Embedding — `src/embeddings/local_bge.py`（本地 BGE）
6. 向量数据库 — `src/vectordb/chroma_store.py`（Chroma）
7. 文档解析 — `src/parsing/document.py`（PyMuPDF）
8. RAG — `src/rag/`（检索 + 重排序 + 生成）
9. LangGraph — `src/agent/graph.py`（状态图编排）
10. FastAPI — `src/api/`（REST + SSE）
11. LangFuse — `src/observability/tracing.py`（可观测性）
12. 基础安全防护 — `src/security/`（护栏 + 注入检测）
13. Python 工程化 — `pyproject.toml` + 类型提示 + 测试
