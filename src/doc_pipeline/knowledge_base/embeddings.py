"""Embedding service supporting OpenAI and Ollama."""

import json
import urllib.error
import urllib.request
from typing import Protocol

from doc_pipeline.config import EmbeddingProvider, settings


class EmbeddingProvider_(Protocol):
    """Protocol for embedding providers."""

    def embed_text(self, text: str) -> list[float]:
        """Create embedding for a single text."""
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts."""
        ...


class OllamaEmbedding:
    """Ollama embedding provider using local models."""

    # Max characters to send (nomic-embed-text supports ~8192 tokens)
    # Chinese chars use more tokens, so we limit to 4000 chars
    MAX_CHARS = 4000

    def __init__(self, base_url: str, model: str):
        """
        Initialize Ollama embedding provider.

        Args:
            base_url: Ollama API base URL (e.g., http://localhost:11434)
            model: Embedding model name (e.g., nomic-embed-text)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _truncate(self, text: str) -> str:
        """Truncate text to max allowed length."""
        if len(text) > self.MAX_CHARS:
            return text[: self.MAX_CHARS]
        return text

    def embed_text(self, text: str) -> list[float]:
        """
        Create embedding for a single text using Ollama.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model,
            "input": self._truncate(text),
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                embeddings = result.get("embeddings", [[]])
                return embeddings[0] if embeddings else []
        except urllib.error.URLError as e:
            print(f"Ollama embedding error: {e.reason}. Is Ollama running?")
            return []
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model,
            "input": [self._truncate(t) for t in texts],
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("embeddings", [[] for _ in texts])
        except urllib.error.URLError as e:
            print(f"Ollama embedding error: {e.reason}. Is Ollama running?")
            return [[] for _ in texts]
        except Exception as e:
            print(f"Embedding error: {e}")
            return [[] for _ in texts]


class OpenAIEmbedding:
    """OpenAI embedding provider."""

    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key
            model: Embedding model name (e.g., text-embedding-3-small)
        """
        self.api_key = api_key
        self.model = model

    def embed_text(self, text: str) -> list[float]:
        """
        Create embedding for a single text using OpenAI.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            return []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            return [[] for _ in texts]


class EmbeddingService:
    """
    Unified embedding service supporting multiple providers.

    Supports:
    - Ollama (local, default)
    - OpenAI (cloud)
    """

    def __init__(self):
        """Initialize embedding service based on settings."""
        self.config = settings.get_embedding_config()
        self.provider_name = self.config["provider"]

        if self.provider_name == "ollama":
            self.provider = OllamaEmbedding(
                base_url=self.config["base_url"],
                model=self.config["model"],
            )
        else:  # openai
            self.provider = OpenAIEmbedding(
                api_key=self.config["api_key"],
                model=self.config["model"],
            )

    def embed_text(self, text: str) -> list[float]:
        """
        Create embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Embedding vector as list of floats
        """
        return self.provider.embed_text(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.provider.embed_texts(texts)

    @property
    def dimension(self) -> int:
        """Get the embedding dimension for the current model."""
        # nomic-embed-text: 768 dimensions
        # text-embedding-3-small: 1536 dimensions
        if self.provider_name == "ollama":
            return 768  # nomic-embed-text default
        else:
            return 1536  # OpenAI text-embedding-3-small


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    if not vec1 or not vec2:
        return 0.0

    import math

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
