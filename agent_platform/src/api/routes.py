"""API 路由：RAG 问答、Agent 对话、文档管理、健康检查。"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

_rag = None
_agent = None


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    session_id: str = Field(default="default")


class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str


class AgentResponse(BaseModel):
    answer: str
    tool_log: list[str]
    session_id: str


class HealthResponse(BaseModel):
    status: str
    version: str


class DocumentUploadResponse(BaseModel):
    message: str
    file_count: int
    chunks_processed: int


def _get_rag():
    global _rag
    if _rag is None:
        from ..vectordb.chroma_store import ChromaVectorStore
        from ..rag.retriever import Retriever
        from ..rag.generator import RAGGenerator
        from ..embeddings.local_bge import get_embedding_provider
        from ..config import load_config

        cfg = load_config()
        emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
        store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
        retriever = Retriever(store)
        _rag = RAGGenerator(retriever)
    return _rag


def _get_agent():
    global _agent
    if _agent is None:
        from ..agent.graph import AgentWorkflow
        _agent = AgentWorkflow(rag_generator=_get_rag())
    return _agent


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/rag/ask", response_model=RAGResponse)
async def rag_ask(req: QuestionRequest):
    from ..security.guard import SecurityGuard
    from ..security.sanitizer import InputSanitizer

    guard = SecurityGuard()
    sanitizer = InputSanitizer()

    clean = sanitizer.sanitize(req.question)
    violations = guard.check_input(clean)
    if violations:
        raise HTTPException(status_code=400, detail=f"输入违反安全策略：{'; '.join(violations)}")

    rag = _get_rag()
    try:
        answer = rag.generate(clean)
    except Exception as e:
        logger.error("RAG 生成错误：%s", e)
        raise HTTPException(status_code=500, detail=f"生成回答失败：{e}")

    violations = guard.check_output(answer.answer)
    final_answer = answer.answer
    if violations:
        final_answer = f"[回答已被安全护栏修改] 原回答包含违规内容：{'; '.join(violations)}"

    return RAGResponse(
        answer=final_answer,
        sources=answer.sources,
        session_id=req.session_id,
    )


@router.post("/rag/stream")
async def rag_ask_stream(req: QuestionRequest):
    from ..security.guard import SecurityGuard
    from ..security.sanitizer import InputSanitizer

    guard = SecurityGuard()
    sanitizer = InputSanitizer()

    clean = sanitizer.sanitize(req.question)
    violations = guard.check_input(clean)
    if violations:
        raise HTTPException(status_code=400, detail=f"输入违反安全策略：{'; '.join(violations)}")

    rag = _get_rag()

    async def generate():
        try:
            for chunk in rag.generate_stream(clean):
                yield chunk
        except Exception as e:
            yield f"\n[错误: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/agent/ask", response_model=AgentResponse)
async def agent_ask(req: QuestionRequest):
    from ..security.guard import SecurityGuard
    from ..security.sanitizer import InputSanitizer
    from ..agent.memory import ConversationMemory

    guard = SecurityGuard()
    sanitizer = InputSanitizer()

    clean = sanitizer.sanitize(req.question)
    violations = guard.check_input(clean)
    if violations:
        raise HTTPException(status_code=400, detail=f"输入违反安全策略：{'; '.join(violations)}")

    agent = _get_agent()
    try:
        result = agent.run(clean, req.session_id)
    except Exception as e:
        logger.error("Agent 执行错误：%s", e)
        raise HTTPException(status_code=500, detail=f"Agent 执行失败：{e}")

    return AgentResponse(
        answer=result.get("final_answer", "未能生成回答"),
        tool_log=result.get("tool_log", []),
        session_id=req.session_id,
    )


@router.post("/documents/upload")
async def upload_documents(directory: str):
    """批量导入文档目录到知识库。"""
    from ..parsing.document import parse_and_chunk, SUPPORTED_SUFFIXES
    from ..vectordb.chroma_store import ChromaVectorStore
    from ..embeddings.local_bge import get_embedding_provider
    from ..config import load_config

    cfg = load_config()
    emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
    store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)

    p = Path(directory)
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"目录不存在：{directory}")

    files = [f for f in p.iterdir() if f.suffix.lower() in SUPPORTED_SUFFIXES]
    if not files:
        raise HTTPException(
            status_code=400,
            detail=f"未找到支持的文档格式。支持：{sorted(SUPPORTED_SUFFIXES)}",
        )

    all_chunks = []
    for f in files:
        try:
            chunks = parse_and_chunk(f)
            all_chunks.extend(chunks)
            logger.info("解析完成：%s -> %d 个分块", f.name, len(chunks))
        except Exception as e:
            logger.warning("解析失败 %s：%s", f.name, e)

    if all_chunks:
        store.add_documents(all_chunks)

    return DocumentUploadResponse(
        message="文档导入完成",
        file_count=len(files),
        chunks_processed=len(all_chunks),
    )


@router.get("/documents/count")
async def document_count():
    try:
        rag = _get_rag()
        count = rag._retriever._store.count
        return {"count": count}
    except Exception:
        return {"count": 0}
