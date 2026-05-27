from typing import AsyncGenerator
import httpx
import json
from config import settings


async def stream_chat(messages: list[dict], model: str | None = None) -> AsyncGenerator[str, None]:
    """Stream chat response from Ollama, yielding content chunks."""
    model = model or settings.ollama_model
    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                content = data.get("message", {}).get("content", "")
                if content:
                    yield content

                if data.get("done"):
                    return


async def health_check() -> bool:
    """Return True if Ollama is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
