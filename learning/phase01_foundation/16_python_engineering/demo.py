"""离线可运行：检查共享配置结构，但不输出任何密钥。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import load_dev_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    config = load_dev_config()
    openai_config = config.get("openai", {})
    logger.info("已读取 dev.json。")
    # 只打印密钥是否存在，不打印真实值。
    logger.info("openai.api_key 已配置：%s", bool(openai_config.get("api_key")))
    logger.info("openai.base_url：%s", openai_config.get("base_url", "<missing>"))
    logger.info("openai.model：%s", openai_config.get("model", "<missing>"))


if __name__ == "__main__":
    main()
