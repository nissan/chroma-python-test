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
from services.neo4j_client import Neo4jClient
from agent import create_agent

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

    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    try:
        neo4j.verify_connectivity()
        logger.info("Neo4j connected at %s", settings.neo4j_uri)
    except Exception as e:
        logger.warning("Neo4j not reachable at startup: %s — graph features will degrade gracefully", e)
    app.state.neo4j = neo4j

    app.state.agent = create_agent(app.state.embedder, app.state.chroma_collection, neo4j)
    logger.info("Strands orchestrator agent ready.")

    yield

    neo4j.close()
    logger.info("Shutting down.")


app = FastAPI(title="Orchestrator", version="0.2.0", lifespan=lifespan)

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
    try:
        app.state.neo4j.verify_connectivity()
        neo4j_status = "ok"
    except Exception:
        neo4j_status = "unreachable"
    return {
        "status": "ok",
        "model": settings.ollama_model,
        "collection": settings.chroma_collection,
        "ollama_reachable": ollama_ok,
        "neo4j": neo4j_status,
    }
