"""Vector-enabled knowledge base for document storage and semantic search."""

import json
from pathlib import Path
from typing import Any

from doc_pipeline.config import settings
from doc_pipeline.document.models import ChunkType, DocumentChunk, DocumentMetadata
from doc_pipeline.knowledge_base.embeddings import EmbeddingService, cosine_similarity


class KnowledgeBase:
    """
    Vector-enabled knowledge base for document storage and semantic search.

    Provides:
    - Document storage as JSON files with embeddings
    - Semantic search using vector similarity
    - Keyword-based search fallback
    - Filtering by metadata (type, source, etc.)

    Supports both Ollama (local) and OpenAI embeddings.
    """

    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | Path | None = None,
        use_embeddings: bool = True,
    ):
        """
        Initialize the knowledge base.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
            use_embeddings: Whether to use vector embeddings for search
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = Path(
            persist_directory or settings.chroma_persist_dir
        )
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self._data_file = self.persist_directory / f"{self.collection_name}.json"
        self._chunks: list[dict[str, Any]] = []
        self._use_embeddings = use_embeddings
        self._embedding_service: EmbeddingService | None = None

        self._load()

    def _get_embedding_service(self) -> EmbeddingService:
        """Lazy load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def _load(self) -> None:
        """Load existing data from file."""
        if self._data_file.exists():
            try:
                with open(self._data_file, encoding="utf-8") as f:
                    self._chunks = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._chunks = []

    def _save(self) -> None:
        """Save data to file."""
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f, ensure_ascii=False, indent=2)

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        compute_embeddings: bool | None = None,
    ) -> list[str]:
        """
        Add document chunks to the knowledge base.

        Args:
            chunks: List of DocumentChunk objects
            compute_embeddings: Whether to compute embeddings (default: use_embeddings setting)

        Returns:
            List of added document IDs
        """
        if compute_embeddings is not None:
            should_embed = compute_embeddings
        else:
            should_embed = self._use_embeddings
        ids = []

        # Prepare contents for batch embedding
        contents = [chunk.content for chunk in chunks]

        # Compute embeddings if enabled
        embeddings: list[list[float]] = []
        if should_embed and contents:
            try:
                service = self._get_embedding_service()
                embeddings = service.embed_texts(contents)
            except Exception as e:
                print(f"Warning: Failed to compute embeddings: {e}")
                embeddings = [[] for _ in contents]

        for i, chunk in enumerate(chunks):
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
                "embedding": embeddings[i] if i < len(embeddings) else [],
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
        use_semantic: bool | None = None,
    ) -> list[DocumentChunk]:
        """
        Search for documents using semantic or keyword search.

        Args:
            query: Search query
            k: Number of results to return
            filter_type: Filter by chunk type
            filter_source: Filter by source file (partial match)
            use_semantic: Use semantic search (default: True if embeddings available)

        Returns:
            List of matching DocumentChunk objects
        """
        # Determine if we should use semantic search
        should_use_semantic = use_semantic if use_semantic is not None else self._use_embeddings

        # Check if we have embeddings
        has_embeddings = any(
            chunk.get("embedding") and len(chunk.get("embedding", [])) > 0
            for chunk in self._chunks
        )

        if should_use_semantic and has_embeddings:
            return self._semantic_search(query, k, filter_type, filter_source)
        else:
            return self._keyword_search(query, k, filter_type, filter_source)

    def _semantic_search(
        self,
        query: str,
        k: int = 5,
        filter_type: ChunkType | None = None,
        filter_source: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Search using vector similarity.

        Args:
            query: Search query
            k: Number of results to return
            filter_type: Filter by chunk type
            filter_source: Filter by source file

        Returns:
            List of matching DocumentChunk objects sorted by similarity
        """
        # Get query embedding
        try:
            service = self._get_embedding_service()
            query_embedding = service.embed_text(query)
        except Exception as e:
            print(f"Warning: Failed to compute query embedding: {e}")
            return self._keyword_search(query, k, filter_type, filter_source)

        if not query_embedding:
            return self._keyword_search(query, k, filter_type, filter_source)

        results = []

        for chunk_data in self._chunks:
            # Apply filters
            if filter_type and chunk_data.get("chunk_type") != filter_type.value:
                continue

            if filter_source:
                source = chunk_data.get("source_file", "")
                if filter_source.lower() not in source.lower():
                    continue

            # Calculate similarity
            chunk_embedding = chunk_data.get("embedding", [])
            if chunk_embedding:
                similarity = cosine_similarity(query_embedding, chunk_embedding)
                results.append((chunk_data, similarity))

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:k]

        return [self._dict_to_chunk(r[0]) for r in top_results]

    def _keyword_search(
        self,
        query: str,
        k: int = 5,
        filter_type: ChunkType | None = None,
        filter_source: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Search using keyword matching (fallback).

        Args:
            query: Search query
            k: Number of results to return
            filter_type: Filter by chunk type
            filter_source: Filter by source file

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

    def has_embeddings(self) -> bool:
        """Check if chunks have embeddings."""
        return any(
            chunk.get("embedding") and len(chunk.get("embedding", [])) > 0
            for chunk in self._chunks
        )

    def recompute_embeddings(self) -> int:
        """
        Recompute embeddings for all chunks.

        Returns:
            Number of chunks updated
        """
        if not self._chunks:
            return 0

        contents = [chunk.get("content", "") for chunk in self._chunks]

        try:
            service = self._get_embedding_service()
            embeddings = service.embed_texts(contents)

            for i, embedding in enumerate(embeddings):
                if i < len(self._chunks):
                    self._chunks[i]["embedding"] = embedding

            self._save()
            return len(embeddings)
        except Exception as e:
            print(f"Error recomputing embeddings: {e}")
            return 0

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
