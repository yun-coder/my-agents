# 13 短期记忆 / 对话历史管理

## 学习目标

- 理解模型没有天然的无限记忆。
- 掌握消息历史、滑动窗口、摘要压缩和 Token 预算。
- 知道短期记忆与长期记忆、状态持久化的区别。

## 常见策略

| 策略 | 优点 | 局限 |
|---|---|---|
| 全量历史 | 简单 | 上下文增长快 |
| 最近 N 轮 | 成本可控 | 会遗忘早期信息 |
| 摘要 + 最近 N 轮 | 平衡成本与信息 | 摘要可能丢细节 |
| 检索式记忆 | 按需召回 | 增加检索复杂度 |

## 工程实践

- 统计 Token，而不是只按字符数猜测。
- 把系统规则与可裁剪历史分开。
- 重要业务状态写数据库，不要只依赖聊天历史。
- 为摘要过程保留审计记录。

`demo.py` 为了不引入 tokenizer 依赖，使用字符数近似预算。它用于展示滑动窗口算法，
不等于生产级 Token 统计。

## 参考资料

- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)

## 验收清单

- 能实现最近 N 轮窗口。
- 能解释历史消息与业务状态的区别。
- 能说明摘要压缩可能损失什么。
