# 阶段一：AI Agent 基础闭环

阶段一目标不是一次学完所有框架，而是从最小模型调用出发，逐步跑通：

```text
Prompt -> 结构化输出 -> OpenAI / Claude API -> Tool Calling
-> Embedding -> 向量检索 -> 文档解析 -> RAG
-> LangChain / LlamaIndex / LangGraph -> 短期记忆
-> FastAPI 服务化 -> LangSmith Trace -> Python 工程化
```

## 学习方式

每个目录包含：

- `theory.md`：先理解原理、边界和工程注意事项。
- `demo.py`：尽量小而完整的 Python 示例。
- 文档末尾的验收清单：不要只读代码，要亲自运行和修改。

示例分为三类：

| 标记 | 含义 |
|---|---|
| 离线可运行 | 不需要网络或密钥，适合先理解算法和流程 |
| 使用现有 OpenAI 配置 | 读取仓库根目录 `dev.json` 的 OpenAI 兼容配置 |
| 需要额外服务或依赖 | 安装对应包或启动本地服务后运行 |

## 推荐顺序

| 序号 | 知识点 | 最小产出 |
|---:|---|---|
| 01 | Prompt Engineering | 可复用 Prompt 模板 |
| 02 | 结构化输出 | 工单信息抽取器 |
| 03 | OpenAI API | Responses API 文本与流式调用 |
| 04 | Anthropic Claude API | Messages API 示例 |
| 05 | Function Calling / Tool Use | 完整工具调用循环 |
| 06 | Embedding 模型 | 相似度检索 |
| 07 | 向量数据库 | 内存向量库与 Chroma 迁移思路 |
| 08 | 文档解析 | 多格式解析 Pipeline |
| 09 | RAG 基础 | 可解释的最小 RAG |
| 10 | LangChain | Runnable 管道 |
| 11 | LlamaIndex | 文档索引与查询 |
| 12 | LangGraph 入门 | 条件分支工作流 |
| 13 | 短期记忆 | Token 预算与滑动窗口 |
| 14 | FastAPI | Agent REST API |
| 15 | LangSmith | Trace 包装 |
| 16 | Python 工程化 | 配置、日志、测试与目录规范 |

## 环境准备

在仓库根目录运行：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r learning\phase01_foundation\requirements.txt
```

已有 `dev.json` 会被共享模块自动读取。不要把真实密钥写进示例代码、Markdown 或 Git。

先运行不需要网络的检查：

```powershell
python learning\phase01_foundation\01_prompt_engineering\demo.py
python learning\phase01_foundation\06_embeddings\demo.py
python learning\phase01_foundation\07_vector_databases\demo.py
python learning\phase01_foundation\08_document_parsing\demo.py
python learning\phase01_foundation\12_langgraph_intro\demo.py
python learning\phase01_foundation\13_short_term_memory\demo.py
python -m unittest discover -s learning\phase01_foundation\tests -v
```

## 关于第三方 OpenAI 兼容接口

你的配置使用 OpenAI 兼容 `base_url`。文本生成通常最容易兼容，但以下能力要以服务商实际支持为准：

- Responses API
- Structured Outputs
- Embeddings
- 文件上传
- Hosted tools，例如 Web Search、File Search
- MCP 工具

课程中会把能力差异显式写出来。遇到不支持时，先区分“课程代码问题”和“兼容端点未实现该能力”。

## 阶段一验收

- 能解释一次 Agent 请求从 Prompt 到答案的完整链路。
- 能实现一个结构化输出接口和一个工具调用循环。
- 能解释切分、Embedding、召回、上下文组装和生成之间的关系。
- 能运行最小 RAG，并知道何时替换为真实向量数据库。
- 能用 LangGraph 表达条件分支。
- 能把 Agent 封装为 FastAPI 服务，并用 LangSmith 追踪调用。

本次生成后已经执行过的本地检查见 `VERIFICATION.md`。
