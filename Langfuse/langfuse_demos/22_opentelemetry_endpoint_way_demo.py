"""
Demo: raw OpenTelemetry endpoint.

Use this route when your app, framework, collector, or non-Python language
already emits OpenTelemetry spans. Langfuse accepts OTLP/HTTP at:
    <LANGFUSE_BASE_URL>/api/public/otel
or trace-specific:
    <LANGFUSE_BASE_URL>/api/public/otel/v1/traces

Required for a real raw OTel export:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
"""

from __future__ import annotations

import base64
import os

from _common import configure_langfuse_from_dev_json


def _configure_otel_env() -> None:
    """Configure the standard OTEL env vars expected by many instrumentors."""

    configure_langfuse_from_dev_json()

    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    base_url = os.environ["LANGFUSE_BASE_URL"].rstrip("/")

    auth = base64.b64encode(f"{public_key}:{secret_key}".encode("utf-8")).decode("ascii")

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{base_url}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{base_url}/api/public/otel/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = (
        f"Authorization=Basic {auth},x-langfuse-ingestion-version=4"
    )
    os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = os.environ["OTEL_EXPORTER_OTLP_HEADERS"]
    os.environ["OTEL_SERVICE_NAME"] = "langfuse-raw-otel-demo"


def main() -> None:
    _configure_otel_env()

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        print("OpenTelemetry packages are not installed.")
        print("Install the packages listed in this file docstring to run the raw OTel demo.")
        print(f"Original import error: {exc}")
        return

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
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("langfuse.raw_otel.demo")
    with tracer.start_as_current_span("raw-otel-generation-demo") as span:
        # Langfuse maps common GenAI semantic attributes into its data model.
        # Also propagate trace-level attributes to spans for filtering.
        span.set_attribute("gen_ai.system", "openai")
        span.set_attribute("gen_ai.request.model", "mock-gpt-4o-mini")
        span.set_attribute("gen_ai.prompt.0.role", "user")
        span.set_attribute("gen_ai.prompt.0.content", "What does Langfuse observe?")
        span.set_attribute("gen_ai.completion.0.role", "assistant")
        span.set_attribute("gen_ai.completion.0.content", "Langfuse observes LLM app traces.")
        span.set_attribute("langfuse.user.id", "user_raw_otel_001")
        span.set_attribute("langfuse.session.id", "session_raw_otel_001")
        span.set_attribute("langfuse.trace.tags", "demo,raw-otel")
        span.set_attribute("langfuse.trace.metadata.source", "22_opentelemetry_endpoint_way_demo.py")

    provider.force_flush()
    provider.shutdown()
    print("Sent raw OpenTelemetry demo span to Langfuse.")


if __name__ == "__main__":
    main()
