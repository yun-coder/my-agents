# 24. RAG 评估：RAGAS / DeepEval

## 学习目标

- 区分检索质量、回答质量和端到端质量。
- 理解为什么不能只用“回答看起来不错”判断 RAG。
- 会先用确定性指标做本地回归，再接入 RAGAS 或 DeepEval 做模型评估。

## 核心概念

RAG 评估通常拆成三层：

| 层级 | 关注问题 | 常见指标 |
| --- | --- | --- |
| 检索层 | 找到的内容是否相关、是否覆盖答案依据 | Context Precision、Context Recall |
| 生成层 | 答案是否忠于上下文、是否回答问题 | Faithfulness、Answer Relevancy |
| 系统层 | 延迟、成本、失败率是否可接受 | P95 延迟、Token 成本、错误率 |

RAGAS 和 DeepEval 可以调用模型评审更复杂的语义质量。模型评审有价值，但它不是唯一真相：评审模型、提示词和样本都会影响分数。生产系统应保留一组稳定的“黄金问题集”，同时记录确定性指标和模型评审指标。

## 示例说明

`demo.py` 不调用外部模型，演示三个适合持续集成的基础指标：

- `keyword_recall`：期望关键词有多少出现在检索上下文中。
- `answer_coverage`：期望关键词有多少出现在最终答案中。
- `citation_coverage`：答案是否给出可追溯来源。

这些指标不能替代语义评估，但适合先建立最小可复现基线。

## 运行

```powershell
python .\learning\phase02_production\24_rag_evaluation\demo.py
```

## 延伸阅读

- [RAGAS 官方文档](https://docs.ragas.io/)
- [DeepEval 官方仓库](https://github.com/confident-ai/deepeval)
