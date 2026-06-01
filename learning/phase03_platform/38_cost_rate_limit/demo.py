"""Token 成本估算、预算检查与滑动窗口限流。"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class Price:
    """每百万 Token 的可配置价格。"""

    input_per_million: float  # 输入 Token 单价。
    output_per_million: float  # 输出 Token 单价。


@dataclass(frozen=True)
class Usage:
    """一次模型调用的 Token 用量。"""

    input_tokens: int  # 输入 Token 数量。
    output_tokens: int  # 输出 Token 数量。


def estimate_cost(price: Price, usage: Usage) -> float:
    """估算一次模型调用费用。"""

    cost = usage.input_tokens * price.input_per_million / 1_000_000
    cost += usage.output_tokens * price.output_per_million / 1_000_000
    return round(cost, 6)


class SlidingWindowLimiter:
    """按租户记录请求时间的教学级滑动窗口限流器。"""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit  # 单个窗口允许的请求数量。
        self.window_seconds = window_seconds  # 窗口长度。
        self.events: dict[str, deque[float]] = defaultdict(deque)  # 每个租户的请求时间。

    def allow(self, tenant_id: str, now: float) -> bool:
        events = self.events[tenant_id]
        while events and events[0] <= now - self.window_seconds:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True


def main() -> None:
    price = Price(input_per_million=0.25, output_per_million=2.0)
    usage = Usage(input_tokens=1500, output_tokens=300)
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    allowed = [limiter.allow("tenant-a", now) for now in (0.0, 10.0, 20.0, 61.0)]
    print(json.dumps({"price": asdict(price), "usage": asdict(usage), "estimated_cost": estimate_cost(price, usage), "allowed": allowed}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
