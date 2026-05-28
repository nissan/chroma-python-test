"""Orchestrator Strands agent — routes requests to coding/research agents and filters by tech level."""
import httpx
from strands import Agent, tool
from strands.models.ollama import OllamaModel

from config import settings

_SYSTEM_PROMPT = """\
You are a helpful AI concierge for a multi-agent RAG system.

Your capabilities:
1. Answer broad, general questions directly from your knowledge.
2. Route code/repository questions to the Coding Intelligence Agent.
3. Route library best-practices or troubleshooting questions to the Research Agent.

After composing your answer, rewrite it at the specified technical level:
- deep: implementation details, algorithm complexity, code references, precise terminology
- mid: explain concepts with examples, minimal jargon, assume basic programming knowledge
- junior: plain English, real-world analogies, no assumed technical knowledge

Always cite sources when sub-agents provide them. Format citations as footnotes: [1], [2], etc.
"""


def create_agent(embedder, collection, neo4j_client) -> Agent:
    from services.chroma_client import graph_augmented_query

    @tool
    def search_knowledge_base(query: str) -> str:
        """Search the orchestrator's general knowledge base for context."""
        results = graph_augmented_query(collection, embedder, query, neo4j_client)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        if not docs:
            return "No relevant content found in knowledge base."
        parts = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source", "unknown") if meta else "unknown"
            parts.append(f"[Source: {source}]\n{doc}")
        return "\n\n---\n\n".join(parts)

    @tool
    def call_coding_agent(question: str) -> str:
        """Route a code, repository, or implementation question to the Coding Intelligence Agent.

        Use this when the user asks about specific repositories, code patterns, programming languages,
        frameworks, or implementation details of software projects.
        """
        try:
            resp = httpx.post(
                f"{settings.coding_agent_url}/chat/internal",
                json={"message": question},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("answer", "Coding agent returned no answer.")
        except httpx.HTTPError as e:
            return f"Coding agent unavailable: {e}"

    @tool
    def call_research_agent(question: str) -> str:
        """Route a research question to the Research Agent for web search and best-practice lookup.

        Use this when the user asks about library documentation, best practices, troubleshooting,
        or needs current information from the web beyond the knowledge base.
        """
        try:
            resp = httpx.post(
                f"{settings.research_agent_url}/chat/internal",
                json={"message": question},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("answer", "Research agent returned no answer.")
        except httpx.HTTPError as e:
            return f"Research agent unavailable: {e}"

    model = OllamaModel(host=settings.ollama_base_url, model_id=settings.ollama_model)
    return Agent(
        model=model,
        tools=[search_knowledge_base, call_coding_agent, call_research_agent],
        system_prompt=_SYSTEM_PROMPT,
    )
