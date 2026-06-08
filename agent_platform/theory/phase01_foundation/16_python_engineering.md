# 16 Python 工程化：AI Agent 项目最佳实践

## 一、概念概述

### 1.1 什么是 Python 工程化

Python 工程化（Python Engineering）是指将 Python 项目的开发、测试、部署过程系统化、标准化的实践方法。对于 AI Agent 这类复杂度较高的项目，良好的工程化实践是保证代码质量、团队协作效率和项目可持续性的基础。

工程化的核心目标：
- **可维护性**：代码易于理解和修改
- **可测试性**：能够快速发现和定位问题
- **可复现性**：依赖和环境在任何机器上都能复现
- **可观测性**：运行状态可以被监控和诊断
- **可部署性**：能够一键构建和部署

### 1.2 为什么 AI Agent 项目需要工程化

AI Agent 项目相比传统 Web 项目有以下特殊性，更需要工程化保障：

- **LLM 输出的不确定性**：需要更强的测试和评估体系
- **复杂的调用链**：RAG 检索、工具调用、多轮对话交织在一起
- **昂贵的运行成本**：每次 LLM 调用都产生费用，需要日志和监控
- **快速迭代的需求**：提示词、模型、检索策略频繁变化
- **多环境部署**：开发、测试、生产环境需要一致的行为

---

## 二、核心原理

### 2.1 项目结构：src Layout

推荐的 Python 项目结构使用 `src` 布局，将源代码与配置、测试、文档等分离。

```text
project_name/
+-- src/                          # 源代码目录
|   +-- agent/                    # Agent 模块
|   |   +-- __init__.py
|   |   +-- graph.py              # LangGraph 工作流
|   |   +-- memory.py             # 对话记忆
|   |   +-- tools.py              # 工具定义
|   +-- rag/                      # RAG 模块
|   |   +-- __init__.py
|   |   +-- retriever.py          # 检索器
|   |   +-- generator.py          # 生成器
|   |   +-- reranker.py           # 重排序器
|   +-- api/                      # API 模块
|   |   +-- __init__.py
|   |   +-- app.py                # FastAPI 应用入口
|   |   +-- routes.py             # 路由定义
|   |   +-- middleware.py         # 中间件
|   +-- embeddings/               # 嵌入模块
|   |   +-- __init__.py
|   |   +-- local_bge.py          # 本地 BGE 嵌入
|   +-- vectordb/                 # 向量数据库
|   |   +-- __init__.py
|   |   +-- chroma_store.py       # Chroma 存储
|   +-- observability/            # 可观测性
|   |   +-- __init__.py
|   |   +-- tracing.py            # LangFuse 追踪
|   +-- config.py                 # 全局配置
|   +-- __init__.py
+-- tests/                        # 测试目录
|   +-- test_retriever.py
|   +-- test_generator.py
|   +-- test_graph.py
|   +-- test_api.py
|   +-- conftest.py               # Pytest 共享 fixtures
+-- docs/                         # 文档目录
|   +-- api/                      # API 文档
|   +-- architecture.md           # 架构文档
+-- scripts/                      # 工具脚本
|   +-- setup.sh
|   +-- seed_documents.py         # 数据初始化
+-- pyproject.toml                # 项目配置（核心）
+-- .env.example                  # 环境变量模板
+-- .gitignore
+-- README.md
+-- Dockerfile
+-- docker-compose.yml
```

src 布局的优势：
1. **明确的命名空间**：`from src.rag.retriever import Retriever`
2. **避免导入混淆**：测试和其他代码不会误导入本地模块
3. **打包友好**：`pyproject.toml` 中的 `packages = ["src"]` 直接指向源码

### 2.2 pyproject.toml

`pyproject.toml` 是 PEP 621 定义的项目配置标准，取代了 `setup.py` 和 `setup.cfg`。

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-platform"
version = "1.0.0"
description = "企业级 AI Agent 平台 - RAG + LangGraph + Tool Calling"
readme = "README.md"
requires-python = ">=3.11"

authors = [
    { name = "Your Name", email = "your@email.com" },
]

dependencies = [
    # LLM 与 Agent 框架
    "langchain-core>=0.3.0",
    "langgraph>=0.2.0",
    "openai>=1.30.0",

    # RAG 组件
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",
    "FlagEmbedding>=1.2.0",
    "pdfplumber>=0.11.0",
    "python-docx>=1.1.0",

    # API 服务
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",

    # 可观测性
    "langfuse>=2.30.0",

    # 工具库
    "httpx>=0.27.0",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
]

[tool.ruck]
# Ruff 配置：Python 代码风格检查
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "ANN"]

[tool.mypy]
# MyPy 配置：类型检查
python_version = "3.11"
strict = false
ignore_missing_imports = true
disallow_untyped_defs = false

[tool.pytest.ini_options]
# Pytest 配置
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
```

### 2.3 类型提示（Type Hints + MyPy）

类型提示是 Python 工程化的基石，它让代码自文档化并支持静态检查。

```python
from __future__ import annotations  # PEP 604: 支持 | 语法

from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypedDict,
    Union,
)
from typing_extensions import (
    NotRequired,     # TypedDict 可选字段
    Required,        # TypedDict 必选字段
    Literal,         # 字面量类型
    Protocol,        # 协议（结构子类型）
)


# TypedDict：结构化字典类型
class AgentState(TypedDict, total=False):
    """Agent 状态的类型定义。"""
    messages: list[dict[str, Any]]
    query: str
    session_id: str
    iteration_count: int
    final_answer: str
    tool_log: list[str]
    error: NotRequired[str]  # 可选字段


# Protocol：鸭子类型检查
class Retrievable(Protocol):
    """可检索协议的接口定义。"""
    def search(self, query: str, *, top_k: int) -> list[dict[str, Any]]: ...


# 泛型
from typing import TypeVar, Generic

T = TypeVar("T")

class Result(Generic[T]):
    """泛型结果包装器。"""
    def __init__(self, value: T, success: bool = True):
        self.value = value
        self.success = success
        self.error: Optional[str] = None


# Union 和 Optional
def parse_document(path: str) -> str | None:
    """解析文档，失败返回 None。"""
    ...


# Literal 类型
def set_mode(mode: Literal["fast", "balanced", "accurate"]) -> None:
    """仅接受三个字面量值。"""
    ...


# 运行 mypy 检查
# mypy src/ --strict
```

### 2.4 代码风格（Ruff）

Ruff 是用 Rust 写的极速 Python 代码检查器，可以替代 flake8、isort、pylint 等多个工具。

```python
# 运行 ruff 检查和格式化
# ruff check src/          # 检查代码问题
# ruff format src/         # 自动格式化代码
# ruff check --fix src/    # 自动修复

# 常见检查规则说明
# E: pycodestyle 错误
# F: pyflakes 错误（未使用的导入等）
# I: isort 导入排序
# N: 命名规范
# W: 警告
# UP: pyupgrade（检查过时的 Python 语法）
# ANN: 缺少类型注解
```

### 2.5 测试（Pytest + Coverage）

测试是保证 Agent 行为正确的关键，尤其是 LLM 输出具有不确定性时。

```python
# tests/test_retriever.py
import pytest
from src.rag.retriever import Retriever


@pytest.fixture
def retriever():
    """创建测试用的检索器实例。"""
    from src.vectordb.chroma_store import ChromaVectorStore
    from src.embeddings.local_bge import get_embedding_provider

    emb = get_embedding_provider("BAAI/bge-small-zh-v1.5", device="cpu")
    store = ChromaVectorStore(":memory:", embedding=emb)  # 内存模式
    return Retriever(store)


@pytest.fixture
def sample_docs():
    """准备测试用的文档。"""
    return [
        {"id": "1", "text": "RAG 是检索增强生成的缩写。",
         "metadata": {"source": "test.md"}},
        {"id": "2", "text": "LangGraph 是图结构 Agent 框架。",
         "metadata": {"source": "test.md"}},
    ]


class TestRetriever:
    """检索器测试套件。"""

    def test_search_returns_results(self, retriever, sample_docs):
        """测试检索能返回结果。"""
        # Arrange
        for doc in sample_docs:
            retriever._store.add_documents([doc])

        # Act
        results = retriever.search("什么是 RAG?", top_k=2)

        # Assert
        assert len(results) > 0
        assert "text" in results[0]

    def test_search_empty_store(self, retriever):
        """测试空知识库检索。"""
        results = retriever.search("任何问题", top_k=5)
        assert len(results) == 0

    def test_format_context(self, retriever, sample_docs):
        """测试上下文格式化。"""
        context = retriever.format_context(sample_docs)
        assert "[来源1:" in context
        assert "[来源2:" in context
        assert sample_docs[0]["text"] in context

    def test_format_sources_deduplication(self, retriever):
        """测试来源去重。"""
        docs = [
            {"id": "1", "text": "A", "metadata": {"source": "doc.md#section1"}},
            {"id": "2", "text": "B", "metadata": {"source": "doc.md#section2"}},
            {"id": "3", "text": "C", "metadata": {"source": "other.md"}},
        ]
        sources = retriever.format_sources(docs)
        assert len(sources) == 2  # doc.md 去重了
        assert "doc.md" in sources


# tests/test_generator.py
class TestRAGGenerator:
    """RAG 生成器测试。"""

    def test_generate_without_docs(self, generator):
        """测试无检索结果时的回答。"""
        answer = generator.generate("不存在的问题")
        assert "无法回答" in answer.answer

    def test_generate_with_docs(self, generator, sample_docs, mocker):
        """测试有检索结果时的回答。"""
        # Mock LLM 调用
        mocker.patch.object(
            generator._llm, "chat",
            return_value="RAG 是检索增强生成。"
        )
        answer = generator.generate("什么是 RAG?")
        assert answer.answer == "RAG 是检索增强生成。"
        assert len(answer.sources) > 0
```

### 2.6 日志系统

```python
# src/config/logging_config.py
import logging
import sys
from pathlib import Path


def setup_logging(
    name: str = "agent-platform",
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """配置日志系统。

    Args:
        name: Logger 名称
        level: 日志级别
        log_file: 日志文件路径（可选）

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（可选）
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 使用方式
logger = setup_logging(
    name="agent-platform",
    level=logging.INFO,
    log_file="logs/agent.log",
)

logger.info("Agent 工作流启动")
logger.warning("检索结果为空")
logger.error("LLM 调用失败: %s", str(e))
```

### 2.7 环境变量管理

```python
# src/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置：从环境变量和环境文件读取。"""

    # 项目基本配置
    APP_NAME: str = "Agent Platform"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # LLM 配置
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    LLM_BASE_URL: str = ""

    # Chroma 向量库
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"

    # 嵌入模型
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"

    # LangFuse 可观测性
    LANGFUSE_HOST: str = "http://localhost:3000"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_ENABLE: bool = True

    class Config:
        """配置元数据。"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略未定义的环境变量


# 全局单例
settings = Settings()

# 在代码中使用
from src.config import settings

llm_api_key = settings.LLM_API_KEY
chroma_dir = settings.CHROMA_PERSIST_DIR
```

### 2.8 依赖管理（Uv/Pip）

```bash
# 使用 uv（推荐——比 pip 快 10-100 倍）
uv venv                          # 创建虚拟环境
uv pip install -e .              # 安装项目依赖
uv pip install -e ".[dev]"       # 安装开发依赖
uv pip install -r requirements.txt  # 从 requirements 安装
uv pip freeze > requirements.txt    # 导出依赖

# 使用 pip
python -m venv .venv             # 创建虚拟环境
pip install -e .                 # 安装项目依赖
pip install -e ".[dev]"          # 安装开发依赖

# 使用 pip sync（确保完全一致）
pip install -r requirements.txt --require-hashes
```

### 2.9 CI/CD 基础

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: 安装 Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: 安装 uv
        run: pip install uv

      - name: 安装项目依赖
        run: uv pip install -e ".[dev]"

      - name: 代码检查（Ruff）
        run: ruff check src/

      - name: 类型检查（MyPy）
        run: mypy src/

      - name: 运行测试
        run: pytest tests/ --cov=src --cov-report=term-missing

      - name: 检查测试覆盖率
        run: pytest tests/ --cov=src --cov-fail-under=80
```

---

## 三、实战指南

### 3.1 项目初始化完整流程

```bash
# 1. 创建项目目录
mkdir agent-platform && cd agent-platform

# 2. 创建虚拟环境
uv venv

# 3. 创建目录结构
mkdir -p src/{agent,rag,api,embeddings,vectordb,observability}
mkdir -p tests docs scripts

# 4. 创建基本文件
touch src/__init__.py
touch src/config.py
touch src/agent/__init__.py
touch src/rag/__init__.py
# ...

# 5. 创建 pyproject.toml
# 6. 创建 .env.example
# 7. 创建 .gitignore
# 8. 初始化 git
git init

# 9. 安装依赖
uv pip install -e ".[dev]"

# 10. 设置 pre-commit 钩子
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
EOF

pre-commit install
```

### 3.2 完整测试配置

```python
# tests/conftest.py — 共享 Fixtures
import pytest
from src.config import Settings


@pytest.fixture(autouse=True)
def test_settings():
    """测试配置：覆盖环境变量。"""
    settings = Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        LLM_API_KEY="test-key",
        CHROMA_PERSIST_DIR=":memory:",
        LANGFUSE_ENABLE=False,
    )
    return settings


@pytest.fixture
def sample_texts():
    """常用的测试文本。"""
    return [
        "RAG 是检索增强生成（Retrieval-Augmented Generation）的缩写。",
        "它通过从知识库中检索相关文档来增强 LLM 的生成能力。",
        "LangGraph 是一个基于图结构的 Agent 编排框架。",
        "FastAPI 是一个现代、高性能的 Python Web 框架。",
    ]
```

### 3.3 .env.example 模板

```env
# ============================================
# Agent Platform 环境变量配置
# 复制此文件为 .env 并填写实际值
# ============================================

# ---- 应用配置 ----
APP_NAME=Agent Platform
DEBUG=false
LOG_LEVEL=INFO

# ---- LLM 配置 ----
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4
LLM_BASE_URL=

# ---- Chroma 向量库 ----
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=documents

# ---- 嵌入模型（本地 BGE） ----
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu

# ---- LangFuse 可观测性 ----
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_ENABLE=true
```

### 3.4 .gitignore

```text
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# 虚拟环境
.venv/
venv/

# 环境变量
.env

# IDE
.vscode/
.idea/

# 数据库
*.db
chroma_db/

# 日志
logs/
*.log

# 测试覆盖率
htmlcov/
.coverage
coverage.xml

# 临时文件
*.tmp
```

---

## 四、最佳实践

### 4.1 代码组织原则

- **按模块分组**：agent、rag、api 等模块职责清晰
- **最小导入**：避免 `from x import *`，使用显式导入
- **循环依赖避免**：使用 Protocol 或接口抽象来打破循环
- **配置集中管理**：所有配置集中在 `config.py`

### 4.2 开发工作流

```bash
# 开发循环
ruff check src/          # 1. 检查代码
ruff format src/         # 2. 格式化代码
mypy src/                # 3. 类型检查
pytest tests/            # 4. 运行测试
uvicorn src.api.app:app --reload  # 5. 启动开发服务器
```

### 4.3 版本管理

```python
# src/__init__.py
__version__ = "1.0.0"

# pyproject.toml 中引用
# version = "1.0.0"
```

### 4.4 预提交检查

使用 pre-commit 钩子在每次提交前自动执行检查，确保代码质量。

---

## 五、常见陷阱

### 5.1 src 布局导入错误

**陷阱**：使用 `python src/api/app.py` 运行时报错 `ImportError`。

**解决**：使用 `python -m src.api.app` 或通过 `uvicorn src.api.app:app` 启动。

### 5.2 环境变量泄露

**陷阱**：将包含 API Key 的 `.env` 文件提交到了 Git 仓库。

**解决**：将 `.env` 加入 `.gitignore`，只提交 `.env.example` 模板。

### 5.3 测试依赖真实 LLM

**陷阱**：测试直接调用真实 LLM 端点，导致费用和速度问题。

**解决**：使用 `mocker.patch` 或 `pytest-mock` 模拟 LLM 调用。

### 5.4 虚拟环境污染

**陷阱**：没有使用 venv，全局安装依赖导致版本冲突。

**解决**：始终使用 `uv venv` 创建隔离的虚拟环境。

### 5.5 缺少 __init__.py

**陷阱**：Python 3.3+ 虽然 namespace package 不需要 `__init__.py`，但某些工具（mypy、pytest）在缺少时可能出问题。

**解决**：在每个包目录中添加 `__init__.py`，至少包含版本信息。

---

## 六、API Key 依赖

| 工具 | 需要 API Key? | 说明 |
|------|--------------|------|
| Python 标准库 | 否 | 语言本身 |
| Ruff | 否 | 本地代码检查 |
| MyPy | 否 | 本地类型检查 |
| Pytest | 否 | 本地测试框架 |
| Pytest-cov | 否 | 本地覆盖率检查 |
| Pre-commit | 否 | 本地 Git 钩子 |
| Uvicorn | 否 | 本地 ASGI 服务器 |
| 项目运行时（LLM） | 是 | 需要 LLM API Key |

---

## 七、技术关系

```text
Python 工程化工具链:

开发阶段
  +-- uv / pip（依赖管理）
  +-- ruff（代码风格检查）
  +-- mypy（类型检查）
  +-- pre-commit（提交前检查）
  +-- pyproject.toml（项目配置）

测试阶段
  +-- pytest（测试框架）
  +-- pytest-cov（覆盖率）
  +-- pytest-asyncio（异步测试）
  +-- pytest-mock（模拟）

部署阶段
  +-- Docker（容器化）
  +-- uvicorn（ASGI 服务器）
  +-- gunicorn（WSGI 服务器，可配合 uvicorn）
  +-- systemd / supervisor（进程管理）

CI/CD
  +-- GitHub Actions
  +-- GitLab CI
  +-- pytest --cov-fail-under（质量门禁）

AI Agent 特定
  +-- 模拟 LLM 响应（测试）
  +-- 回归测试数据集
  +-- 评估 Pipeline（正确性、安全性）
```

---

## 八、验收清单

- [ ] 理解 src 布局的优势和标准目录结构
- [ ] 掌握 pyproject.toml 的编写（项目元数据、依赖、工具配置）
- [ ] 使用类型提示标注函数签名（TypedDict、Protocol、Literal）
- [ ] 熟练使用 ruff 进行代码检查和格式化
- [ ] 能编写 pytest 测试（Fixture、Mock、断言）
- [ ] 会配置和使用 pytest-cov 覆盖率检查
- [ ] 理解日志系统的配置（控制台 + 文件输出）
- [ ] 掌握 pydantic-settings 管理环境变量
- [ ] 理解 uv/pip 依赖管理的基本命令
- [ ] 了解 CI/CD 的基本流程和配置

---

## 九、学习资源

- **Python 项目打包指南**: https://packaging.python.org/en/latest/
- **pyproject.toml 规范（PEP 621）**: https://peps.python.org/pep-0621/
- **Ruff 文档**: https://docs.astral.sh/ruff/
- **MyPy 文档**: https://mypy-lang.org/
- **Pytest 文档**: https://docs.pytest.org/en/stable/
- **Pydantic Settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **Uv 文档**: https://docs.astral.sh/uv/
- **src Layout 说明**: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- **平台参考代码**: agent_platform/src/ 的完整目录结构
