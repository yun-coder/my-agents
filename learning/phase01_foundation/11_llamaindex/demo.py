"""默认展示流程；传入 --online 使用 LlamaIndex 构建最小索引。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from openai import BadRequestError, NotFoundError  # noqa: E402

from shared.config import get_openai_settings  # noqa: E402


def run_online() -> None:
    try:
        from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
    except ImportError:
        print("缺少 LlamaIndex OpenAI 集成，请按阶段 README 安装依赖。")
        return

    settings = get_openai_settings()
    # Settings.llm：查询阶段用于生成最终答案的文本模型。
    Settings.llm = OpenAI(
        model=settings.model,
        api_key=settings.api_key,
        api_base=settings.base_url,
    )
    # Settings.embed_model：建索引和检索阶段使用的向量化模型。
    Settings.embed_model = OpenAIEmbedding(
        # model_name 支持第三方兼容服务自定义的 Embedding 模型 ID。
        # 如果使用 model=，LlamaIndex 会先按内置 OpenAI 模型枚举校验。
        model_name=settings.embedding_model,
        api_key=settings.api_key,
        api_base=settings.base_url,
    )

    # documents：由目录读取器生成的文档对象列表。
    documents = SimpleDirectoryReader(str(Path(__file__).with_name("data"))).load_data()
    # index：将文档切分并向量化后的内存索引。
    try:
        index = VectorStoreIndex.from_documents(documents)
    except (BadRequestError, NotFoundError) as exc:
        raise RuntimeError(
            "LlamaIndex 建索引失败：请确认兼容端点支持 /embeddings，"
            "并检查 dev.json 中的 openai.embedding_model。"
        ) from exc
    # query_engine：封装检索与生成步骤的查询入口。
    response = index.as_query_engine().query("Agent 由哪些部分组成？")
    print(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--online",
        action="store_true",
        help="读取 dev.json，调用在线 Embedding 和文本生成模型。",
    )
    args = parser.parse_args()
    if not args.online:
        print("SimpleDirectoryReader -> Documents -> VectorStoreIndex -> Query Engine")
        print("使用 --online 执行真实索引构建。")
        return
    try:
        run_online()
    except RuntimeError as exc:
        print(exc)


if __name__ == "__main__":
    main()
