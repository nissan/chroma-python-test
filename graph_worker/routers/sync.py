from fastapi import APIRouter, Request, BackgroundTasks
from services.scheduler import run_deep_sync

router = APIRouter()


@router.post("")
async def trigger_sync(req: Request, background_tasks: BackgroundTasks):
    """Manually trigger a full Neo4j entity/relationship sync across all ChromaDB collections.

    Runs in the background — returns immediately with a 202 status.
    Check logs for completion.
    """
    neo4j = req.app.state.neo4j
    background_tasks.add_task(run_deep_sync, neo4j)
    return {"status": "sync_started", "message": "Deep sync running in background. Check logs for progress."}
