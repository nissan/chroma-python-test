import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services import ollama_client, chroma_client

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("")
async def chat(request: ChatRequest, req: Request):
    embedder = req.app.state.embedder
    collection = req.app.state.chroma_collection

    # Embed the user message (fastembed returns a generator)
    embedding = list(embedder.embed([request.message]))[0].tolist()

    # Retrieve relevant context from ChromaDB
    context = ""
    try:
        results = chroma_client.query_collection(collection, embedding, n_results=5)
        docs = results.get("documents", [[]])[0]
        if docs:
            context = "\n\n".join(d for d in docs if d)
    except Exception:
        pass  # No documents yet — proceed without context

    # Build messages for Ollama
    system_content = (
        "You are a helpful assistant. Use the following context to answer the user's question.\n\n"
        f"Context:\n{context}\n\n"
        "If the context does not contain relevant information, answer from your general knowledge "
        "and let the user know the context was not helpful."
        if context
        else "You are a helpful assistant."
    )

    messages = [
        {"role": "system", "content": system_content},
        *request.history,
        {"role": "user", "content": request.message},
    ]

    async def sse_generator():
        try:
            async for chunk in ollama_client.stream_chat(messages):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
