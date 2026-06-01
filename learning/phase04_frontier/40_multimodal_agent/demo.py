"""构造 Responses API 的文本 + 图片输入结构。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class MultimodalQuestion:
    """发送给视觉模型的问题。"""

    prompt: str  # 用户希望模型回答的文本问题。
    image_url: str  # 可访问的图片 URL；私有图片应使用受控上传方式。
    detail: str = "auto"  # 图片理解精度提示，例如 auto、low 或 high。


def build_responses_payload(model: str, question: MultimodalQuestion) -> dict[str, object]:
    """生成 OpenAI Responses API 风格的请求体。"""

    return {
        "model": model,  # 必须选择支持视觉输入的模型。
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": question.prompt},
                    {"type": "input_image", "image_url": question.image_url, "detail": question.detail},
                ],
            }
        ],
    }


def main() -> None:
    question = MultimodalQuestion("请描述图片中的主要内容。", "https://example.com/course-diagram.png")
    print(json.dumps({"question": asdict(question), "payload": build_responses_payload("vision-capable-model", question)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
