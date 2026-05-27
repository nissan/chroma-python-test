import chromadb
from config import settings


def get_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)


def get_or_create_collection(client: chromadb.HttpClient):
    return client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    collection,
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str],
) -> None:
    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )


def query_collection(
    collection,
    embedding: list[float],
    n_results: int = 5,
) -> dict:
    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def delete_by_doc_id(collection, doc_id: str) -> None:
    collection.delete(where={"doc_id": doc_id})


def list_documents(collection) -> list[dict]:
    """Return unique documents grouped by doc_id with chunk count."""
    result = collection.get(include=["metadatas"])
    metadatas = result.get("metadatas") or []

    docs: dict[str, dict] = {}
    for meta in metadatas:
        if not meta:
            continue
        doc_id = meta.get("doc_id", "unknown")
        if doc_id not in docs:
            docs[doc_id] = {
                "doc_id": doc_id,
                "source_file": meta.get("source_file", "unknown"),
                "file_type": meta.get("file_type", "unknown"),
                "chunk_count": 0,
            }
        docs[doc_id]["chunk_count"] += 1

    return list(docs.values())
