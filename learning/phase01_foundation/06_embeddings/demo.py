"""默认离线相似度；传入 --online 调用 OpenAI 兼容 embeddings 端点。"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from openai import BadRequestError, NotFoundError  # noqa: E402

from shared.config import get_openai_settings  # noqa: E402
from shared.offline_embeddings import bag_of_words, cosine_similarity  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402

DOCUMENTS = [
    "Python 列表推导式可以简洁地创建列表。",
    "向量数据库用于保存和检索 Embedding。",
    "FastAPI 可以把 Python 函数封装成 HTTP API。",
]
QUERY = "如何使用 Python 创建列表？"


def dense_cosine(left: list[float], right: list[float]) -> float:
    """计算两个稠密向量的余弦相似度，数值越大通常表示方向越接近。"""

    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm)


def run_offline() -> None:
    query_vector = bag_of_words(QUERY)
    scores = [
        (cosine_similarity(query_vector, bag_of_words(document)), document)
        for document in DOCUMENTS
    ]
    for score, document in sorted(scores, reverse=True):
        print(f"{score:.3f}  {document}")


def run_online() -> None:
    settings = get_openai_settings()
    client = create_openai_client(settings)
    try:
        result = client.embeddings.create(
            # model：dev.json 中的向量化模型 ID，不是文本生成模型。
            model=settings.embedding_model,
            # input：批量提交查询和候选文档，减少 API 往返次数。
            input=[QUERY, *DOCUMENTS],
        )
    except (BadRequestError, NotFoundError) as exc:
        raise RuntimeError(
            "Embeddings 调用失败：当前兼容端点可能未实现 /embeddings，"
            "或 dev.json 中的 openai.embedding_model 不可用。"
        ) from exc
    # 返回顺序与 input 一致：第 0 条是查询向量，其余是文档向量。
    query_vector = result.data[0].embedding
    scores = [
        (dense_cosine(query_vector, item.embedding), document)
        for item, document in zip(result.data[1:], DOCUMENTS, strict=True)
    ]
    for score, document in sorted(scores, reverse=True):
        print(f"{score:.3f}  {document}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args()
    try:
        (run_online if args.online else run_offline)()
    except RuntimeError as exc:
        print(exc)


if __name__ == "__main__":
    main()
