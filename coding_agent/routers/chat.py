import json
from typing import Literal
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

TechLevel = Literal["deep", "mid", "junior"]


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    tech_level: TechLevel = "mid"


@router.post("")
async def chat(request: ChatRequest, req: Request):
    agent = req.app.state.agent

    async def sse_generator():
        try:
            response = agent(request.message)
            yield f"data: {json.dumps({'content': str(response)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/internal")
async def chat_internal(request: ChatRequest, req: Request):
    """Non-streaming endpoint for orchestrator-to-agent calls."""
    agent = req.app.state.agent
    try:
        response = agent(request.message)
        return {"answer": str(response)}
    except Exception as e:
        return {"answer": f"Error: {e}"}
