"""离线可运行：比较基础 Prompt 与工程化 Prompt。"""

from __future__ import annotations

from textwrap import dedent


def build_basic_prompt(review: str) -> str:
    return f"分析评价：{review}"


def build_engineered_prompt(review: str) -> str:
    """把角色、任务、边界、输出格式和外部输入明确分区。"""

    return dedent(
        f"""
        你是电商评论分析助手。

        任务：
        1. 判断评论情感：positive、neutral 或 negative。
        2. 提取最多 3 个明确提到的产品方面。
        3. 如果信息不足，不要猜测。

        输出要求：
        - 使用简洁中文。
        - 按“情感 / 方面 / 理由”三行输出。

        <review>
        {review}
        </review>
        """
    ).strip()


def main() -> None:
    review = "耳机佩戴很舒服，降噪也不错，但切换设备有点慢。"
    print("=== 基础版 ===")
    print(build_basic_prompt(review))
    print("\n=== 工程化版本 ===")
    print(build_engineered_prompt(review))


if __name__ == "__main__":
    main()
