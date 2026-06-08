# 25 LLM 可观测性

## 概念概述

LLM 可观测性（Observability）是指通过收集、分析和可视化 LLM 应用运行时的各类数据，实现对系统行为理解、问题诊断和性能优化的能力。与传统软件的可观测性不同，LLM 应用的可观测性不仅要关注延迟、错误率等常规指标，还需要追踪 Token 消耗、成本、Prompt 版本、模型输出质量等 AI 特有的维度。

随着 LLM 应用从原型阶段进入生产环境，可观测性成为不可或缺的基础设施。一次 LLM 调用涉及 API 请求、Prompt 构建、响应解析、上下文管理等多个环节，任何一个环节出现问题都可能导致用户体验下降。完善的观测体系可以帮助团队快速定位问题、优化 Prompt、控制成本。

当前主流的 LLM 可观测性平台包括 LangFuse、Arize Phoenix、Helicone 等。这些平台大多基于 OpenTelemetry 标准构建，提供 Trace/Span 层级的数据采集能力。

## 核心原理

### OpenTelemetry 与 LLM Trace

OpenTelemetry（OTel）是 CNCF 下的可观测性标准，定义了 Trace 和 Span 的数据模型：

- **Trace**：代表一次完整的请求链路，从用户发起请求到最终响应。
- **Span**：Trace 中的每个独立操作单元，如一次 LLM 调用、一次向量检索、一次工具执行。
- **Span Context**：跨进程传播的上下文信息，用于串联整个请求链路。

在 LLM 场景中，典型的 Trace 结构如下：

```
User Request (Root Span)
  ├── Build Prompt (Span)
  ├── LLM Call (Span)
  │   ├── Token Usage (Attributes)
  │   └── Model Parameters (Attributes)
  ├── RAG Retrieval (Span)
  │   └── Vector DB Query (Span)
  ├── Tool Execution (Span)
  └── Response Formatting (Span)
```

### 三大平台对比

| 特性 | LangFuse | Arize Phoenix | Helicone |
|------|----------|---------------|----------|
| 部署方式 | 自托管 / 云 | 自托管 / 云 | 云服务为主 |
| 开源协议 | MIT | Elastic License 2.0 | MIT |
| Trace 支持 | 原生支持 | 深度支持 | 代理转发 |
| Token 统计 | 自动 | 自动 | 自动 |
| Prompt 管理 | 内置版本管理 | 无 | 有 |
| 评估集成 | 评分 / 人工标注 | 内置评估器 | 外部集成 |
| 成本追踪 | 支持 | 支持 | 支持 |
| 告警规则 | Webhook | 自定义 | 邮件通知 |
| Python SDK | langfuse | openinference | helicone |

### 关键监控指标

LLM 可观测性需要追踪的核心指标包括：

**延迟指标**：TTFT（首 Token 生成时间）、TPOT（每个输出 Token 时间）、端到端延迟、P50/P95/P99 延迟分布。

**Token 指标**：输入 Token 数、输出 Token 数、总 Token 数、Token 增长速度（Tokens/s）。

**成本指标**：单次调用成本、每日/月累计成本、按模型/用户/功能的成本分布。

**质量指标**：用户反馈评分、自动评估分数、错误率、重试率、幻觉率。

**流量指标**：QPS（每秒请求数）、活跃用户数、并发数、模型调用分布。

## 实战指南

### 集成 LangFuse 追踪

以下代码基于本项目的 `src/observability/tracing.py` 实现：

```python
"""LangFuse 追踪集成：生产环境中的 LLM 观测。"""
import logging
import os
import time
from contextlib import contextmanager
from typing import Any

import openai

logger = logging.getLogger(__name__)

# 全局 LangFuse 客户端
_langfuse_client = None


def init_langfuse_tracing() -> None:
    """从环境变量初始化 LangFuse，与项目 config.py 配合使用。"""
    global _langfuse_client
    try:
        from langfuse import Langfuse

        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

        if not public_key or not secret_key:
            logger.warning("LangFuse 密钥未配置，追踪已禁用")
            return

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        logger.info("LangFuse 追踪已初始化: %s", host)
    except ImportError:
        logger.warning("langfuse 包未安装，追踪已禁用")
    except Exception as exc:
        logger.warning("LangFuse 初始化失败: %s", exc)


class LLMTracer:
    """LLM 调用追踪器，封装对 LangFuse 的调用。"""

    def __init__(self) -> None:
        self.client = _langfuse_client

    def create_trace(
        self, name: str, user_id: str | None = None, metadata: dict | None = None
    ) -> Any:
        """创建一个新的 Trace。"""
        if self.client is None:
            return None
        return self.client.trace(
            name=name,
            user_id=user_id,
            metadata=metadata or {},
        )

    def trace_llm_call(
        self,
        trace_name: str,
        model: str,
        prompt: str,
        response: str,
        usage: dict[str, int] | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """追踪一次 LLM 调用。"""
        if self.client is None:
            return
        try:
            trace = self.client.trace(name=trace_name)
            generation = trace.generation(
                name=f"{trace_name}-llm",
                model=model,
                input=prompt,
                output=response,
                usage=usage,
                metadata={
                    "duration_ms": duration_ms,
                    "input_tokens": (usage or {}).get("prompt_tokens", 0),
                    "output_tokens": (usage or {}).get("completion_tokens", 0),
                },
            )
            self.client.flush()
            return generation
        except Exception as exc:
            logger.debug("LangFuse 记录 LLM 调用失败: %s", exc)

    def trace_retrieval(
        self,
        name: str,
        query: str,
        results: list[dict[str, Any]],
        duration_ms: float | None = None,
    ) -> None:
        """追踪一次 RAG 检索操作。"""
        if self.client is None:
            return
        try:
            trace = self.client.trace(name=name)
            trace.span(
                name=f"{name}-retrieval",
                input=query,
                output={
                    "documents": [r.get("text", "")[:200] for r in results],
                    "count": len(results),
                },
                metadata={
                    "duration_ms": duration_ms,
                    "result_count": len(results),
                },
            )
            self.client.flush()
        except Exception as exc:
            logger.debug("LangFuse 记录检索失败: %s", exc)

    def score_trace(
        self,
        trace_name: str,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """为 Trace 添加评分，用于评估和反馈。"""
        if self.client is None:
            return
        try:
            trace = self.client.trace(name=trace_name)
            trace.score(
                name=name,
                value=value,
                comment=comment or "",
            )
            self.client.flush()
        except Exception as exc:
            logger.debug("LangFuse 评分失败: %s", exc)


@contextmanager
def monitor_llm_call(model: str, prompt: str):
    """上下文管理器：自动监控 LLM 调用的延迟和 Token。"""
    tracer = LLMTracer()
    start = time.perf_counter()
    error: Exception | None = None
    try:
        yield
    except Exception as e:
        error = e
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        if error:
            logger.error(
                "LLM 调用失败 [%s]: %.1fms - %s", model, elapsed, error
            )
        else:
            logger.info(
                "LLM 调用完成 [%s]: %.1fms", model, elapsed
            )
```

### 使用 OpenInference 与 Arize Phoenix

```python
"""使用 OpenInference / Arize Phoenix 进行 LLM 可观测性。"""
import os
from typing import Any

import openai
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


def setup_phoenix_tracing(endpoint: str = "http://localhost:6006") -> None:
    """配置 Arize Phoenix 追踪。"""
    resource = Resource(attributes={
        "service.name": "agent-platform",
        "service.version": "1.0.0",
    })

    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
    )
    tracer_provider.add_span_processor(
        SimpleSpanProcessor(span_exporter)
    )
    otel_trace.set_tracer_provider(tracer_provider)

    OpenAIInstrumentor().instrument()
    print(f"Arize Phoenix 追踪已启用: {endpoint}")


def traced_llm_call(
    prompt: str, model: str = "gpt-4o"
) -> tuple[str, dict[str, Any]]:
    """使用 OpenTelemetry 追踪的 LLM 调用。"""
    tracer = otel_trace.get_tracer(__name__)
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("model", model)
        span.set_attribute("prompt.length", len(prompt))

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        span.set_attribute("completion_tokens", usage["completion_tokens"])
        span.set_attribute("total_tokens", usage["total_tokens"])
        span.set_attribute("response.length", len(content))

        return content, usage


if __name__ == "__main__":
    setup_phoenix_tracing()
    result, usage = traced_llm_call("简述 Python 的 GIL 机制。")
    print(f"响应: {result[:100]}...")
    print(f"用量: {usage}")
```

### 自定义监控仪表板

```python
"""轻量级 LLM 监控统计，无需外部服务。"""
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class LLMCallRecord:
    """单次 LLM 调用的记录。"""

    timestamp: float
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    success: bool
    error_type: str = ""


class LocalMonitor:
    """本地监控统计器，将数据写入 JSON 文件。"""

    def __init__(self, log_dir: str = "./data/monitor") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._records: list[LLMCallRecord] = []
        self._load_existing()

    def _load_existing(self) -> None:
        """加载已有的监控记录。"""
        log_file = self.log_dir / "llm_calls.jsonl"
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self._records.append(
                            LLMCallRecord(**json.loads(line))
                        )

    def record_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool = True,
        error_type: str = "",
    ) -> None:
        """记录一次 LLM 调用。"""
        total_tokens = prompt_tokens + completion_tokens
        input_cost = (prompt_tokens / 1_000_000) * 5.0
        output_cost = (completion_tokens / 1_000_000) * 15.0

        record = LLMCallRecord(
            timestamp=time.time(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=input_cost + output_cost,
            success=success,
            error_type=error_type,
        )
        self._records.append(record)
        self._append_to_file(record)

    def _append_to_file(self, record: LLMCallRecord) -> None:
        """追加记录到 JSONL 文件。"""
        log_file = self.log_dir / "llm_calls.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.__dict__, ensure_ascii=False) + "\n")

    def get_stats(self) -> dict[str, Any]:
        """获取聚合统计信息。"""
        if not self._records:
            return {"message": "无记录"}

        total_calls = len(self._records)
        success_calls = sum(1 for r in self._records if r.success)
        total_cost = sum(r.cost_usd for r in self._records)
        total_tokens = sum(r.total_tokens for r in self._records)

        latencies = [r.latency_ms for r in self._records]
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        model_stats: dict[str, dict] = {}
        for r in self._records:
            if r.model not in model_stats:
                model_stats[r.model] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                }
            model_stats[r.model]["calls"] += 1
            model_stats[r.model]["total_tokens"] += r.total_tokens
            model_stats[r.model]["cost"] += r.cost_usd

        return {
            "time_range": {
                "start": datetime.fromtimestamp(
                    self._records[0].timestamp
                ).isoformat(),
                "end": datetime.fromtimestamp(
                    self._records[-1].timestamp
                ).isoformat(),
            },
            "summary": {
                "total_calls": total_calls,
                "success_rate": round(success_calls / total_calls, 4),
                "total_cost_usd": round(total_cost, 4),
                "total_tokens": total_tokens,
            },
            "latency_ms": {
                "p50": round(p50, 1),
                "p95": round(p95, 1),
                "p99": round(p99, 1),
            },
            "by_model": model_stats,
        }

    def print_report(self) -> None:
        """打印监控报告到控制台。"""
        stats = self.get_stats()
        if "message" in stats:
            print(stats["message"])
            return

        print("=" * 60)
        print(f"LLM 监控报告")
        print(f"时间范围: {stats['time_range']['start']} ~ {stats['time_range']['end']}")
        print("=" * 60)
        s = stats["summary"]
        print(f"总调用次数:     {s['total_calls']}")
        print(f"成功率:         {s['success_rate'] * 100:.2f}%")
        print(f"总 Token 数:    {s['total_tokens']:,}")
        print(f"总费用(USD):    ${s['total_cost_usd']:.4f}")
        print(f"\n延迟分布:")
        l = stats["latency_ms"]
        print(f"  P50: {l['p50']:.1f}ms | P95: {l['p95']:.1f}ms | P99: {l['p99']:.1f}ms")
        print(f"\n按模型统计:")
        for model, ms in stats["by_model"].items():
            print(f"  {model}: {ms['calls']} 次, {ms['total_tokens']:,} tokens, ${ms['cost']:.4f}")
```

## 最佳实践

1. **尽早接入可观测性**：在项目原型阶段就集成可观测性，避免生产环境发现问题时缺乏历史数据对比。

2. **采样策略**：生产环境 QPS 较高时，采用采样策略（如 10% 采样率）减少存储开销。对错误调用保持全量采样。

3. **结构化日志**：所有 LLM 调用日志使用 JSON 格式，包含 Trace ID、Span ID、模型名称、Token 数等关键字段。

4. **告警规则设置**：设置延迟 P99 超过阈值、错误率突增、Token 消耗异常等告警规则。

5. **成本归因**：为每个请求添加用户 ID 或功能 ID 标签，实现成本的分账和追踪。

6. **Prompt 版本管理**：将 Prompt 模板纳入版本管理，与 Trace 关联，方便追溯每次输出的 Prompt 版本。

## 常见陷阱

1. **过度采集**：不加采样的全量采集会导致存储成本快速增长，同时增加 API 延迟。建议生产环境采样率控制在 1-10%。

2. **忽略用户隐私**：Trace 中可能包含用户敏感信息。确保在发送到观测平台前过滤或脱敏 PII 数据。

3. **观测平台自身延迟**：同步发送追踪数据会增加 API 调用的响应时间。使用异步发送或批处理模式。

4. **指标定义不一致**：团队内部对延迟、成功率等指标的定义不一致会导致监控数据矛盾。建立统一的指标字典。

5. **忽略冷启动问题**：首次 LLM 调用通常包含模型加载时间，与后续调用延迟差异很大。分析时区分冷热请求。

## API Key 依赖

LLM 可观测性的 API Key 依赖相对较少：

- **LangFuse**：需要 `LANGFUSE_PUBLIC_KEY` 和 `LANGFUSE_SECRET_KEY`，自托管时可使用默认值
- **Arize Phoenix**：自托管时不需要 API Key，云版本需要 `PHOENIX_API_KEY`
- **Helicone**：需要 `HELICONE_API_KEY` 作为代理转发
- **OpenTelemetry**：不需要 API Key，通过 OTLP 协议直接上报
- **本地监控**：完全不需要 API Key

## 技术关系

LLM 可观测性连接了开发、部署和运维三个阶段：

- **项目 compose.yaml**：定义了 LangFuse Server 和 PostgreSQL 的服务
- **[RAG 评估](../phase02_production/24_rag_evaluation.md)**：评估结果作为观测数据的一部分，关联 Trace 进行根因分析
- **[Guardrails 安全护栏](../phase02_production/26_guardrails.md)**：安全拦截事件也需要被追踪，形成安全事件的观测视图
- **成本优化**：观测数据驱动成本分析和模型选择决策

## 验收清单

- [ ] 集成了至少一个 LLM 观测平台（LangFuse / Arize / Helicone）
- [ ] 所有 LLM 调用都被自动追踪
- [ ] RAG 检索操作被记录为独立 Span
- [ ] Token 使用量和成本被准确统计
- [ ] 设置了延迟和错误率的告警规则
- [ ] 实现了采样策略（生产环境）
- [ ] Prompt 版本被纳入追踪
- [ ] 用户敏感信息在追踪中被脱敏
- [ ] 建立了成本分账和归因机制
- [ ] 监控报告可自动生成和发送

## 学习资源

- [LangFuse 官方文档](https://langfuse.com/docs)
- [Arize Phoenix 文档](https://docs.arize.com/phoenix)
- [Helicone 文档](https://docs.helicone.ai/)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenInference](https://github.com/Arize-ai/openinference)
