"""Research Strands agent — web search + cached knowledge for library docs and best practices."""
from strands import Agent, tool
from strands.models.ollama import OllamaModel

from config import settings

_SYSTEM_PROMPT = """\
You are a Research Agent. You specialise in finding current technical documentation, library best practices,
troubleshooting guides, and up-to-date information from the web.

When answering:
1. First search your local knowledge base for cached research.
2. Then use web_search to find current information if needed.
3. Use url_scrape to read specific pages in full when a search result looks highly relevant.
4. Always cite your sources with URLs.
5. Prefer official documentation and reputable technical sources.
"""


def create_agent(embedder, collection, neo4j_client) -> Agent:
    from services.chroma_client import graph_augmented_query
    from rag_skills.web_search import web_search
    from rag_skills.url_scrape import url_scrape
    from rag_skills.url_ingest import make_url_ingest_tool

    @tool
    def search_research_cache(query: str) -> str:
        """Search the cached research knowledge base for previously found documentation and articles."""
        results = graph_augmented_query(collection, embedder, query, neo4j_client)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        if not docs:
            return "No cached research found for this query."
        parts = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source", "unknown") if meta else "unknown"
            parts.append(f"[Source: {source}]\n{doc}")
        return "\n\n---\n\n".join(parts)

    url_ingest = make_url_ingest_tool(collection, embedder)

    model = OllamaModel(host=settings.ollama_base_url, model_id=settings.ollama_model)
    return Agent(
        model=model,
        tools=[search_research_cache, web_search, url_scrape, url_ingest],
        system_prompt=_SYSTEM_PROMPT,
    )
