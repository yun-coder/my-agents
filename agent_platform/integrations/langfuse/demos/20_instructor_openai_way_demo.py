"""
演示 20: Instructor + Langfuse OpenAI 包装器方式。

Instructor 通过 monkey-patch OpenAI 兼容客户端来返回结构化的
Pydantic 对象。Langfuse 文档建议对 Langfuse OpenAI 包装器
进行 patch，这样结构化输出调用仍然会被自动观测。

实际调用所需依赖：
    pip install instructor pydantic openai langfuse
    设置环境变量 OPENAI_API_KEY=...
"""

from __future__ import annotations

import os

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 未设置 API Key 时跳过实际调用
    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="instructor-demo-skipped",
            input={"reason": "OPENAI_API_KEY 未设置"},
            metadata={"integration": "instructor.patch(langfuse.openai.OpenAI())"},
        ) as span:
            span.update(output={"next_step": "安装 Instructor 相关包并设置 OPENAI_API_KEY。"})
        flush_and_print(langfuse, "instructor-openai-way-demo-skipped")
        return

    import instructor
    from langfuse.openai import OpenAI               # 使用 Langfuse 包装版 OpenAI
    from pydantic import BaseModel

    # 定义 Pydantic 数据模型，用于结构化输出
    class WeatherDetail(BaseModel):
        city: str                                    # 城市
        temperature_celsius: int                     # 摄氏温度

    # 关键步骤：用 instructor 包装 Langfuse OpenAI 客户端
    # 这样 Langfuse 仍然能自动观测，同时 Instructor 提供结构化输出
    client = instructor.patch(OpenAI())

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=WeatherDetail,                # 指定响应模型，Instructor 自动解析
        messages=[
            {"role": "user", "content": "巴黎的天气是 18 摄氏度。"},
        ],
    )
    print(response.model_dump_json(indent=2))

    flush_and_print(langfuse, "instructor-openai-way-demo")


if __name__ == "__main__":
    main()
