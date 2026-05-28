from strands import tool
from ._chunker import chunk_text, generate_doc_id


def make_docx_ingest_tool(collection, embedder):
    """Return a Strands @tool that ingests DOCX bytes into the given ChromaDB collection."""

    @tool
    def docx_ingest(filename: str, content_base64: str) -> str:
        """Ingest a Word document (.docx) into the knowledge base.

        Args:
            filename: Original filename.
            content_base64: Base64-encoded DOCX bytes.

        Returns:
            Summary of chunks ingested.
        """
        import base64
        import io
        from docx import Document

        raw = base64.b64decode(content_base64)
        doc = Document(io.BytesIO(raw))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

        doc_id = generate_doc_id(filename)
        chunks = chunk_text(text, filename, doc_id, "docx")
        _store_chunks(collection, embedder, chunks, doc_id)
        return f"Ingested {len(chunks)} chunks from DOCX '{filename}' (doc_id={doc_id})"

    return docx_ingest


def _store_chunks(collection, embedder, chunks: list[tuple[str, dict]], doc_id: str) -> None:
    if not chunks:
        return
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    embeddings = [e.tolist() for e in embedder.embed(texts)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
