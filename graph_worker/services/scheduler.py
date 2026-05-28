"""APScheduler nightly deep-sync job and on-demand sync logic."""
import logging
import chromadb
from fastembed import TextEmbedding
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from services.neo4j_client import Neo4jClient
from services.extractor import extract_entities_and_relationships

logger = logging.getLogger(__name__)

_COLLECTIONS = ["orchestrator_docs", "coding_intel", "research_cache"]


async def run_deep_sync(neo4j: Neo4jClient):
    """Scan all ChromaDB collections and upsert entities/relationships to Neo4j."""
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    total_processed = 0

    for col_name in _COLLECTIONS:
        try:
            col = client.get_collection(col_name)
        except Exception:
            logger.debug("Collection %s does not exist yet, skipping", col_name)
            continue

        count = col.count()
        if count == 0:
            continue

        # Fetch all chunks in batches of 100
        offset = 0
        batch_size = 100
        while offset < count:
            batch = col.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
            docs = batch.get("documents") or []
            metas = batch.get("metadatas") or []
            ids = batch.get("ids") or []

            for chunk_text, meta, chunk_id in zip(docs, metas, ids):
                doc_id = meta.get("doc_id", "unknown")
                source = meta.get("source", "")
                entities, relationships = extract_entities_and_relationships(
                    chunk_text, settings.ollama_base_url, settings.ollama_model
                )
                neo4j.upsert_document(doc_id, source, source, col_name)
                for ent in entities:
                    neo4j.upsert_entity(ent["name"], ent.get("type", "concept"), doc_id, col_name)
                for rel in relationships:
                    neo4j.upsert_relationship(
                        rel["from"], rel["to"], rel.get("type", "related_to"),
                        rel.get("confidence", 0.8), chunk_id,
                    )
                total_processed += 1

            offset += batch_size

    logger.info("Deep sync complete: processed %d chunks across %d collections", total_processed, len(_COLLECTIONS))
    return total_processed


def create_scheduler(neo4j: Neo4jClient) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: run_deep_sync(neo4j),
        CronTrigger(hour=2, minute=0),
        id="nightly_deep_sync",
        name="Nightly Neo4j deep sync",
        replace_existing=True,
    )
    return scheduler
