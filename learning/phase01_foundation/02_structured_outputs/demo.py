"""使用现有 OpenAI 配置：从客服文本抽取结构化工单。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import get_openai_settings  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402

TICKET_SCHEMA = {
    # 根节点是一个 JSON object，表示一张客服工单。
    "type": "object",
    "properties": {
        "category": {
            # category：问题分类，只允许从枚举中选择，避免模型自由创造类别。
            "type": "string",
            "enum": ["refund", "delivery", "product_quality", "other"],
            "description": "工单分类：退款、配送、产品质量或其他问题。",
        },
        "urgency": {
            # urgency：处理优先级，用于后续排队或升级人工客服。
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "处理优先级：低、中、高。",
        },
        "summary": {
            # summary：面向客服人员的简短中文摘要。
            "type": "string",
            "description": "不添加用户未提供信息的中文问题摘要。",
        },
    },
    # required：模型必须返回的字段集合。
    "required": ["category", "urgency", "summary"],
    # 禁止模型返回 Schema 之外的字段，便于下游程序稳定解析。
    "additionalProperties": False,
}


def main() -> None:
    settings = get_openai_settings()
    client = create_openai_client(settings)
    response = client.responses.create(
        # model：根目录 dev.json 中配置的文本生成模型 ID。
        model=settings.model,
        # input：本次需要抽取结构化信息的用户原文。
        input="订单昨天显示已签收，但我完全没有收到。请尽快处理。",
        text={
            "format": {
                # type=json_schema：启用 Structured Outputs，而不是旧式 JSON mode。
                "type": "json_schema",
                # name：本次输出格式的稳定标识，只使用字母、数字、下划线或短横线。
                "name": "support_ticket",
                # strict=True：要求模型遵守 OpenAI 支持的 JSON Schema 子集。
                "strict": True,
                # schema：真正的业务字段契约。
                "schema": TICKET_SCHEMA,
            }
        },
    )
    ticket = json.loads(response.output_text)
    print(json.dumps(ticket, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
