import httpx
from bs4 import BeautifulSoup
from strands import tool


@tool
def url_scrape(url: str) -> str:
    """Fetch a web page and return its clean text content.

    Strips navigation, scripts, and boilerplate — returns the main readable text.
    Use this to read documentation pages, articles, or any web content for context.

    Args:
        url: The full URL to fetch (must include http:// or https://).

    Returns:
        Clean plain text extracted from the page, or an error message.
    """
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        return f"Error fetching {url}: {e}"

    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse excessive blank lines
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)
