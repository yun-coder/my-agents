# 41. Agent 微调 / Fine-tuning / RLHF

## 学习目标

- 区分提示词、RAG、监督微调和偏好优化。
- 会检查监督微调样本的基本结构。
- 知道什么时候不应急着微调。

## 核心概念

遇到效果问题时，优先确认问题来自哪里：

| 方法 | 适合解决 |
| --- | --- |
| 提示词与结构化输出 | 任务说明、格式和少量示例 |
| RAG | 模型缺少动态、私有或可追溯知识 |
| 工具调用 | 需要访问外部系统或执行动作 |
| 监督微调 SFT | 希望稳定学习特定风格、格式或行为模式 |
| 偏好优化 / RLHF | 希望模型更偏向人类认可的回答 |

微调不能自动让模型知道最新业务知识，也不能替代权限控制。训练数据要经过脱敏、授权确认、质量抽检和独立验证。

OpenAI 微调数据通常使用 JSONL，每行是一条训练样本。聊天任务使用 `messages` 数组描述对话。开源模型训练可以评估 Hugging Face TRL。

## 示例说明

`demo.py` 读取 `data/sft_examples.jsonl`，检查：

- 每行是否为 JSON 对象。
- 是否存在非空 `messages`。
- 每条消息是否包含合法 `role` 和非空 `content`。

## 运行

```powershell
python .\learning\phase04_frontier\41_fine_tuning\demo.py
```

## 延伸阅读

- [OpenAI Model Optimization 官方指南](https://developers.openai.com/api/docs/guides/model-optimization)
- [Hugging Face TRL 官方文档](https://huggingface.co/docs/trl/)
