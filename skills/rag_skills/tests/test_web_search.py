from unittest.mock import patch, MagicMock
from rag_skills.web_search import web_search


def test_web_search_formats_results():
    mock_results = [
        {"title": "FastAPI Docs", "href": "https://fastapi.tiangolo.com", "body": "FastAPI is a modern web framework."},
        {"title": "Starlette", "href": "https://www.starlette.io", "body": "Starlette is the foundation."},
    ]
    with patch("duckduckgo_search.DDGS") as MockDDGS:
        MockDDGS.return_value.text.return_value = mock_results
        result = web_search("fastapi python")

    assert "FastAPI Docs" in result
    assert "https://fastapi.tiangolo.com" in result
    assert "[1]" in result
    assert "[2]" in result


def test_web_search_no_results():
    with patch("duckduckgo_search.DDGS") as MockDDGS:
        MockDDGS.return_value.text.return_value = []
        result = web_search("zzznoresultsquery")
    assert "No results" in result
