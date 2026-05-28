"""
rag-skills: shared Strands tool library for the multi-agent RAG system.

Stateless tools (use directly):
    web_search      — DuckDuckGo full-text search
    url_scrape      — fetch a URL and return clean text

Stateful skill factories (inject collection + embedder, get a @tool back):
    make_pdf_ingest_tool(collection, embedder)
    make_docx_ingest_tool(collection, embedder)
    make_url_ingest_tool(collection, embedder)
    make_github_ingest_tool(collection, embedder, *, github_token=None)
    make_youtube_ingest_tool(collection, embedder)   # requires yt-dlp extra
"""

from .web_search import web_search
from .url_scrape import url_scrape
from .pdf_ingest import make_pdf_ingest_tool
from .docx_ingest import make_docx_ingest_tool
from .url_ingest import make_url_ingest_tool
from .github_ingest import make_github_ingest_tool

__all__ = [
    "web_search",
    "url_scrape",
    "make_pdf_ingest_tool",
    "make_docx_ingest_tool",
    "make_url_ingest_tool",
    "make_github_ingest_tool",
]
