"""Embedding service placeholder.

Note: This is a placeholder for when vector embeddings are needed.
The current implementation uses simple text matching instead.
For production semantic search, use ChromaDB with Python 3.11/3.12.
"""

from doc_pipeline.config import settings


class EmbeddingService:
    """
    Placeholder embedding service.

    In a full implementation with ChromaDB, this would create
    vector embeddings using OpenAI's text-embedding-3-small model.
    """

    def __init__(self):
        """Initialize embedding service."""
        self.model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        """
        Create embedding for a single text.

        Note: This is a placeholder that returns an empty list.
        For actual embeddings, use OpenAI API.

        Args:
            text: The text to embed

        Returns:
            Empty list (placeholder)
        """
        # Placeholder - in production, use OpenAI embeddings
        return []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of empty lists (placeholder)
        """
        return [[] for _ in texts]
