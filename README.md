# Multi-Agent RAG System

A multi-agent retrieval-augmented generation system built with [AWS Strands Agents SDK](https://github.com/strands-agents/sdk-python), FastAPI, ChromaDB, and Neo4j.

## Architecture

```
Mac Host (Ollama at :11434)
└── Docker network: rag-network
    ├── frontend       :3010  Vite + React + shadcn/ui
    ├── orchestrator   :8040  Strands concierge — routes + tech-level filter
    ├── coding_agent   :8041  GitHub / YouTube / URL / file ingest + code Q&A
    ├── research_agent :8042  DuckDuckGo web search + best-practice lookup
    ├── graph_worker   :8043  Neo4j entity extractor + nightly APScheduler sync
    ├── chromadb       :8030  Vector store (3 collections)
    └── neo4j          :7688  Graph database (Bolt)
```

Each agent owns one ChromaDB collection: `orchestrator_docs`, `coding_intel`, `research_cache`.

GraphRAG pattern: at query time, Neo4j related entities are appended to the query text before the vector search, improving recall across connected concepts.

## Quickstart

### Prerequisites

- Docker Desktop
- [Ollama](https://ollama.ai) installed and running (`ollama serve`)
- At least one model pulled: `ollama pull granite4` (or `mistral`, `codellama`)

### Setup

```bash
# Clone and configure
git clone https://github.com/nissan/chroma-python-test.git
cd chroma-python-test

cp .env.example .env
# Edit .env — set OLLAMA_MODEL_* to your pulled model names

# Build and start all services
docker compose build
docker compose up -d

# Verify all 7 services are healthy
docker compose ps
```

### Health checks

```bash
curl http://localhost:8040/health   # orchestrator
curl http://localhost:8041/health   # coding_agent
curl http://localhost:8042/health   # research_agent
curl http://localhost:8043/health   # graph_worker
```

### Use the UI

Open [http://localhost:3010](http://localhost:3010).

- **Chat tab** — ask questions; select tech level (Deep / Mid / Junior) in the header
- **Documents tab** — upload PDFs, DOCX, Markdown, plain text, or paste a URL

## Ingest content

```bash
# Ingest a URL into the coding agent
curl -X POST http://localhost:8041/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://fastapi.tiangolo.com/tutorial/"}'

# Ingest a GitHub repo
curl -X POST http://localhost:8041/ingest/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/tiangolo/fastapi"}'

# Trigger graph entity extraction manually
curl -X POST http://localhost:8043/graph/sync
```

## Agent responsibilities

| Agent | Port | Speciality |
|-------|------|-----------|
| **orchestrator** | 8040 | Routes requests, applies tech-level filter, emits sources |
| **coding_agent** | 8041 | Ingests repos/YouTube/docs; answers implementation questions |
| **research_agent** | 8042 | Web search via DuckDuckGo; library docs and best practices |
| **graph_worker** | 8043 | Extracts entities to Neo4j; nightly deep relationship mining at 02:00 |

## Shared skills package

All ingest and search tools live in `skills/rag_skills/` as Strands `@tool` functions. Agents register only what they need — update a skill once and rebuild the relevant agents.

| Skill | Used by |
|-------|---------|
| `github_ingest` | coding_agent |
| `youtube_ingest` | coding_agent |
| `url_ingest` | coding_agent, research_agent |
| `url_scrape` | orchestrator, research_agent |
| `pdf_ingest` | coding_agent, orchestrator |
| `docx_ingest` | coding_agent, orchestrator |
| `web_search` | research_agent |

## Environment variables

See `.env.example` for all variables. Key ones:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama endpoint |
| `OLLAMA_MODEL_ORCHESTRATOR` | `mistral` | Orchestrator model |
| `OLLAMA_MODEL_CODING` | `codellama` | Coding agent model |
| `OLLAMA_MODEL_RESEARCH` | `mistral` | Research agent model |
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j Bolt connection |
| `GITHUB_TOKEN` | _(optional)_ | Raises GitHub API limit to 5000 req/hr |

## Development

```bash
# Run skills unit tests
cd skills && pip install -e ".[youtube]" && pytest rag_skills/tests/ -v

# Rebuild a single service after code changes
docker compose build coding_agent && docker compose up -d coding_agent

# Watch logs
docker compose logs -f orchestrator
```

## Tags

- `v0.1.0-boilerplate` — single FastAPI + ChromaDB + React starter
- `v0.2.0-multi-agent` — full multi-agent architecture with Neo4j + GraphRAG
