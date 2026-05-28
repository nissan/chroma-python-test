from unittest.mock import patch, MagicMock
from rag_skills.url_scrape import url_scrape


def _mock_response(html: str, status: int = 200):
    mock = MagicMock()
    mock.text = html
    mock.status_code = status
    mock.raise_for_status = MagicMock()
    return mock


def test_url_scrape_extracts_text():
    html = "<html><body><p>Hello world</p><script>bad</script></body></html>"
    with patch("httpx.get", return_value=_mock_response(html)):
        result = url_scrape("https://example.com")
    assert "Hello world" in result
    assert "bad" not in result


def test_url_scrape_strips_nav():
    html = "<html><body><nav>Menu</nav><main><p>Content</p></main></body></html>"
    with patch("httpx.get", return_value=_mock_response(html)):
        result = url_scrape("https://example.com")
    assert "Content" in result


def test_url_scrape_http_error():
    import httpx
    with patch("httpx.get", side_effect=httpx.HTTPError("connection refused")):
        result = url_scrape("https://bad.example.com")
    assert "Error" in result


def test_url_scrape_is_strands_tool():
    from strands.tools.decorator import DecoratedFunctionTool
    assert isinstance(url_scrape, DecoratedFunctionTool)
