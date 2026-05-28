import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from services.neo4j_client import Neo4jClient
from services.scheduler import create_scheduler
from routers.sync import router as sync_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    try:
        neo4j.verify_connectivity()
        neo4j.create_indexes()
        logger.info("Neo4j connected at %s", settings.neo4j_uri)
    except Exception as e:
        logger.warning("Neo4j not reachable at startup: %s — will retry on requests", e)

    app.state.neo4j = neo4j

    scheduler = create_scheduler(neo4j)
    scheduler.start()
    logger.info("Nightly sync scheduler started (runs at 02:00)")

    yield

    scheduler.shutdown(wait=False)
    neo4j.close()


app = FastAPI(title="Graph Worker", lifespan=lifespan)
app.include_router(sync_router, prefix="/graph/sync")


@app.get("/health")
async def health():
    try:
        app.state.neo4j.verify_connectivity()
        neo4j_status = "ok"
    except Exception:
        neo4j_status = "unreachable"
    return {"status": "ok", "neo4j": neo4j_status}
