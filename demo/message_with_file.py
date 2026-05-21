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


def main() -> None:
    config = load_config()
    client = create_client(config)
    model = config["openai"]["model"]

    # 分析图像内容
    # response = client.responses.create(
    #     model=model,
    #     input=[
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "input_text",
    #                     "text": "What teams are playing in this image?",
    #                 },
    #                 {
    #                     "type": "input_image",
    #                     "image_url": "https://api.nga.gov/iiif/a2e6da57-3cd1-4235-b20e-95dcaefed6c8/full/!800,800/0/default.jpg",
    #                 },
    #             ],
    #         }
    #     ],
    # )

    # Use a file URL as input
    # response = client.responses.create(
    #     model=model,
    #     input=[
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "input_text",
    #                     "text": "Analyze the letter and provide a summary of the key points.use chinese.",
    #                 },
    #                 {
    #                     "type": "input_file",
    #                     "file_url": "https://www.berkshirehathaway.com/letters/2024ltr.pdf",
    #                 },
    #             ],
    #         },
    #     ],
    # )

    # Upload a file and use it as input
    # 这里中转的模型不支持文件上传的
    FILE_PATH = Path(__file__).resolve().parent.parent / "assets" / "2024ltr.pdf"
    file = client.files.create(
        file=open(FILE_PATH, "rb"),
        purpose="input",
    )

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": file.id,
                    },
                    {
                        "type": "input_text",
                        "text": "What is the first word in the book?",
                    },
                ],
            }
        ],
    )

    print(response.output_text)


if __name__ == "__main__":
    main()
