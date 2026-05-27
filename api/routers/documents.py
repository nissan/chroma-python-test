import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi import Request
from services import chroma_client, ingestion

router = APIRouter()


class UrlRequest(BaseModel):
    url: str


def _ingest_chunks(
    collection,
    embedder,
    chunks: list[tuple[str, dict]],
    doc_id: str,
) -> int:
    if not chunks:
        return 0
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    embeddings = [e.tolist() for e in embedder.embed(texts)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    chroma_client.add_chunks(collection, texts, embeddings, metadatas, ids)
    return len(chunks)


def _check_duplicate(collection, doc_id: str) -> bool:
    existing = collection.get(where={"doc_id": doc_id}, include=["metadatas"])
    return bool(existing.get("metadatas"))


@router.get("")
async def list_documents(req: Request):
    collection = req.app.state.chroma_collection
    return chroma_client.list_documents(collection)


@router.post("/upload")
async def upload_document(req: Request, file: UploadFile = File(...)):
    collection = req.app.state.chroma_collection
    embedder = req.app.state.embedder

    filename = file.filename or "unknown"
    doc_id = ingestion.generate_doc_id(filename)

    if _check_duplicate(collection, doc_id):
        raise HTTPException(
            status_code=409,
            detail=f"Document '{filename}' already ingested (doc_id={doc_id}). Delete it first.",
        )

    content = await file.read()
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf" or file.content_type == "application/pdf":
        text = ingestion.parse_pdf(content)
        file_type = "pdf"
    elif ext == ".docx" or file.content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        text = ingestion.parse_docx(content)
        file_type = "docx"
    elif ext in (".md", ".txt", ".markdown") or (file.content_type or "").startswith("text/"):
        text = ingestion.parse_text(content)
        file_type = ext.lstrip(".") or "text"
    else:
        text = ingestion.parse_text(content)
        file_type = "text"

    chunks = ingestion.chunk_text(text, filename, doc_id, file_type)
    count = _ingest_chunks(collection, embedder, chunks, doc_id)

    return {"doc_id": doc_id, "chunks_ingested": count, "source_file": filename}


@router.post("/url")
async def ingest_url(req: Request, body: UrlRequest):
    collection = req.app.state.chroma_collection
    embedder = req.app.state.embedder

    url = str(body.url)
    doc_id = ingestion.generate_doc_id(url)

    if _check_duplicate(collection, doc_id):
        raise HTTPException(
            status_code=409,
            detail=f"URL already ingested (doc_id={doc_id}). Delete it first.",
        )

    try:
        text = ingestion.parse_url(url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to fetch URL: {e}")

    chunks = ingestion.chunk_text(text, url, doc_id, "url")
    count = _ingest_chunks(collection, embedder, chunks, doc_id)

    return {"doc_id": doc_id, "chunks_ingested": count, "source_file": url}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, req: Request):
    collection = req.app.state.chroma_collection
    chroma_client.delete_by_doc_id(collection, doc_id)
    return {"deleted": True, "doc_id": doc_id}
