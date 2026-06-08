# 24 RAG 评估体系

## 概念概述

RAG（检索增强生成）评估是衡量 RAG 系统整体质量的系统性方法论。与传统 NLP 评估不同，RAG 评估需要同时考量检索模块的相关性和生成模块的准确性，以及二者的协同效果。RAG 系统由检索器（Retriever）和生成器（Generator）组成，评估必须覆盖检索质量（是否召回相关文档）和生成质量（是否正确利用检索结果生成答案）。

生产环境中的 RAG 评估通常分为离线评估和在线评估两大类。离线评估使用标注好的基准数据集（Ground Truth），在开发阶段快速迭代优化；在线评估则通过用户反馈、A/B 测试等手段持续监控生产环境中的表现。

RAGAS（RAG Assessment）是目前最流行的开源 RAG 评估框架，提供了一系列无需人工标注的自动评估指标。DeepEval 则是另一个功能更全面的评估框架，支持 RAGAS 指标并扩展了更多评估维度。LLM-as-Judge 模式使用大语言模型本身作为评估者，通过精心设计的评估提示词来评判答案质量。

## 核心指标详解

### RAGAS 四大指标

**Faithfulness（忠实度）**：衡量生成答案是否忠实于检索到的上下文，即答案中的每个陈述是否都能从上下文中找到依据。计算方式是将答案拆分为多个声明（Claim），逐一判断是否被上下文支持。

**Answer Relevancy（答案相关性）**：衡量生成的答案与原始问题的相关程度，通过让 LLM 从答案反向生成问题，再计算生成的问题与原始问题的相似度。

**Context Precision（上下文精确度）**：衡量检索结果中相关文档的排名质量，相关文档越靠前得分越高，体现了检索排序的效果。

**Context Recall（上下文召回率）**：衡量检索结果是否覆盖了回答所需的所有信息，即是否需要的信息都被检索到了。

### 离线评估指标体系

除 RAGAS 指标外，实际生产中还需要关注以下指标：

| 指标类别 | 具体指标 | 说明 |
|---------|---------|------|
| 检索质量 | Hit Rate | 前 k 个结果中是否包含相关文档 |
| 检索质量 | MRR | 第一个相关文档的平均倒数排名 |
| 检索质量 | NDCG | 考虑排序位置的归一化折损累计增益 |
| 生成质量 | BLEU | 生成文本与参考答案的 n-gram 重合度 |
| 生成质量 | ROUGE-L | 基于最长公共子序列的召回率 |
| 生成质量 | BERTScore | 基于 BERT 嵌入的语义相似度 |
| 端到端 | 正确率 | 人工标注的答案是否正确 |
| 端到端 | 幻觉率 | 答案中包含幻觉信息的比例 |

## 实战指南

### 使用 RAGAS 进行离线评估

```python
"""RAGAS 框架评估 RAG 系统，需要设置 OPENAI_API_KEY。"""
import os
from typing import Any

from datasets import Dataset

# RAGAS 需要 LLM API Key 来计算指标
assert os.getenv("OPENAI_API_KEY"), "请设置 OPENAI_API_KEY 环境变量"

# 构建测试数据集
test_data = {
    "question": [
        "Python 中的 GIL 是什么？",
        "什么是 Docker？",
    ],
    "answer": [
        "GIL 是全局解释器锁，限制同一时刻只有一个线程执行 Python 字节码。",
        "Docker 是一种容器化平台，用于打包和运行应用。",
    ],
    "contexts": [
        [
            "GIL（全局解释器锁）是 CPython 解释器中的一种机制，"
            "确保同一时刻只有一个线程执行 Python 字节码。这对于内存管理是必要的，"
            "但会限制多线程 CPU 密集型任务的性能。",
        ],
        [
            "Docker 是一个开源的容器化平台，允许开发者将应用及其依赖打包到容器中。"
            "容器是轻量级的、可移植的，并且可以在任何安装了 Docker 的环境中运行。",
        ],
    ],
    "ground_truth": [
        "GIL 是 CPython 的全局解释器锁，用于线程安全，但限制了多线程并行执行。",
        "Docker 是容器化平台，通过容器实现应用的打包和部署。",
    ],
}

dataset = Dataset.from_dict(test_data)

# 方法一：使用 ragas 框架进行评估
def evaluate_with_ragas(dataset: Dataset) -> dict[str, Any]:
    """使用 RAGAS 框架计算评估指标。"""
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )

    result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
    )
    return dict(result)

# 方法二：逐指标手动计算（演示原理）
def manual_faithfulness_score(
    question: str, answer: str, contexts: list[str]
) -> float:
    """手动计算忠实度：将答案拆分成声明，逐一验证。"""
    from ragas.dataset_schema import SingleSample

    sample = SingleSample(
        question=question,
        contexts=contexts,
        ground_truth="",
    )

    from ragas.metrics._faithfulness import Faithfulness

    scorer = Faithfulness()
    score = scorer.score(sample)
    return score


if __name__ == "__main__":
    result = evaluate_with_ragas(dataset)
    for metric, value in result.items():
        print(f"{metric}: {value:.4f}")

    # 输出示例：
    # faithfulness: 0.9500
    # answer_relevancy: 0.9200
    # context_precision: 0.8800
    # context_recall: 1.0000
```

### 使用 DeepEval 框架评估

```python
"""DeepEval 框架评估，提供更丰富的 RAG 评估能力。"""
import os
from typing import Any

import pytest


@pytest.fixture
def api_key() -> str:
    """Fixture 确保 API Key 已配置。"""
    key = os.getenv("OPENAI_API_KEY", "")
    assert key, "DeepEval 评估需要设置 OPENAI_API_KEY"
    return key


def test_rag_pipeline(api_key: str) -> None:
    """使用 DeepEval 测试 RAG 管道的多个指标。"""
    from deepeval import assert_test
    from deepeval.metrics.answer_relevancy import AnswerRelevancyMetric
    from deepeval.metrics.faithfulness import FaithfulnessMetric
    from deepeval.metrics.contextual_precision import ContextualPrecisionMetric
    from deepeval.metrics.contextual_recall import ContextualRecallMetric
    from deepeval.metrics.hallucination import HallucinationMetric
    from deepeval.test_case import LLMTestCase

    test_case = LLMTestCase(
        input="Python 的装饰器是什么？",
        actual_output="装饰器是一种高阶函数，可以在不修改原函数代码的情况下增强其功能。",
        retrieval_context=[
            "装饰器是 Python 中的一种设计模式，允许在不修改原函数代码的情况下，"
            "向函数或类添加额外功能。装饰器本质上是一个接受函数作为参数的可调用对象。",
        ],
        expected_output="装饰器是用于增强函数功能的高阶函数。",
    )

    metrics_to_test = [
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
        ContextualPrecisionMetric(threshold=0.7),
        ContextualRecallMetric(threshold=0.7),
        HallucinationMetric(threshold=0.5),
    ]

    for metric in metrics_to_test:
        metric.measure(test_case)
        print(f"{metric.__class__.__name__}: {metric.score:.4f}")
        assert metric.is_successful(), f"{metric.__class__.__name__} 未通过阈值"


def test_batch_evaluation() -> None:
    """批量评估 RAG 系统的整体表现。"""
    from deepeval import evaluate
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase

    test_cases = [
        LLMTestCase(
            input="什么是 RESTful API？",
            actual_output="RESTful API 是基于 REST 架构风格的 Web API 设计规范。",
            retrieval_context=[
                "REST（Representational State Transfer）是一种软件架构风格，"
                "用于设计网络应用程序。RESTful API 遵循 REST 原则，使用 HTTP 方法操作资源。",
            ],
        ),
        LLMTestCase(
            input="Git 的 merge 和 rebase 区别？",
            actual_output="merge 保留分支历史，rebase 重写提交历史使分支呈线性。",
            retrieval_context=[
                "git merge 会创建一个新的合并提交，保留所有分支的历史记录。"
                "git rebase 则将当前分支的提交移到目标分支的顶部，产生线性历史。",
            ],
        ),
    ]

    metrics = [
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
    ]

    results = evaluate(test_cases, metrics)
    for test_result in results:
        print(f"Test: {test_result.test_case.input}")
        for metric_result in test_result.metrics:
            print(f"  {metric_result.name}: {metric_result.score:.4f}")
```

### LLM-as-Judge 评估

```python
"""使用 LLM-as-Judge 模式评估 RAG 答案质量。"""
from typing import Any

import openai


class LLMJudge:
    """使用 LLM 作为裁判评估 RAG 输出质量。"""

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model
        self.client = openai.OpenAI()

    def evaluate_faithfulness(
        self, question: str, answer: str, context: str
    ) -> dict[str, Any]:
        """评估答案是否忠实于上下文。"""
        prompt = f"""作为一个公正的评估者，判断以下答案是否忠实于给定的上下文。

上下文：
{context}

问题：{question}
答案：{answer}

请按以下维度评分（1-5分）：
1. 事实正确性：答案中的事实是否都有上下文支持？
2. 无幻觉：答案是否没有添加上下文之外的信息？
3. 完整性：答案是否使用了上下文中的关键信息？

同时给出总体忠实度评分（1-5分）和简要解释。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个严格的 RAG 答案评估者，"
                    "请公正地评估答案质量。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        import json

        return json.loads(response.choices[0].message.content or "{}")

    def evaluate_relevancy(self, question: str, answer: str) -> float:
        """评估答案与问题的相关性。"""
        prompt = f"""评估以下答案与问题的相关程度。

问题：{question}
答案：{answer}

请输出一个 JSON 包含：
- score: 1-5 的相关性评分
- reason: 评分的理由"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        import json

        result = json.loads(response.choices[0].message.content or "{}")
        return result.get("score", 3) / 5.0  # 归一化到 0-1

    def evaluate_context_utilization(
        self, answer: str, context: str
    ) -> dict[str, Any]:
        """评估答案对上下文的利用程度。"""
        prompt = f"""分析以下答案对给定上下文的利用情况。

上下文：
{context}

答案：
{answer}

请评估：
1. utilization_rate: 答案使用了上下文信息的比例（0-1）
2. key_info_coverage: 答案覆盖了多少上下文中的关键信息点
3. missing_info: 上下文中有但答案遗漏的重要内容
4. overall_score: 总体利用评分（1-5）

输出 JSON 格式。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        import json

        return json.loads(response.choices[0].message.content or "{}")


if __name__ == "__main__":
    judge = LLMJudge()
    result = judge.evaluate_faithfulness(
        question="什么是 Python 装饰器？",
        answer="装饰器是高阶函数，用于增强其他函数的功能。",
        context="装饰器是 Python 中一种强大的工具，允许程序员修改函数或类的行为。"
        "装饰器本身是一个可调用对象，接受一个函数作为参数并返回另一个函数。",
    )
    print(result)
```

### 离线评估流水线

```python
"""完整的 RAG 离线评估流水线。"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EvaluationResult:
    """单次评估的结果。"""

    timestamp: str = ""
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    latency_ms: float = 0.0
    total_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class RAGEvaluator:
    """RAG 离线评估器，支持多种评估策略。"""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.results: list[EvaluationResult] = []

    def load_test_set(self, path: str) -> list[dict[str, Any]]:
        """加载测试数据集。"""
        path_obj = Path(path)
        if path_obj.suffix == ".json":
            with path_obj.open("r", encoding="utf-8") as f:
                return json.load(f)
        elif path_obj.suffix == ".jsonl":
            data = []
            with path_obj.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            return data
        else:
            raise ValueError(f"不支持的文件格式: {path_obj.suffix}")

    def evaluate_retrieval_only(
        self,
        questions: list[str],
        retrieved_docs: list[list[str]],
        relevant_docs: list[list[str]],
    ) -> dict[str, float]:
        """仅评估检索模块的质量（无需 API Key）。"""
        total_hit_rate = 0.0
        total_mrr = 0.0

        for ret_docs, rel_docs in zip(retrieved_docs, relevant_docs):
            rel_set = set(rel_docs)
            hits = sum(1 for d in ret_docs if d in rel_set)
            total_hit_rate += hits / len(ret_docs) if ret_docs else 0
            for rank, doc in enumerate(ret_docs, 1):
                if doc in rel_set:
                    total_mrr += 1.0 / rank
                    break

        n = len(questions)
        return {
            "hit_rate": total_hit_rate / n if n else 0,
            "mrr": total_mrr / n if n else 0,
        }

    def run_pipeline(
        self, test_set_path: str, rag_pipeline: Any
    ) -> list[EvaluationResult]:
        """运行完整的评估流水线。"""
        import time

        test_data = self.load_test_set(test_set_path)
        results: list[EvaluationResult] = []

        for item in test_data:
            question = item.get("question", "")
            ground_truth = item.get("ground_truth", "")

            start = time.perf_counter()
            response = rag_pipeline.query(question)
            elapsed = (time.perf_counter() - start) * 1000

            result = EvaluationResult(
                timestamp=datetime.now().isoformat(),
                latency_ms=elapsed,
                total_tokens=response.get("total_tokens", 0),
                metadata={
                    "question": question,
                    "ground_truth": ground_truth,
                    "model_used": response.get("model", ""),
                },
            )
            results.append(result)

        self.results.extend(results)
        return results

    def generate_report(self, output_path: str) -> None:
        """生成评估报告。"""
        if not self.results:
            print("没有评估结果可供报告。")
            return

        avg_faithfulness = sum(r.faithfulness for r in self.results) / len(self.results)
        avg_relevancy = sum(r.answer_relevancy for r in self.results) / len(self.results)
        avg_precision = sum(r.context_precision for r in self.results) / len(self.results)
        avg_recall = sum(r.context_recall for r in self.results) / len(self.results)
        avg_latency = sum(r.latency_ms for r in self.results) / len(self.results)

        report = {
            "total_samples": len(self.results),
            "average_scores": {
                "faithfulness": round(avg_faithfulness, 4),
                "answer_relevancy": round(avg_relevancy, 4),
                "context_precision": round(avg_precision, 4),
                "context_recall": round(avg_recall, 4),
            },
            "average_latency_ms": round(avg_latency, 2),
            "generated_at": datetime.now().isoformat(),
        }

        path_obj = Path(output_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with path_obj.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"评估报告已保存: {output_path}")
        for name, score in report["average_scores"].items():
            print(f"  {name}: {score:.4f}")
```

## 最佳实践

1. **构建高质量的基准数据集**：每个测试用例应包括问题、标准答案、相关上下文。使用人工标注确保数据质量，通常需要 100-200 个测试用例作为最小有效集。

2. **多维度评估**：不要只看单一指标。Faithfulness 反映幻觉程度，Answer Relevancy 反映回答针对性，两者结合才能全面评估生成质量。

3. **LLM-as-Judge 校准**：使用 LLM 作为评估者时，需要定期校准，确保评估的一致性和公正性。可以引入多个 LLM 评估并取平均值。

4. **离线与在线评估结合**：离线评估用于快速迭代开发，在线评估（用户反馈、A/B 测试）用于发现真实场景中的问题，两者缺一不可。

5. **版本化管理评估结果**：每次修改 RAG 系统后，重新运行评估并对比结果。将评估结果纳入 CI/CD 流水线，防止回归。

6. **关注边缘案例**：特别关注模糊问题、多义性问题、需要多步推理的问题，这些场景最容易暴露 RAG 系统的缺陷。

## 常见陷阱

1. **评估数据泄露**：测试集中的文档被用于检索库中，导致检索指标虚高。构建测试集时确保测试文档与检索库完全隔离。

2. **LLM-as-Judge 偏见**：评估 LLM 倾向于偏好自己的输出或风格相似的答案。使用不同的评估 LLM 或引入人工抽检来校正。

3. **指标间的不一致性**：Faithfulness 高但 Relevancy 低的情况很常见（答得准但答非所问）。需要综合解读多个指标。

4. **忽略延迟成本**：评估只关注质量指标而忽略推理延迟和 Token 消耗。生产环境中需要在质量、延迟、成本之间做权衡。

5. **测试集分布偏差**：测试集不能代表真实用户问题的分布。从生产日志中采样构建测试集可以缓解此问题。

## API Key 依赖

RAG 评估的 API Key 依赖集中在以下场景：

- **RAGAS 框架**：需要 `OPENAI_API_KEY` 来计算 Faithfulness、Answer Relevancy 等指标
- **DeepEval 框架**：需要 LLM API Key 进行 LLM-as-Judge 评估
- **LLM-as-Judge**：直接调用 OpenAI/Anthropic 等 API
- **检索评估**：Hit Rate、MRR 等检索指标不需要 API Key
- **建议配置**：评估专用的 API Key 并设置用量限制，避免生产环境误用

## 技术关系

RAG 评估在整个 RAG 生态中处于质量保障的核心位置：

- **[LLM 可观测性](../phase02_production/25_observability.md)**：评估结果需要与线上监控数据关联，发现离线评估无法覆盖的场景
- **[Guardrails 安全护栏](../phase02_production/26_guardrails.md)**：评估时需要确保输出不违反安全规则，两者协同保障输出质量
- **RAG 核心**：评估指标体系与 RAG 管道的检索器、生成器、重排序器直接对应

## 验收清单

- [ ] 构建了至少 100 个测试用例的评估数据集
- [ ] 能够运行 RAGAS 四项核心指标评估
- [ ] 集成了 DeepEval 框架作为备选评估方案
- [ ] 实现了 LLM-as-Judge 评估机制
- [ ] 建立了离线评估流水线
- [ ] 实现了评估结果版本化管理
- [ ] 建立了在线评估（用户反馈）机制
- [ ] 确认 API Key 配置正确并设置用量限制
- [ ] 制定了评估阈值标准（如 Faithfulness > 0.8）
- [ ] 将评估纳入 CI/CD 流水线

## 学习资源

- [RAGAS 官方文档](https://docs.ragas.io/)
- [DeepEval 框架](https://docs.confident-ai.com/)
- [LangFuse RAG Evaluation](https://langfuse.com/docs/scores/)
- [Evaluating RAG Systems Guide](https://www.rungalileo.io/blog/evaluating-rag-systems)
- [LLM-as-Judge 论文](https://arxiv.org/abs/2306.05685)
