"""阶段一不访问网络的基础测试。"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import ConfigError, get_openai_settings, load_dev_config  # noqa: E402
from shared.offline_embeddings import bag_of_words, cosine_similarity  # noqa: E402


def load_mvp_core():
    path = PHASE_ROOT / "projects" / "rag_agent_mvp" / "core.py"
    spec = importlib.util.spec_from_file_location("rag_agent_mvp_core", path)
    if not spec or not spec.loader:
        raise RuntimeError("无法加载 RAG Agent MVP core.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ConfigTests(unittest.TestCase):
    def test_load_missing_config(self) -> None:
        with self.assertRaises(ConfigError):
            load_dev_config(Path("missing-dev.json"))

    def test_openai_settings(self) -> None:
        settings = get_openai_settings(
            {
                "openai": {
                    "api_key": "test-key",
                    "base_url": "https://example.com/v1/",
                    "model": "test-model",
                }
            }
        )
        self.assertEqual(settings.base_url, "https://example.com/v1")
        self.assertEqual(settings.embedding_model, "text-embedding-3-small")

    def test_empty_config_does_not_fall_back_to_local_file(self) -> None:
        with self.assertRaises(ConfigError):
            get_openai_settings({})


class EmbeddingTests(unittest.TestCase):
    def test_similar_text_scores_higher(self) -> None:
        query = bag_of_words("Python 列表")
        similar = cosine_similarity(query, bag_of_words("Python 列表 推导式"))
        unrelated = cosine_similarity(query, bag_of_words("FastAPI 服务"))
        self.assertGreater(similar, unrelated)

    def test_chinese_lexical_overlap_is_detected(self) -> None:
        query = bag_of_words("如何检索资料？")
        document = bag_of_words("RAG 会先检索外部资料。")
        self.assertGreater(cosine_similarity(query, document), 0)


class MvpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = load_mvp_core()

    def test_calculator(self) -> None:
        self.assertEqual(self.core.calculate("12 * (3 + 2)"), 60.0)
        self.assertEqual(self.core.calculate("-2 + 5"), 3.0)

    def test_rag_retrieval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "notes.md").write_text("RAG 会先检索外部资料。", encoding="utf-8")
            kb = self.core.KnowledgeBase.from_markdown_directory(Path(temp_dir))
            result = self.core.KnowledgeAgent(kb).ask("RAG 是什么？")
            self.assertIn("RAG", result.answer)
            self.assertEqual(result.sources, ["notes.md#chunk-1"])

    def test_unrelated_question_returns_no_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "notes.md").write_text("RAG 会先检索外部资料。", encoding="utf-8")
            kb = self.core.KnowledgeBase.from_markdown_directory(Path(temp_dir))
            result = self.core.KnowledgeAgent(kb).ask("如何烤蛋糕？")
            self.assertEqual(result.answer, "未找到相关资料，无法基于知识库回答。")
            self.assertEqual(result.sources, [])

    def test_unknown_weather_city_is_not_treated_as_beijing(self) -> None:
        kb = self.core.KnowledgeBase([])
        result = self.core.KnowledgeAgent(kb).ask("查询广州天气")
        self.assertIn("只支持北京和上海", result.answer)


if __name__ == "__main__":
    unittest.main()
