from __future__ import annotations
import json, time
from dataclasses import dataclass, field
from typing import Any

@dataclass
class StepResult:
    step_name: str
    duration_ms: float
    input_data: Any
    output_data: Any
    metadata: dict = field(default_factory=dict)

class WorkflowTracer:
    def __init__(self):
        self.steps = []
        self._start_time = time.perf_counter()

    def _record(self, name, inp, out, **meta):
        d = (time.perf_counter() - self._start_time) * 1000
        s = StepResult(name, d, inp, out, meta)
        self.steps.append(s)
        return s

    def _store_and_emb(self):
        from src.embeddings.local_bge import get_embedding_provider
        from src.vectordb.chroma_store import ChromaVectorStore
        from src.config import load_config
        cfg = load_config()
        emb = get_embedding_provider(cfg.embedding.model_name)
        store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
        return cfg, emb, store

    def step1_parse(self, directory):
        from src.parsing.document import parse_and_chunk, SUPPORTED_SUFFIXES
        from pathlib import Path
        p = Path(directory)
        files = [f for f in p.iterdir() if f.suffix.lower() in SUPPORTED_SUFFIXES]
        all_chunks = []
        details = []
        for f in files:
            chunks = parse_and_chunk(f)
            all_chunks.extend(chunks)
            details.append({"file": f.name, "format": f.suffix, "chunks": len(chunks)})
        out = {"files": len(files), "total_chunks": len(all_chunks), "details": details}
        self._record("1. 文档解析与分块", {"directory": directory}, out)
        return all_chunks

    def step2_load_model(self, model_name):
        from src.embeddings.local_bge import get_embedding_provider
        t0 = time.perf_counter()
        emb = get_embedding_provider(model_name)
        lt = (time.perf_counter() - t0) * 1000
        out = {"model": model_name, "dimension": emb.dimension, "load_ms": round(lt, 1)}
        self._record("2. 加载Embedding模型", {"model": model_name}, out)
        return out

    def step3_vectorize(self, all_chunks):
        from src.vectordb.chroma_store import ChromaVectorStore
        from src.embeddings.local_bge import get_embedding_provider
        from src.config import load_config
        cfg = load_config()
        emb = get_embedding_provider(cfg.embedding.model_name)
        store = ChromaVectorStore(cfg.chroma_persist_dir, embedding=emb)
        sample_text = all_chunks[0].text if all_chunks else ""
        sample_vec = emb.embed_query(sample_text) if sample_text else []
        store.add_documents(all_chunks)
        out = {
            "total_chunks": len(all_chunks), "total_vectors": store.count,
            "vector_dim": len(sample_vec),
            "sample_vector": [round(v, 4) for v in sample_vec[:3]] if sample_vec else [],
            "sample_text": sample_text[:120],
        }
        self._record("3. 向量化与存储", {"chunks": len(all_chunks)}, out)
        return out

    def step4_query_vector(self, query):
        cfg, emb, store = self._store_and_emb()
        qv = emb.embed_query(query)
        out = {"query": query, "dim": len(qv), "vector_preview": [round(v, 4) for v in qv[:3]]}
        self._record("4. 查询向量化", {"query": query}, out)
        return out

    def step5_retrieve(self, query, top_k=5):
        cfg, emb, store = self._store_and_emb()
        results = store.search(query, top_k=top_k)
        fmt = []
        for i, r in enumerate(results):
            sim = 1 - r["distance"]
            fmt.append({
                "rank": i + 1,
                "source": r.get("metadata", {}).get("source", r["id"]),
                "text": r["text"][:180] + ("..." if len(r["text"]) > 180 else ""),
                "similarity": round(sim, 4),
            })
        out = {"query": query, "top_k": top_k, "count": len(fmt), "results": fmt}
        self._record("5. 向量检索", {"query": query, "top_k": top_k}, out)
        return out

    def step6_build_prompt(self, query):
        cfg, emb, store = self._store_and_emb()
        from src.rag.retriever import Retriever
        rt = Retriever(store)
        docs = store.search(query, top_k=5)
        ctx = rt.format_context(docs)
        sources = rt.format_sources(docs)
        sp = "只根据提供的资料回答问题。资料不足时明确说明。回答时引用来源编号。"
        full = "<system>\n" + sp + "\n</system>\n\n<资料>\n" + ctx + "\n</资料>\n\n问题：" + query
        out = {
            "system_prompt": sp,
            "context_chars": len(ctx),
            "context_preview": ctx[:250] + ("..." if len(ctx) > 250 else ""),
            "sources": sources,
            "prompt_preview": full[:400] + ("..." if len(full) > 400 else ""),
            "est_tokens": len(full) // 3,
        }
        self._record("6. 上下文组装与Prompt构造", {"query": query}, out)
        return out

    def step7_generate(self, query):
        cfg, emb, store = self._store_and_emb()
        from src.rag.retriever import Retriever
        from src.llm.client import get_llm_client
        rt = Retriever(store)
        llm = get_llm_client()
        docs = store.search(query, top_k=5)
        ctx = rt.format_context(docs)
        sources = rt.format_sources(docs)
        msgs = [
            {"role": "system", "content": "只根据资料回答。引用来源。不足时说不知道。"},
            {"role": "user", "content": "<资料>\n" + ctx + "\n</资料>\n\n问题：" + query},
        ]
        t0 = time.perf_counter()
        answer = llm.chat(msgs)
        gt = (time.perf_counter() - t0) * 1000
        out = {
            "query": query, "answer": answer, "sources": sources,
            "gen_ms": round(gt, 1), "model": llm.model, "answer_len": len(answer),
        }
        self._record("7. LLM生成回答", {"query": query, "model": llm.model}, out)
        return out

    def run(self, query, docs_dir="data/documents"):
        self.steps.clear()
        self._start_time = time.perf_counter()
        chunks = self.step1_parse(docs_dir)
        self.step2_load_model("BAAI/bge-small-zh-v1.5")
        self.step3_vectorize(chunks)
        self.step4_query_vector(query)
        self.step5_retrieve(query)
        self.step6_build_prompt(query)
        result = self.step7_generate(query)
        return result

    def print_report(self):
        print()
        print("=" * 65)
        print("  RAG Workflow Trace Report")
        print("=" * 65)
        for s in self.steps:
            print()
            print("-" * 50)
            print("  [" + s.step_name + "]  (" + str(int(s.duration_ms)) + "ms)")
            print("-" * 50)
            out = s.output_data
            if not isinstance(out, dict):
                continue
            for k, v in out.items():
                if k == "results" and isinstance(v, list):
                    print("    results:")
                    for r in v:
                        src = str(r.get("source", ""))
                        sim = r.get("similarity", 0)
                        txt = str(r.get("text", ""))[:100]
                        print("      #" + str(r.get("rank")) + " [" + src + "] sim=" + str(sim))
                        print("        " + txt)
                elif k == "prompt_preview":
                    print("    prompt_preview:")
                    for line in str(v).split("\n")[:6]:
                        print("      | " + line)
                elif k == "answer":
                    print("    answer: " + str(v))
                elif k == "sources":
                    print("    sources: " + str(v))
                elif isinstance(v, (str, int, float, bool)):
                    vs = str(v)
                    if len(vs) > 120:
                        vs = vs[:120] + "..."
                    print("    " + k + ": " + vs)
                elif isinstance(v, list) and len(v) <= 10:
                    print("    " + k + ": " + str(v))
        total = sum(s.duration_ms for s in self.steps)
        print()
        print("=" * 65)
        print("  Total: " + str(int(total)) + "ms")
        print("=" * 65)
        print()

    def to_dict(self):
        return {
            "total_duration_ms": sum(s.duration_ms for s in self.steps),
            "steps": [{"step": s.step_name, "duration_ms": round(s.duration_ms, 1), "input": s.input_data, "output": s.output_data, "metadata": s.metadata} for s in self.steps],
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, default=str)
