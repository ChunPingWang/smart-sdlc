"""Simple file-based storage for document knowledge base."""

import json
from pathlib import Path
from typing import Any

from doc_pipeline.config import settings
from doc_pipeline.document.models import ChunkType, DocumentChunk, DocumentMetadata


class KnowledgeBase:
    """
    Simple file-based knowledge base for document storage.

    Provides:
    - Document storage as JSON files
    - Basic text search
    - Filtering by metadata (type, source, etc.)

    Note: This is a simplified implementation without vector embeddings.
    For production use with semantic search, consider using ChromaDB
    with Python 3.11 or 3.12.
    """

    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | Path | None = None,
    ):
        """
        Initialize the knowledge base.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = Path(
            persist_directory or settings.chroma_persist_dir
        )
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self._data_file = self.persist_directory / f"{self.collection_name}.json"
        self._chunks: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load existing data from file."""
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    self._chunks = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._chunks = []

    def _save(self) -> None:
        """Save data to file."""
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f, ensure_ascii=False, indent=2)

    def add_chunks(self, chunks: list[DocumentChunk]) -> list[str]:
        """
        Add document chunks to the knowledge base.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            List of added document IDs
        """
        ids = []

        for chunk in chunks:
            chunk_dict = {
                "id": chunk.id,
                "content": chunk.content,
                "source_file": str(chunk.metadata.source_file),
                "chapter": chunk.metadata.chapter,
                "section": chunk.metadata.section,
                "chunk_type": chunk.chunk_type.value,
                "confidence": chunk.confidence,
                "entities": chunk.entities,
                "dependencies": chunk.dependencies,
                "extra": chunk.metadata.extra,
            }
            self._chunks.append(chunk_dict)
            ids.append(chunk.id)

        self._save()
        return ids

    def search(
        self,
        query: str,
        k: int = 5,
        filter_type: ChunkType | None = None,
        filter_source: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Search for documents containing query text.

        Args:
            query: Search query
            k: Number of results to return
            filter_type: Filter by chunk type
            filter_source: Filter by source file (partial match)

        Returns:
            List of matching DocumentChunk objects
        """
        query_lower = query.lower()
        results = []

        for chunk_data in self._chunks:
            # Apply filters
            if filter_type and chunk_data.get("chunk_type") != filter_type.value:
                continue

            if filter_source:
                source = chunk_data.get("source_file", "")
                if filter_source.lower() not in source.lower():
                    continue

            # Check if query matches content
            content = chunk_data.get("content", "").lower()
            if query_lower in content:
                # Calculate simple relevance score
                score = content.count(query_lower)
                results.append((chunk_data, score))

        # Sort by score and take top k
        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:k]

        return [self._dict_to_chunk(r[0]) for r in top_results]

    def get_by_type(
        self,
        chunk_type: ChunkType,
        limit: int = 100,
    ) -> list[DocumentChunk]:
        """
        Get all chunks of a specific type.

        Args:
            chunk_type: The type to filter by
            limit: Maximum number of results

        Returns:
            List of DocumentChunk objects
        """
        results = []

        for chunk_data in self._chunks:
            if chunk_data.get("chunk_type") == chunk_type.value:
                results.append(self._dict_to_chunk(chunk_data))
                if len(results) >= limit:
                    break

        return results

    def get_all(self, limit: int = 1000) -> list[DocumentChunk]:
        """
        Get all documents in the knowledge base.

        Args:
            limit: Maximum number of results

        Returns:
            List of DocumentChunk objects
        """
        return [self._dict_to_chunk(c) for c in self._chunks[:limit]]

    def delete_by_source(self, source_file: str | Path) -> int:
        """
        Delete all chunks from a specific source file.

        Args:
            source_file: Path to the source file

        Returns:
            Number of deleted documents
        """
        source_str = str(source_file)
        original_count = len(self._chunks)

        self._chunks = [
            c for c in self._chunks
            if c.get("source_file") != source_str
        ]

        deleted = original_count - len(self._chunks)
        if deleted > 0:
            self._save()

        return deleted

    def clear(self) -> None:
        """Clear all documents from the knowledge base."""
        self._chunks = []
        self._save()

    def count(self) -> int:
        """Return the number of documents in the knowledge base."""
        return len(self._chunks)

    def _dict_to_chunk(self, data: dict[str, Any]) -> DocumentChunk:
        """Convert dictionary to DocumentChunk."""
        metadata = DocumentMetadata(
            source_file=Path(data.get("source_file", "unknown")),
            chapter=data.get("chapter", ""),
            section=data.get("section", ""),
            extra=data.get("extra", {}),
        )

        return DocumentChunk(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=metadata,
            chunk_type=ChunkType(data.get("chunk_type", "unknown")),
            confidence=data.get("confidence", 0.0),
            entities=data.get("entities", []),
            dependencies=data.get("dependencies", []),
        )
