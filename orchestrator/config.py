from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "mistral"
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "orchestrator_docs"
    api_cors_origins: str = "http://localhost:3010"
    log_level: str = "INFO"

    # Agent routing
    coding_agent_url: str = "http://coding_agent:8000"
    research_agent_url: str = "http://research_agent:8000"
    graph_worker_url: str = "http://graph_worker:8000"

    # Neo4j
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    model_config = {"env_file": ".env"}


settings = Settings()
