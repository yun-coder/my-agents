# 阶段一验证记录

生成后已在当前仓库虚拟环境中执行以下验证。

## 已通过

```powershell
.\.venv\Scripts\python.exe -m compileall -q .\learning\phase01_foundation
.\.venv\Scripts\python.exe -m unittest discover -s .\learning\phase01_foundation\tests -v
```

结果：全部 Python 文件编译通过，9 个离线单元测试通过。

已实际运行的离线示例：

- `01_prompt_engineering/demo.py`
- `05_function_calling/demo.py`
- `06_embeddings/demo.py`
- `07_vector_databases/demo.py`
- `08_document_parsing/demo.py`
- `09_rag_foundation/demo.py`
- `11_llamaindex/demo.py` 默认流程说明模式
- `13_short_term_memory/demo.py`
- `16_python_engineering/demo.py`
- `projects/rag_agent_mvp/cli.py`

综合项目已验证：

- RAG 召回
- 无关问题停止生成
- 计算器工具
- 一元负数计算
- 天气工具
- 未知城市不再默认按北京处理
- 配置读取不打印密钥

## 安装依赖

阶段一新增依赖可以通过以下命令安装或复核：

```powershell
python -m pip install -r learning\phase01_foundation\requirements.txt
```

当前环境已实际验证：

```powershell
python learning\phase01_foundation\10_langchain\demo.py
python learning\phase01_foundation\12_langgraph_intro\demo.py
```

FastAPI 主服务和综合项目 API 已完成导入、健康检查以及 OpenAPI Schema 字段检查。
综合项目 `/ask` 已使用离线计算器工具完成接口调用验证。

## 手动启用在线调用

以下示例会读取根目录 `dev.json` 并产生真实模型请求：

```powershell
python learning\phase01_foundation\02_structured_outputs\demo.py
python learning\phase01_foundation\03_openai_api\demo.py
python learning\phase01_foundation\05_function_calling\demo.py --online
python learning\phase01_foundation\06_embeddings\demo.py --online
python learning\phase01_foundation\09_rag_foundation\demo.py --online
python learning\phase01_foundation\15_langsmith\demo.py
python learning\phase01_foundation\projects\rag_agent_mvp\cli.py --online "RAG 是什么？"
```

由于当前使用第三方 OpenAI 兼容端点，各项能力是否完整支持需要逐项验证。

本机现有配置的实测结果：

| 能力 | 结果 |
|---|---|
| Responses API 文本生成 | 通过 |
| Structured Outputs | 通过 |
| Function Calling 完整工具循环 | 通过，使用应用侧显式消息链 |
| Responses API 流式输出 | 通过 |
| 基础 RAG 在线回答 | 通过 |
| 综合项目在线回答 | 通过 |
| FastAPI `/chat` 在线模型调用 | 通过 |
| LangSmith 包装调用 | 通过；Trace 是否入库仍需在对应 LangSmith UI 中确认 |
| Embeddings | 未通过：端点返回 `404`，需确认服务支持情况与 Embedding 模型 ID |
| LlamaIndex 在线索引 | 依赖 Embeddings，暂不具备在线运行条件 |
