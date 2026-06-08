# 32 开源模型 — 本地部署与私有化推理

## 1. 概念概述

### 1.1 开源大语言模型生态

开源大语言模型是 Agent 基础设施中至关重要的一环。与闭源 API 模型不同，开源模型允许开发者完全控制模型的运行环境、数据流和成本结构。2024-2025 年，开源模型生态经历了爆发式增长，Meta Llama 系列、阿里 Qwen 系列、Mistral AI 系列和 DeepSeek 系列成为四大主流阵营。

开源模型的核心价值主张：
- **数据隐私**：所有推理在本地完成，敏感数据不外传
- **无 API 调用成本**：一次硬件投入后，推理边际成本趋近于零
- **完全定制**：可以进行微调、量化、蒸馏等定制化操作
- **离线可用**：不依赖互联网连接，适合内网和边缘场景
- **无速率限制**：没有 API 调用的 QPS 上限

### 1.2 四大模型系列对比

| 特性 | Llama 3 (Meta) | Qwen 2.5 (阿里) | Mistral (Mistral AI) | DeepSeek V3/R1 |
|------|---------------|-----------------|---------------------|----------------|
| 开源协议 | Llama 3 Community | Apache 2.0 | Apache 2.0 | MIT |
| 中文能力 | 中等 (13% 中文训练) | 优秀 (原生中文) | 一般 (主要英文) | 优秀 (原生中文) |
| 最大参数 | 405B | 72B / 110B | 123B | 671B (MoE) |
| 最小参数 | 8B | 0.5B | 7B | 1.5B |
| MoE 支持 | 无 | 有 (Qwen2.5-MoE) | 有 (Mixtral) | 有 (DeepSeekMoE) |
| 上下文长度 | 128K | 128K-1M | 32K | 128K |
| 工具调用 | 优秀 | 优秀 | 良好 | 优秀 |
| 社区生态 | 最活跃 | 中文社区活跃 | 欧洲社区活跃 | 中文社区活跃 |

### 1.3 模型量化技术

量化是将模型参数从高精度（FP16/FP32）转换为低精度（INT4/INT8）的技术，核心目标是减少显存占用和加速推理。

| 量化格式 | 精度 | 显存节省 | 推理速度 | 质量损失 | 适用场景 |
|---------|------|---------|---------|---------|---------|
| GGUF | 2-8 bit | 4-6x | 中等 (CPU 友好) | 可控 | Ollama, llama.cpp |
| GPTQ | 4 bit | 3-4x | 快 (GPU) | 低 | GPU 批量推理 |
| AWQ | 4 bit | 3-4x | 更快 (GPU) | 极低 | GPU 高吞吐场景 |
| bitsandbytes | 4/8 bit | 2-4x | 中等 | 低 | HuggingFace 快速实验 |

## 2. 核心原理

### 2.1 Transformer 推理架构

开源模型基于 Transformer 架构，推理过程包含两个阶段：

1. **预填充阶段（Prefill）**: 并行处理输入 token，生成 Key-Value Cache
2. **解码阶段（Decode）**: 逐个生成 token，每一步重用 KV Cache

KV Cache 的显存占用计算公式：
```
显存占用 = 2 * batch_size * num_layers * num_heads * head_dim * seq_len * dtype_bytes
```

### 2.2 量化原理

量化将浮点数映射到低精度整数空间。以 INT4 量化为例：
```
量化值 = round(原始值 / scale) + zero_point
反量化值 = (量化值 - zero_point) * scale
```

其中 scale 和 zero_point 是校准数据集计算得到的参数。

### 2.3 MoE (Mixture of Experts) 架构

MoE 模型（如 DeepSeek V3, Mixtral）包含多个"专家"子网络，推理时只激活其中一部分：
```
Router(x) -> top_k experts -> 加权求和
```

优势：同样推理成本下获得更大的模型容量。
劣势：需要更多显存加载所有专家参数。

### 2.4 推理服务化架构

本地模型需要部署为服务才能被 Agent 调用，常见的架构模式：
```
Agent 应用 -> HTTP 请求 -> 推理引擎 (vLLM/Ollama) -> 模型权重 -> GPU/CPU
```

## 3. 实战指南

### 3.1 Ollama 本地快速部署

Ollama 是目前最简单的本地模型部署方案。

```bash
# 安装 Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Windows 从 https://ollama.com/download 下载安装包

# 下载并运行模型（首次自动下载）
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull deepseek-r1:8b

# 运行模型（交互模式）
ollama run qwen2.5:7b

# 通过 API 调用
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "请用中文回答：什么是 Agent？",
  "stream": false
}'
```

### 3.2 使用 Ollama Python 客户端

```python
import requests
import json

class OllamaClient:
    """Ollama 本地模型客户端封装。"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, system: str = "", stream: bool = False) -> str:
        """发送生成请求并返回完整响应。"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": stream,
        }
        resp = requests.post(f"{self.base_url}/api/generate", json=payload)
        return resp.json()["response"]

    def chat(self, messages: list[dict], stream: bool = False) -> str:
        """对话接口，兼容 OpenAI 消息格式。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload)
        data = resp.json()
        return data["message"]["content"]

    def generate_stream(self, prompt: str, system: str = ""):
        """流式生成。"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": True,
        }
        with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break

# 使用示例
client = OllamaClient(model="qwen2.5:7b")
response = client.chat([
    {"role": "system", "content": "你是一个助手。"},
    {"role": "user", "content": "用 Python 写一个快速排序算法。"},
])
print(response)
```

### 3.3 vLLM 高性能推理服务

vLLM 是生产环境的首选推理引擎，支持 PagedAttention 和连续批处理。

```bash
# 安装 vLLM
pip install vLLM

# 启动 OpenAI 兼容 API 服务
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --tensor-parallel-size 1 \
    --port 8000
```

```python
# 使用 OpenAI 客户端调用 vLLM 服务
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-not-needed",  # vLLM 不验证 key
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[
        {"role": "system", "content": "你是一个编程助手。"},
        {"role": "user", "content": "解释 Python 装饰器的原理。"},
    ],
    temperature=0.7,
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

### 3.4 模型量化实践

```python
# 使用 AutoGPTQ 进行 GPTQ 量化
from transformers import AutoTokenizer
from auto_gptq import AutoGPTQForCausalLM
import torch

model_name = "Qwen/Qwen2.5-7B-Instruct"
quantized_path = "./qwen2.5-7b-gptq-int4"

# 准备校准数据集
calibration_samples = [
    "人工智能是计算机科学的一个分支。",
    "Python 是一种广泛使用的编程语言。",
    "深度学习通过神经网络模拟人脑工作方式。",
]

tokenizer = AutoTokenizer.from_pretrained(model_name)

def get_calibration_dataset():
    inputs = tokenizer(calibration_samples, return_tensors="pt", padding=True)
    return [{"input_ids": inputs.input_ids, "attention_mask": inputs.attention_mask}]

# 执行量化
model = AutoGPTQForCausalLM.from_pretrained(
    model_name,
    quantize_config=None,
)

model.quantize(
    get_calibration_dataset(),
    use_triton=False,
    batch_size=1,
)

# 保存量化模型
model.save_quantized(quantized_path)
tokenizer.save_pretrained(quantized_path)

print(f"模型已量化保存至: {quantized_path}")
```

### 3.5 HuggingFace Transformers 集成

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 加载模型和分词器
model_name = "Qwen/Qwen2.5-7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",  # 自动分配到可用 GPU
    trust_remote_code=True,
)

# 构造对话
messages = [
    {"role": "system", "content": "你是一个有用的助手。"},
    {"role": "user", "content": "什么是机器学习？"},
]

# 应用对话模板
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
)

# 生成响应
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(
    **inputs,
    max_new_tokens=512,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
)

response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(response)
```

### 3.6 ModelScope 中国模型下载

对于中国用户，ModelScope 提供比 HuggingFace 更快的下载速度。

```python
# 从 ModelScope 下载模型
from modelscope import snapshot_download, AutoModelForCausalLM, AutoTokenizer

# 下载 Qwen 模型
model_dir = snapshot_download("Qwen/Qwen2.5-7B-Instruct", cache_dir="./models")

# 直接从 ModelScope 加载
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
```

### 3.7 构建 Agent 本地推理管道

```python
import json
import requests
from typing import Optional

class LocalAgent:
    """基于本地开源模型的 Agent 实现。"""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        system_prompt: str = "你是一个智能助手。",
        tools: Optional[list[dict]] = None,
    ):
        self.model = model
        self.base_url = base_url
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.messages = [{"role": "system", "content": system_prompt}]

    def add_tool(self, name: str, description: str, parameters: dict):
        """注册工具描述。"""
        self.tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        })

    def chat(self, user_input: str) -> str:
        """执行一次对话。"""
        self.messages.append({"role": "user", "content": user_input})

        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": False,
        }
        if self.tools:
            payload["tools"] = self.tools

        resp = requests.post(f"{self.base_url}/api/chat", json=payload)
        data = resp.json()
        assistant_message = data["message"]
        self.messages.append(assistant_message)

        return assistant_message["content"]

    def stream_chat(self, user_input: str):
        """流式对话。"""
        self.messages.append({"role": "user", "content": user_input})
        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": True,
        }
        full_content = ""
        with requests.post(f"{self.base_url}/api/chat", json=payload, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    if "content" in data.get("message", {}):
                        chunk = data["message"]["content"]
                        full_content += chunk
                        yield chunk
                    if data.get("done", False):
                        break
        self.messages.append({"role": "assistant", "content": full_content})

# 使用示例
agent = LocalAgent(
    model="qwen2.5:7b",
    system_prompt="你是一个知识渊博的中文助手，请用中文回答。",
)

agent.add_tool(
    name="get_weather",
    description="获取指定城市的天气信息",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"},
        },
        "required": ["city"],
    },
)

for chunk in agent.stream_chat("请介绍一下开源大模型的主要类别。"):
    print(chunk, end="", flush=True)
```

## 4. 最佳实践

### 4.1 模型选择策略

1. **根据任务选择**：编程任务优先 DeepSeek Coder / Qwen Coder；通用对话选 Llama 3 / Qwen 2.5
2. **根据硬件选择**：消费级 GPU (24GB) 选 7B-8B 参数；企业级 GPU (80GB) 选 70B-72B 参数
3. **先量化再部署**：7B 模型 FP16 需 14GB，INT4 仅需 4GB
4. **测试多个模型**：在同一任务上对比不同模型的输出质量

### 4.2 硬件配置建议

| 模型规模 | 最小显存 (FP16) | 最小显存 (INT4) | 推荐 GPU |
|---------|----------------|----------------|---------|
| 1.5-3B  | 4 GB           | 2 GB           | RTX 3060 |
| 7-8B     | 16 GB          | 4-6 GB         | RTX 4090 |
| 20B      | 40 GB          | 10-12 GB       | A100 40G |
| 70-72B   | 140 GB         | 35-40 GB       | 2x A100 |
| 405B     | 800 GB         | 200 GB         | 8x A100 |

### 4.3 推理优化技巧

1. **开启 Flash Attention**：减少显存占用，加速推理（`--enable-flash-attn`）
2. **使用连续批处理**：vLLM 自动合并多个请求为 batch
3. **调整 max-model-len**：按实际需求设置上下文长度，过长会浪费显存
4. **前缀缓存**：对系统提示词等重复前缀进行 KV Cache 复用

### 4.4 中文模型推荐

中文场景优先考虑：
- **Qwen2.5 系列**：阿里出品，中文能力最强，从 0.5B 到 110B 全覆盖
- **DeepSeek V3/R1**：深度求索出品，推理和编程能力强
- **Yi 1.5 系列**：零一万物出品，中文对话体验好
- **InternLM 2.5**：上海 AI 实验室出品，工具调用能力出色

## 5. 常见陷阱

### 5.1 显存不足导致 OOM

```python
# 错误：直接加载 FP16 模型到 8GB GPU
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# 正确：使用 device_map="auto" 或量化
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    load_in_4bit=True,  # 4bit 量化
)
```

### 5.2 忽略对话模板

不同模型的对话格式不同，必须使用正确的 template：
- Qwen: `<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n`
- Llama 3: `<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n...`
- DeepSeek: 使用 `apply_chat_template` 自动处理

### 5.3 生产环境使用 Ollama

Ollama 适合开发和测试，生产环境建议使用 vLLM 或 TGI：
- Ollama 的并发能力有限
- vLLM 支持 PagedAttention 和更多优化

### 5.4 模型版本不匹配

HuggingFace 上的模型可能频繁更新，指定 commit hash 固定版本：
```python
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    revision="a1b2c3d4e5f6",  # 固定 commit
)
```

## 6. API Key 依赖

**本地部署开源模型无需任何 API Key。** 这是开源模型相比闭源 API 模型的最大优势。

需要 API Key 的场景：
- 从 HuggingFace 下载托管模型（非必需，但未登录有速率限制）
- 使用 ModelScope 下载（国内用户推荐，无需特殊网络）
- 使用商业开源模型的云服务版本（如 Together AI, Fireworks AI）

| 服务 | 是否需要 Key | 用途 |
|------|------------|------|
| HuggingFace Hub | 可选（登录提升速率） | 模型下载 |
| ModelScope | 可选 | 模型下载（国内） |
| Ollama | 不需要 | 本地推理 |
| vLLM | 不需要 | 本地推理 |

## 7. 技术关系

开源模型在 Agent 技术栈中的位置：
- **上层**：LocalAgent -> 基于开源模型的 Agent 应用
- **本层**：Ollama / vLLM -> 推理服务框架
- **下层**：Transformers / llama.cpp -> 模型加载引擎
- **基础设施**：NVIDIA GPU / CUDA -> 硬件加速
- **量化工具**：AutoGPTQ / AWQ / llama.cpp -> 模型压缩

## 8. 验收清单

- [ ] 理解四大开源模型系列的核心差异和适用场景
- [ ] 能够使用 Ollama 在本地部署至少一个模型
- [ ] 掌握 vLLM 的安装和 API 服务启动
- [ ] 理解 GGUF、GPTQ、AWQ 三种量化格式的区别
- [ ] 能够使用 HuggingFace Transformers 加载模型进行推理
- [ ] 了解 ModelScope 的使用方法（中国用户）
- [ ] 掌握对话模板的正确使用方法
- [ ] 能够根据硬件配置选择合适的模型规模和量化方式
- [ ] 实现基于开源模型的本地 Agent
- [ ] 理解 MoE 架构和 KV Cache 的原理

## 9. 学习资源

- Ollama 官方文档：https://github.com/ollama/ollama
- vLLM 文档：https://docs.vllm.ai
- HuggingFace Transformers：https://huggingface.co/docs/transformers
- ModelScope：https://modelscope.cn
- llama.cpp：https://github.com/ggerganov/llama.cpp
- AutoGPTQ：https://github.com/AutoGPTQ/AutoGPTQ
- Qwen 官方：https://github.com/QwenLM/Qwen2.5
- DeepSeek 官方：https://github.com/deepseek-ai/DeepSeek-V3
- 开源模型排行榜：https://huggingface.co/spaces/open-llm-leaderboard
