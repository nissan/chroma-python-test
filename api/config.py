from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "mistral"
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "rag_documents"
    api_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
