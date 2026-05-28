import json
from typing import Literal
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services import chroma_client

router = APIRouter()

TechLevel = Literal["deep", "mid", "junior"]

_TECH_LEVEL_SUFFIX = {
    "deep": (
        "\n\nPresent this answer at a deep technical level: include implementation details, "
        "algorithmic complexity, precise terminology, and code-level references where relevant."
    ),
    "mid": (
        "\n\nPresent this answer at a mid level: explain concepts clearly with practical examples, "
        "avoid heavy jargon but assume basic programming knowledge."
    ),
    "junior": (
        "\n\nPresent this answer at a junior-friendly level: use plain English, real-world analogies, "
        "and avoid assumed technical knowledge."
    ),
}


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    tech_level: TechLevel = "mid"


@router.post("")
async def chat(request: ChatRequest, req: Request):
    agent = req.app.state.agent
    embedder = req.app.state.embedder
    collection = req.app.state.chroma_collection
    neo4j = req.app.state.neo4j

    # GraphRAG: expand query with Neo4j entities then retrieve sources for citation
    sources: list[dict] = []
    try:
        results = chroma_client.graph_augmented_query(collection, embedder, request.message, neo4j)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        sources = [
            {"title": m.get("source", "unknown"), "url": m.get("source", ""), "chunk": d[:300]}
            for d, m in zip(docs, metas) if d
        ]
    except Exception:
        pass

    # Append tech-level instruction to the message before sending to the Strands agent
    augmented_message = request.message + _TECH_LEVEL_SUFFIX.get(request.tech_level, "")

    async def sse_generator():
        try:
            # Strands Agent is called synchronously; wrap in async iteration
            # agent() returns the full response; we stream it token-by-token via Ollama callback
            # For now, stream the full response as a single SSE event then emit sources
            response = agent(augmented_message)
            answer_text = str(response)
            yield f"data: {json.dumps({'content': answer_text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if sources:
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/internal")
async def chat_internal(request: ChatRequest, req: Request):
    """Non-streaming endpoint used by orchestrator to call this agent directly."""
    agent = req.app.state.agent
    augmented_message = request.message + _TECH_LEVEL_SUFFIX.get(request.tech_level, "")
    try:
        response = agent(augmented_message)
        return {"answer": str(response)}
    except Exception as e:
        return {"answer": f"Error: {e}"}
