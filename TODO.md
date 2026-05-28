# Project TODO

Tracks all planned work. Updated with each commit — checked items are stable and merged to `main`.

## Phase 0 — Boilerplate (complete)
- [x] FastAPI `api` container with fastembed (BAAI/bge-small-en-v1.5) and SSE streaming chat
- [x] ChromaDB container with cosine-distance collection (`rag_documents`)
- [x] React + Vite + shadcn/ui frontend (Chat tab + Documents tab)
- [x] PDF / DOCX / MD / TXT / URL ingestion pipeline
- [x] Docker Compose with port mapping (api:8040, chromadb:8030, frontend:3010)
- [x] Git repo initialised, tagged `v0.1.0-boilerplate`, pushed to GitHub

---

## Phase 1 — Shared Skills Package

- [x] Create `skills/` directory with `pyproject.toml` (`rag-skills` package)
- [x] `skills/rag_skills/url_scrape.py` — Strands `@tool`: httpx + BeautifulSoup scrape
- [x] `skills/rag_skills/pdf_ingest.py` — Strands `@tool` factory: PyMuPDF bytes → chunks
- [x] `skills/rag_skills/docx_ingest.py` — Strands `@tool` factory: python-docx bytes → chunks
- [x] `skills/rag_skills/url_ingest.py` — Strands `@tool` factory: URL → chunks (persistent ingestion)
- [x] `skills/rag_skills/github_ingest.py` — Strands `@tool` factory: fetch repo tree + raw files → chunks
- [x] `skills/rag_skills/youtube_ingest.py` — Strands `@tool` factory: yt-dlp VTT → text chunks
- [x] `skills/rag_skills/web_search.py` — Strands `@tool`: DuckDuckGo `DDGS().text()` wrapper
- [x] `skills/rag_skills/_chunker.py` — shared chunking utility used by all ingest skills
- [x] Unit-test each skill independently (14/14 passing)

---

## Phase 2 — Infrastructure: Neo4j + docker-compose updates

- [x] Add `neo4j:4.4` service to `docker-compose.yml` (ports 7475/7688 remapped to avoid conflicts; platform: linux/amd64; Bolt-only healthcheck)
- [x] Add `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` to `.env.example`
- [x] Add per-agent model vars: `OLLAMA_MODEL_ORCHESTRATOR`, `OLLAMA_MODEL_CODING`, `OLLAMA_MODEL_RESEARCH`
- [x] Add `CODING_AGENT_URL`, `RESEARCH_AGENT_URL`, `GRAPH_WORKER_URL` to `.env.example`
- [x] Add `GITHUB_TOKEN` to `.env.example` (optional, raises GitHub API rate limit to 5000/hr)
- [x] Neo4j container healthy (Bolt at bolt://localhost:7688; HTTP disabled)

---

## Phase 3 — graph_worker service

- [x] `graph_worker/Dockerfile` (python:3.12-slim, installs skills package; starlette==0.46.2 re-pinned after skills install)
- [x] `graph_worker/requirements.txt` (neo4j, apscheduler, httpx, fastembed, starlette==0.46.2)
- [x] `graph_worker/services/neo4j_client.py` — `upsert_entity()`, `upsert_relationship()`, `query_related_entities()`
- [x] `graph_worker/services/extractor.py` — Ollama LLM call to extract `(entity, type, relationship, entity)` triples from text chunks
- [x] `graph_worker/services/scheduler.py` — APScheduler `CronTrigger(hour=2)` nightly deep sync
- [x] `graph_worker/routers/sync.py` — `POST /graph/sync` manual trigger endpoint
- [x] `graph_worker/main.py` — FastAPI + lifespan starts scheduler
- [x] Add `graph_worker` service to `docker-compose.yml` (port 8043, depends_on: neo4j healthy)
- [x] Verified `POST /graph/sync` runs extraction and populates Neo4j nodes (3 chunks processed)

---

## Phase 4 — orchestrator service (rename + upgrade from api)

- [x] Renamed `api/` → `orchestrator/`
- [x] `orchestrator/Dockerfile` — installs skills package; starlette==0.46.2 re-pinned
- [x] `orchestrator/requirements.txt` — added `strands-agents`
- [x] `orchestrator/agent.py` — Strands `Agent` with `search_knowledge_base`, `call_coding_agent`, `call_research_agent` tools
- [x] `orchestrator/services/neo4j_client.py` — `query_related_entities()` for GraphRAG expansion
- [x] `orchestrator/services/chroma_client.py` — added `graph_augmented_query()` using Neo4j entity expansion
- [x] `orchestrator/routers/chat.py` — added `tech_level` param; level-filter prompt suffix; `sources` SSE event before `[DONE]`; `/internal` non-SSE endpoint
- [x] `orchestrator/config.py` — added `coding_agent_url`, `research_agent_url`, `graph_worker_url`, `neo4j_*` settings
- [x] Updated `docker-compose.yml`: renamed `api` → `orchestrator`; build `./orchestrator`
- [x] Verified orchestrator health: `{"status":"ok","model":"granite4:latest","collection":"orchestrator_docs","ollama_reachable":true,"neo4j":"ok"}`

---

## Phase 5 — coding_agent service

- [x] `coding_agent/Dockerfile` (installs skills[youtube] + ffmpeg; starlette==0.46.2 re-pinned)
- [x] `coding_agent/requirements.txt` (strands-agents, yt-dlp)
- [x] `coding_agent/agent.py` — registers `github_ingest`, `youtube_ingest`, `url_ingest`, `pdf_ingest` from `rag_skills`; `search_code_knowledge` tool over `coding_intel` collection
- [x] `coding_agent/routers/ingest.py` — `GET /ingest`, `POST /ingest/github`, `POST /ingest/youtube`, `POST /ingest/url`, `POST /ingest/file`, `DELETE /ingest/{doc_id}`
- [x] `coding_agent/routers/chat.py` — `POST /chat` SSE + `POST /chat/internal`
- [x] `coding_agent/services/chroma_client.py` — `coding_intel` collection, `graph_augmented_query()`
- [x] Add `coding_agent` service to `docker-compose.yml` (port 8041)
- [x] Verified URL ingest: `POST /ingest/url` ingested 3 chunks from FastAPI tutorial into `coding_intel`
- [x] Fix: `_parse_github_url` used `rstrip(".git")` which stripped individual chars — repos like `fastapi` lost trailing `i`; fixed to `removesuffix(".git")` + regression test added (14/14 pass)
- [x] Fix: GitHub API calls now use `follow_redirects=True` (httpx doesn't follow by default)
- [x] Fix: error message now surfaced if GitHub API returns 404/rate-limit to help diagnosis
- [ ] Full GitHub repo ingest (large repos require GITHUB_TOKEN to avoid 60 req/hr anonymous rate limit)

---

## Phase 6 — research_agent service

- [x] `research_agent/Dockerfile` (installs skills package; starlette==0.46.2 re-pinned)
- [x] `research_agent/requirements.txt` (strands-agents)
- [x] `research_agent/agent.py` — registers `web_search`, `url_scrape`, `url_ingest` from `rag_skills`; `search_research_cache` tool
- [x] `research_agent/routers/chat.py` — `POST /chat` SSE + `POST /chat/internal`
- [x] `research_agent/services/chroma_client.py` — `research_cache` collection
- [x] Add `research_agent` service to `docker-compose.yml` (port 8042)
- [x] Verified research_agent health: `{"status":"ok","model":"granite4:latest","collection":"research_cache"}`
- [x] Verified: Strands agent calls `web_search` tool (DuckDuckGo) + `search_research_cache` (ChromaDB) — confirmed in logs
- [x] Verified: research_agent `/internal` returns DuckDuckGo-enriched responses

---

## Phase 7 — Frontend updates

- [x] `TechLevelSelector.tsx` — Deep / Mid / Junior toggle buttons in chat header; state lifted to `App.tsx`
- [x] `Chat.tsx` — pass `tech_level` in POST /chat body; render collapsible `<Sources>` panel per assistant message (toggle open/close)
- [x] `api.ts` — parse `sources` SSE event; `onSources` callback in `streamChat()`; `TechLevel` type; `Source` interface
- [x] `App.tsx` — thread `techLevel` state through to `Chat`; header shows Ollama/ChromaDB/Neo4j branding
- [x] Verified tech level filter works: junior response uses kitchen metaphors and plain English analogies
- [x] Verified: Sources panel populated — ingested Claude models doc into orchestrator_docs, chat returned 4 source chunks in `sources` SSE event

---

## Phase 8 — Orchestrator routing integration (end-to-end)

- [x] Orchestrator agent.py wired with `call_coding_agent` and `call_research_agent` Strands tools
- [x] Tech level filter applied as prompt suffix: deep/mid/junior all verified working
- [x] Sources SSE event emitted before `[DONE]`; frontend parses and renders collapsible panel
- [x] Verified `POST /coding_agent/chat/internal` returns detailed dependency injection answer
- [x] Verified `POST /research_agent/chat/internal` returns DuckDuckGo-enriched error handling answer
- [x] Orchestrator routes to sub-agents via Strands tool calls (system prompt guides routing decisions)

---

## Phase 9 — GraphRAG integration

- [x] `graph_augmented_query()` wired into all three agent `chroma_client.py` files
- [x] Neo4j entities extracted: FastAPI, Pydantic (from FastAPI tutorial URL ingest)
- [x] `POST /graph/sync` verified: 3 chunks processed across 3 collections, entities upserted to Neo4j
- [x] Nightly APScheduler job confirmed started (`INFO: Nightly sync scheduler started (runs at 02:00)`)
- [x] Quick entity extraction fires during deep sync; hybrid pattern operational
- [x] Verified: GraphRAG query expansion tested — Neo4j entities (FastAPI, Pydantic) appended to query embedding, improving context retrieval

---

## Phase 10 — Hardening & docs

- [x] `GITHUB_TOKEN` optional env var wired through coding_agent config → `make_github_ingest_tool`
- [x] README.md documents: quickstart, architecture, per-agent ports, ingest examples, env vars, dev workflow
- [x] Health endpoints on coding_agent and research_agent now include `neo4j` status field (consistent with orchestrator)
- [x] Fix: `skills/rag_skills/_chunker.py` lazy-initializes tiktoken splitter (not at import time) to prevent network download at startup
- [x] Fix: all agent `download_models.py` scripts pre-cache tiktoken `cl100k_base` encoding at Docker build time
- [x] All 4 agents healthy with `neo4j: ok` after tiktoken fix: orchestrator, coding_agent, research_agent, graph_worker
- [x] Final tag: `v0.2.0-multi-agent`
