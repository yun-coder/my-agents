# 37 DSPy — 编程式提示词优化框架

## 1. 概念概述

### 1.1 什么是 DSPy

DSPy（Declarative Self-improving Python）是斯坦福大学 NLP 团队开发的提示词编程框架。它的核心理念是：**用代码而非手动编写来优化提示词**。

传统开发模式中，工程师花费大量时间手动调整提示词（Prompt Engineering），这不仅效率低下，而且结果不可复现。DSPy 将提示词优化系统化，通过声明式编程和自动化编译器实现：

- 从"手动调提示词"转变为"编程式自动化化"
- 将 LLM 调用抽象为有类型的 Signatures
- 使用编译器自动选择和优化提示词策略
- 通过评估驱动的方式持续改进

### 1.2 DSPy vs 手动提示词工程

| 维度 | 手动提示词工程 | DSPy |
|------|-------------|------|
| 方法 | 反复试验、凭经验调整 | 声明式编程、自动优化 |
| 可复现性 | 低（提示词版本混乱） | 高（代码版本化管理） |
| 优化效率 | 数小时到数天 | 几分钟到几小时 |
| 鲁棒性 | 提示词修改易引入新问题 | 自动适配不同模型 |
| 学习曲线 | 低门槛 | 需要理解编程范式 |
| 最适合 | 简单、一次性任务 | 复杂、生产级任务 |

### 1.3 适用场景

- **需要高精度的分类/抽取任务**：手动提示词难以达到理想精度
- **多模型适配**：同一任务需要在不同 LLM 上达到相似效果
- **频繁迭代**：需求变化迅速，每次重新优化提示词
- **管道式任务**：多个 LLM 调用串联的复杂管道
- **知识蒸馏**：从强模型（GPT-4）向弱模型（开源模型）迁移能力

### 1.4 核心概念

DSPy 的三个核心抽象：
1. **Signature（签名）**：有类型的输入输出声明
2. **Module（模块）**：可组合的 LLM 任务单元
3. **Optimizer（优化器）**：自动优化提示词的编译器

## 2. 核心原理

### 2.1 Signature 声明式编程

Signature 是 DSPy 最基础的抽象，它声明了 LLM 任务的输入和输出及其类型：

```python
class SentimentAnalysis(dspy.Signature):
    """分析文本的情感倾向。"""
    text: str = dspy.InputField(desc="待分析的文本")
    sentiment: str = dspy.OutputField(desc="情感分类: 正面/负面/中性")
    confidence: float = dspy.OutputField(desc="置信度分数 0-1")
```

Signature 的类型提示告诉优化器：
- 输入是什么（InputField）
- 期望输出什么（OutputField）
- 每个字段的描述（优化器的优化信号）

### 2.2 Module 组合模式

Module 是可组合的 LLM 调用单元，类似于 PyTorch 的 nn.Module：

```python
# 基础模块
class BasicQA(dspy.Module):
    def __init__(self):
        self.answer = dspy.ChainOfThought("question -> answer")
    
    def forward(self, question):
        return self.answer(question=question)

# 模块可以嵌套组合
class AdvancedQA(dspy.Module):
    def __init__(self):
        self.retrieve = dspy.Retrieve(k=3)           # 检索模块
        self.generate = dspy.ChainOfThought("context, question -> answer")  # 生成模块
    
    def forward(self, question):
        context = self.retrieve(question)             # 先检索
        return self.generate(context=context, question=question)
```

### 2.3 Optimizer 编译优化

Optimizer 是 DSPy 的核心创新，它通过编译过程自动优化提示词：

**BootstrapFewShot**：从少量示例中自动构建少样本学习示例
1. 使用 Teacher 模型（通常是强模型）生成示例
2. 从生成的示例中筛选最佳示例
3. 将筛选的示例添加到 Student 模型的提示词中

**MIPROv2**：更先进的优化器，使用贝叶斯搜索
1. 生成候选指令变体
2. 探索少样本示例组合
3. 贝叶斯优化搜索最佳配置
4. 评估并选择最优方案

### 2.4 评估驱动优化

DSPy 的优化过程是基于评估的循环：

```
定义任务 -> 准备数据 -> 声明优化器 -> 编译 ->
评估结果 -> 满足要求? -> 是: 部署 | 否: 调整后重新编译
```

## 3. 实战指南

### 3.1 安装与配置

```bash
# 安装 DSPy
pip install dspy-ai

# 安装可选的 LLM 客户端
pip install openai anthropic
```

```python
# 基本配置
import dspy

# 配置 OpenAI
lm = dspy.LM("openai/gpt-4o-mini", api_key="sk-...")
dspy.configure(lm=lm)

# 或配置 Anthropic
# lm = dspy.LM("anthropic/claude-sonnet-4-20250514", api_key="sk-ant-...")
# dspy.configure(lm=lm)

# 或配置本地模型（通过 Ollama）
# lm = dspy.LM("openai/qwen2.5:7b", api_base="http://localhost:11434/v1")
# dspy.configure(lm=lm)
```

### 3.2 定义 Signature

```python
import dspy
from typing import Literal

# 基础分类签名
class EmailClassifier(dspy.Signature):
    """将电子邮件分类到指定类别。"""
    email_content: str = dspy.InputField(
        desc="邮件正文内容，包含发件人、主题和正文"
    )
    category: Literal["inquiry", "complaint", "feedback", "spam", "other"] = dspy.OutputField(
        desc="邮件类别"
    )
    priority: Literal["high", "medium", "low"] = dspy.OutputField(
        desc="处理优先级"
    )
    reasoning: str = dspy.OutputField(
        desc="分类原因的简要解释"
    )

# 复杂抽取签名
class InvoiceExtractor(dspy.Signature):
    """从发票文本中提取关键信息。"""
    invoice_text: str = dspy.InputField(desc="发票的原始文本内容")
    invoice_number: str = dspy.OutputField(desc="发票号码")
    date: str = dspy.OutputField(desc="发票日期 (YYYY-MM-DD)")
    total_amount: float = dspy.OutputField(desc="发票总金额")
    vendor_name: str = dspy.OutputField(desc="供应商名称")
    line_items: list[str] = dspy.OutputField(desc="商品/服务明细列表")

# 问答签名
class QASignature(dspy.Signature):
    """基于上下文回答问题。"""
    context: str = dspy.InputField(desc="相关的背景信息")
    question: str = dspy.InputField(desc="用户的问题")
    answer: str = dspy.OutputField(desc="基于上下文的准确回答")
    confidence: float = dspy.OutputField(desc="回答的置信度 0-1")
```

### 3.3 定义 Module

```python
import dspy

# 基础 Module：使用 ChainOfThought
class ClassifyEmail(dspy.Module):
    """邮件分类 Module。"""

    def __init__(self):
        super().__init__()
        self.classifier = dspy.ChainOfThought(EmailClassifier)

    def forward(self, email_content: str):
        result = self.classifier(email_content=email_content)
        return dspy.Prediction(
            category=result.category,
            priority=result.priority,
            reasoning=result.reasoning,
        )

# 复杂 Module：多步骤推理
class CustomerSupportPipeline(dspy.Module):
    """客户支持管道：分类 -> 意图识别 -> 生成回复。"""

    def __init__(self):
        super().__init__()
        self.classify = dspy.ChainOfThought(EmailClassifier)
        self.intent = dspy.ChainOfThought("category, content -> intent, required_info")
        self.respond = dspy.ChainOfThought("intent, context, info -> response")

    def forward(self, email_content: str):
        # 第一步：分类
        classification = self.classify(email_content=email_content)

        # 第二步：识别意图
        intent_result = self.intent(
            category=classification.category,
            content=email_content,
        )

        # 第三步：生成回复
        response = self.respond(
            intent=intent_result.intent,
            context=email_content[:500],
            info=intent_result.required_info,
        )

        return dspy.Prediction(
            category=classification.category,
            priority=classification.priority,
            response=response.response,
        )

# 检索增强生成 (RAG) Module
class RAGModule(dspy.Module):
    """检索增强生成 Module。"""

    def __init__(self, num_docs: int = 3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_docs)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question: str):
        context = self.retrieve(question)
        result = self.generate(context=context, question=question)
        return dspy.Prediction(answer=result.answer, context=context)
```

### 3.4 准备训练数据

```python
# datasets.py — 训练和评估数据集
import dspy

# 邮件分类训练数据
email_trainset = [
    dspy.Example(
        email_content="""发件人: customer@example.com
主题: 订单延迟
正文: 我的订单 #12345 已经延迟三天了，请尽快处理！""",
        category="complaint",
        priority="high",
        reasoning="用户表达了对订单延迟的不满，需要紧急处理",
    ).with_inputs("email_content"),
    dspy.Example(
        email_content="""发件人: vendor@ads.com
主题: 限时优惠
正文: 恭喜您获得我们的独家优惠！立即购买享受 50% 折扣。""",
        category="spam",
        priority="low",
        reasoning="典型的促销邮件，与业务无关",
    ).with_inputs("email_content"),
    dspy.Example(
        email_content="""发件人: partner@company.com
主题: 合作咨询
正文: 我们公司对贵司的 Agent 平台非常感兴趣，希望能安排一次会议。""",
        category="inquiry",
        priority="medium",
        reasoning="商业合作伙伴咨询，需要跟进但非紧急",
    ).with_inputs("email_content"),
]

# 问答训练数据
qa_trainset = [
    dspy.Example(
        context="DSPy 是斯坦福大学开发的提示词编程框架。",
        question="DSPy 是由哪所大学开发的？",
        answer="斯坦福大学",
        confidence=0.95,
    ).with_inputs("context", "question"),
    dspy.Example(
        context="Transformer 架构由 Google 在 2017 年提出。",
        question="Transformer 架构是哪一年提出的？",
        answer="2017 年",
        confidence=0.98,
    ).with_inputs("context", "question"),
]

# 验证集
email_devset = [
    dspy.Example(
        email_content="""发件人: user@test.com
主题: 功能建议
正文: 希望能增加批量导出功能，这会大大提高我们的工作效率。""",
        category="feedback",
        priority="medium",
        reasoning="用户提出了产品改进建议",
    ).with_inputs("email_content"),
]
```

### 3.5 评估指标

```python
# metrics.py — 评估指标
import dspy

def email_accuracy(example: dspy.Example, prediction: dspy.Prediction) -> float:
    """邮件分类准确率评估。"""
    score = 0.0
    total = 2  # category + priority

    # 类别正确
    if prediction.category == example.category:
        score += 1.0

    # 优先级正确
    if prediction.priority == example.priority:
        score += 1.0

    # 额外：reasoning 不为空（质量检查）
    if prediction.reasoning and len(prediction.reasoning) > 5:
        score += 0.5  # 额外奖励

    return score / total


def exact_match(example: dspy.Example, prediction: dspy.Prediction) -> float:
    """精确匹配评估。"""
    return float(prediction.answer == example.answer)


def fuzzy_match(example: dspy.Example, prediction: dspy.Prediction) -> float:
    """模糊匹配：计算答案相似度的评估。"""
    pred = prediction.answer.lower().strip()
    gold = example.answer.lower().strip()

    if pred == gold:
        return 1.0
    if gold in pred or pred in gold:
        return 0.7

    # 计算词重叠率
    pred_words = set(pred.split())
    gold_words = set(gold.split())
    if len(gold_words) > 0:
        overlap = len(pred_words & gold_words) / len(gold_words)
        return overlap

    return 0.0
```

### 3.6 编译优化

```python
# compile.py — DSPy 编译优化示例
import dspy
from dspy.teleprompt import BootstrapFewShot, MIPROv2

# 设置 LLM
lm = dspy.LM("openai/gpt-4o-mini")
dspy.configure(lm=lm)

# 初始化模块
classifier = ClassifyEmail()

# ========= BootstrapFewShot 优化 =========
print("===== BootstrapFewShot 优化 =====")

fewshot_optimizer = BootstrapFewShot(
    metric=email_accuracy,
    max_bootstrapped_demos=4,  # 最多生成 4 个示例
    max_labeled_demos=8,       # 最多使用 8 个标注示例
    max_rounds=1,              # 优化轮数
    teacher_settings=dict(lm=dspy.LM("openai/gpt-4o")),  # Teacher 模型
)

# 编译
optimized_classifier = fewshot_optimizer.compile(
    classifier,
    trainset=email_trainset,
    valset=email_devset,
)

# 保存编译结果
optimized_classifier.save("optimized_classifier_fewshot.json")

# ========= MIPROv2 优化（更强大） =========
print("===== MIPROv2 优化 =====")

mipro_optimizer = MIPROv2(
    metric=email_accuracy,
    num_candidates=10,       # 候选指令数
    init_temperature=1.0,    # 探索温度
    verbose=True,
)

# 编译（更耗时但效果更好）
optimized_mipro = mipro_optimizer.compile(
    classifier,
    trainset=email_trainset,
    num_trials=15,           # 尝试次数
    max_bootstrapped_demos=3,
    max_labeled_demos=5,
)

# 保存
optimized_mipro.save("optimized_classifier_mipro.json")

print("优化完成！")
```

### 3.7 使用优化后的模型

```python
# inference.py — 使用优化后的模型进行推理
import dspy

# 加载 LLM
lm = dspy.LM("openai/gpt-4o-mini")
dspy.configure(lm=lm)

# 加载优化后的模块
classifier = ClassifyEmail()
classifier.load("optimized_classifier_mipro.json")

# 进行推理
def predict_email(email_content: str) -> dict:
    """预测邮件分类。"""
    result = classifier(email_content=email_content)
    return {
        "category": result.category,
        "priority": result.priority,
        "reasoning": result.reasoning,
    }

# 批量预测
emails = [
    "发件人: angry@user.com\n主题: 退款\n正文: 我要退款！立刻！",
    "发件人: partner@co.com\n主题: 合作\n正文: 希望能成为贵司的合作伙伴。",
    "发件人: ads@spam.com\n主题: 中奖\n正文: 恭喜你中奖了！",
]

for email in emails:
    result = predict_email(email)
    print(f"类别: {result['category']}, 优先级: {result['priority']}")
```

### 3.8 与手动提示词对比实验

```python
# comparison.py — DSPy 优化 vs 手动提示词对比
import dspy
import time

lm = dspy.LM("openai/gpt-4o-mini")
dspy.configure(lm=lm)

# 手动编写的提示词
MANUAL_PROMPT = """你是一个邮件分类助手。
请分析以下邮件内容，将其分类为 inquiry/complaint/feedback/spam/other，
并给出处理优先级 high/medium/low。

请严格按 JSON 格式返回。

邮件内容:
{email}
"""

def manual_classify(email: str) -> dict:
    """使用手动编写的提示词分类。"""
    prompt = MANUAL_PROMPT.format(email=email)
    response = lm(prompt)
    return {"raw_response": response}

# DSPy 优化后的分类器
classifier = ClassifyEmail()
classifier.load("optimized_classifier_mipro.json")

def dspy_classify(email: str) -> dict:
    """使用 DSPy 优化后的分类器。"""
    result = classifier(email_content=email)
    return {
        "category": result.category,
        "priority": result.priority,
    }

# 对比测试
test_emails = [
    ("投诉邮件", "发件人: customer@x.com\n主题: 质量问题\n正文: 产品质量有问题，要求退货。"),
    ("咨询邮件", "发件人: prospect@y.com\n主题: 产品咨询\n正文: 请问你们的 API 如何集成？"),
]

for name, email in test_emails:
    print(f"\n=== {name} ===")

    start = time.time()
    manual = manual_classify(email)
    manual_time = time.time() - start

    start = time.time()
    dspy_result = dspy_classify(email)
    dspy_time = time.time() - start

    print(f"手动提示词: {manual['raw_response'][:100]}... ({manual_time:.2f}s)")
    print(f"DSPy 优化: {dspy_result} ({dspy_time:.2f}s)")
```

## 4. 最佳实践

### 4.1 数据集准备

1. **质量优先于数量**：20-50 个高质量标注示例优于 500 个低质量示例
2. **覆盖边缘情况**：确保训练数据包含边界情况和异常样本
3. **输入字段标记**：使用 `.with_inputs()` 明确标记输入字段
4. **数据多样性**：不同风格、长度的样本混合

### 4.2 优化器选择

| 优化器 | 数据需求 | 优化时间 | 效果 | 适合场景 |
|--------|---------|---------|------|---------|
| BootstrapFewShot | 少 (10-20) | 快 (<5min) | 中等 | 快速原型 |
| BootstrapFewShotWithRandomSearch | 中 (20-50) | 中 (10-30min) | 良好 | 标准任务 |
| MIPROv2 | 中 (20-100) | 较长 (30-120min) | 最佳 | 生产级任务 |
| COPRO | 少 (10-30) | 快 (<10min) | 良好 | 指令优化 |

### 4.3 评估策略

1. **留出验证集**：千万不要用训练数据评估
2. **多维度评估**：准确率、召回率、F1 分数、推理时间
3. **跨模型验证**：在 GPT-4 上优化，在 GPT-4o-mini 上验证
4. **人工抽检**：定期抽取结果人工复核

### 4.4 Pipeline 最佳实践

1. **分解复杂任务**：将长管道拆分为可独立优化的子模块
2. **中间结果检查**：在管道中间步骤插入验证点
3. **模块复用**：通用模块（如分类器）可以在多个管道中复用
4. **渐进式优化**：先从单模块开始，逐步扩展到全管道

## 5. 常见陷阱

### 5.1 优化过度（Overfitting）

编译后的模块在训练集表现完美，但在新数据上性能下降。
- 解决方案：使用独立的测试集，限制 bootstrap 示例数量

### 5.2 数据偏差

训练数据中类别分布不均导致优化器偏向多数类。
- 解决方案：确保训练数据中各类别数量均衡

### 5.3 Teacher 模型过强

GPT-4 生成的示例可能过于复杂，导致 GPT-4o-mini 无法模仿。
- 解决方案：使用与部署模型相同或相近的 Teacher 模型

### 5.4 忽略成本

MIPROv2 优化过程中需要大量 LLM 调用，可能产生显著费用。
- 解决方案：控制 num_trials 和 max_bootstrapped_demos

### 5.5 模块状态管理

DSPy Module 的 `load` 和 `save` 在不同版本间可能不兼容。

## 6. API Key 依赖

| LLM 后端 | 需要 Key | 说明 |
|---------|---------|------|
| OpenAI | 需要 | 最常用后端 |
| Anthropic | 需要 | Claude 模型 |
| Ollama | 不需要 | 本地开源模型 |
| Together AI | 需要 | 云推理 |
| vLLM | 不需要 | 本地推理 |

优化过程中需要大量 LLM 调用，建议：
- 开发阶段使用 OpenAI 或 Anthropic
- 生产部署时可切换到本地开源模型（通过 DSPy 编译的提示词可迁移）

## 7. 技术关系

- **上层**：Agent 应用 -> 使用 DSPy 优化的 LLM 模块
- **本层**：DSPy 框架 -> 提示词声明和优化
- **下层**：LLM API -> 底层模型调用
- **并行**：LangChain LCEL -> 不同的编排范式
- **工具**：评估框架 -> 质量度量

## 8. 验收清单

- [ ] 理解 DSPy 的核心概念：Signature、Module、Optimizer
- [ ] 掌握 Signature 的声明式定义方法
- [ ] 能够编写可组合的 Module
- [ ] 理解 BootstrapFewShot 和 MIPROv2 的区别
- [ ] 准备训练和评估数据集
- [ ] 实现自定义评估指标
- [ ] 完成一次完整的编译优化流程
- [ ] 保存和加载优化后的模块
- [ ] 对比优化前后的性能差异
- [ ] 了解 DSPy 在复杂管道中的应用

## 9. 学习资源

- DSPy 官方文档：https://dspy.ai
- GitHub：https://github.com/stanfordnlp/dspy
- 论文《DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines》
- DSPy 示例集：https://github.com/stanfordnlp/dspy/tree/main/examples
- DSPy 论文解读：https://arxiv.org/abs/2310.03714
- Discord 社区：DSPy Discord
