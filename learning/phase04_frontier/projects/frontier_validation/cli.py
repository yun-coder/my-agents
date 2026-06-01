"""运行阶段四前沿能力验证集。"""

from __future__ import annotations

import json
from pathlib import Path

from core import report


def main() -> None:
    data_path = Path(__file__).with_name("validation_set.json")
    print(json.dumps(report(data_path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
