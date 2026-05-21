from openai import OpenAI
from pathlib import Path
import json

CONFIG_PATH = Path(__file__).resolve().parent.parent / "dev.json"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def create_client(config: dict) -> OpenAI:
    openai_config = config["openai"]
    return OpenAI(
        api_key=openai_config["api_key"],
        base_url=openai_config["base_url"],
    )


def main() -> None:
    config = load_config()
    client = create_client(config)
    model = config["openai"]["model"]

    # Use web search in a response 网络搜索
    # response = client.responses.create(
    #     model=model,
    #     tools=[
    #         {
    #             "type": "web_search",
    #         }
    #     ],
    #     input="What is the capital of China?",
    # )

    # File Search 文件搜索
    # 这里中转的模型不支持文件功能
    # response = client.responses.create(
    #     model="gpt-5.5",
    #     # 真实存在的向量库 ID，向量库中有关于 OpenAI 深度研究的文件
    #     # tools=[{"type": "file_search", "vector_store_ids": ["vs_my_store_01"]}],
    #     input="What is deep research by OpenAI?",
    # )

    # Function Calling 函数调用
    # response = client.responses.create(
    #     model=model,
    #     tools=[
    #         {
    #             "type": "function",
    #             "name": "get_weather",
    #             "description": "Get current temperature for a given location.",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "location": {
    #                         "type": "string",
    #                         "description": "City and country beijing, china",
    #                     }
    #                 },
    #                 "required": ["location"],
    #                 "additionalProperties": False,
    #             },
    #             "strict": True,
    #         },
    #     ],
    #     input=[
    #         {"role": "user", "content": "What is the weather like in beijing today?"},
    #     ],
    # )
    # print(response.output[0].to_json()) 这里的输出是模型调用工具的结果，模型会根据输入自动调用工具并返回结果

    # {
    #     "arguments": '{"location":"beijing, china"}',
    #     "call_id": "call_dDwCEKh4NkYptfcrWk45or7a",
    #     "name": "get_weather",
    #     "type": "function_call",
    #     "id": "fc_0f37ee32c59c5623006a0dc62cb6208190ad46f0011997eff2",
    #     "status": "completed",
    # }

    response = client.responses.create(
        model=model,
        tools=[
            {
                "type": "mcp",
                "server_label": "dmcp",
                "server_description": "A Dungeons and Dragons MCP server to assist with dice rolling.",
                "server_url": "https://dmcp-server.deno.dev/sse",
                "require_approval": "never",
            },
        ],
        input="Roll 2d4+1",
        # 不是所有骰子都是 6 面的。
        # 在桌面角色扮演游戏里，常用多种类型的骰子：
        # d4：4 面骰
        # d6：6 面骰
        # d8：8 面骰
        # d10：10 面骰
        # d12：12 面骰
        # d20：20 面骰
        # Roll 2d4+1 里用的是 d4，也就是 4 面骰。它表示“掷两个 4 面骰，然后加上 1”。这种记法是 RPG 游戏中的标准骰子表达方式。
    )
    print(response.output_text)


if __name__ == "__main__":
    main()
