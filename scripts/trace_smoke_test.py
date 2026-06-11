"""LangFuse 端到端烟测。

跑法:
    cd "D:/学习院/my-agents"
    ./.venv/Scripts/python.exe -m scripts.trace_smoke_test

期望: 控制台打印 `enabled=True` + LangFuse UI Traces 页面出现
      smoke.llm / smoke.rag / smoke.agent 三条 trace。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# 让 `python -m scripts.trace_smoke_test` 也能 import src.*
ROOT = Path(__file__).resolve().parents[1] / "agent_platform"
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from src.config import load_config  # noqa: E402
from src.llm.client import get_llm_client  # noqa: E402
from src.observability import flush, init_tracing, is_enabled, traced_operation  # noqa: E402


def main() -> int:
    cfg = load_config()
    if cfg.langfuse:
        print(f"[cfg] langfuse host={cfg.langfuse.host}")
        print(f"[cfg] public_key={cfg.langfuse.public_key[:18]}… "
              f"secret_len={len(cfg.langfuse.secret_key)}")

    ok = init_tracing()
    print(f"[init] enabled={is_enabled()} ok={ok}")
    if not is_enabled():
        print("⚠️  LangFuse 未启用，trace 不会进 dashboard。")
        print("   检查 dev.json / dev.local.json / 环境变量里的密钥是否含 '...'。")
        return 1

    # 1) 纯 LLM
    llm = get_llm_client()
    with traced_operation(
        "smoke.llm",
        input="ping",
        model=llm.model,
        as_type="generation",
        metadata={"smoke": True},
    ) as op:
        out = llm.chat([{"role": "user", "content": "用一句话说 hi"}])
        op.update(output=out)
        print(f"[smoke.llm] {out[:80]}")

    # 2) 完整 RAG
    from src.rag.generator import RAGGenerator
    from src.rag.retriever import Retriever
    from src.vectordb.chroma_store import ChromaVectorStore
    from src.embeddings.local_bge import get_embedding_provider

    emb = get_embedding_provider(cfg.embedding.model_name)
    store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
    if store.count > 0:
        rag = RAGGenerator(Retriever(store))
        with traced_operation("smoke.rag", input={"query": "用一句话总结资料"}):
            ans = rag.generate("用一句话总结资料")
            print(f"[smoke.rag] {ans.answer[:80]}")
    else:
        print("[smoke.rag] 知识库为空，跳过（先跑 python -m src.cli ingest --dir ...）")

    # 3) Agent (可选 —— 不强求有 knowledge_base)
    try:
        from src.agent.graph import AgentWorkflow
        agent = AgentWorkflow(rag_generator=(
            RAGGenerator(Retriever(store)) if store.count > 0 else None
        ))
        with traced_operation("smoke.agent", input={"task": "现在几点了"}):
            result = agent.run("现在几点了？")
            print(f"[smoke.agent] {result.get('final_answer', '')[:80]}")
    except Exception as e:
        print(f"[smoke.agent] 跳过：{e}")

    flush()
    print("\n✅ 完成。打开 http://localhost:3000 查看 Traces 页面。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
