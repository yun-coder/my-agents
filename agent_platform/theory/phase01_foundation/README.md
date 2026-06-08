# 阶段一：基础闭环（第 1-12 周）

> 核心目标：跑通 LLM + RAG + Tool Calling + API 服务闭环

## 16 个专题

| # | 专题 | Key依赖 | agent_platform 代码位置 |
|---|---|---|---|
| 01 | Prompt Engineering | 🔑 LLM | `src/llm/client.py`, `src/rag/generator.py` |
| 02 | 结构化输出 | 🔑 LLM | `src/llm/structured.py` |
| 03 | OpenAI API | 🔑 LLM | `src/llm/client.py` |
| 04 | Claude API | 🔐 Anthropic Key | — |
| 05 | Function Calling | 🔑 LLM | `src/agent/tools.py`, `src/agent/graph.py` |
| 06 | Embedding 模型 | 🔓 本地BGE | `src/embeddings/local_bge.py` |
| 07 | 向量数据库 | 🔓 Chroma本地 | `src/vectordb/chroma_store.py` |
| 08 | 文档解析 | 🔓 PyMuPDF | `src/parsing/document.py` |
| 09 | RAG 基础 | 🔑 LLM | `src/rag/` (retriever, generator, reranker) |
| 10 | LangChain | 🔑 LLM | — |
| 11 | LlamaIndex | 🔑 LLM | — |
| 12 | LangGraph 入门 | 🔑 LLM | `src/agent/graph.py` |
| 13 | 短期记忆 | 🔓 本地 | `src/agent/memory.py` |
| 14 | FastAPI | 🔓 本地 | `src/api/` (app, routes, middleware) |
| 15 | LangFuse 可观测性 | 🔓 自托管 | `src/observability/tracing.py` |
| 16 | Python 工程化 | 🔓 本地 | `pyproject.toml`, `tests/` |

## 综合项目

**企业知识库问答 Agent MVP** → 对应 `agent_platform/` 源代码

功能：文档上传 → 解析 → Embedding → 向量检索 → RAG 问答 → 工具调用 → 流式 API → 追踪

## 验收标准

- [ ] 支持 PDF / Word / Markdown 至少 3 种文档格式
- [ ] 至少接入 1 个向量数据库（Chroma）
- [ ] 支持至少 3 个工具调用
- [ ] 每次 LLM 调用可在 LangFuse 中追踪
- [ ] 有 README、启动脚本、测试样例
