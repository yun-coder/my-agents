# AI Agent 技术栈 — API Key 依赖分析

> 分析日期：2026-06-08

## 一、分类标准

| 分类 | 含义 |
|---|---|
| **免费本地** | pip/brew 安装即可用，无需任何外部 Key |
| **本地部署需Key** | 工具本身免费，但运行时依赖 LLM API Key |
| **需单独申请Key** | 必须去官网注册申请（有免费额度或付费） |
| **纯SaaS付费** | 必须付费才能使用 |

---

## 二、当前项目可用的"零额外Key"方案

基于现有资源（OpenAI 兼容 API via okinto.com + 本地 Docker），**无需申请任何新 Key** 即可运行的技术栈：

```
LLM 调用        -> OpenAI 兼容 API (okinto.com)           <- 已有 Key
Agent 框架      -> LangChain / LangGraph                   <- 免费 pip
结构化输出      -> Instructor + Pydantic                   <- 免费 pip
Embedding       -> BGE (sentence-transformers 本地)        <- 免费本地
向量数据库      -> Chroma (pip) 或 Qdrant (Docker)         <- 免费本地
文档解析        -> PyMuPDF / Docling                       <- 免费 pip
记忆管理        -> 自实现 + Redis (Docker)                  <- 免费本地
Reranker        -> BGE-Reranker (FlagEmbedding 本地)       <- 免费本地
Agent 编排      -> LangGraph (开源)                        <- 免费 pip
MCP 协议        -> MCP Python SDK                          <- 免费 pip
安全护栏        -> 自定义 Guard + 注入检测                  <- 免费本地
可观测性        -> LangFuse 自托管 (Docker, localhost:3000) <- 免费本地
API 服务        -> FastAPI                                  <- 免费 pip
部署            -> Docker Compose                           <- 免费本地
RAG 评估        -> RAGAS (本地指标计算)                     <- 免费 pip
```

---

## 三、需要额外申请 Key 的技术（标⭐建议申请）

| 技术 | 优先级 | 免费额度 |
|---|---|---|
| ⭐ Anthropic Claude API | 高 | 无（需充值） |
| ⭐ Google Gemini API | 高 | 有免费额度 |
| Cohere API | 中 | 10万次/月 |
| Pinecone | 中 | 1个免费索引 |
| E2B | 低 | 有限免费 |
| Helicone | 低 | 有限免费 |

---

## 四、LangSmith 说明

LangSmith 本地部署需要官方 API Key（lsv2_pt_xxx），即使本地部署也无法绕过。
本项目使用 **LangFuse 自托管**（Docker，localhost:3000）完全替代 LangSmith 的追踪、评估功能。
