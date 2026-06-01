# 14 FastAPI / API 服务封装

## 学习目标

- 把 Agent 能力封装为 HTTP 服务。
- 理解请求模型、响应模型、异常处理和健康检查。
- 为后续 SSE、WebSocket、鉴权和限流打基础。

## 最小服务

```text
POST /chat -> 校验请求 -> 调用模型 -> 返回答案
GET /health -> 返回服务状态
```

## 工程实践

- 使用 Pydantic 模型约束请求和响应。
- 不把异常堆栈直接暴露给外部用户。
- 为模型调用设置超时、重试和请求 ID。
- 区分同步接口、流式 SSE 和 WebSocket 的适用场景。

## 运行

```powershell
uvicorn demo:app --app-dir learning\phase01_foundation\14_fastapi --reload
```

## 参考资料

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

## 验收清单

- 能调用 `/health`。
- 能通过 `/chat` 发送问题。
- 能解释为什么 API 服务必须做输入校验。
