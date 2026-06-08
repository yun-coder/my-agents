"""结构化输出：使用 Instructor 强制 LLM 输出符合 Pydantic Schema 的数据。"""

from __future__ import annotations

import instructor
from pydantic import BaseModel

from .client import get_llm_client


def extract_structured(
    prompt: str,
    response_model: type[BaseModel],
    *,
    system: str = "你是一个精确的信息提取专家。",
) -> BaseModel:
    """从自然语言文本中提取结构化信息。

    用法:
        class Person(BaseModel):
            name: str
            age: int

        result = extract_structured("张三今年25岁", Person)
        assert isinstance(result, Person)
    """
    client = get_llm_client()
    instructor_client = instructor.from_openai(client._client)

    return instructor_client.chat.completions.create(
        model=client.model,
        response_model=response_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )


def extract_structured_with_retry(
    prompt: str,
    response_model: type[BaseModel],
    *,
    max_retries: int = 3,
    system: str = "你是一个精确的信息提取专家。",
) -> BaseModel:
    """带重试的结构化提取。Instructor 内部会处理校验失败重试。"""
    client = get_llm_client()
    instructor_client = instructor.from_openai(client._client)

    return instructor_client.chat.completions.create(
        model=client.model,
        response_model=response_model,
        max_retries=max_retries,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
