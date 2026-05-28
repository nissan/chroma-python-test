import httpx
from strands import tool
from ._chunker import chunk_text, generate_doc_id

_ALLOWED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json", ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h"}
_MAX_FILE_BYTES = 100_000


def make_github_ingest_tool(collection, embedder, *, github_token: str | None = None):
    """Return a Strands @tool that ingests a GitHub repository into the given ChromaDB collection.

    Args:
        collection: ChromaDB collection object.
        embedder: fastembed TextEmbedding instance.
        github_token: Optional GitHub personal access token (raises rate limit from 60 to 5000 req/hr).
    """
    headers = {"Authorization": f"token {github_token}"} if github_token else {}

    @tool
    def github_ingest(repo_url: str) -> str:
        """Fetch all source files from a GitHub repository and ingest them into the knowledge base.

        Ingests .py, .ts, .js, .md, .yaml, .go, .rs, .java, .cs and similar source files.
        Files larger than 100KB are skipped.

        Args:
            repo_url: Full GitHub repository URL, e.g. https://github.com/owner/repo

        Returns:
            Summary of files and chunks ingested.
        """
        owner, repo = _parse_github_url(repo_url)
        if not owner:
            return f"Could not parse GitHub URL: {repo_url}. Expected https://github.com/owner/repo"

        api_base = f"https://api.github.com/repos/{owner}/{repo}"

        # Get default branch
        try:
            meta = httpx.get(api_base, headers=headers, timeout=15).json()
            branch = meta.get("default_branch", "main")
        except Exception as e:
            return f"Error fetching repo metadata: {e}"

        # Get recursive file tree
        try:
            tree_resp = httpx.get(
                f"{api_base}/git/trees/{branch}?recursive=1",
                headers=headers,
                timeout=30,
            ).json()
        except Exception as e:
            return f"Error fetching file tree: {e}"

        blobs = [
            item for item in tree_resp.get("tree", [])
            if item["type"] == "blob"
            and any(item["path"].endswith(ext) for ext in _ALLOWED_EXTENSIONS)
            and item.get("size", 0) <= _MAX_FILE_BYTES
        ]

        total_chunks = 0
        skipped = 0
        raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"

        for blob in blobs:
            try:
                raw = httpx.get(f"{raw_base}/{blob['path']}", headers=headers, timeout=15)
                raw.raise_for_status()
                text = raw.text
            except Exception:
                skipped += 1
                continue

            ext = "." + blob["path"].rsplit(".", 1)[-1] if "." in blob["path"] else ""
            source = f"{repo_url}/blob/{branch}/{blob['path']}"
            doc_id = generate_doc_id(source)
            chunks = chunk_text(
                text, source, doc_id, "github",
                extra_meta={"repo": f"{owner}/{repo}", "filepath": blob["path"], "language": ext.lstrip(".")},
            )
            _store_chunks(collection, embedder, chunks, doc_id)
            total_chunks += len(chunks)

        return (
            f"Ingested {len(blobs) - skipped}/{len(blobs)} files, "
            f"{total_chunks} chunks from {repo_url} (skipped {skipped} errors)"
        )

    return github_ingest


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL."""
    url = url.rstrip("/").rstrip(".git")
    # Strip protocol and check domain is exactly github.com
    domain_part = url.split("://", 1)[-1]
    if not domain_part.startswith("github.com/"):
        return "", ""
    parts = url.split("github.com/")
    if len(parts) != 2:
        return "", ""
    segments = parts[1].split("/")
    if len(segments) < 2:
        return "", ""
    return segments[0], segments[1]


def _store_chunks(collection, embedder, chunks: list[tuple[str, dict]], doc_id: str) -> None:
    if not chunks:
        return
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    embeddings = [e.tolist() for e in embedder.embed(texts)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
