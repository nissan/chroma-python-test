"""Ingest router — explicit document ingestion endpoints for the Coding Intelligence Agent."""
import base64
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel

from rag_skills.github_ingest import make_github_ingest_tool
from rag_skills.youtube_ingest import make_youtube_ingest_tool
from rag_skills.url_ingest import make_url_ingest_tool
from rag_skills.pdf_ingest import make_pdf_ingest_tool
from rag_skills.docx_ingest import make_docx_ingest_tool
from rag_skills._chunker import generate_doc_id
from config import settings

router = APIRouter()


class UrlBody(BaseModel):
    url: str


class GitHubBody(BaseModel):
    repo_url: str


class YouTubeBody(BaseModel):
    video_url: str


def _check_duplicate(collection, doc_id: str) -> bool:
    existing = collection.get(where={"doc_id": doc_id}, include=["metadatas"])
    return bool(existing.get("metadatas"))


@router.get("")
async def list_ingested(req: Request):
    from services.chroma_client import list_documents
    return list_documents(req.app.state.chroma_collection)


@router.post("/github")
async def ingest_github(body: GitHubBody, req: Request):
    collection = req.app.state.chroma_collection
    embedder = req.app.state.embedder
    tool = make_github_ingest_tool(collection, embedder, github_token=settings.github_token or None)
    result = tool(body.repo_url)
    return {"result": result}


@router.post("/youtube")
async def ingest_youtube(body: YouTubeBody, req: Request):
    collection = req.app.state.chroma_collection
    embedder = req.app.state.embedder
    tool = make_youtube_ingest_tool(collection, embedder)
    result = tool(body.video_url)
    return {"result": result}


@router.post("/url")
async def ingest_url(body: UrlBody, req: Request):
    collection = req.app.state.chroma_collection
    embedder = req.app.state.embedder
    doc_id = generate_doc_id(body.url)
    if _check_duplicate(collection, doc_id):
        raise HTTPException(status_code=409, detail=f"URL already ingested (doc_id={doc_id}). Delete it first.")
    tool = make_url_ingest_tool(collection, embedder)
    result = tool(body.url)
    return {"result": result}


@router.post("/file")
async def ingest_file(req: Request, file: UploadFile = File(...)):
    collection = req.app.state.chroma_collection
    embedder = req.app.state.embedder
    filename = file.filename or "unknown"
    content = await file.read()
    content_b64 = base64.b64encode(content).decode()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        tool = make_pdf_ingest_tool(collection, embedder)
        result = tool(filename, content_b64)
    elif ext == "docx":
        tool = make_docx_ingest_tool(collection, embedder)
        result = tool(filename, content_b64)
    else:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: .{ext}. Use /ingest/url for text/markdown.")
    return {"result": result}


@router.delete("/{doc_id}")
async def delete_ingested(doc_id: str, req: Request):
    req.app.state.chroma_collection.delete(where={"doc_id": doc_id})
    return {"deleted": True, "doc_id": doc_id}
