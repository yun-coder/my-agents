# AI Agent 技术栈学习项目

> 基于 [AI Agent 技术栈学习计划](./AI_Agent技术栈学习计划.md) 的完整实践项目，覆盖 41 个知识点，从 Prompt Engineering 到 Agent 微调。

## 快速开始

```bash
cd agent_platform

# 安装依赖
pip install -e ".[dev]"

# 导入示例知识库
python -m src.cli ingest --dir data/documents

# RAG 问答
python -m src.cli ask "什么是 RAG？"

# Agent 模式（带工具调用）
python -m src.cli agent "现在几点？帮我计算 3*5"

# 启动 API 服务
python -m src.cli serve --port 8000
# 访问 http://localhost:8000/docs 查看 API 文档
```

## 项目结构

```
agent_platform/
├── src/                          # 生产级代码
│   ├── config.py                 # 配置管理（dev.json + 环境变量）
│   ├── cli.py                    # CLI（ingest / ask / agent / serve）
│   ├── llm/                      # LLM 客户端 + Instructor 结构化输出
│   ├── embeddings/               # 本地 BGE Embedding（零 API Key）
│   ├── parsing/                  # 文档解析（PyMuPDF / python-docx）
│   ├── vectordb/                 # Chroma 向量存储
│   ├── rag/                      # RAG：检索器 + BGE Reranker + 生成器
│   ├── agent/                    # LangGraph 工作流 + Tools + 记忆管理
│   ├── api/                      # FastAPI REST + SSE 流式
│   ├── security/                 # 安全护栏 + Prompt 注入检测
│   └── observability/            # LangFuse 自托管追踪
├── theory/                       # 41 篇详细理论（每篇 450-980 行）
│   ├── phase01_foundation/       # 16 篇：Prompt → Python 工程化
│   ├── phase02_production/       # 14 篇：LangGraph 深入 → Docker
│   ├── phase03_platform/         # 8 篇：Pydantic AI → 成本控制
│   └── phase04_frontier/         # 3 篇：GUI Agent → 微调
├── integrations/                 # 外部工具集成
│   ├── langfuse/                 # LangFuse 自托管 + 22 个 Demo
│   └── langsmith/                # LangSmith vs LangFuse 对比分析
├── tests/test_all.py             # 集成测试（可离线运行）
├── data/documents/               # 示例知识库文档
├── compose.yaml                  # Docker Compose 一键部署
├── README.md                     # 本项目文档
└── API_KEY_DEPENDENCY_ANALYSIS.md # API Key 依赖分析
```

## 技术栈

| 模块 | 技术选型 | Key 依赖 |
|---|---|---|
| LLM | OpenAI 兼容 API | 已有 |
| 结构化输出 | Instructor + Pydantic | 免费 |
| Embedding | BGE (sentence-transformers) | **免费本地** |
| 向量数据库 | Chroma | **免费本地** |
| 文档解析 | PyMuPDF | **免费本地** |
| Reranker | BGE-Reranker | **免费本地** |
| Agent 编排 | LangGraph | **免费 pip** |
| API 服务 | FastAPI + SSE | 免费 |
| 可观测性 | LangFuse 自托管 | **免费本地** |
| 安全护栏 | 自实现 + 注入检测 | 免费 |
| 部署 | Docker Compose | 免费 |

## 配置

复制 `dev.example.json` 为 `dev.json` 并填写 LLM API 配置：

```json
{
  "openai": {
    "api_key": "your-api-key",
    "base_url": "https://your-api-provider.example.com/v1",
    "model": "gpt-4.1-mini"
  },
  "langfuse": {
    "host": "http://localhost:3000",
    "public_key": "pk-lf-...",
    "secret_key": "sk-lf-..."
  }
}
```

`dev.json` 已在 `.gitignore` 中，不会提交到 Git。

## Docker 部署

```bash
cd agent_platform
docker compose up -d
# API: http://localhost:8000
# LangFuse: http://localhost:3000
```

## 测试

```bash
cd agent_platform
python -m pytest tests/ -v
```

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/rag/ask` | RAG 问答 |
| POST | `/api/v1/rag/stream` | RAG 流式 (SSE) |
| POST | `/api/v1/agent/ask` | Agent 对话（工具调用） |
| POST | `/api/v1/documents/upload` | 批量导入文档 |
| GET | `/api/v1/documents/count` | 知识库文档数 |

## 学习路线

```
阶段一 (1-12周)          阶段二 (13-24周)          阶段三 (25-34周)          阶段四 (35-44周)
基础闭环                  Agent编排与生产化          平台化与高级工程          前沿探索
─────────────────────────────────────────────────────────────────────────────────────
01 Prompt Engineering     17 LangGraph 深入          31 Pydantic AI           39 Computer Use
02 结构化输出             18 AutoGen / AG2           32 开源模型               40 多模态 Agent
03 OpenAI API             19 CrewAI                  33 Agent 托管平台         41 Agent 微调
04 Claude API             20 MCP 协议                34 消息队列
05 Function Calling       21 长期记忆                35 Kubernetes
06 Embedding 模型         22 状态持久化              36 多租户权限
07 向量数据库             23 Reranker 重排序         37 DSPy
08 文档解析               24 RAG 评估                38 成本控制与限流
09 RAG 基础               25 LLM 可观测性
10 LangChain              26 Guardrails 护栏
11 LlamaIndex             27 Prompt 注入防御
12 LangGraph 入门         28 浏览器自动化
13 短期记忆管理            29 代码执行沙箱
14 FastAPI 服务           30 Docker Compose
15 LangFuse 可观测性
16 Python 工程化
```

详细理论见 `agent_platform/theory/` 目录，代码实现见 `agent_platform/src/`。

## API Key 依赖速查

| 符号 | 含义 |
|---|---|
| 🔓 | 完全免费本地，无需任何 Key |
| 🔑 | 需要 LLM API Key（已有） |
| 🔐 | 需要单独申请第三方 Key |
| ⚡ | 可本地部署替代云服务 |

详见 [API_KEY_DEPENDENCY_ANALYSIS.md](./agent_platform/API_KEY_DEPENDENCY_ANALYSIS.md)。
