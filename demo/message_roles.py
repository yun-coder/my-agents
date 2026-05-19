from pathlib import Path
from openai import OpenAI
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

def main()->None:
    config = load_config()
    client = create_client(config)
    model = config["openai"]["model"]
    # prompt_path = Path(__file__).resolve().parent.parent / "assets" / "prompt.txt"
    # with prompt_path.open("r", encoding="utf-8") as f:
    #     instructions = f.read()


    prompt_path = Path(__file__).resolve().parent.parent / "assets" / "prompt2.txt"
    with prompt_path.open("r", encoding="utf-8") as f:
        instructions = f.read()

    response = client.responses.create(
        model=model,
        reasoning={"effort":"low"},
        # instructions 参数为模型提供生成响应时的高级指令，包括语气、目标和正确响应示例
        # 第一版
        # instructions='你是一个专业的娱乐主持人',
        # input='说一个冷笑话'
        # 给你来个超冷的：有个人掉进井里，后来他就井（精）神了。


        # 第二版：区别在于可以输入数组，每个元素包含一个角色和内容，模型会根据不同角色的内容来生成响应
        # input=[
        #     {
        #         "role": "system",
        #         "content": "你是一个专业的娱乐主持人"
        #     },
        #     {
        #         "role": "user",
        #         "content": "说一个冷笑话"
        #     }
        # ]

        # 第三版：使用文件读取 第一次读取会出现错误，不是自己的名字，而是模型自己生成的名字，第二次读取就正常了
        # instructions=instructions,
        # input="How do I declare a string variable for a first name?"


        # 第四版 [重点关注] Few-shot learning
        instructions=instructions,
        # 我今天买的这款耳机怎么样?
        input="What do you think of the headphones I bought today?"

    )
    print(response.output_text)


if __name__ == "__main__":
    main()
