"""离线可运行：教学用内存向量数据库。"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.offline_embeddings import bag_of_words, cosine_similarity  # noqa: E402


@dataclass(frozen=True)
class Record:
    # record_id：向量库中的唯一标识，用于更新、删除和追踪来源。
    record_id: str
    # text：原始文本。生产系统也可以只存外部文档定位信息。
    text: str
    # metadata：过滤条件，例如租户、文档类型、权限范围。
    metadata: dict[str, str]


class InMemoryVectorStore:
    def __init__(self) -> None:
        # 教学版在写入时完成“向量化”，模拟真实向量库保存向量的行为。
        self._records: list[tuple[Record, Counter[str]]] = []

    def add(self, record: Record) -> None:
        self._records.append((record, bag_of_words(record.text)))

    def query(
        self,
        # text：用户查询文本，进入检索前也要转换成向量。
        text: str,
        # top_k：最多返回多少条候选记录。
        top_k: int = 3,
        # where：元数据过滤条件。真实系统应先按租户和权限过滤。
        where: dict[str, str] | None = None,
    ) -> list[tuple[float, Record]]:
        query_vector = bag_of_words(text)
        candidates = self._records
        if where:
            candidates = [
                (record, vector)
                for record, vector in candidates
                if all(record.metadata.get(key) == value for key, value in where.items())
            ]
        scored = [
            (cosine_similarity(query_vector, vector), record)
            for record, vector in candidates
        ]
        # 过滤完全不相关的结果，避免把零相关文档交给后续生成步骤。
        relevant = [item for item in scored if item[0] > 0]
        return sorted(relevant, key=lambda item: item[0], reverse=True)[:top_k]


def main() -> None:
    store = InMemoryVectorStore()
    store.add(Record("1", "Python 列表推导式用于创建列表。", {"tenant": "demo"}))
    store.add(Record("2", "FastAPI 可以创建 REST API。", {"tenant": "demo"}))
    store.add(Record("3", "另一个租户的内部文档。", {"tenant": "private"}))

    for score, record in store.query("Python 怎么创建列表？", where={"tenant": "demo"}):
        print(f"{score:.3f}  {record.record_id}  {record.text}")


if __name__ == "__main__":
    main()
