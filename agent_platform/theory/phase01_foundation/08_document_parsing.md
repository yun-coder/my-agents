# 08 文档解析 Document Parsing

> 文档解析是将非结构化文档（PDF、Word、HTML 等）转化为可处理的文本数据的过程。
> 它是 RAG 和知识库系统的第一道关卡——文档解析的质量直接决定了整个系统的上限。

---

## 1. 概念概述

### 1.1 什么是文档解析

文档解析（Document Parsing）是指从各种格式的文档中提取文本内容和元数据的过程。不同于简单的"读取文本"，文档解析需要处理：

- PDF 中的文本提取（包括布局、表格、页眉页脚）
- Word 文档中的段落、列表、样式信息
- HTML 中的内容和结构标签
- 扫描件中的 OCR 文字识别
- 表格结构的识别和提取

### 1.2 为什么需要文档解析

- **知识库构建**：企业知识库中 80% 以上的知识存储在各种文档格式中
- **RAG 数据准备**：向量数据库的输入需要从原始文档中提取的纯净文本
- **信息提取**：文档中的表格、列表、标题结构需要被保留以保持语义
- **多格式统一**：不同来源的文档（PDF、DOCX、网页）需要统一处理

### 1.3 何时使用文档解析

- 构建企业 RAG 系统时导入文档
- 需要从 PDF 报告中提取数据和分析结果
- 批量处理历史文档构建知识库
- 网页抓取后的内容清洗和结构化
- 扫描文档的数字化工

---

## 2. 核心原理

### 2.1 PyMuPDF（fitz）PDF 解析

PyMuPDF 是目前 Python 生态中最快的 PDF 解析库。它基于 MuPDF 渲染引擎，支持提取文本、图片、注释、目录等。

```python
import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> str:
    \"\"\"使用 PyMuPDF 提取 PDF 文本。\"\"\"
    doc = fitz.open(file_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append(f"--- 第 {page_num + 1} 页 ---\\n{text}")

    doc.close()
    return "\\n\\n".join(pages)


def extract_text_with_positions(file_path: str) -> list[dict]:
    \"\"\"提取文本及其位置信息（保留布局）。\"\"\"
    doc = fitz.open(file_path)
    blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # 获取页面上的文本块（包含位置信息）
        page_dict = page.get_text("dict")
        for block in page_dict["blocks"]:
            if block["type"] == 0:  # 文本块
                text = "".join(
                    span["text"]
                    for line in block["lines"]
                    for span in line["spans"]
                )
                if text.strip():
                    blocks.append({
                        "page": page_num + 1,
                        "text": text,
                        "bbox": block["bbox"],  # 边界框 [x0, y0, x1, y1]
                        "font": block["lines"][0]["spans"][0].get("font", "") if block["lines"] else "",
                    })
            elif block["type"] == 1:  # 图片块
                blocks.append({
                    "page": page_num + 1,
                    "type": "image",
                    "bbox": block["bbox"],
                })

    doc.close()
    return blocks
```

**PyMuPDF 的优势**：

- 速度极快（C 底层实现）
- 无需任何外部工具或 API
- 支持提取文本位置信息（保留阅读顺序）
- 支持 PDF 目录/书签提取
- 支持嵌入图片提取
- 纯 Python 绑定，安装简单

**PyMuPDF 的局限性**：

- 对复杂排版的处理有限（多栏文本可能读取顺序错误）
- 不原生支持 OCR
- 表格提取能力较弱

### 2.2 python-docx Word 文档解析

```python
from docx import Document


def extract_from_docx(file_path: str) -> dict:
    \"\"\"从 Word 文档提取文本和样式。\"\"\"
    doc = Document(file_path)

    # 提取段落文本及其样式
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append({
                "text": para.text,
                "style": para.style.name if para.style else "Normal",
                "heading_level": para.style.name.startswith("Heading"),
            })

    # 提取表格
    tables = []
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        tables.append(table_data)

    return {
        "paragraphs": paragraphs,
        "tables": tables,
        "metadata": {
            "sections": len(doc.sections),
            "paragraphs_count": len(doc.paragraphs),
            "tables_count": len(doc.tables),
        },
    }
```

### 2.3 Unstructured 库

Unstructured 是一个强大的文档解析库，支持多种格式的文档解析，并内置了分区（partitioning）功能。

```python
from unstructured.partition.auto import partition


def parse_with_unstructured(file_path: str) -> list[dict]:
    \"\"\"使用 Unstructured 解析文档（自动识别格式）。\"\"\"
    elements = partition(filename=file_path)

    parsed = []
    for element in elements:
        parsed.append({
            "type": type(element).__name__,  # 如 Title, NarrativeText, Table, ListItem
            "text": str(element),
            "metadata": element.metadata.to_dict(),
        })
    return parsed


# 按类型筛选
def filter_elements(elements: list[dict], types: list[str]) -> list[dict]:
    \"\"\"筛选特定类型的元素。\"\"\"
    return [e for e in elements if e["type"] in types]
```

**Unstructured 支持的分区类型**：

- Title/LayoutTitle：标题
- NarrativeText：正文段落
- Table：表格
- ListItem：列表项
- Header/Footer：页眉页脚
- PageBreak：分页符
- FigureCaption：图片说明

### 2.4 Docling

Docling 是 IBM 开发的文档解析框架，特别擅长 PDF 文档的理解，支持 Table Extraction 和 Layout Detection。

```python
from docling.document_converter import DocumentConverter


def parse_with_docling(file_path: str) -> dict:
    \"\"\"使用 Docling 解析文档（强在表格和布局识别）。\"\"\"
    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document

    # 提取 Markdown 格式文本
    markdown_text = doc.export_to_markdown()

    # 提取表格
    tables = []
    for table in doc.tables:
        table_data = []
        for row in table.data:
            table_data.append([cell.text for cell in row])
        tables.append(table_data)

    return {
        "markdown": markdown_text,
        "tables": tables,
        "metadata": {
            "pages": len(doc.pages) if hasattr(doc, "pages") else 0,
        },
    }
```

### 2.5 表格提取

表格提取是文档解析中最困难的挑战之一：

```python
import pandas as pd


class TableExtractor:
    \"\"\"多引擎表格提取器。\"\"\"

    def __init__(self):
        self._tables = []

    def extract_pymupdf(self, pdf_path: str) -> list[pd.DataFrame]:
        \"\"\"使用 PyMuPDF 提取表格（基于文本对齐检测）。\"\"\"
        import fitz
        doc = fitz.open(pdf_path)
        tables = []

        for page in doc:
            # 获取页面上的表格
            tabs = page.find_tables()
            for tab in tabs:
                df = pd.DataFrame(tab.extract())
                if not df.empty:
                    tables.append(df)

        doc.close()
        return tables

    def extract_camelot(self, pdf_path: str) -> list[pd.DataFrame]:
        \"\"\"使用 Camelot 提取表格（基于图形检测）。\"\"\"
        import camelot
        tables = camelot.read_pdf(pdf_path, flavor="lattice")
        return [table.df for table in tables]

    def extract_tabula(self, pdf_path: str) -> list[pd.DataFrame]:
        \"\"\"使用 Tabula 提取表格（基于 PDF 解析）。\"\"\"
        import tabula
        dfs = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)
        return [df for df in dfs if not df.empty]

    def extract_all(self, pdf_path: str) -> list[pd.DataFrame]:
        \"\"\"综合使用所有引擎提取表格。\"\"\"
        all_tables = []
        try:
            all_tables.extend(self.extract_pymupdf(pdf_path))
        except Exception as e:
            print(f"PyMuPDF 表格提取失败：{e}")

        try:
            all_tables.extend(self.extract_camelot(pdf_path))
        except Exception as e:
            print(f"Camelot 提取失败：{e}")

        return all_tables
```

### 2.6 OCR 文字识别

对于扫描件或图片型 PDF（非可搜索 PDF），需要使用 OCR 技术：

```python
from PIL import Image
import pytesseract


class OCRProcessor:
    \"\"\"OCR 文字识别处理器。\"\"\"

    def __init__(self, lang: str = "chi_sim+eng"):
        \"\"\"初始化 OCR 处理器。
        
        Args:
            lang: Tesseract 语言包，chi_sim=简体中文，eng=英文
        \"\"\"
        self._lang = lang

    def image_to_text(self, image_path: str) -> str:
        \"\"\"将图片转换为文字。\"\"\"
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=self._lang)
        return text

    def pdf_to_text(self, pdf_path: str, dpi: int = 300) -> str:
        \"\"\"将扫描版 PDF 转换为文字（先转图片，再 OCR）。\"\"\"
        import fitz
        doc = fitz.open(pdf_path)
        all_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            # 将页面渲染为图片
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # OCR
            text = pytesseract.image_to_string(img, lang=self._lang)
            if text.strip():
                all_text.append(f"--- 第 {page_num + 1} 页 ---\\n{text}")

        doc.close()
        return "\\n\\n".join(all_text)

    @staticmethod
    def is_scanned_pdf(pdf_path: str) -> bool:
        \"\"\"判断 PDF 是否为扫描件（无可搜索文本）。\"\"\"
        import fitz
        doc = fitz.open(pdf_path)
        total_text = ""
        for page in doc:
            total_text += page.get_text()
        doc.close()
        # 如果提取到的文本极少，可能是扫描件
        return len(total_text.strip()) < 100
```

### 2.7 分块策略（Chunking）

分块（Chunking）是将解析后的长文本切分为适合 Embedding 的小块的过程。它直接影响 RAG 的检索质量。

```python
from typing import Callable


class TextSplitter:
    \"\"\"文本分块器基类。\"\"\"

    def split(self, text: str) -> list[str]:
        raise NotImplementedError


# 1. 固定大小分块
class FixedSizeSplitter(TextSplitter):
    \"\"\"固定 token 数分块，带重叠。\"\"\"

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            if end < len(text):
                # 在边界处寻找合适的断点（句号、换行）
                cut = text.rfind("。", start, end)
                if cut > start + self._chunk_size // 2:
                    end = cut + 1
                else:
                    cut = text.rfind("\\n", start, end)
                    if cut > start + self._chunk_size // 2:
                        end = cut + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self._chunk_overlap if end < len(text) else len(text)

        return chunks


# 2. 语义分块（基于标题/段落）
class SemanticSplitter(TextSplitter):
    \"\"\"基于 Markdown 标题的语义分块。\"\"\"

    def __init__(self, max_chunk_size: int = 1000):
        self._max_chunk_size = max_chunk_size

    def split(self, text: str) -> list[str]:
        lines = text.split("\\n")
        chunks = []
        current_chunk = []
        current_title = ""

        for line in lines:
            if line.startswith("#"):
                # 遇到标题，保存当前块
                if current_chunk:
                    chunk_text = "\\n".join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                current_title = line
                current_chunk = [line]
            else:
                current_chunk.append(line)
                # 检查是否超过最大长度
                if len("\\n".join(current_chunk)) > self._max_chunk_size:
                    current_chunk.pop()
                    if current_chunk:
                        chunk_text = "\\n".join(current_chunk).strip()
                        if chunk_text:
                            chunks.append(chunk_text)
                    current_chunk = [line]

        if current_chunk:
            chunk_text = "\\n".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks


# 3. 递归字符分块（LangChain 风格）
class RecursiveSplitter(TextSplitter):
    \"\"\"递归分块，由大到小依次尝试分隔符。\"\"\"

    SEPARATORS = ["\\n\\n", "\\n", "。", ".", " ", ""]

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        return self._recursive_split(text, self.SEPARATORS)

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        \"\"\"递归分割文本。\"\"\"
        if len(text) <= self._chunk_size or not separators:
            return [text] if text.strip() else []

        separator = separators[0]
        if separator:
            parts = text.split(separator)
        else:
            parts = list(text)

        if len(parts) == 1:
            # 当前分隔符无法分割，尝试下一个
            return self._recursive_split(text, separators[1:])

        chunks = []
        current = ""
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(current) + len(part) + len(separator) <= self._chunk_size:
                current = (current + separator + part).strip() if current else part
            else:
                if current:
                    chunks.append(current)
                # 处理可能超长的部分
                if len(part) > self._chunk_size:
                    sub_chunks = self._recursive_split(
                        part, separators[1:]
                    )
                    chunks.extend(sub_chunks)
                    current = sub_chunks[-1][-self._chunk_overlap:] if sub_chunks else ""
                else:
                    current = part

        if current:
            chunks.append(current)

        return chunks
```

---

## 3. 实战指南

### 3.1 agent_platform 中的文档解析

在 `agent_platform/src/parsing/document.py` 中，我们实现了一套完整的文档解析流水线：

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class ParsedDocument:
    \"\"\"解析后的文档。\"\"\"
    file_path: str
    text: str
    metadata: dict = field(default_factory=dict)
    page_count: int = 0


@dataclass
class TextChunk:
    \"\"\"文本分块。\"\"\"
    text: str
    source: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


# 解析器注册表
PARSERS: dict[str, Callable] = {
    ".pdf": lambda p: _parse_pdf_pymupdf(p),
    ".docx": lambda p: _parse_docx(p),
    ".doc": lambda p: _parse_docx(p),
    ".md": lambda p: _parse_text_file(p),
    ".txt": lambda p: _parse_text_file(p),
    ".html": lambda p: _parse_text_file(p),
    ".htm": lambda p: _parse_text_file(p),
}


def parse_document(file_path: str | Path) -> ParsedDocument:
    \"\"\"自动识别文件格式并解析。\"\"\"
    path = Path(file_path)
    suffix = path.suffix.lower()
    parser = PARSERS.get(suffix)
    if not parser:
        raise ValueError(f"不支持的格式：{suffix}")
    return parser(path)


def chunk_text(text: str, *, chunk_size: int = 500, chunk_overlap: int = 50, source: str = "unknown") -> list[TextChunk]:
    \"\"\"滑动窗口分块。\"\"\"
    paragraphs = text.split("\\n")
    chunks = []
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk = (current_chunk + "\\n" + para).strip()
        else:
            if current_chunk:
                chunks.append(TextChunk(text=current_chunk, source=f"{source}#chunk{chunk_index}", chunk_index=chunk_index))
                chunk_index += 1
                overlap = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""
                current_chunk = (overlap + "\\n" + para).strip() if overlap else para

    if current_chunk:
        chunks.append(TextChunk(text=current_chunk, source=f"{source}#chunk{chunk_index}", chunk_index=chunk_index))
    return chunks


def parse_and_chunk(file_path: str | Path, *, chunk_size: int = 500, chunk_overlap: int = 50) -> list[TextChunk]:
    \"\"\"解析并分块，一步完成。\"\"\"
    doc = parse_document(file_path)
    return chunk_text(doc.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap, source=Path(file_path).name)
```

### 3.2 多格式文档批量处理

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchDocumentProcessor:
    \"\"\"批量文档处理器。\"\"\"

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        max_workers: int = 4,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._max_workers = max_workers

    def process_single(self, file_path: str) -> list[TextChunk]:
        \"\"\"处理单个文档。\"\"\"
        try:
            return parse_and_chunk(
                file_path,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
            )
        except Exception as e:
            print(f"处理失败 [{file_path}]: {e}")
            return []

    def process_batch(self, file_paths: list[str]) -> dict[str, list[TextChunk]]:
        \"\"\"并发处理多个文档。\"\"\"
        results = {}
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self.process_single, path): path
                for path in file_paths
            }
            for future in as_completed(futures):
                path = futures[future]
                results[path] = future.result()
        return results

    def process_directory(
        self, directory: str, pattern: str = "*"
    ) -> dict[str, list[TextChunk]]:
        \"\"\"处理目录下的所有文档。\"\"\"
        from pathlib import Path
        supported = {".pdf", ".docx", ".doc", ".md", ".txt", ".html", ".htm"}
        files = [
            str(p) for p in Path(directory).rglob(pattern)
            if p.suffix.lower() in supported and p.is_file()
        ]
        print(f"找到 {len(files)} 个文档待处理")
        return self.process_batch(files)
```

### 3.3 解析结果的质量评估

```python
class ParsingQualityChecker:
    \"\"\"文档解析质量检查器。\"\"\"

    @staticmethod
    def check_text_quality(text: str) -> dict:
        \"\"\"检查提取文本的质量。\"\"\"
        issues = []

        # 1. 文本是否过短
        if len(text.strip()) < 100:
            issues.append("文本过短，可能解析不完整")

        # 2. 是否包含乱码
        import re
        garbage_ratio = len(re.findall(r"[\\u0000-\\u0008\\u000b\\u000c\\u000e-\\u001f]", text)) / max(len(text), 1)
        if garbage_ratio > 0.01:
            issues.append(f"包含 {garbage_ratio:.1%} 的控制字符")

        # 3. 是否包含 PDF 页眉页脚
        common_headers = ["第 * 页", "Page * of *", "机密", "Confidential"]
        for pattern in common_headers:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"可能包含页眉页脚：{pattern}")

        # 4. 是否重复段落
        paragraphs = text.split("\\n")
        unique_paras = set(p.strip() for p in paragraphs if p.strip())
        if len(unique_paras) < len(paragraphs) * 0.5:
            issues.append("存在大量重复段落")

        return {
            "total_length": len(text),
            "paragraph_count": len(paragraphs),
            "issues": issues,
            "quality": "good" if len(issues) == 0 else "fair" if len(issues) <= 2 else "poor",
        }

    @staticmethod
    def check_chunk_quality(chunks: list[TextChunk]) -> dict:
        \"\"\"检查分块质量。\"\"\"
        if not chunks:
            return {"issues": ["无分块数据"]}

        issues = []
        lengths = [len(c.text) for c in chunks]

        # 1. 检查分块长度分布
        avg_len = sum(lengths) / len(lengths)
        for i, c in enumerate(chunks):
            if len(c.text) < 20:
                issues.append(f"分块 {i} 过短（{len(c.text)} 字符）")

        # 2. 检查是否在句子中间截断
        for i, c in enumerate(chunks):
            if c.text and c.text[-1] not in "。！？.!?\\n":
                issues.append(f"分块 {i} 可能未在完整句子处结束")

        return {
            "chunk_count": len(chunks),
            "avg_length": avg_len,
            "min_length": min(lengths),
            "max_length": max(lengths),
            "issues": issues,
            "quality": "good" if len(issues) == 0 else "fair" if len(issues) <= len(chunks) * 0.1 else "poor",
        }
```

---

## 4. 最佳实践

### 4.1 解析引擎选择

- **PDF 纯文本**：PyMuPDF 最快、最可靠
- **PDF 扫描件**：先用 PyMuPDF 检测是否为扫描件，是则使用 OCR
- **PDF 表格**：使用 Camelot 或 Tabula
- **Word 文档**：python-docx
- **通用方案**：Unstructured（支持格式最多，但速度较慢）
- **高精度布局**：Docling（IBM 出品，布局理解能力强）

### 4.2 元数据保留

- 保留文档来源信息（文件路径、上传时间、作者）
- 保留页面编号，便于溯源
- 保留标题层级结构，用于语义分块
- 保留表格的原始结构，避免信息丢失

### 4.3 分块策略选择

- **固定大小分块**：简单，适用于大部分场景
- **语义分块**：基于标题/段落切分，检索效果更好
- **递归分块**：从大到小尝试分隔符，适应性最强
- **重叠策略**：5-10% 的重叠率，避免信息在边界处丢失

---

## 5. 常见陷阱与反模式

### 5.1 忽略扫描件检测

反模式：对所有 PDF 使用相同的解析方法。扫描件 PDF 没有可提取的文本层，直接解析会得到空文本。正确做法是先检测是否为扫描件，然后使用 OCR 兜底。

### 5.2 分块时忽略语义边界

反模式：严格按照固定字符数切分，不考虑段落和句子边界。这会导致在句子中间断开，检索时失去完整语义。正确做法是在分块边界处寻找自然断点。

### 5.3 不保留元数据

反模式：解析后只保留文本内容，丢弃文件来源、页码等信息。在 Agent 回答时无法引用来源。正确做法是始终保留并传递元数据。

### 5.4 多栏 PDF 提取顺序混乱

反模式：PyMuPDF 的默认文本提取可能混淆多栏文档的阅读顺序（从左到右读取第一栏所有文本，再读取第二栏）。正确做法是使用 text blocks 的位置信息重新排序。

### 5.5 忽略编码问题

反模式：假设所有文档都是 UTF-8 编码。一些旧文档可能是 GBK、Shift-JIS 等编码。正确做法是尝试检测编码并兜底使用多种编码。

---

## 6. API Key 依赖

文档解析（未使用云服务时）**不需要**任何 API Key：

- **PyMuPDF**：开源，本地解析，无需 Key
- **python-docx**：开源，无需 Key
- **Unstructured**：开源，无需 Key（快速模式）
- **Docling**：开源，无需 Key
- **Tesseract OCR**：开源，无需 Key
- **Camelot/Tabula**：开源，无需 Key

如果使用云文档解析服务（如 Unstructured API、Google Document AI、Azure Form Recognizer），则需要对应的 API Key。

在 agent_platform 的 `src/parsing/document.py` 中，所有解析器都是本地的，不需要任何外部 API Key。

---

## 7. 与其他技术的关系

| 技术 | 关系说明 |
|------|----------|
| **RAG** | 文档解析是 RAG 数据准备的第一步 |
| **Embedding** | 解析后的分块文本需要 Embedding 才能被检索 |
| **向量数据库** | 解析分块 + Embedding 后写入向量数据库 |
| **Agent 系统** | Agent 通过 RAG 检索知识库，知识库来自文档解析 |
| **结构化输出** | 解析后的表格数据可通过结构化输出进一步提取 |

在 agent_platform 中，`src/parsing/document.py` 是整个知识库流水线的起点，解析结果流向 `src/embeddings/` 进行向量化，然后写入 `src/vectordb/`，最终由 `src/rag/` 用于检索增强生成。

---

## 8. 验收清单

- [ ] 了解不同 PDF 解析引擎的差异（PyMuPDF, Unstructured, Docling）
- [ ] 掌握 Word 文档的解析方法
- [ ] 理解 OCR 的使用场景和方法
- [ ] 掌握表格提取的多种方式
- [ ] 理解固定大小分块和语义分块的差异
- [ ] 能够实现递归分块算法
- [ ] 了解元数据保留的重要性
- [ ] 能编写多格式文档的批量处理流水线
- [ ] 理解解析质量评估的方法
- [ ] 能在实际项目中设计文档解析 -> 分块 -> 向量化的完整流程

---

## 9. 推荐学习资源

### 官方文档
- PyMuPDF: https://pymupdf.readthedocs.io/
- python-docx: https://python-docx.readthedocs.io/
- Unstructured: https://docs.unstructured.io/
- Docling: https://ds4sd.github.io/docling/
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract

### 开源项目
- Unstructured: https://github.com/Unstructured-IO/unstructured
- Docling: https://github.com/DS4SD/docling
- Camelot: https://github.com/camelot-dev/camelot
- Tabula: https://github.com/chezou/tabula-py

### 项目代码参考
- `agent_platform/src/parsing/document.py` — 多格式文档解析，分块，Pydantic 数据结构
- `agent_platform/src/embeddings/local_bge.py` — 解析结果的向量化
- `agent_platform/src/vectordb/chroma_store.py` — 解析分块的存储和检索
