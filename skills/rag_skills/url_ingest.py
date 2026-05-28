import httpx
from bs4 import BeautifulSoup
from strands import tool
from ._chunker import chunk_text, generate_doc_id


def make_url_ingest_tool(collection, embedder):
    """Return a Strands @tool that fetches a URL and ingests it into the given ChromaDB collection."""

    @tool
    def url_ingest(url: str) -> str:
        """Fetch a web page and ingest its content into the knowledge base.

        Use this to permanently add documentation pages, articles, or web resources
        to the agent's knowledge base for future retrieval.

        Args:
            url: The full URL to fetch and ingest.

        Returns:
            Summary of chunks ingested.
        """
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=15)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return f"Error fetching {url}: {e}"

        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = "\n".join(ln for ln in soup.get_text(separator="\n", strip=True).splitlines() if ln.strip())

        doc_id = generate_doc_id(url)
        chunks = chunk_text(text, url, doc_id, "url")
        _store_chunks(collection, embedder, chunks, doc_id)
        return f"Ingested {len(chunks)} chunks from {url} (doc_id={doc_id})"

    return url_ingest


def _store_chunks(collection, embedder, chunks: list[tuple[str, dict]], doc_id: str) -> None:
    if not chunks:
        return
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    embeddings = [e.tolist() for e in embedder.embed(texts)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
