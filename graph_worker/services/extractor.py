"""Entity + relationship extraction from text chunks using Ollama LLM."""
import json
import logging
import httpx

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
Analyse the following text chunk and extract named entities and relationships between them.

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "entities": [
    {{"name": "FastAPI", "type": "library"}},
    {{"name": "Pydantic", "type": "library"}}
  ],
  "relationships": [
    {{"from": "FastAPI", "to": "Pydantic", "type": "depends_on", "confidence": 0.95}}
  ]
}}

Entity types: library, framework, class, function, concept, pattern, language, tool, person, organisation, url
Relationship types: depends_on, extends, implements, uses, defines, part_of, related_to, documented_by

Text chunk:
{chunk}
"""


def extract_entities_and_relationships(
    chunk_text: str,
    ollama_base_url: str,
    model: str,
) -> tuple[list[dict], list[dict]]:
    """Call Ollama to extract entities and relationships from a text chunk.

    Returns:
        (entities, relationships) where each is a list of dicts.
        Returns ([], []) on parse failure.
    """
    prompt = _EXTRACTION_PROMPT.format(chunk=chunk_text[:2000])
    try:
        resp = httpx.post(
            f"{ollama_base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        # Strip any accidental markdown fences
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        return data.get("entities", []), data.get("relationships", [])
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.warning("Entity extraction failed for chunk: %s", e)
        return [], []
