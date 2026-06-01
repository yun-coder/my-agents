"""使用 Pydantic 定义 Agent 结构化输出边界。"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field


class TicketTriage(BaseModel):
    """客服 Agent 返回的结构化分类结果。"""

    category: Literal["billing", "technical", "general"]  # 工单分类。
    priority: int = Field(ge=1, le=5)  # 优先级，1 最低，5 最高。
    summary: str = Field(min_length=1, max_length=120)  # 面向客服的摘要。
    needs_human: bool  # 是否需要人工客服继续处理。


def main() -> None:
    result = TicketTriage(
        category="technical",
        priority=4,
        summary="用户无法恢复已暂停的 Agent 工作流",
        needs_human=True,
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
