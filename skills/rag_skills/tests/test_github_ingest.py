from unittest.mock import patch, MagicMock, call
from rag_skills.github_ingest import make_github_ingest_tool, _parse_github_url


def test_parse_github_url():
    assert _parse_github_url("https://github.com/owner/repo") == ("owner", "repo")
    assert _parse_github_url("https://github.com/owner/repo.git") == ("owner", "repo")
    assert _parse_github_url("https://github.com/owner/repo/") == ("owner", "repo")
    assert _parse_github_url("https://notgithub.com/x/y") == ("", "")
    # Repos whose names end with letters in ".git" must not be truncated
    assert _parse_github_url("https://github.com/fastapi/fastapi") == ("fastapi", "fastapi")
    assert _parse_github_url("https://github.com/tiangolo/fastapi") == ("tiangolo", "fastapi")


def test_make_github_ingest_tool_returns_tool():
    from strands.tools.decorator import DecoratedFunctionTool
    collection = MagicMock()
    embedder = MagicMock()
    tool = make_github_ingest_tool(collection, embedder)
    assert isinstance(tool, DecoratedFunctionTool)


def test_github_ingest_bad_url():
    collection = MagicMock()
    embedder = MagicMock()
    tool = make_github_ingest_tool(collection, embedder)
    result = tool("https://notgithub.com/foo")
    assert "Could not parse" in result


def test_github_ingest_stores_chunks():
    collection = MagicMock()
    embedder = MagicMock()
    # embed() is called once per file; return one mock embedding per text in the batch
    embedder.embed.side_effect = lambda texts: [MagicMock(tolist=lambda: [0.1] * 384) for _ in texts]

    meta_resp = MagicMock()
    meta_resp.json.return_value = {"default_branch": "main"}

    tree_resp = MagicMock()
    tree_resp.json.return_value = {
        "tree": [
            {"type": "blob", "path": "README.md", "size": 100},
            {"type": "blob", "path": "main.py", "size": 200},
            {"type": "tree", "path": "src", "size": 0},  # directory, should be skipped
        ]
    }

    file_resp = MagicMock()
    file_resp.text = "# Hello\nThis is a test file with enough content to chunk properly."
    file_resp.raise_for_status = MagicMock()

    with patch("httpx.get", side_effect=[meta_resp, tree_resp, file_resp, file_resp]):
        tool = make_github_ingest_tool(collection, embedder)
        result = tool("https://github.com/owner/repo")

    assert "Ingested" in result
    assert collection.add.called
