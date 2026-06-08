# 38 成本控制与限流 — Agent 系统经济性运营

## 1. 概念概述

### 1.1 为什么需要成本控制

AI Agent 系统的成本结构与传统软件有本质区别。传统软件的成本主要是基础设施（服务器、数据库、带宽），而 Agent 系统的成本大头是 LLM API 调用费用。一次复杂的 Agent 任务可能涉及多次 LLM 调用，单次对话的费用可能高达数美元。

成本失控的典型场景：
- **无限重试循环**：Agent 在工具调用中陷入死循环，不断消耗 Token
- **过长上下文**：Agent 对话不断累积，上下文窗口膨胀导致 Token 消耗激增
- **并发失控**：突发流量导致 LLM API 调用量暴涨
- **模型选择不当**：简单任务使用昂贵的大模型
- **无缓存策略**：相同的 LLM 请求重复执行

### 1.2 限流的必要性

限流（Rate Limiting）保护系统和预算不被过度使用：
- **防止 API 被滥用**：单个用户过度调用影响其他用户
- **控制月度预算**：避免超出预期的 API 费用
- **避免 API 限速处罚**：超出 LLM 提供商的 QPS 限制会被限流
- **保障系统稳定性**：防止流量尖峰压垮后端服务

### 1.3 成本优化全景图

```
Agent 成本优化策略：
├── 模型层面
│   ├── 模型级联（先用便宜模型，复杂情况升级）
│   ├── 模型蒸馏（大模型训练小模型）
│   └── 批量处理（合并多个请求）
├── 缓存层面
│   ├── 精确缓存（完全相同请求）
│   └── 语义缓存（语义相似的请求）
├── 调用层面
│   ├── Token 预算控制
│   ├── 上下文窗口管理
│   └── 限流控制
└── 监控层面
    ├── 成本跟踪
    ├── 预算告警
    └── 用量分析
```

## 2. 核心原理

### 2.1 Token 计费模型

LLM API 的计费通常基于 Token 数量：

```
单次调用成本 = (输入 Token 数 * 输入价格) + (输出 Token 数 * 输出价格)
```

各模型定价示例（2025 年）：
```
GPT-4o:        $2.50 / 1M 输入 Token,  $10.00 / 1M 输出 Token
GPT-4o-mini:   $0.15 / 1M 输入 Token,  $0.60 / 1M 输出 Token
Claude Sonnet: $3.00 / 1M 输入 Token,  $15.00 / 1M 输出 Token
Claude Haiku:  $0.25 / 1M 输入 Token,  $1.25 / 1M 输出 Token
```

### 2.2 滑动窗口限流算法

滑动窗口限流维护一个时间窗口内的请求计数，以秒级精度控制速率：

```
请求到达 -> 检查窗口内计数 -> 超出限制? -> 是: 拒绝请求
                                      -> 否: 增加计数，处理请求
```

相比固定窗口（每分钟 N 个请求），滑动窗口避免了"边界突发"问题：
- 固定窗口：23:59:30 到 00:00:30 之间可能 2 倍流量
- 滑动窗口：任意 60 秒窗口内严格限制 N 个请求

### 2.3 语义缓存

语义缓存不是精确匹配请求内容，而是通过嵌入向量(Embedding)比较请求的语义相似度：

```
请求 -> 生成嵌入向量 -> 向量数据库搜索相似缓存 ->
  相似度 > 阈值? -> 是: 返回缓存结果
                -> 否: 调用 LLM，缓存结果
```

语义缓存大幅减少 LLM 调用量，特别适合客服、FAQ 等重复性高的场景。

### 2.4 模型级联架构

模型级联（Model Cascade）根据任务复杂度自动选择模型：

```
请求 -> 轻量分类器 -> 简单问题? -> 是: 便宜模型 (Haiku/Mini)
                              -> 否: 复杂问题 -> 昂贵模型 (Sonnet/GPT-4o)
```

期望效果：
- 80% 的请求由便宜模型处理 (成本降低 10x)
- 20% 的复杂请求由昂贵模型处理
- 整体成本降低约 70-80%

## 3. 实战指南

### 3.1 Token 计数与成本估算

```python
# token_counter.py — Token 计数和成本估算
import tiktoken
from typing import Optional

MODEL_PRICING = {
    "gpt-4o": {
        "input": 2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
    "gpt-4-turbo": {
        "input": 10.00 / 1_000_000,
        "output": 30.00 / 1_000_000,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000,
    },
    "claude-haiku-3-5-20241022": {
        "input": 0.25 / 1_000_000,
        "output": 1.25 / 1_000_000,
    },
}


class TokenCostCalculator:
    """Token 计数和成本计算器。"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """计算文本的 Token 数。"""
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: list[dict]) -> int:
        """计算消息列表的 Token 数。"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += 4  # 消息格式开销
        total += 2  # 回复格式开销
        return total

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """估算调用成本（美元）。"""
        pricing = MODEL_PRICING.get(self.model)
        if not pricing:
            return 0.0
        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        return input_cost + output_cost

    def estimate_conversation_cost(self, messages: list[dict], output_len: int = 500) -> dict:
        """估算一次对话的成本。"""
        input_tokens = self.count_messages_tokens(messages)
        total_cost = self.estimate_cost(input_tokens, output_len)
        return {
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_len,
            "total_tokens": input_tokens + output_len,
            "cost_usd": round(total_cost, 6),
        }


# 使用示例
calculator = TokenCostCalculator("gpt-4o-mini")
messages = [
    {"role": "system", "content": "你是一个助手。"},
    {"role": "user", "content": "用 Python 写一个排序算法。"},
]
cost = calculator.estimate_conversation_cost(messages)
print(f"估算成本: ${cost['cost_usd']:.6f}")
print(f"Token 数: {cost['total_tokens']}")
```

### 3.2 Redis 滑动窗口限流器

```python
# rate_limiter.py — 基于 Redis 的滑动窗口限流器
import redis
import time
import uuid
from typing import Optional

class SlidingWindowRateLimiter:
    """滑动窗口限流器。"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.client = redis.from_url(redis_url)

    def _window_key(self, key: str) -> str:
        return f"ratelimit:{key}"

    def check_rate(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> tuple[bool, dict]:
        """
        检查是否超过速率限制。

        返回: (是否允许请求, 限流信息)
        """
        now = time.time()
        window_start = now - window_seconds
        redis_key = self._window_key(key)

        # 使用 Redis Pipeline 确保原子性
        pipe = self.client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)  # 移除窗口外的记录
        pipe.zcard(redis_key)  # 获取当前计数
        pipe.zadd(redis_key, {str(uuid.uuid4()): now})  # 添加当前请求
        pipe.expire(redis_key, window_seconds * 2)  # 设置过期时间
        _, current_count, _, _ = pipe.execute()

        allowed = current_count <= max_requests

        info = {
            "allowed": allowed,
            "current_count": current_count,
            "max_requests": max_requests,
            "remaining": max(0, max_requests - current_count),
            "window_seconds": window_seconds,
            "reset_at": int(now) + window_seconds,
        }

        if not allowed:
            # 移除刚添加的记录
            self.client.zremrangebyscore(redis_key, now, now)

        return allowed, info

    def check_rate_by_token(
        self,
        token_count: int,
        max_tokens: int = 100000,
        window_seconds: int = 3600,
        user_id: str = "global",
    ) -> tuple[bool, dict]:
        """基于 Token 用量的限流（适用于 LLM API 成本控制）。"""
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:token:{user_id}"

        pipe = self.client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        pipe.execute()

        # 获取窗口内已使用的 Token 总量
        tokens_used = 0
        token_entries = self.client.zrange(redis_key, 0, -1, withscores=True)
        for entry, _ in token_entries:
            tokens_used += int(entry.split(":")[0])

        allowed = (tokens_used + token_count) <= max_tokens
        if allowed:
            self.client.zadd(redis_key, {f"{token_count}:{uuid.uuid4()}": now})
            self.client.expire(redis_key, window_seconds * 2)

        return allowed, {
            "allowed": allowed,
            "tokens_used": tokens_used,
            "tokens_requested": token_count,
            "max_tokens": max_tokens,
            "remaining_tokens": max(0, max_tokens - tokens_used - token_count),
        }


# 使用示例
limiter = SlidingWindowRateLimiter()

# API 调用限流：每分钟最多 60 次
for i in range(65):
    allowed, info = limiter.check_rate("api:user_123", max_requests=60)
    if not allowed:
        print(f"请求 {i+1}: 被限流，剩余 {info['remaining']} 次")
        break
    else:
        print(f"请求 {i+1}: 允许")

# Token 用量限流：每小时最多 100K Token
allowed, info = limiter.check_rate_by_token(
    token_count=15000,
    max_tokens=100000,
    user_id="user_456",
)
print(f"Token 限流: {'允许' if allowed else '拒绝'}, 信息: {info}")
```

### 3.3 LiteLLM 代理成本跟踪

```python
# litellm_proxy.py — LiteLLM 代理配置与成本跟踪
import litellm
from litellm import Router
import os
from datetime import datetime, timedelta
from typing import Optional

# 配置多个模型
model_list = [
    {
        "model_name": "gpt-4o-mini",
        "litellm_params": {
            "model": "openai/gpt-4o-mini",
            "api_key": os.environ["OPENAI_API_KEY"],
            "rpm": 500,  # 每分钟请求数限制
            "tpm": 100000,  # 每分钟 Token 数限制
        },
    },
    {
        "model_name": "gpt-4o",
        "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": os.environ["OPENAI_API_KEY"],
            "rpm": 100,
            "tpm": 50000,
        },
    },
    {
        "model_name": "claude-sonnet",
        "litellm_params": {
            "model": "anthropic/claude-sonnet-4-20250514",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
            "rpm": 50,
        },
    },
]

# 创建路由器
router = Router(model_list=model_list)

# 成本跟踪
class CostTracker:
    """LLM 调用成本跟踪器。"""

    def __init__(self):
        self.calls: list[dict] = []
        self.daily_budget: Optional[float] = None
        self.monthly_budget: Optional[float] = None

    def set_budgets(self, daily: float, monthly: float):
        """设置预算上限。"""
        self.daily_budget = daily
        self.monthly_budget = monthly

    def track_call(self, model: str, input_tokens: int, output_tokens: int):
        """记录一次 LLM 调用。"""
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        entry = {
            "timestamp": datetime.utcnow(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
        }
        self.calls.append(entry)
        self._check_budgets()
        return entry

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算调用成本。"""
        pricing = MODEL_PRICING.get(model, {})
        input_cost = input_tokens * pricing.get("input", 0)
        output_cost = output_tokens * pricing.get("output", 0)
        return input_cost + output_cost

    def get_daily_cost(self) -> float:
        """获取今日总成本。"""
        today = datetime.utcnow().date()
        return sum(
            c["cost"] for c in self.calls
            if c["timestamp"].date() == today
        )

    def get_monthly_cost(self) -> float:
        """获取本月总成本。"""
        this_month = datetime.utcnow().month
        return sum(
            c["cost"] for c in self.calls
            if c["timestamp"].month == this_month
        )

    def _check_budgets(self):
        """检查是否超出预算。"""
        daily = self.get_daily_cost()
        monthly = self.get_monthly_cost()

        if self.daily_budget and daily > self.daily_budget:
            print(f"警告: 今日预算 ${self.daily_budget} 已超限 (当前: ${daily:.2f})")

        if self.monthly_budget and monthly > self.monthly_budget:
            print(f"警告: 月度预算 ${self.monthly_budget} 已超限 (当前: ${monthly:.2f})")

    def get_report(self) -> dict:
        """获取成本报告。"""
        total_cost = sum(c["cost"] for c in self.calls)
        total_input = sum(c["input_tokens"] for c in self.calls)
        total_output = sum(c["output_tokens"] for c in self.calls)

        # 按模型统计
        by_model = {}
        for c in self.calls:
            by_model.setdefault(c["model"], {"calls": 0, "cost": 0.0, "tokens": 0})
            by_model[c["model"]]["calls"] += 1
            by_model[c["model"]]["cost"] += c["cost"]
            by_model[c["model"]]["tokens"] += c["input_tokens"] + c["output_tokens"]

        return {
            "total_calls": len(self.calls),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_input + total_output,
            "daily_cost": round(self.get_daily_cost(), 4),
            "monthly_cost": round(self.get_monthly_cost(), 4),
            "by_model": by_model,
        }


# 全局成本跟踪器
cost_tracker = CostTracker()
cost_tracker.set_budgets(daily=5.0, monthly=100.0)

# 使用 LiteLLM Router 自动路由和跟踪
async def llm_call_with_tracking(prompt: str, model_group: str = "gpt-4o-mini"):
    """使用 LiteLLM Router 并跟踪成本。"""
    response = await router.acompletion(
        model=model_group,
        messages=[{"role": "user", "content": prompt}],
    )

    # 跟踪成本
    usage = response["usage"]
    cost_tracker.track_call(
        model=model_group,
        input_tokens=usage["prompt_tokens"],
        output_tokens=usage["completion_tokens"],
    )

    return response
```

### 3.4 模型级联实现

```python
# model_cascade.py — 模型级联路由器
from typing import Optional
import asyncio

class ModelCascade:
    """模型级联：先用便宜模型，按需升级。"""

    def __init__(self, router, cost_tracker):
        self.router = router
        self.cost_tracker = cost_tracker
        self.tiers = [
            {"name": "cheap", "models": ["gpt-4o-mini", "claude-haiku"], "max_retries": 1},
            {"name": "medium", "models": ["gpt-4o", "claude-sonnet"], "max_retries": 1},
        ]

    async def query(
        self,
        prompt: str,
        system_prompt: str = "",
        min_quality: str = "cheap",
        confidence_threshold: float = 0.8,
    ) -> dict:
        """
        级联查询：从便宜模型开始，如果需要高质量则升级。

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            min_quality: 最低质量要求 (cheap/medium)
            confidence_threshold: 置信度阈值，低于此值则升级
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 决定从哪个层级开始
        start_tier = 0 if min_quality == "cheap" else 1

        for tier_idx in range(start_tier, len(self.tiers)):
            tier = self.tiers[tier_idx]

            for model in tier["models"]:
                try:
                    response = await self.router.acompletion(
                        model=model,
                        messages=messages,
                    )

                    # 跟踪成本
                    usage = response["usage"]
                    self.cost_tracker.track_call(
                        model=model,
                        input_tokens=usage["prompt_tokens"],
                        output_tokens=usage["completion_tokens"],
                    )

                    content = response["choices"][0]["message"]["content"]

                    # 检查是否需要在当前层级重试
                    if tier_idx == 0:
                        # 简单评估：检查回答是否合理
                        if self._check_confidence(content) >= confidence_threshold:
                            return {
                                "content": content,
                                "model": model,
                                "tier": tier["name"],
                                "cost": self.cost_tracker.calls[-1]["cost"],
                            }
                    else:
                        # 高质量模型的回答直接返回
                        return {
                            "content": content,
                            "model": model,
                            "tier": tier["name"],
                            "cost": self.cost_tracker.calls[-1]["cost"],
                        }

                except Exception as e:
                    print(f"模型 {model} 调用失败: {e}")
                    continue

        return {"error": "所有模型调用失败"}

    def _check_confidence(self, content: str) -> float:
        """简单评估回答质量。"""
        # 启发式评估：长度、完整性等
        if len(content) < 10:
            return 0.3
        if "我不确定" in content or "我不知道" in content:
            return 0.4
        if "?" in content or "?" in content:
            return 0.5
        return 0.85  # 默认认为质量足够


# 使用示例
async def example():
    cascade = ModelCascade(router, cost_tracker)

    # 简单问题走便宜模型
    result = await cascade.query("什么是 Python 列表推导式？")
    print(f"模型: {result['model']}, 层级: {result['tier']}")
    print(f"成本: ${result['cost']:.6f}")

    # 复杂问题自动升级到高质量模型
    result = await cascade.query(
        "解释 Transformer 架构中的多头注意力机制实现细节",
        min_quality="medium",
    )
    print(f"模型: {result['model']}, 层级: {result['tier']}")
```

### 3.5 语义缓存实现

```python
# semantic_cache.py — 语义缓存
import numpy as np
from typing import Optional
import json
import hashlib

class SemanticCache:
    """基于嵌入向量的语义缓存。"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", similarity_threshold: float = 0.92):
        import redis
        self.client = redis.from_url(redis_url)
        self.similarity_threshold = similarity_threshold

    def _get_embedding(self, text: str) -> list[float]:
        """获取文本的嵌入向量 (使用 OpenAI Embedding API)。"""
        import openai
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """计算余弦相似度。"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _cache_key(self, prefix: str, query: str) -> str:
        return f"semantic_cache:{prefix}:{hashlib.md5(query.encode()).hexdigest()}"

    def get(self, query: str, prefix: str = "default") -> Optional[str]:
        """查找语义相似的缓存结果。"""
        query_emb = self._get_embedding(query)
        cache_key = self._cache_key(prefix, query)

        # 检查精确匹配
        exact = self.client.get(f"{cache_key}:exact")
        if exact:
            return json.loads(exact)

        # 搜索最近的缓存条目
        cursor = 0
        best_similarity = 0
        best_result = None

        while True:
            cursor, keys = self.client.scan(cursor, match=f"semantic_cache:{prefix}:*:exact")
            for key in keys:
                cached_data = json.loads(self.client.get(key))
                if "embedding" in cached_data:
                    sim = self._cosine_similarity(query_emb, cached_data["embedding"])
                    if sim > best_similarity:
                        best_similarity = sim
                        best_result = cached_data.get("result")

            if cursor == 0:
                break

        if best_similarity >= self.similarity_threshold:
            return best_result

        return None

    def set(self, query: str, result: str, prefix: str = "default"):
        """缓存查询结果。"""
        embedding = self._get_embedding(query)
        cache_key = self._cache_key(prefix, query)

        cache_entry = {
            "query": query,
            "result": result,
            "embedding": embedding,
            "timestamp": __import__("time").time(),
        }

        self.client.setex(
            f"{cache_key}:exact",
            86400,  # 24 小时过期
            json.dumps(cache_entry),
        )

    def get_stats(self) -> dict:
        """获取缓存统计。"""
        cursor = 0
        count = 0
        while True:
            cursor, keys = self.client.scan(cursor, match="semantic_cache:*:exact")
            count += len(keys)
            if cursor == 0:
                break
        return {"cached_entries": count}


# 简化版：精确缓存
class ExactCache:
    """精确匹配缓存（更快、更省）。"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        import redis
        self.client = redis.from_url(redis_url)

    def get(self, model: str, messages_hash: str) -> Optional[str]:
        """获取缓存的 LLM 响应。"""
        key = f"llm_cache:{model}:{messages_hash}"
        result = self.client.get(key)
        return result.decode() if result else None

    def set(self, model: str, messages_hash: str, response: str, ttl: int = 3600):
        """缓存 LLM 响应。"""
        key = f"llm_cache:{model}:{messages_hash}"
        self.client.setex(key, ttl, response)

    def compute_hash(self, messages: list[dict]) -> str:
        """计算消息的哈希值（用于精确匹配）。"""
        serialized = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()


# 带缓存的 LLM 调用
async def cached_llm_call(prompt: str, cache: SemanticCache, router) -> dict:
    """带语义缓存的 LLM 调用。"""
    # 尝试从缓存获取
    cached = cache.get(prompt)
    if cached:
        return {"content": cached, "from_cache": True, "cost": 0}

    # 调用 LLM
    response = await router.acompletion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    content = response["choices"][0]["message"]["content"]

    # 存入缓存
    cache.set(prompt, content)

    return {"content": content, "from_cache": False, "cost": 0.001}
```

### 3.6 预算告警系统

```python
# budget_alerts.py — 预算告警系统
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Optional
import json

class BudgetAlertSystem:
    """预算告警系统：当成本超过阈值时发送通知。"""

    def __init__(self, cost_tracker, redis_url: str = "redis://localhost:6379/0"):
        import redis
        self.cost_tracker = cost_tracker
        self.client = redis.from_url(redis_url)
        self.alert_configs = []

    def add_alert(self, name: str, threshold: float, period: str = "daily"):
        """添加告警规则。"""
        rule = {
            "name": name,
            "threshold": threshold,
            "period": period,  # "daily" or "monthly"
        }
        self.alert_configs.append(rule)
        key = f"alert:{name}:last_sent"
        self.client.set(key, "0")

    def check_alerts(self):
        """检查所有告警规则。"""
        for rule in self.alert_configs:
            if rule["period"] == "daily":
                current = self.cost_tracker.get_daily_cost()
            else:
                current = self.cost_tracker.get_monthly_cost()

            if current >= rule["threshold"]:
                self._send_alert(rule["name"], current, rule["threshold"])

    def _send_alert(self, name: str, current: float, threshold: float):
        """发送告警通知（示例：打印日志，实际可集成邮件/钉钉/企业微信）。"""
        key = f"alert:{name}:last_sent"
        last_sent = float(self.client.get(key) or 0)
        now = datetime.utcnow().timestamp()

        # 每小时最多发送一次相同告警
        if now - last_sent < 3600:
            return

        self.client.set(key, str(now))

        message = f"[告警] {name}: 当前成本 ${current:.2f} 已超过阈值 ${threshold:.2f}"
        print(message)

        # 实际项目中集成通知渠道
        # self._send_email(message)
        # self._send_dingtalk(message)
        # self._send_wechat(message)

    def get_cost_summary(self) -> str:
        """获取成本摘要（可用于 Dashboard 展示）。"""
        report = self.cost_tracker.get_report()
        summary = f"""
=== 成本摘要 ===
总调用次数: {report['total_calls']}
总成本: ${report['total_cost']:.4f}
今日成本: ${report['daily_cost']:.4f}
本月成本: ${report['monthly_cost']:.4f}
总 Token 数: {report['total_tokens']:,}

按模型统计:
"""
        for model, stats in report["by_model"].items():
            summary += f"  {model}: {stats['calls']} 次, ${stats['cost']:.4f}, {stats['tokens']:,} Tokens\n"

        return summary
```

### 3.7 Agent 成本控制完整示例

```python
# cost_controlled_agent.py — 带成本控制的 Agent
import asyncio
from datetime import datetime
from typing import Optional

class CostControlledAgent:
    """集成了成本控制和限流的 Agent。"""

    def __init__(
        self,
        router,
        cost_tracker,
        rate_limiter,
        cache: Optional[SemanticCache] = None,
        daily_budget: float = 10.0,
        max_tokens_per_hour: int = 500000,
    ):
        self.router = router
        self.cost_tracker = cost_tracker
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.daily_budget = daily_budget
        self.max_tokens_per_hour = max_tokens_per_hour

    async def query(self, prompt: str, user_id: str = "anonymous") -> dict:
        """执行一次带成本控制的查询。"""
        # 1. 检查预算
        if self.cost_tracker.get_daily_cost() >= self.daily_budget:
            return {
                "error": "今日预算已用完",
                "daily_cost": self.cost_tracker.get_daily_cost(),
                "budget": self.daily_budget,
            }

        # 2. 检查 Token 限流
        allowed, info = self.rate_limiter.check_rate_by_token(
            token_count=500,  # 预估 Token 数
            max_tokens=self.max_tokens_per_hour,
            user_id=user_id,
        )
        if not allowed:
            return {"error": "Token 用量超限", "rate_info": info}

        # 3. 尝试缓存
        if self.cache:
            cached = self.cache.get(prompt)
            if cached:
                return {"content": cached, "from_cache": True, "cost": 0}

        # 4. 调用 LLM（使用模型级联）
        cascade = ModelCascade(self.router, self.cost_tracker)
        result = await cascade.query(prompt)

        if "error" not in result and self.cache:
            self.cache.set(prompt, result["content"])

        return result


# 启动完整系统
async def main():
    import os

    # 初始化组件
    from litellm import Router
    router = Router(model_list=model_list)

    cost_tracker = CostTracker()
    cost_tracker.set_budgets(daily=10.0, monthly=200.0)

    rate_limiter = SlidingWindowRateLimiter()
    cache = SemanticCache()

    agent = CostControlledAgent(
        router=router,
        cost_tracker=cost_tracker,
        rate_limiter=rate_limiter,
        cache=cache,
        daily_budget=10.0,
    )

    # 执行查询
    result = await agent.query("什么是 K8s 中的 Pod？")
    print(f"结果: {result.get('content', result.get('error', '未知'))}")
    print(f"缓存: {result.get('from_cache', False)}")
    print(f"成本: ${result.get('cost', 0):.6f}")

    # 打印报告
    print(cost_tracker.get_report())

asyncio.run(main())
```

## 4. 最佳实践

### 4.1 分层成本控制

1. **请求级别**：限制单次调用的 Token 上限
2. **用户级别**：每个用户的日/月预算限制
3. **应用级别**：应用的总预算控制
4. **全局级别**：跨应用的全局预算熔断

### 4.2 缓存策略

1. **精确缓存优先**：最便宜，最可靠
2. **语义缓存辅助**：覆盖语义相似但表述不同的查询
3. **短 TTL**：缓存结果设置合理的过期时间
4. **分级缓存**：热门缓存（1h）、普通缓存（1d）、冷数据（7d）

### 4.3 限流策略

1. **分层限流**：API 级别、用户级别、功能级别
2. **渐进式限流**：先告警、再限速、最后熔断
3. **排队机制**：超出限制的请求排队等待而非直接拒绝
4. **优先级队列**：付费用户高优先级

### 4.4 成本监控

1. **实时跟踪**：每次 LLM 调用记录成本
2. **日/周/月报告**：定期成本分析
3. **异常检测**：成本突增告警
4. **成本归因**：按用户、功能、模型分摊成本

## 5. 常见陷阱

### 5.1 只关注模型价格忽略 Token 消耗

便宜模型可能因为需要更多重试而总成本更高。

### 5.2 缓存过期时间设置不合理

缓存时间过短则命中率低，过长则影响回答新鲜度。

### 5.3 限流阈值设置过高

限流不生效而导致 API 费用超出预算。

### 5.4 忽视上下文积累

对话式 Agent 的上下文不断增长，单次调用的 Token 消耗持续增加。

### 5.5 模型级联导致延迟增加

级联策略在等待便宜模型失败后才调用贵模型，增加了用户等待时间。

## 6. API Key 依赖

| 组件 | 需要 Key | 说明 |
|------|---------|------|
| OpenAI | 需要 | LLM 调用 |
| Anthropic | 需要 | LLM 调用 |
| Redis | 不需要 | 本地部署 |
| LiteLLM | 不需要 | 代理层 |
| 语义缓存 (Embedding) | 需要 OpenAI | 生成嵌入向量 |

## 7. 技术关系

- **上层**：Agent 业务逻辑 -> 调用方
- **本层**：限流 + 缓存 + 模型路由 -> 成本控制层
- **下层**：LLM API + Redis -> 基础设施
- **监控**：成本跟踪器 + 告警 -> 可见性
- **工具**：LiteLLM / tiktoken -> 代理和计数

## 8. 验收清单

- [ ] 理解 Token 计费模型和各模型定价
- [ ] 掌握 tiktoken 进行 Token 计数
- [ ] 实现 Redis 滑动窗口限流器
- [ ] 理解语义缓存的工作原理
- [ ] 实现带缓存的 LLM 调用
- [ ] 掌握 LiteLLM 代理的配置和成本跟踪
- [ ] 实现模型级联策略
- [ ] 配置预算告警系统
- [ ] 实现完整的 Agent 成本控制
- [ ] 理解模型级联和限流的 trade-off

## 9. 学习资源

- LiteLLM 文档：https://docs.litellm.ai
- tiktoken 使用指南：https://github.com/openai/tiktoken
- Redis 限流模式：https://redis.io/glossary/rate-limiting
- OpenAI Tokenizer 可视化：https://platform.openai.com/tokenizer
- 语义缓存论文：https://arxiv.org/abs/2105.03075
- 模型级联研究：https://arxiv.org/abs/2308.11796
