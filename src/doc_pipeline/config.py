"""Configuration management using Pydantic Settings."""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    OPENAI = "openai"
    # Future: add more providers


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Provider Settings
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model name")

    # Anthropic Configuration
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model name",
    )

    # Embedding Settings
    embedding_provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.OPENAI,
        description="Embedding provider",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name",
    )

    # ChromaDB Settings
    chroma_persist_dir: Path = Field(
        default=Path("./data/chromadb"),
        description="ChromaDB persistence directory",
    )
    chroma_collection_name: str = Field(
        default="doc_pipeline",
        description="ChromaDB collection name",
    )

    # Processing Settings
    chunk_size: int = Field(default=2000, description="Default chunk size in tokens")
    chunk_overlap: int = Field(default=200, description="Chunk overlap in tokens")

    # Output Settings
    output_dir: Path = Field(
        default=Path("./output"),
        description="Output directory for generated specs",
    )

    def get_llm_config(self) -> dict:
        """Get LLM configuration based on selected provider."""
        if self.llm_provider == LLMProvider.OPENAI:
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        else:
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            }

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
