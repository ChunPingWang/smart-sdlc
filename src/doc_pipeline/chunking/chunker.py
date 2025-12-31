"""Smart document chunker."""

from pathlib import Path
from typing import Literal

from doc_pipeline.chunking.strategies import (
    ChunkingStrategy,
    DocumentTypeStrategy,
    HybridStrategy,
    SemanticStrategy,
    StructuralStrategy,
)
from doc_pipeline.document.models import (
    DocumentChunk,
    DocumentMetadata,
    ParsedDocument,
)

StrategyType = Literal["structural", "semantic", "hybrid", "auto"]


class SmartChunker:
    """
    Intelligent document chunker with multiple strategies.

    Supports:
    - Structural: Based on headers/sections
    - Semantic: Based on content meaning
    - Hybrid: Combination of both
    - Auto: Automatically selects based on content
    """

    def __init__(
        self,
        default_strategy: StrategyType = "hybrid",
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the smart chunker.

        Args:
            default_strategy: Default chunking strategy to use
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.default_strategy = default_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._strategies: dict[str, ChunkingStrategy] = {
            "structural": StructuralStrategy(),
            "semantic": SemanticStrategy(chunk_size * 4, chunk_overlap),
            "hybrid": HybridStrategy(chunk_size, chunk_overlap),
        }

    def chunk_document(
        self,
        document: ParsedDocument,
        strategy: StrategyType | None = None,
    ) -> list[DocumentChunk]:
        """
        Chunk a parsed document.

        Args:
            document: The parsed document to chunk
            strategy: Chunking strategy (uses default if None)

        Returns:
            List of document chunks
        """
        strategy = strategy or self.default_strategy

        # Combine all content from document chunks
        full_content = "\n\n".join(chunk.content for chunk in document.chunks)

        metadata = DocumentMetadata(
            source_file=document.source_file,
            chapter=document.title,
        )

        return self.chunk_text(full_content, metadata, strategy)

    def chunk_text(
        self,
        content: str,
        metadata: DocumentMetadata,
        strategy: StrategyType | None = None,
    ) -> list[DocumentChunk]:
        """
        Chunk raw text content.

        Args:
            content: Text content to chunk
            metadata: Metadata for the chunks
            strategy: Chunking strategy

        Returns:
            List of document chunks
        """
        strategy = strategy or self.default_strategy

        if strategy == "auto":
            strategy = self._detect_best_strategy(content)

        chunking_strategy = self._strategies.get(strategy)
        if not chunking_strategy:
            raise ValueError(f"Unknown strategy: {strategy}")

        return chunking_strategy.chunk(content, metadata)

    def chunk_by_type(
        self,
        content: str,
        metadata: DocumentMetadata,
        content_type: str,
    ) -> list[DocumentChunk]:
        """
        Chunk content using type-specific settings.

        Args:
            content: Text content to chunk
            metadata: Metadata for the chunks
            content_type: Type of content (business_rule, api_spec, etc.)

        Returns:
            List of document chunks
        """
        strategy = DocumentTypeStrategy(content_type)
        return strategy.chunk(content, metadata)

    def rechunk(
        self,
        chunks: list[DocumentChunk],
        max_tokens: int | None = None,
    ) -> list[DocumentChunk]:
        """
        Re-chunk existing chunks if they exceed token limits.

        Args:
            chunks: Existing chunks to potentially re-chunk
            max_tokens: Maximum tokens per chunk

        Returns:
            List of chunks respecting token limits
        """
        max_tokens = max_tokens or self.chunk_size
        result = []

        semantic = SemanticStrategy(
            chunk_size=max_tokens * 4,
            chunk_overlap=self.chunk_overlap,
        )

        for chunk in chunks:
            token_count = semantic.count_tokens(chunk.content)

            if token_count <= max_tokens:
                result.append(chunk)
            else:
                # Re-chunk using semantic strategy
                sub_chunks = semantic.chunk(chunk.content, chunk.metadata)
                result.extend(sub_chunks)

        return result

    def _detect_best_strategy(self, content: str) -> Literal["structural", "semantic", "hybrid"]:
        """
        Detect the best chunking strategy for content.

        Args:
            content: The content to analyze

        Returns:
            Strategy name
        """
        # Check for markdown headers
        has_headers = any(
            line.startswith("#") for line in content.split("\n") if line.strip()
        )

        if has_headers:
            # Has structure, use hybrid
            return "hybrid"

        # Check content length
        if len(content) < 5000:
            # Short content, semantic is fine
            return "semantic"

        # Default to hybrid for longer content
        return "hybrid"

    def add_strategy(self, name: str, strategy: ChunkingStrategy) -> None:
        """Register a custom chunking strategy."""
        self._strategies[name] = strategy


def chunk_file(
    file_path: str | Path,
    strategy: StrategyType = "hybrid",
) -> list[DocumentChunk]:
    """
    Convenience function to chunk a file.

    Args:
        file_path: Path to the file
        strategy: Chunking strategy to use

    Returns:
        List of document chunks
    """
    from doc_pipeline.document.parser import DocumentParser

    parser = DocumentParser()
    document = parser.parse(file_path)

    chunker = SmartChunker()
    return chunker.chunk_document(document, strategy)
