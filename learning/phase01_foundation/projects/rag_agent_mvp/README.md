# 阶段一综合项目：企业知识库问答 Agent MVP

这是阶段一知识点的组合练习。它刻意保持轻量，先帮助你看清完整链路：

```text
用户问题
-> 短期记忆
-> 本地工具路由
-> 知识库检索
-> 组装上下文
-> 离线可解释回答 或 在线模型生成
```

## 已包含

- Markdown 文档摄取
- 简单分块
- 教学用内存向量检索
- 来源引用
- 会话级短期记忆
- 三个工具：天气、计算器、知识库来源列表
- FastAPI `/health` 与 `/ask`
- 离线模式和在线 OpenAI 兼容模式
- 基础测试

## 为什么仍然叫 MVP

为了适合第一阶段学习，它尚未替换为生产组件：

| 当前实现 | 后续替换方向 |
|---|---|
| 中文单字与双字组合的离线稀疏词法向量 | OpenAI Embeddings / BGE |
| 内存列表 | Qdrant / Chroma |
| 简单关键词工具路由 | Tool Calling |
| 进程内会话记忆 | Redis / PostgreSQL |
| Markdown 读取 | Docling / Unstructured / OCR |

## 运行命令

离线问答：

```powershell
python learning\phase01_foundation\projects\rag_agent_mvp\cli.py "RAG 是什么？"
python learning\phase01_foundation\projects\rag_agent_mvp\cli.py "计算 12 * (3 + 2)"
python learning\phase01_foundation\projects\rag_agent_mvp\cli.py "查询北京天气"
```

在线生成：

```powershell
python learning\phase01_foundation\projects\rag_agent_mvp\cli.py --online "RAG 是什么？"
```

API 服务：

```powershell
uvicorn app:app --app-dir learning\phase01_foundation\projects\rag_agent_mvp --reload
```

## 验收任务

1. 新增一篇 Markdown 文档并重新提问。
2. 新增第四个只读工具。
3. 把工具路由替换为第 05 课的 Tool Calling 循环。
4. 把离线稀疏词法向量替换为第 06 课的在线 Embedding。
5. 为回答增加 LangSmith Trace。
