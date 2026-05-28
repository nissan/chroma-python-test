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

- [ ] Add `neo4j:5` service to `docker-compose.yml` (ports 7474, 7687; volume `neo4j-data`)
- [ ] Add `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` to `.env.example`
- [ ] Add per-agent model vars: `OLLAMA_MODEL_ORCHESTRATOR`, `OLLAMA_MODEL_CODING`, `OLLAMA_MODEL_RESEARCH`
- [ ] Add `CODING_AGENT_URL`, `RESEARCH_AGENT_URL`, `GRAPH_WORKER_URL` to `.env.example`
- [ ] Add `GITHUB_TOKEN` to `.env.example` (optional, raises GitHub API rate limit to 5000/hr)
- [ ] Verify `neo4j` container starts and browser console accessible at `http://localhost:7474`

---

## Phase 3 — graph_worker service

- [ ] `graph_worker/Dockerfile` (python:3.12-slim, installs skills package)
- [ ] `graph_worker/requirements.txt` (neo4j, apscheduler, httpx, fastembed, strands-agents)
- [ ] `graph_worker/services/neo4j_client.py` — `upsert_entity()`, `upsert_relationship()`, `query_related_entities()`
- [ ] `graph_worker/services/extractor.py` — Ollama LLM call to extract `(entity, type, relationship, entity)` triples from text chunks
- [ ] `graph_worker/services/scheduler.py` — APScheduler `CronTrigger(hour=2)` nightly deep sync
- [ ] `graph_worker/routers/sync.py` — `POST /graph/sync` manual trigger endpoint
- [ ] `graph_worker/main.py` — FastAPI + lifespan starts scheduler
- [ ] Add `graph_worker` service to `docker-compose.yml` (port 8043, depends_on: neo4j)
- [ ] Verify `POST /graph/sync` runs extraction and populates Neo4j nodes/relationships

---

## Phase 4 — orchestrator service (rename + upgrade from api)

- [ ] Rename `api/` → `orchestrator/`
- [ ] `orchestrator/Dockerfile` — add `COPY ../skills ./skills && pip install -e ./skills`
- [ ] `orchestrator/requirements.txt` — add `strands-agents`, `strands-agents-tools`
- [ ] `orchestrator/agent.py` — Strands `Agent` with `route_to_coding_agent` and `route_to_research_agent` tools
- [ ] `orchestrator/services/neo4j_client.py` — `query_related_entities()` for GraphRAG expansion
- [ ] `orchestrator/services/chroma_client.py` — add `graph_augmented_query()` using Neo4j entity expansion
- [ ] `orchestrator/routers/chat.py` — add `tech_level` param; apply level-filter prompt; emit `sources` SSE event before `[DONE]`
- [ ] `orchestrator/config.py` — add `coding_agent_url`, `research_agent_url`, `graph_worker_url`, `neo4j_*` settings
- [ ] Update `docker-compose.yml`: rename `api` → `orchestrator`, build `./orchestrator`
- [ ] Verify orchestrator health check and basic chat still works before adding routing

---

## Phase 5 — coding_agent service

- [ ] `coding_agent/Dockerfile` (installs skills package + yt-dlp + ffmpeg via apt)
- [ ] `coding_agent/requirements.txt` (strands-agents, yt-dlp)
- [ ] `coding_agent/agent.py` — registers `github_ingest`, `youtube_ingest`, `url_scrape`, `pdf_ingest` from `rag_skills`; adds `search_collection` tool over `coding_intel` ChromaDB collection
- [ ] `coding_agent/routers/ingest.py` — `POST /ingest/github`, `POST /ingest/youtube`, `POST /ingest/url`
- [ ] `coding_agent/routers/chat.py` — `POST /chat` SSE + `POST /chat/internal` (non-SSE, for orchestrator calls)
- [ ] `coding_agent/services/chroma_client.py` — `coding_intel` collection, `graph_augmented_query()`
- [ ] `coding_agent/services/neo4j_client.py` — trigger quick entity extraction after each ingest
- [ ] Add `coding_agent` service to `docker-compose.yml` (port 8041)
- [ ] Verify ingest of a GitHub repo URL populates `coding_intel` collection and Neo4j entities
- [ ] Verify chat question about ingested repo returns relevant code context

---

## Phase 6 — research_agent service

- [ ] `research_agent/Dockerfile` (installs skills package)
- [ ] `research_agent/requirements.txt` (strands-agents)
- [ ] `research_agent/agent.py` — registers `web_search`, `url_scrape` from `rag_skills`; adds `search_collection` over `research_cache` collection
- [ ] `research_agent/routers/chat.py` — `POST /chat` SSE + `POST /chat/internal`
- [ ] `research_agent/services/chroma_client.py` — `research_cache` collection
- [ ] Add `research_agent` service to `docker-compose.yml` (port 8042)
- [ ] Verify web search tool returns DuckDuckGo results and caches to `research_cache`
- [ ] Verify orchestrator can route to research agent and return answer

---

## Phase 7 — Frontend updates

- [ ] `TechLevelSelector.tsx` — Deep / Mid / Junior dropdown in chat header; state lifted to `App.tsx`
- [ ] `Chat.tsx` — pass `tech_level` in POST /chat body; render collapsible `<Sources>` panel per assistant message
- [ ] `api.ts` — parse `sources` SSE event (separate from token stream); expose as `onSources` callback in `streamChat()`
- [ ] `App.tsx` — thread `techLevel` state through to `Chat`
- [ ] Verify tech level selector persists across messages in a session
- [ ] Verify Sources panel shows chunk text + source URL/file per assistant message

---

## Phase 8 — Orchestrator routing integration (end-to-end)

- [ ] Wire orchestrator agent to detect coding vs research vs general questions and route accordingly
- [ ] Tech level filter applied as post-processing prompt step in orchestrator
- [ ] Citations from sub-agent responses surfaced in orchestrator `sources` SSE event
- [ ] End-to-end test: coding question → routed to coding_agent → response filtered to selected tech level → sources shown in UI
- [ ] End-to-end test: library/best-practice question → routed to research_agent → DuckDuckGo results cited

---

## Phase 9 — GraphRAG integration

- [ ] `graph_augmented_query()` wired into all three agent collections (not just orchestrator)
- [ ] Nightly graph_worker job verified to run and add cross-document relationships
- [ ] Hybrid sync tested: quick entity extraction fires on ingest, deep mining fires nightly
- [ ] Verify GraphRAG improves retrieval quality vs. pure vector search on a known example

---

## Phase 10 — Hardening & docs

- [ ] Add `GITHUB_TOKEN` optional env var to coding_agent for higher GitHub API rate limits
- [ ] Add `ollama pull codellama` to setup notes (coding_agent model)
- [ ] Health check endpoints on all agent containers return model + collection status
- [ ] `README.md` with quickstart, architecture diagram, and per-agent responsibility
- [ ] Final tag: `v0.2.0-multi-agent`
