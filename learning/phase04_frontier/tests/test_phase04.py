"""阶段四核心行为的离线回归测试。"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


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


computer_use = load_module("phase04_computer_use", "39_computer_use/demo.py")
multimodal = load_module("phase04_multimodal", "40_multimodal_agent/demo.py")
fine_tuning = load_module("phase04_fine_tuning", "41_fine_tuning/demo.py")
validation = load_module("phase04_validation", "projects/frontier_validation/core.py")


class Phase04Tests(unittest.TestCase):
    def test_gui_submit_needs_approval(self) -> None:
        action = computer_use.GuiAction("submit", "https://example.com/publish", "发布")
        decision = computer_use.review(action)
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.needs_approval)

    def test_gui_unknown_domain_is_rejected(self) -> None:
        decision = computer_use.review(computer_use.GuiAction("read", "https://unsafe.invalid", "页面"))
        self.assertFalse(decision.allowed)

    def test_multimodal_payload_has_image_item(self) -> None:
        question = multimodal.MultimodalQuestion("描述图片", "https://example.com/image.png")
        payload = multimodal.build_responses_payload("vision-model", question)
        content = payload["input"][0]["content"]
        self.assertEqual(content[1]["type"], "input_image")

    def test_sft_examples_are_valid(self) -> None:
        path = PHASE_DIR / "41_fine_tuning/data/sft_examples.jsonl"
        self.assertEqual(fine_tuning.validate_jsonl(path), [{"line": 1, "issues": []}, {"line": 2, "issues": []}])

    def test_high_risk_capability_stays_explicit(self) -> None:
        case = validation.CapabilityCase("computer-use", "high", 0.95, 0.9, ("evidence",))
        decision = validation.decide(case)
        self.assertEqual(decision.status, "candidate")
        self.assertIn("安全评审", decision.reason)


if __name__ == "__main__":
    unittest.main()
