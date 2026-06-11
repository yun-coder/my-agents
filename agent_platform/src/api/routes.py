"""API 路由：RAG 问答、Agent 对话、文档管理、健康检查。"""

from __future__ import annotations

import logging
from pathlib import Path

import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
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


class ChunkPreview(BaseModel):
    index: int
    text_preview: str  # 前120字符
    char_count: int


class DocumentUploadResponse(BaseModel):
    message: str
    file_count: int
    chunks_processed: int
    total_chars: int = 0
    chunk_previews: list[ChunkPreview] = []


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


@router.post("/documents/upload-file", response_model=DocumentUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50,
):
    """上传单个文件并导入知识库。支持 PDF、Word、Markdown、TXT、HTML。"""
    from ..parsing.document import parse_and_chunk, SUPPORTED_SUFFIXES
    from ..vectordb.chroma_store import ChromaVectorStore
    from ..embeddings.local_bge import get_embedding_provider
    from ..config import load_config

    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{suffix}。支持：{sorted(SUPPORTED_SUFFIXES)}",
        )

    # 保存上传文件到临时目录
    tmp_path = None
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        logger.info("文件上传完成：%s（%.1f KB）", file.filename, len(content) / 1024)

        # 解析并分块
        chunks = parse_and_chunk(
            tmp_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        if not chunks:
            raise HTTPException(status_code=400, detail="文件内容为空或无法解析")

        # 写入向量数据库
        cfg = load_config()
        emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
        store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
        store.add_documents(chunks)

        logger.info(
            "文档入库完成：%s -> %d 个分块", file.filename, len(chunks)
        )

        previews = [
            ChunkPreview(
                index=c.chunk_index,
                text_preview=c.text[:120] + ("..." if len(c.text) > 120 else ""),
                char_count=len(c.text),
            )
            for c in chunks[:5]  # 最多返回5个分块预览
        ]
        total_chars = sum(len(c.text) for c in chunks)

        return DocumentUploadResponse(
            message=f"上传成功：{file.filename}",
            file_count=1,
            chunks_processed=len(chunks),
            total_chars=total_chars,
            chunk_previews=previews,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("文件上传处理失败：%s", e)
        raise HTTPException(status_code=500, detail=f"文件处理失败：{e}")
    finally:
        # 清理临时文件
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


@router.get("/documents/count")
async def document_count():
    try:
        rag = _get_rag()
        count = rag._retriever._store.count
        return {"count": count}
    except Exception:
        return {"count": 0}


@router.post("/rag/trace")
async def rag_trace(req: QuestionRequest):
    """RAG 全流程追踪：返回每一步的输入输出和中间数据。"""
    from ..workflow_trace import WorkflowTracer

    tracer = WorkflowTracer()
    try:
        tracer.run(req.question)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Trace error: %s", e)
        raise HTTPException(status_code=500, detail=f"流程追踪失败：{e}")

    return tracer.to_dict()


@router.post("/rag/trace-query")
async def rag_trace_query(req: QuestionRequest):
    """RAG 查询流程可视化：仅追踪查询 → 检索 → 生成，不复用全量导入流程。"""
    import time
    from ..workflow_trace import StepResult

    steps: list[dict] = []
    t_start = time.perf_counter()

    def record(step_name: str, input_data: dict, output_data: dict) -> dict:
        elapsed = (time.perf_counter() - t_start) * 1000
        steps.append({
            "step": step_name,
            "duration_ms": round(elapsed, 1),
            "input": input_data,
            "output": output_data,
        })
        return output_data

    try:
        from ..embeddings.local_bge import get_embedding_provider
        from ..vectordb.chroma_store import ChromaVectorStore
        from ..rag.retriever import Retriever
        from ..llm.client import get_llm_client
        from ..config import load_config

        cfg = load_config()
        emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
        store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
        retriever = Retriever(store)
        llm = get_llm_client()

        q = req.question

        # Step 1: 查询向量化
        qv = emb.embed_query(q)
        record("1. 查询向量化", {"query": q}, {
            "dimension": len(qv),
            "vector_preview": [round(float(v), 4) for v in qv[:5]],
        })

        # Step 2: 向量检索
        top_k = 5
        hits = store.search(q, top_k=top_k)
        results = []
        for i, r in enumerate(hits):
            sim = 1 - r.get("distance", 0)
            results.append({
                "rank": i + 1,
                "source": r.get("metadata", {}).get("source", r["id"]),
                "text_preview": r["text"][:150] + ("..." if len(r["text"]) > 150 else ""),
                "similarity": round(sim, 4),
            })
        record("2. 向量检索", {"query": q, "top_k": top_k}, {
            "hits_count": len(hits),
            "results": results,
        })

        # Step 3: 上下文组装
        ctx = retriever.format_context(hits)
        sources = retriever.format_sources(hits)
        record("3. 上下文组装", {"hits_count": len(hits)}, {
            "context_chars": len(ctx),
            "context_preview": ctx[:300] + ("..." if len(ctx) > 300 else ""),
            "sources": sources,
            "est_tokens": len(ctx) // 3,
        })

        # Step 4: LLM 生成
        msgs = [
            {"role": "system", "content": "只根据提供的资料回答问题。资料不足时明确说明。回答时引用来源编号。"},
            {"role": "user", "content": f"<资料>\n{ctx}\n</资料>\n\n问题：{q}"},
        ]
        t_gen = time.perf_counter()
        answer = llm.chat(msgs)
        gen_ms = (time.perf_counter() - t_gen) * 1000
        record("4. LLM生成回答", {"model": llm.model}, {
            "answer": answer,
            "answer_len": len(answer),
            "gen_ms": round(gen_ms, 1),
            "sources": sources,
        })

        total_ms = (time.perf_counter() - t_start) * 1000
        return {
            "total_duration_ms": round(total_ms, 1),
            "steps": steps,
        }

    except Exception as e:
        logger.error("查询追踪失败：%s", e)
        raise HTTPException(status_code=500, detail=f"查询追踪失败：{e}")
