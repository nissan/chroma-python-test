import chromadb
from config import settings


def get_client():
    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)


def get_or_create_collection(client):
    return client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def graph_augmented_query(collection, embedder, query_text: str, neo4j_client, n_results: int = 5) -> dict:
    try:
        terms = [w for w in query_text.split() if len(w) > 3]
        entity_names = neo4j_client.query_related_entities(terms, limit=10)
        expanded = query_text + (" " + " ".join(entity_names) if entity_names else "")
    except Exception:
        expanded = query_text
    embedding = list(embedder.embed([expanded]))[0].tolist()
    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def list_documents(collection) -> list[dict]:
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
                "source": meta.get("source", "unknown"),
                "source_type": meta.get("source_type", "unknown"),
                "chunk_count": 0,
            }
        docs[doc_id]["chunk_count"] += 1
    return list(docs.values())
