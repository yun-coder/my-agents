# 阶段二：Agent 编排与生产化

阶段二在阶段一闭环之上增加状态恢复、多人协作、工具协议、安全、评估和部署。

| 序号 | 知识点 | 默认 Demo |
|---:|---|---|
| 17 | LangGraph 深入 | Checkpoint 与人工审批 |
| 18 | AutoGen / AG2 | 多角色消息协作 |
| 19 | CrewAI | Agent、Task、Crew 顺序流程 |
| 20 | MCP | FastMCP 工具服务器 |
| 21 | 长期记忆 | SQLite 用户偏好记忆 |
| 22 | 状态持久化 | SQLite 任务 Checkpoint |
| 23 | Reranker | 召回后精排 |
| 24 | RAG 评估 | 离线评估指标 |
| 25 | LLM 可观测性 | Trace 与 Observation |
| 26 | Guardrails | 输入、检索、执行、输出护栏 |
| 27 | Prompt Injection Defense | 直接与间接注入检测 |
| 28 | 浏览器自动化 | Playwright 安全浏览 |
| 29 | 代码执行沙箱 | AST 校验与超时 |
| 30 | Docker Compose | 服务编排配置 |

运行验证：

```powershell
python -m compileall -q learning\phase02_production
python -m unittest discover -s learning\phase02_production\tests -v
```

综合项目见 `projects/secure_workflow/README.md`。
