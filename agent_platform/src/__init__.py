"""Agent Platform — 企业级 AI Agent 集成演示项目。

本平台展示以下技术的生产级集成：
- LLM 统一客户端（OpenAI 兼容 API）
- 本地 BGE Embedding（无需外部 Key）
- Chroma 向量数据库（本地持久化）
- 多格式文档解析（PyMuPDF / Docling）
- RAG 检索增强生成 + 本地 BGE Reranker
- LangGraph Agent 工作流编排 + Tool Calling
- FastAPI REST/SSE 服务
- 安全护栏 + Prompt 注入检测
- LangFuse 自托管可观测性
- Docker Compose 一键部署
"""
