from strands import tool


@tool
def web_search(query: str, max_results: int = 8) -> str:
    """Search the web using DuckDuckGo and return a summary of results.

    Use this for finding current technical documentation, library best practices,
    troubleshooting guides, or any information not in the local knowledge base.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 8).

    Returns:
        Formatted string with result titles, URLs, and snippets.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "Error: duckduckgo-search package not installed."

    results = list(DDGS().text(query, max_results=max_results))
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', 'No title')}")
        lines.append(f"    URL: {r.get('href', '')}")
        lines.append(f"    {r.get('body', '')}\n")
    return "\n".join(lines)
