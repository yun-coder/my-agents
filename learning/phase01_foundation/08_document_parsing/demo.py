"""离线可运行：多格式文档解析与简单分块。"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_document(path: Path) -> str:
    """根据文件扩展名选择解析器，并统一返回纯文本。"""

    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if suffix == ".docx":
        from docx import Document

        return "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    raise ValueError(f"暂不支持的文件格式：{suffix}")


def split_text(text: str, max_chars: int = 120) -> list[str]:
    """按非空行累计文本块；max_chars 是教学用近似上限。"""

    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def main() -> None:
    default_path = Path(__file__).with_name("sample.md")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=default_path,
        help="待解析文件路径，支持 .md、.txt、.pdf 和 .docx。",
    )
    args = parser.parse_args()

    for index, chunk in enumerate(split_text(parse_document(args.path)), start=1):
        print(f"--- chunk {index} | source={args.path.name} ---")
        print(chunk)


if __name__ == "__main__":
    main()
