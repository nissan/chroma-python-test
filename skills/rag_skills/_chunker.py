import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = None


def _get_splitter():
    global _splitter
    if _splitter is None:
        _splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=500,
            chunk_overlap=50,
        )
    return _splitter


def generate_doc_id(source: str) -> str:
    return hashlib.md5(source.encode()).hexdigest()[:12]


def chunk_text(text: str, source: str, doc_id: str, source_type: str, extra_meta: dict | None = None) -> list[tuple[str, dict]]:
    """Split text into chunks and attach metadata. Returns list of (text, metadata) tuples."""
    parts = _get_splitter().split_text(text)
    base_meta = {"source": source, "doc_id": doc_id, "source_type": source_type}
    if extra_meta:
        base_meta.update(extra_meta)
    return [(part, {**base_meta, "chunk_index": i}) for i, part in enumerate(parts)]
