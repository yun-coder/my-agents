"""
Demo: Instructor + Langfuse OpenAI wrapper.

Instructor patches an OpenAI-compatible client to return structured Pydantic
objects. The Langfuse docs recommend patching the Langfuse OpenAI wrapper so
the structured-output call is still observed automatically.

Required for a real call:
    pip install instructor pydantic openai langfuse
    set OPENAI_API_KEY=...
"""

from __future__ import annotations

import os

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    if not os.environ.get("OPENAI_API_KEY"):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="instructor-demo-skipped",
            input={"reason": "OPENAI_API_KEY is not set"},
            metadata={"integration": "instructor.patch(langfuse.openai.OpenAI())"},
        ) as span:
            span.update(output={"next_step": "Install Instructor packages and set OPENAI_API_KEY."})
        flush_and_print(langfuse, "instructor-openai-way-demo-skipped")
        return

    import instructor
    from langfuse.openai import OpenAI
    from pydantic import BaseModel

    class WeatherDetail(BaseModel):
        city: str
        temperature_celsius: int

    client = instructor.patch(OpenAI())

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=WeatherDetail,
        messages=[
            {"role": "user", "content": "The weather in Paris is 18 degrees Celsius."},
        ],
    )
    print(response.model_dump_json(indent=2))

    flush_and_print(langfuse, "instructor-openai-way-demo")


if __name__ == "__main__":
    main()
