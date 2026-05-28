from strands import tool
from ._chunker import chunk_text, generate_doc_id


def make_pdf_ingest_tool(collection, embedder):
    """Return a Strands @tool that ingests PDF bytes into the given ChromaDB collection.

    Args:
        collection: ChromaDB collection object.
        embedder: fastembed TextEmbedding instance.
    """

    @tool
    def pdf_ingest(filename: str, content_base64: str) -> str:
        """Ingest a PDF document into the knowledge base by parsing and chunking it.

        Args:
            filename: Original filename (used as source identifier).
            content_base64: Base64-encoded PDF bytes.

        Returns:
            Summary of chunks ingested.
        """
        import base64
        import fitz  # PyMuPDF

        raw = base64.b64decode(content_base64)
        doc = fitz.open(stream=raw, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()

        doc_id = generate_doc_id(filename)
        chunks = chunk_text(text, filename, doc_id, "pdf")
        _store_chunks(collection, embedder, chunks, doc_id)
        return f"Ingested {len(chunks)} chunks from PDF '{filename}' (doc_id={doc_id})"

    return pdf_ingest


def _store_chunks(collection, embedder, chunks: list[tuple[str, dict]], doc_id: str) -> None:
    if not chunks:
        return
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    embeddings = [e.tolist() for e in embedder.embed(texts)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
