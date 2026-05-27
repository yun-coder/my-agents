# Langfuse Observability Demos

These demos are based on current Langfuse documentation for the Python SDK,
OpenAI wrapper, LangChain callback handler, LlamaIndex/OpenInference,
Instructor, LiteLLM, and OpenTelemetry ingestion.

## Setup

Create or reuse `../dev.json`:

```json
{
  "langfuse": {
    "host": "http://localhost:3000",
    "public_key": "pk-lf-...",
    "secret_key": "sk-lf-...",
    "debug": false
  }
}
```

Install the core SDK:

```powershell
pip install langfuse
```

Run one demo:

```powershell
python langfuse_demos\03_generation_observation_demo.py
```

## What Langfuse Can Observe

- `01_trace_attributes_demo.py`: trace input/output, user, session, tags, metadata, version.
- `02_span_observation_demo.py`: generic timed application work.
- `03_generation_observation_demo.py`: LLM calls, model parameters, token usage, costs.
- `04_agent_observation_demo.py`: agent planning and decisions.
- `05_tool_observation_demo.py`: agent tools and external system calls.
- `06_chain_observation_demo.py`: multi-step chains and pipelines.
- `07_retriever_observation_demo.py`: RAG retrieval/search.
- `08_embedding_observation_demo.py`: embedding calls and vectorization batches.
- `09_evaluator_observation_demo.py`: LLM-as-judge or rule-based evaluation steps.
- `10_guardrail_observation_demo.py`: safety, policy, schema, or compliance checks.
- `11_event_observation_demo.py`: zero-duration events such as cache misses and retries.
- `12_score_demo.py`: trace and observation scores.

## How Langfuse Can Observe It

- `13_observe_decorator_way_demo.py`: `@observe` decorator.
- `14_context_manager_way_demo.py`: `start_as_current_observation(...)` context manager.
- `15_manual_lifecycle_way_demo.py`: `start_observation(...)` with explicit `end()`.
- `16_async_observe_way_demo.py`: async functions with `@observe`.
- `17_openai_wrapper_way_demo.py`: `langfuse.openai.OpenAI`.
- `18_langchain_callback_way_demo.py`: `langfuse.langchain.CallbackHandler`.
- `19_llamaindex_openinference_way_demo.py`: LlamaIndex via OpenInference instrumentation.
- `20_instructor_openai_way_demo.py`: Instructor patched on Langfuse OpenAI client.
- `21_litellm_callback_way_demo.py`: LiteLLM callback or proxy logging route.
- `22_opentelemetry_endpoint_way_demo.py`: raw OTLP/HTTP export to Langfuse.

## Documentation Sources

- Langfuse Python SDK docs via Context7: `/langfuse/langfuse-python`
- Langfuse docs via Context7: `/langfuse/langfuse-docs`
- LangChain integration: https://langfuse.com/docs/integrations/langchain
- LlamaIndex integration: https://langfuse.com/integrations/frameworks/llamaindex
- Instructor integration: https://langfuse.com/integrations/frameworks/instructor
- LiteLLM integration: https://langfuse.com/integrations/gateways/litellm
- OpenTelemetry integration: https://langfuse.com/integrations/native/opentelemetry
