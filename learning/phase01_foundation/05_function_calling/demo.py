"""默认离线演示工具执行；传入 --online 运行 Responses API 工具循环。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import get_openai_settings  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402

WEATHER_TOOL = {
    # type=function：声明这是由应用程序负责执行的自定义函数工具。
    "type": "function",
    # name：模型返回 function_call 时会使用这个稳定名称。
    "name": "get_weather",
    # description：帮助模型判断何时应调用工具。
    "description": "查询指定城市的演示天气。",
    # parameters：工具入参的 JSON Schema。
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名，例如 北京"},
        },
        "required": ["city"],
        "additionalProperties": False,
    },
    # strict=True：让模型严格生成符合参数 Schema 的 JSON。
    "strict": True,
}


def get_weather(city: str) -> dict[str, Any]:
    demo_data = {
        "北京": {"temperature_c": 26, "condition": "晴"},
        "上海": {"temperature_c": 24, "condition": "多云"},
    }
    return demo_data.get(city, {"temperature_c": None, "condition": "暂无演示数据"})


def execute_tool(name: str, arguments_json: str) -> str:
    arguments = json.loads(arguments_json)
    if name != "get_weather":
        raise ValueError(f"不允许执行未知工具：{name}")
    city = arguments.get("city")
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city 必须是非空字符串。")
    return json.dumps(get_weather(city.strip()), ensure_ascii=False)


def run_offline() -> None:
    print(execute_tool("get_weather", '{"city": "北京"}'))


def run_online() -> None:
    settings = get_openai_settings()
    client = create_openai_client(settings)
    # conversation：由应用显式维护的请求项列表。
    # 这种方式不依赖兼容端点保存 previous_response_id 对应的服务端状态。
    conversation = [
        {"role": "user", "content": "北京今天天气怎么样？"},
    ]
    response = client.responses.create(
        # 第一次请求把工具定义交给模型，由模型决定是否发起 function_call。
        model=settings.model,
        tools=[WEATHER_TOOL],
        input=conversation,
    )
    outputs = []
    for item in response.output:
        if item.type == "function_call":
            outputs.append(
                {
                    # function_call_output：应用执行工具后回传给模型的结果类型。
                    "type": "function_call_output",
                    # call_id：将工具结果与模型之前提出的调用请求关联起来。
                    "call_id": item.call_id,
                    # output：本地函数执行结果。这里序列化为 JSON 字符串。
                    "output": execute_tool(item.name, item.arguments),
                }
            )
    if not outputs:
        print(response.output_text)
        return

    # 把模型提出的 function_call 与应用执行结果显式追加到下一轮输入。
    conversation.extend(response.output)
    conversation.extend(outputs)
    final_response = client.responses.create(
        model=settings.model,
        tools=[WEATHER_TOOL],
        input=conversation,
    )
    print(final_response.output_text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args()
    (run_online if args.online else run_offline)()


if __name__ == "__main__":
    main()
