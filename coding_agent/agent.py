"""Coding Intelligence Strands agent — specialised in code repositories, patterns, and implementations."""
from strands import Agent, tool
from strands.models.ollama import OllamaModel

from config import settings

_SYSTEM_PROMPT = """\
You are a Coding Intelligence Agent. You specialise in understanding source code, software architecture,
programming patterns, and the repositories that have been ingested into your knowledge base.

When answering questions:
1. Search your knowledge base for relevant code examples and documentation.
2. Cite the specific file and repository for any code you reference.
3. Explain patterns concisely — code speaks louder than descriptions.
4. If something is not in your knowledge base, clearly say so.
"""


def create_agent(embedder, collection, neo4j_client) -> Agent:
    from services.chroma_client import graph_augmented_query
    from rag_skills.github_ingest import make_github_ingest_tool
    from rag_skills.youtube_ingest import make_youtube_ingest_tool
    from rag_skills.url_ingest import make_url_ingest_tool
    from rag_skills.pdf_ingest import make_pdf_ingest_tool

    @tool
    def search_code_knowledge(query: str) -> str:
        """Search the coding knowledge base for relevant source code, patterns, and documentation.

        Use this before answering any question about code or repositories.
        """
        results = graph_augmented_query(collection, embedder, query, neo4j_client)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        if not docs:
            return "No relevant code found in knowledge base for this query."
        parts = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source", "unknown") if meta else "unknown"
            filepath = meta.get("filepath", "") if meta else ""
            label = f"{source}" + (f" ({filepath})" if filepath else "")
            parts.append(f"[Source: {label}]\n{doc}")
        return "\n\n---\n\n".join(parts)

    github_ingest = make_github_ingest_tool(
        collection, embedder,
        github_token=settings.github_token or None,
    )
    youtube_ingest = make_youtube_ingest_tool(collection, embedder)
    url_ingest = make_url_ingest_tool(collection, embedder)
    pdf_ingest = make_pdf_ingest_tool(collection, embedder)

    model = OllamaModel(host=settings.ollama_base_url, model_id=settings.ollama_model)
    return Agent(
        model=model,
        tools=[search_code_knowledge, github_ingest, youtube_ingest, url_ingest, pdf_ingest],
        system_prompt=_SYSTEM_PROMPT,
    )
