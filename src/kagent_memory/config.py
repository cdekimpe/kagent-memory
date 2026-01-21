"""Configuration management for Kagent Memory service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="KAGENT_MEMORY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    port: int = 8080
    host: str = "0.0.0.0"
    log_level: str = "info"

    # Qdrant settings
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "kagent-memories"
    qdrant_api_key: str | None = None
    qdrant_top_k: int = 10
    qdrant_score_threshold: float | None = 0.7

    # Embedding settings
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200


class OpenAISettings(BaseSettings):
    """OpenAI-specific settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_openai_settings() -> OpenAISettings:
    """Get OpenAI settings."""
    return OpenAISettings()
