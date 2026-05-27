import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastembed import TextEmbedding

from config import settings
from routers.chat import router as chat_router
from routers.documents import router as documents_router
import services.chroma_client as chroma_svc

os.environ["FASTEMBED_CACHE_PATH"] = "/app/models"

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading fastembed model …")
    app.state.embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    logger.info("Model loaded.")

    logger.info("Connecting to ChromaDB …")
    client = chroma_svc.get_client()
    app.state.chroma_collection = chroma_svc.get_or_create_collection(client)
    logger.info("ChromaDB ready. Collection: %s", settings.chroma_collection)

    yield

    logger.info("Shutting down.")


app = FastAPI(title="RAG API", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in settings.api_cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(documents_router, prefix="/documents", tags=["documents"])


@app.get("/health")
async def health():
    from services.ollama_client import health_check
    ollama_ok = await health_check()
    return {
        "status": "ok",
        "model": settings.ollama_model,
        "collection": settings.chroma_collection,
        "ollama_reachable": ollama_ok,
    }
