from rag_skills._chunker import chunk_text, generate_doc_id


def test_generate_doc_id_deterministic():
    assert generate_doc_id("hello") == generate_doc_id("hello")
    assert generate_doc_id("hello") != generate_doc_id("world")
    assert len(generate_doc_id("anything")) == 12


def test_chunk_text_basic():
    text = " ".join(["word"] * 600)
    chunks = chunk_text(text, "test.txt", "abc123", "text")
    assert len(chunks) > 1
    for content, meta in chunks:
        assert isinstance(content, str)
        assert meta["source"] == "test.txt"
        assert meta["doc_id"] == "abc123"
        assert meta["source_type"] == "text"
        assert "chunk_index" in meta


def test_chunk_text_extra_meta():
    chunks = chunk_text("hello world", "src.py", "def456", "github", extra_meta={"repo": "owner/repo"})
    assert chunks[0][1]["repo"] == "owner/repo"


def test_chunk_text_empty():
    assert chunk_text("", "empty.txt", "000000", "text") == []
