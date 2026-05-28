import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastembed import TextEmbedding

from config import settings
from routers.chat import router as chat_router
import services.chroma_client as chroma_svc
from services.neo4j_client import Neo4jClient
from agent import create_agent

os.environ["FASTEMBED_CACHE_PATH"] = "/app/models"
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    client = chroma_svc.get_client()
    app.state.chroma_collection = chroma_svc.get_or_create_collection(client)
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    try:
        neo4j.verify_connectivity()
    except Exception as e:
        logger.warning("Neo4j not reachable: %s", e)
    app.state.neo4j = neo4j
    app.state.agent = create_agent(app.state.embedder, app.state.chroma_collection, neo4j)
    logger.info("Research Agent ready. Collection: %s", settings.chroma_collection)
    yield
    neo4j.close()


app = FastAPI(title="Research Agent", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.ollama_model, "collection": settings.chroma_collection}
