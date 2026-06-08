# 41 — Agent 微调

## 概念概述

### 什么是 Agent 微调

Agent 微调（Fine-tuning）是指在预训练大语言模型的基础上，使用特定领域的标注数据对模型进行额外训练，使其适应 Agent 场景下的特殊需求。与通用模型相比，微调后的 Agent 模型在工具调用格式遵循、任务规划、多轮对话一致性等方面表现显著提升。

### 为什么需要微调

通用大模型虽然在许多任务上表现出色，但在 Agent 场景下存在以下不足：

- 工具调用格式不稳定：模型偶尔输出不规范的 JSON 工具调用，导致解析失败
- 任务规划逻辑薄弱：复杂多步骤任务中容易遗漏关键步骤或顺序错乱
- 领域术语理解不足：特定行业（医疗、法律、金融）的专有名词理解偏差
- 输出格式不统一：结构化输出的字段名和格式不一致，难以解析

通过微调，可以使模型在这些方面得到显著改善。

### 微调 vs Prompt Engineering

| 维度     | Prompt Engineering | 微调              |
|----------|-------------------|-------------------|
| 成本     | 低（仅 API 费）    | 高（GPU + 标注）   |
| 效果上限 | 受限于基础模型     | 可达专用模型水平   |
| 稳定性   | 受 Prompt 措辞影响 | 稳定行为模式       |
| 迭代速度 | 分钟级             | 小时级             |
| 数据需求 | 零数据             | 100-10000+ 条     |

---

## 核心原理

### 1. SFT（监督微调）

SFT（Supervised Fine-Tuning）是最基础的微调方法，在标注数据上通过最大似然估计进行训练。其核心目标是让模型学会从输入 x 到目标输出 y 的正确映射。

SFT 的训练过程可以概括为：给定输入 x 和目标输出 y，最小化负对数似然 L = -sum(log P(y_t | y_{<t}, x; theta))。

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def prepare_sft_training():
    """准备 SFT 训练的模型和分词器"""
    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-3.2-8B",
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(
        "meta-llama/Llama-3.2-8B"
    )
    return model, tokenizer

# SFT 训练注意事项：
# 1. 损失只在 response 部分计算（忽略 prompt 部分），防止模型忘记通用对话能力
# 2. 使用适当的 learning rate（通常 1e-5 到 5e-5）
# 3. 训练数据质量比数量更重要
```

### 2. RLHF（基于人类反馈的强化学习）

RLHF 通过三个步骤让模型对齐人类偏好：

- 步骤 1：SFT 训练基础模型，使其具备基本的指令跟随能力
- 步骤 2：训练奖励模型（Reward Model），学习对人类偏好的评分
- 步骤 3：使用 PPO 算法微调，最大化奖励模型给出的分数

```python
class PPOTrainer:
    """PPO 强化学习训练器的核心逻辑"""

    def train_step(self, prompts: list[str]):
        # 1. 从当前策略采样输出
        responses = self.model.generate(prompts)

        # 2. 奖励模型评分
        rewards = self.reward_model(prompts, responses)

        # 3. PPO 更新
        for _ in range(self.ppo_epochs):
            advantages = self.compute_advantages(rewards)
            log_probs = self.model.log_prob(prompts, responses)
            ratio = (log_probs - old_log_probs).exp()

            # 裁剪的目标函数防止更新过大
            clipped_ratio = torch.clamp(ratio, 1 - self.eps, 1 + self.eps)
            loss = -torch.min(ratio * advantages, clipped_ratio * advantages)

            # KL 散度惩罚防止过度偏离参考模型
            kl_div = kl_divergence(new_probs, old_probs)
            loss += self.beta * kl_div

            loss.backward()
            self.optimizer.step()
```

### 3. DPO（直接偏好优化）

DPO 是 RLHF 的简化替代方案，不需要显式的奖励模型。其核心创新是将两阶段过程合并为单阶段：

```python
class DPOTrainer:
    """DPO 训练器"""

    def dpo_loss(self, policy_logps, ref_logps, preferred_ids, dispreferred_ids):
        """
        DPO 损失函数:
        L = -E[log sigma(beta * (log pi(y_w|x) - log pi_ref(y_w|x)
                                 - log pi(y_l|x) + log pi_ref(y_l|x)))]

        y_w: 偏好回答（chosen）
        y_l: 非偏好回答（rejected）
        beta: 温度参数
        """
        beta = 0.1

        preferred_diff = (
            policy_logps.gather(1, preferred_ids).sum(dim=1)
            - ref_logps.gather(1, preferred_ids).sum(dim=1)
        )
        dispreferred_diff = (
            policy_logps.gather(1, dispreferred_ids).sum(dim=1)
            - ref_logps.gather(1, dispreferred_ids).sum(dim=1)
        )

        logits = beta * (preferred_diff - dispreferred_diff)
        loss = -torch.nn.functional.logsigmoid(logits).mean()
        return loss
```

### SFT vs RLHF vs DPO 对比

| 维度     | SFT   | RLHF  | DPO   |
|----------|-------|-------|-------|
| 数据需求 | 输入-输出对 | 输出排序（4-9个） | 偏好对（2选1） |
| 训练复杂度 | 低    | 高（3阶段） | 中     |
| 稳定性   | 高    | 中（PPO不稳定） | 高    |
| 对齐效果 | 中    | 高    | 高    |
| 计算资源 | 1x    | 3x    | 1.5x  |

---

## 数据准备

### Agent 场景的指令格式

```json
{
  "instruction": "查询明天北京到上海的航班",
  "tools": [
    {
      "name": "search_flights",
      "description": "搜索航班信息",
      "parameters": {
        "type": "object",
        "properties": {
          "from": {"type": "string"},
          "to": {"type": "string"},
          "date": {"type": "string"}
        },
        "required": ["from", "to", "date"]
      }
    }
  ],
  "response": {
    "role": "assistant",
    "content": "我来帮你查询航班信息。",
    "tool_calls": [
      {
        "name": "search_flights",
        "arguments": {
          "from": "北京",
          "to": "上海",
          "date": "2026-06-09"
        }
      }
    ]
  }
}
```

### 对话式 Agent 数据格式（ChatML）

ChatML 使用特殊 token 来区分不同角色：

```python
def format_chatml(conversation: list[dict]) -> str:
    """将对话格式化为 ChatML 格式"""
    formatted = []
    for turn in conversation:
        role = turn["role"]
        content = turn["content"]
        formatted.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    return "\n".join(formatted) + "\n<|im_start|>assistant\n"

# Agent 工具调用的 ChatML 示例
agent_data = [
    {"role": "system", "content": "你是一个助理 Agent，可以调用工具。"},
    {"role": "user", "content": "查一下明天北京到深圳的航班"},
    {"role": "assistant", "content": "我来查询！\n<tool_call>\n{\"name\": \"search_flights\", \"arguments\": {\"from\": \"北京\", \"to\": \"深圳\", \"date\": \"2026-06-09\"}}\n</tool_call>"},
    {"role": "tool", "content": "{\"flights\": [{\"no\": \"CA1234\", \"time\": \"08:00-10:30\", \"price\": 1200}]}"},
    {"role": "assistant", "content": "CA1234 08:00-10:30 价格 1200 元"}
]
```

### 数据质量过滤

```python
import re
import json

class DataFilter:
    """微调数据质量过滤器"""

    def __init__(self):
        self.filters = [
            self._filter_too_short,
            self._filter_duplicate,
            self._filter_malformed_json,
        ]

    def filter_dataset(self, data: list[dict]) -> list[dict]:
        """过滤整个数据集"""
        passed = []
        rejected = {"too_short": 0, "duplicate": 0, "bad_json": 0}
        seen = set()

        for item in data:
            if len(item.get("instruction", "")) < 20:
                rejected["too_short"] += 1
                continue

            content_hash = hash(item.get("instruction", "") + item.get("response", ""))
            if content_hash in seen:
                rejected["duplicate"] += 1
                continue
            seen.add(content_hash)

            response = item.get("response", "")
            tool_calls = re.findall(r"<tool_call>\n(.*?)\n</tool_call>", response, re.DOTALL)
            for tc in tool_calls:
                try:
                    json.loads(tc)
                except json.JSONDecodeError:
                    rejected["bad_json"] += 1
                    continue

            passed.append(item)

        print(f"过滤结果: 通过 {len(passed)} 条, 拒绝 {sum(rejected.values())} 条")
        return passed
```

---

## 高效微调方法

### LoRA（低秩适配）

LoRA 通过注入可训练的低秩矩阵来适配模型，可训练参数量仅为全参数微调的 0.1%-1%：

```python
from peft import LoraConfig, get_peft_model

def create_lora_model(base_model_name: str = "Qwen/Qwen2.5-7B"):
    """
    创建 LoRA 微调模型

    LoRA 原理: 对于权重矩阵 W，学习低秩分解 W + BA
    其中 B 维度 d x r, A 维度 r x k, r << min(d, k)
    """
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name, torch_dtype=torch.bfloat16, device_map="auto"
    )

    lora_config = LoraConfig(
        r=16,                # 秩，越大能力越强但参数量越大
        lora_alpha=32,       # 缩放系数
        target_modules=[     # 目标模块
            "q_proj", "v_proj", "k_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    lora_model = get_peft_model(model, lora_config)

    trainable = sum(p.numel() for p in lora_model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in lora_model.parameters())
    print(f"可训练参数: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    return lora_model
```

### QLoRA（量化 LoRA）

QLoRA 在 LoRA 基础上引入 4-bit 量化，使单卡 24GB 即可微调 70B 模型：

```python
from transformers import BitsAndBytesConfig

def create_qlora_model():
    """
    QLoRA 配置

    关键创新:
    1. 4-bit NormalFloat 量化: 比普通 int4 更好的精度
    2. Double Quantization: 对量化常数再量化
    3. Paged Optimizer: 利用 CPU 内存缓解显存压力
    """
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-3.1-70B",  # 70B 模型
        quantization_config=bnb_config,
        device_map="auto"
    )

    lora_config = LoraConfig(
        r=8, lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05, bias="none", task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    return model

# 显存参考:
# - Llama-3.1-70B + QLoRA: ~22GB
# - Qwen2.5-72B + QLoRA: ~24GB
# - Qwen2.5-7B + QLoRA: ~8GB
```

---

## 主流微调框架

### 1. HuggingFace TRL

TRL 是 HuggingFace 官方出品的微调工具包，支持 SFT、DPO、PPO 等训练范式：

```python
from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments

def train_with_trl():
    """使用 TRL 进行 SFT 训练"""
    dataset = Dataset.from_list([
        {"prompt": "你好", "response": "你好！有什么可以帮助你的？"},
        {"prompt": "查询上海的天气",
         "response": "<tool_call>{\"name\": \"get_weather\", \"arguments\": {\"city\": \"上海\"}}</tool_call>"},
    ])

    def format_func(example):
        return (f"<|im_start|>user\n{example['prompt']}<|im_end|>\n"
                f"<|im_start|>assistant\n{example['response']}<|im_end|>")

    trainer = SFTTrainer(
        model="Qwen/Qwen2.5-7B",
        train_dataset=dataset,
        formatting_func=format_func,
        args=TrainingArguments(
            output_dir="./agent-sft",
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            num_train_epochs=3,
            logging_steps=10,
            save_steps=500,
            fp16=True,
        ),
        max_seq_length=2048,
        peft_config=LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"], lora_dropout=0.05),
    )

    trainer.train()
    trainer.save_model("./agent-sft-final")
```

### 2. LLaMA-Factory

LLaMA-Factory 是当前最流行的中文微调框架，提供 Web UI 和命令行接口：

```yaml
# LLaMA-Factory 配置文件
model_name: Qwen2.5-7B
template: qwen
stage: sft
finetuning_type: lora
lora_rank: 16
lora_target: all
dataset: agent_training_data
dataset_dir: ./data
max_samples: 10000
per_device_train_batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 5.0e-5
num_train_epochs: 3.0
max_seq_length: 4096
quantization_bit: 4
output_dir: ./output/agent-qwen
logging_steps: 10
save_steps: 500
```

```bash
llamafactory-cli train config.yaml
llamafactory-cli webui   # Web UI 模式
```

### 3. Axolotl

Axolotl 以灵活的配置和高效的训练著称：

```yaml
# axolotl 配置文件
base_model: mistralai/Mistral-7B-v0.1
model_type: MistralForCausalLM
tokenizer_type: LlamaTokenizer
load_in_4bit: true
datasets:
  - path: ./data/agent_train.jsonl
    type: sharegpt
    conversation: chatml
micro_batch_size: 2
gradient_accumulation_steps: 8
num_epochs: 3
learning_rate: 0.0002
train_on_inputs: false
sequence_len: 4096
optimizer: adamw_bnb_8bit
lr_scheduler: cosine
warmup_steps: 100
output_dir: ./axolotl-outputs
```

---

## 评估基准

```python
class AgentEvalBenchmark:
    """Agent 微调效果评估"""

    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def evaluate_tool_call_accuracy(self, test_cases: list[dict]) -> dict:
        """评估工具调用准确性"""
        correct_format = 0
        correct_tool = 0

        for case in test_cases:
            prompt = case["prompt"]
            expected = case["expected_tool_call"]
            output = self._generate(prompt)

            if self._has_valid_json(output):
                correct_format += 1
                if expected["name"] in output:
                    correct_tool += 1

        total = len(test_cases)
        return {
            "format_accuracy": correct_format / total,
            "tool_accuracy": correct_tool / total,
        }

    def _generate(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=512, temperature=0.1, do_sample=False)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def _has_valid_json(self, text: str) -> bool:
        import json
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return False
```

---

## 成本估算

```python
def estimate_training_cost(model_size: str, method: str, dataset_size: int, seq_length: int = 2048, epochs: int = 3) -> dict:
    """估算微调成本"""
    total_tokens = seq_length * dataset_size * epochs

    gpu_requirements = {
        ("7B", "lora"): {"gpu": "RTX 4090 24GB", "count": 1},
        ("7B", "qlora"): {"gpu": "RTX 3060 12GB", "count": 1},
        ("7B", "full"): {"gpu": "A100 80GB", "count": 4},
        ("70B", "qlora"): {"gpu": "A100 80GB", "count": 1},
        ("70B", "full"): {"gpu": "A100 80GB", "count": 64},
    }

    req = gpu_requirements.get((model_size, method), {"gpu": "A100 80GB", "count": 8})

    tokens_per_second = {"7B": 2000, "13B": 1200, "70B": 300}.get(model_size, 1000)
    total_seconds = total_tokens / (tokens_per_second * req["count"])

    hourly_rates = {"RTX 4090 24GB": 0.35, "A100 80GB": 2.00}
    rate = hourly_rates.get(req["gpu"], 1.0)
    cost = rate * req["count"] * (total_seconds / 3600)

    return {
        "total_tokens": total_tokens,
        "gpu": req["gpu"],
        "gpu_count": req["count"],
        "estimated_hours": round(total_seconds / 3600, 1),
        "estimated_cost": round(cost, 2),
    }
```

---

## 最佳实践

### 从 LoRA 开始

总是先尝试 LoRA 或 QLoRA 微调，效果满意后再考虑全参数微调。LoRA 训练速度快、成本低，且不容易过拟合。

### 保持基础模型能力

混合通用数据和领域数据训练，防止灾难性遗忘（Catastrophic Forgetting）。推荐的数据混合比例：

- 40% 工具调用数据（核心 Agent 能力）
- 30% 通用对话数据（保持对话能力）
- 20% 多步推理数据（规划能力）
- 10% 错误恢复数据（Agent 纠错能力）

### 评估先行

在训练前先建立评估基准（Benchmark），量化对比微调前后的效果差异。评估指标应包括工具调用准确率、格式正确率、多轮连贯性等。

### 使用验证集

始终保留 10%-20% 的数据作为验证集，在每个 epoch 结束后评估，防止过拟合。

---

## 常见陷阱

### 陷阱 1：过拟合

小数据集上训练多轮容易过拟合。应使用早停（Early Stopping）、增加 Dropout、使用验证集监控 loss。

### 陷阱 2：灾难性遗忘

只训练 Agent 数据导致通用对话能力退化。应在训练数据中混合通用指令数据，或在指令中明确标注任务类型。

### 陷阱 3：格式过拟合

模型学会输出工具调用格式但内容不对。应在数据中引入负样本（如工具不存在时应该拒绝）和边界情况。

### 陷阱 4：评估偏差

在训练集同分布数据上评估得分高但实际效果差。应使用独立、多样化的测试集进行真实评估。

---

## API Key 与资源依赖

| 资源                | 类型     | 备注                     |
|---------------------|----------|--------------------------|
| 本地 GPU            | 必需     | 至少 12GB VRAM（QLoRA 7B）|
| HuggingFace Token   | 可选     | 部分模型需要授权          |
| W&B Token           | 可选     | 实验追踪                 |
| OpenAI API Key      | 可选     | 用于合成训练数据          |

```bash
HF_TOKEN=hf_xxxxxxxxxxxx
WANDB_API_KEY=xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx  # 仅用于数据生成
```
ENDOFFILE