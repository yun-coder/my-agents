# 08 文档解析

## 学习目标

- 理解文档解析是 RAG 的数据入口。
- 区分提取文本、保留结构、分块和元数据。
- 能处理 Markdown、TXT、PDF 与 DOCX。

## Pipeline

```text
文件 -> 格式识别 -> 文本提取 -> 清洗
-> 分块 -> 元数据补充 -> 送入索引
```

## 工程难点

- PDF 可能只有扫描图片，没有文本层。
- 表格如果被拍平成文本，会丢失行列语义。
- 文档标题、页码和来源链接需要进入元数据。
- 分块不能只按固定长度粗暴切割，要考虑标题和段落。

## 本章设计

`demo.py` 支持 `.md`、`.txt`、`.pdf`、`.docx`。默认解析本章自带 Markdown 样例。PDF 与 Word 依赖 `pypdf` 和 `python-docx`。

## 参考资料

- [Unstructured Documentation](https://docs.unstructured.io/)
- [Docling](https://github.com/docling-project/docling)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)

## 验收清单

- 能解释文档解析为什么不等于简单读取文件。
- 能保留来源路径与分块编号。
- 能指出扫描 PDF 需要 OCR。
