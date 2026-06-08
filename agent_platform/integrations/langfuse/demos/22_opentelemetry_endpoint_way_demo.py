"""
演示 22: 原生 OpenTelemetry 端点方式。

当你的应用、框架、采集器或非 Python 语言已经发出 OpenTelemetry span
时使用此方式。Langfuse 通过 OTLP/HTTP 协议接收 span：
    <LANGFUSE_BASE_URL>/api/public/otel
或 trace 专用端点：
    <LANGFUSE_BASE_URL>/api/public/otel/v1/traces

实际原生 OTel 导出所需依赖：
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
"""

from __future__ import annotations

import base64
import os

from _common import configure_langfuse_from_dev_json


def _configure_otel_env() -> None:
    """配置各种 OpenTelemetry instrumentor 期望的标准 OTEL 环境变量。"""

    configure_langfuse_from_dev_json()

    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    base_url = os.environ["LANGFUSE_BASE_URL"].rstrip("/")

    # Langfuse OTLP 端点使用 Basic Auth，凭据格式为 public_key:secret_key
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode("utf-8")).decode("ascii")

    # 设置 OpenTelemetry 标准环境变量
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{base_url}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{base_url}/api/public/otel/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = (
        f"Authorization=Basic {auth},x-langfuse-ingestion-version=4"
    )
    os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = os.environ["OTEL_EXPORTER_OTLP_HEADERS"]
    os.environ["OTEL_SERVICE_NAME"] = "langfuse-raw-otel-demo"


def main() -> None:
    _configure_otel_env()

    # 尝试导入 OpenTelemetry SDK 包
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        print("OpenTelemetry 包未安装。")
        print("安装本文档字符串中列出的包以运行原生 OTel 演示。")
        print(f"原始导入错误: {exc}")
        return

    # 创建 TracerProvider 并配置 OTLP 导出器
    provider = TracerProvider(resource=Resource.create({"service.name": "langfuse-raw-otel-demo"}))
    exporter = OTLPSpanExporter(
        endpoint=os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"],
        headers={
            key: value
            for key, value in (
                item.split("=", 1) for item in os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"].split(",")
            )
        },
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))  # 批量发送 span
    trace.set_tracer_provider(provider)

    # 创建 tracer 并开始一个 span
    tracer = trace.get_tracer("langfuse.raw_otel.demo")
    with tracer.start_as_current_span("raw-otel-generation-demo") as span:
        # Langfuse 将常见的 GenAI 语义属性映射到其数据模型中。
        # 同时将 trace 级别的属性传播到 span 上，以便筛选。
        span.set_attribute("gen_ai.system", "openai")
        span.set_attribute("gen_ai.request.model", "mock-gpt-4o-mini")
        span.set_attribute("gen_ai.prompt.0.role", "user")
        span.set_attribute("gen_ai.prompt.0.content", "Langfuse 观测什么？")
        span.set_attribute("gen_ai.completion.0.role", "assistant")
        span.set_attribute("gen_ai.completion.0.content", "Langfuse 观测 LLM 应用追踪。")
        # Langfuse 专用属性：用户、会话、标签、元数据
        span.set_attribute("langfuse.user.id", "user_raw_otel_001")
        span.set_attribute("langfuse.session.id", "session_raw_otel_001")
        span.set_attribute("langfuse.trace.tags", "demo,raw-otel")
        span.set_attribute("langfuse.trace.metadata.source", "22_opentelemetry_endpoint_way_demo.py")

    # 强制刷新并关闭 provider
    provider.force_flush()
    provider.shutdown()
    print("已发送原生 OpenTelemetry 演示 span 到 Langfuse。")


if __name__ == "__main__":
    main()
