"""阶段一 RAG Agent MVP FastAPI 入口。"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core import KnowledgeAgent, KnowledgeBase

app = FastAPI(title="Phase 01 RAG Agent MVP")
agent = KnowledgeAgent(
    KnowledgeBase.from_markdown_directory(Path(__file__).with_name("data"))
)


class AskRequest(BaseModel):
    # question：用户问题，必填。
    question: str = Field(
        min_length=1,
        max_length=1000,
        description="用户提交给知识库 Agent 的问题。",
    )
    # session_id：区分会话记忆。演示环境默认使用 default。
    session_id: str = Field(
        default="default",
        min_length=1,
        max_length=100,
        description="短期记忆所属会话 ID。",
    )
    # online：False 时只展示离线召回；True 时调用 dev.json 中配置的模型。
    online: bool = Field(
        default=False,
        description="是否启用在线模型生成。",
    )


class AskResponse(BaseModel):
    # answer：工具结果、离线召回说明或在线模型生成答案。
    answer: str = Field(description="工具结果、离线召回说明或在线模型生成答案。")
    # sources：本次回答使用的知识库分块定位。
    sources: list[str] = Field(description="本次回答使用的知识库分块定位。")
    # tool_name：如果由本地工具直接回答，则返回工具名称。
    tool_name: str | None = Field(
        default=None,
        description="如果由本地工具直接回答，则返回工具名称。",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    result = agent.ask(request.question, request.session_id, request.online)
    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        tool_name=result.tool_name,
    )
