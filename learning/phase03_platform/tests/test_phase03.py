"""阶段三核心行为的离线回归测试。"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

from pydantic import ValidationError


PHASE_DIR = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    path = PHASE_DIR / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pydantic_demo = load_module("phase03_pydantic", "31_pydantic_ai/demo.py")
models = load_module("phase03_models", "32_open_source_models/demo.py")
queue = load_module("phase03_queue", "34_message_queue/demo.py")
multi_tenancy = load_module("phase03_multi_tenancy", "36_multi_tenancy/demo.py")
cost = load_module("phase03_cost", "38_cost_rate_limit/demo.py")
platform = load_module("phase03_platform_core", "projects/multi_tenant_platform/core.py")


class Phase03Tests(unittest.TestCase):
    def test_pydantic_rejects_invalid_priority(self) -> None:
        with self.assertRaises(ValidationError):
            pydantic_demo.TicketTriage(category="general", priority=8, summary="x", needs_human=False)

    def test_model_router_requires_tool_support(self) -> None:
        endpoints = (
            models.ModelEndpoint("plain", "ollama", "http://local", 64000, False),
            models.ModelEndpoint("tools", "vllm", "http://team", 32000, True),
        )
        self.assertEqual(models.choose_endpoint(endpoints, needs_tools=True).name, "tools")

    def test_queue_skips_duplicate(self) -> None:
        tasks = queue.deque((queue.Task("same", "one"), queue.Task("same", "two")))
        events = queue.process_queue(tasks)
        self.assertEqual(events[-1]["status"], "duplicate-skipped")

    def test_tenant_repository_isolated(self) -> None:
        repository = multi_tenancy.TenantDocuments()
        repository.add(multi_tenancy.Document("a", "tenant-a", "A"))
        repository.add(multi_tenancy.Document("b", "tenant-b", "B"))
        self.assertEqual([item.document_id for item in repository.list_for_tenant("tenant-a")], ["a"])

    def test_limiter_expires_old_events(self) -> None:
        limiter = cost.SlidingWindowLimiter(1, 60)
        self.assertTrue(limiter.allow("tenant-a", 0))
        self.assertFalse(limiter.allow("tenant-a", 10))
        self.assertTrue(limiter.allow("tenant-a", 61))

    def test_platform_checks_role_and_tenant(self) -> None:
        service = platform.TenantPlatform()
        service.set_budget("tenant-a", 1.0)
        service.add_document(platform.Document("a", "tenant-a", "A"))
        service.add_document(platform.Document("b", "tenant-b", "B"))
        context = platform.UserContext("user", "tenant-a", "viewer")
        self.assertEqual([item.document_id for item in service.list_documents(context)], ["a"])
        self.assertFalse(service.authorize(context, "draft", 0.1, 0).allowed)


if __name__ == "__main__":
    unittest.main()
