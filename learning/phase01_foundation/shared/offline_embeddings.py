"""用于教学的确定性离线稀疏向量，不用于生产语义检索。"""

from __future__ import annotations

import math
import re
from collections import Counter

ASCII_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
CHINESE_SEQUENCE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """提取英文单词，并把连续中文拆成单字与双字组合。

    中文通常没有空格。如果把整句话当作一个 token，稍微换一种说法就无法
    召回。这里用单字与双字组合改善教学 Demo 的词法匹配效果。它仍然不理解
    同义词和上下文，因此不能代替真正的 Embedding 模型。
    """

    normalized = text.lower()
    tokens = ASCII_TOKEN_PATTERN.findall(normalized)
    for sequence in CHINESE_SEQUENCE_PATTERN.findall(normalized):
        tokens.extend(sequence)
        tokens.extend(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return tokens


def bag_of_words(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    vocabulary = left.keys() | right.keys()
    numerator = sum(left[token] * right[token] for token in vocabulary)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)
