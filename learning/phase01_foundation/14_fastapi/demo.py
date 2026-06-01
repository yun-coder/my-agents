"""需要在线 OpenAI 配置：最小 Agent FastAPI 服务。"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PHASE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE_ROOT))

from shared.config import ConfigError, get_openai_settings  # noqa: E402
from shared.openai_client import create_openai_client  # noqa: E402

app = FastAPI(title="Phase 01 Agent API")


class ChatRequest(BaseModel):
    # question：由调用方提交的问题。长度限制可阻止空输入和异常超长输入。
    question: str = Field(
        min_length=1,
        max_length=1000,
        description="需要交给模型回答的用户问题。",
    )


class ChatResponse(BaseModel):
    # answer：模型生成的最终文本，作为 API 的稳定输出字段。
    answer: str = Field(description="模型生成的最终文本。")


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查不调用模型，适合负载均衡器或部署平台探测。"""

    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """校验请求，调用在线模型，并返回稳定响应结构。"""

    try:
        settings = get_openai_settings()
        client = create_openai_client(settings)
        response = client.responses.create(
            model=settings.model,
            instructions="请使用简洁中文回答。",
            input=request.question,
        )
        return ChatResponse(answer=response.output_text)
    except ConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="模型服务调用失败。") from exc
