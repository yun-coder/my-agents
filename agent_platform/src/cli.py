"""Agent Platform CLI — 命令行工具。

用法:
    # 导入文档到知识库
    python -m src.cli ingest --dir ./data/documents

    # 交互式 RAG 问答
    python -m src.cli ask "什么是 RAG？"

    # 离线验证（不调用 LLM）
    python -m src.cli ask "什么是 RAG？" --offline

    # Agent 模式（带工具调用）
    python -m src.cli agent "帮我计算 3*5+10"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cli")


def cmd_ingest(args) -> None:
    """导入文档目录到知识库。"""
    from src.parsing.document import parse_and_chunk, SUPPORTED_SUFFIXES
    from src.vectordb.chroma_store import ChromaVectorStore
    from src.embeddings.local_bge import get_embedding_provider
    from src.config import load_config

    cfg = load_config()
    emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
    store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)

    directory = Path(args.dir)
    if not directory.exists():
        print(f"错误：目录不存在 - {directory}")
        sys.exit(1)

    files = [f for f in directory.iterdir() if f.suffix.lower() in SUPPORTED_SUFFIXES]
    if not files:
        print(f"未找到支持的文档。支持格式：{sorted(SUPPORTED_SUFFIXES)}")
        return

    print(f"找到 {len(files)} 个文档，开始解析...")
    all_chunks = []
    for f in files:
        try:
            chunks = parse_and_chunk(f)
            all_chunks.extend(chunks)
            print(f"  {f.name} -> {len(chunks)} 个分块")
        except Exception as e:
            logger.warning("解析失败 %s: %s", f.name, e)

    if all_chunks:
        print(f"共 {len(all_chunks)} 个分块，正在向量化写入...")
        store.add_documents(all_chunks)
        print(f"完成！知识库共 {store.count} 条记录。")
    else:
        print("未解析到任何文本内容。")


def cmd_ask(args) -> None:
    """RAG 问答。"""
    from src.rag.generator import RAGGenerator
    from src.rag.retriever import Retriever
    from src.vectordb.chroma_store import ChromaVectorStore
    from src.embeddings.local_bge import get_embedding_provider
    from src.config import load_config

    cfg = load_config()
    emb = get_embedding_provider(cfg.embedding.model_name, cfg.embedding.device)
    store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)

    if store.count == 0:
        print("知识库为空。请先导入文档：python -m src.cli ingest --dir <目录>")
        return

    retriever = Retriever(store)
    rag = RAGGenerator(retriever)

    if args.offline:
        docs = rag.retrieve(args.question)
        if not docs:
            print("未找到相关资料。")
        else:
            print("检索结果（离线模式）：")
            for i, doc in enumerate(docs, 1):
                source = doc.get("metadata", {}).get("source", doc["id"])
                text = doc["text"][:200]
                print(f"  [{i}] {source}")
                print(f"      {text}...")
        return

    print("思考中...")
    answer = rag.generate(args.question)
    print(f"\n回答：{answer.answer}")
    if answer.sources:
        print(f"\n来源：{', '.join(answer.sources)}")


def cmd_agent(args) -> None:
    """Agent 模式。"""
    from src.agent.graph import AgentWorkflow

    agent = AgentWorkflow()
    print("Agent 思考中...")
    result = agent.run(args.task)

    if result.get("tool_log"):
        print("\n工具调用记录：")
        for log in result["tool_log"]:
            print(f"  {log}")

    print(f"\n回答：{result.get('final_answer', '未能生成回答')}")


def cmd_trace(args):
    """完整流程追踪。"""
    from src.workflow_trace import WorkflowTracer

    tracer = WorkflowTracer()
    print('Running RAG pipeline with full tracing...')
    result = tracer.run(args.question, args.dir)
    tracer.print_report()

    if args.json:
        import json
        out = tracer.to_json()
        out_path = 'workflow_trace.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(out)
        print(f'JSON exported to {out_path}')


def cmd_serve(args) -> None:
    """启动 API 服务。"""
    import uvicorn
    from src.api.app import app

    print(f"启动 API 服务：http://{args.host}:{args.port}")
    print(f"API 文档：http://{args.host}:{args.port}/docs")
    uvicorn.run(app, host=args.host, port=args.port)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent Platform CLI — 企业级 AI Agent 平台",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="导入文档到知识库")
    ingest_parser.add_argument("--dir", required=True, help="文档目录路径")

    # ask
    ask_parser = subparsers.add_parser("ask", help="RAG 问答")
    ask_parser.add_argument("question", help="问题")
    ask_parser.add_argument("--offline", action="store_true", help="离线模式（仅检索）")

    # agent
    agent_parser = subparsers.add_parser("agent", help="Agent 模式（带工具调用）")
    agent_parser.add_argument("task", help="任务描述")

    # serve
    trace_parser = subparsers.add_parser("trace", help="RAG 全流程追踪（含每步中间数据）")
    trace_parser.add_argument("question", help="问题")
    trace_parser.add_argument("--dir", default="data/documents", help="文档目录")
    trace_parser.add_argument("--json", action="store_true", help="导出JSON报告")

    serve_parser = subparsers.add_parser("serve", help="启动 API 服务")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "trace":
        cmd_trace(args)
    elif args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "ask":
        cmd_ask(args)
    elif args.command == "agent":
        cmd_agent(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
