from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "mistral"

    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
