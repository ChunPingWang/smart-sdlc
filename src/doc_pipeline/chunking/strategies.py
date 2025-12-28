"""Chunking strategies for document processing."""

import re
from abc import ABC, abstractmethod

import tiktoken

from doc_pipeline.document.models import DocumentChunk, DocumentMetadata


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    def chunk(self, content: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """
        Split content into chunks.

        Args:
            content: The text content to chunk
            metadata: Metadata to attach to chunks

        Returns:
            List of DocumentChunk objects
        """
        pass

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text using tiktoken."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))


class StructuralStrategy(ChunkingStrategy):
    """
    Structural chunking based on document headers.

    Best for: Markdown documents with clear header hierarchy.
    """

    def __init__(
        self,
        headers_to_split_on: list[tuple[str, str]] | None = None,
    ):
        """
        Initialize structural strategy.

        Args:
            headers_to_split_on: List of (header_marker, header_name) tuples
        """
        self.headers_to_split_on = headers_to_split_on or [
            ("#", "chapter"),
            ("##", "section"),
            ("###", "subsection"),
            ("####", "subsubsection"),
        ]

    def chunk(self, content: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """Split content based on markdown headers."""
        lines = content.split("\n")
        chunks = []
        current_chunk_lines = []
        current_headers = {}

        for line in lines:
            # Check if line is a header
            header_match = None
            for marker, name in self.headers_to_split_on:
                pattern = f"^{re.escape(marker)}\\s+(.+)$"
                match = re.match(pattern, line)
                if match:
                    header_match = (marker, name, match.group(1))
                    break

            if header_match:
                # Save current chunk if exists
                if current_chunk_lines:
                    chunk_text = "\n".join(current_chunk_lines).strip()
                    if chunk_text:
                        chunk_metadata = metadata.model_copy()
                        chunk_metadata.extra.update(current_headers)
                        if "chapter" in current_headers:
                            chunk_metadata.chapter = current_headers["chapter"]
                        if "section" in current_headers:
                            chunk_metadata.section = current_headers["section"]

                        chunks.append(DocumentChunk(
                            content=chunk_text,
                            metadata=chunk_metadata,
                        ))
                    current_chunk_lines = []

                # Update headers
                marker, name, text = header_match
                current_headers[name] = text

                # Reset lower-level headers
                found = False
                for m, n in self.headers_to_split_on:
                    if found:
                        current_headers.pop(n, None)
                    if m == marker:
                        found = True

            current_chunk_lines.append(line)

        # Don't forget last chunk
        if current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines).strip()
            if chunk_text:
                chunk_metadata = metadata.model_copy()
                chunk_metadata.extra.update(current_headers)
                if "chapter" in current_headers:
                    chunk_metadata.chapter = current_headers["chapter"]
                if "section" in current_headers:
                    chunk_metadata.section = current_headers["section"]

                chunks.append(DocumentChunk(
                    content=chunk_text,
                    metadata=chunk_metadata,
                ))

        return chunks


class SemanticStrategy(ChunkingStrategy):
    """
    Semantic chunking based on content meaning.

    Best for: Documents where meaning should be preserved across chunks.
    Uses recursive character splitting with semantic separators.
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ):
        """
        Initialize semantic strategy.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: List of separators for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n\n",
            "\n\n",
            "\n",
            "。",
            ".",
            "；",
            ";",
            "，",
            ",",
            " ",
        ]

    def chunk(self, content: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """Split content semantically."""
        texts = self._split_text(content, self.separators)
        chunks = []

        for i, text in enumerate(texts):
            chunk_metadata = metadata.model_copy()
            chunk_metadata.extra["chunk_index"] = i
            chunk_metadata.extra["total_chunks"] = len(texts)

            chunks.append(DocumentChunk(
                content=text,
                metadata=chunk_metadata,
            ))

        return chunks

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using separators."""
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        # Try each separator
        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                result = []
                current = ""

                for part in parts:
                    test = current + sep + part if current else part

                    if len(test) <= self.chunk_size:
                        current = test
                    else:
                        if current:
                            result.append(current)
                        current = part

                if current:
                    result.append(current)

                # Check if we made progress
                if len(result) > 1:
                    return result

        # If no separator works, split by character count
        result = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk:
                result.append(chunk)

        return result


class HybridStrategy(ChunkingStrategy):
    """
    Hybrid strategy combining structural and semantic chunking.

    First splits by structure (headers), then by semantics if chunks are too large.
    Best for: Long documents with mixed content types.
    """

    def __init__(
        self,
        max_chunk_tokens: int = 2000,
        chunk_overlap: int = 200,
        headers_to_split_on: list[tuple[str, str]] | None = None,
    ):
        """
        Initialize hybrid strategy.

        Args:
            max_chunk_tokens: Maximum tokens per chunk
            chunk_overlap: Overlap between semantic sub-chunks
            headers_to_split_on: Headers for structural splitting
        """
        self.max_chunk_tokens = max_chunk_tokens
        self.chunk_overlap = chunk_overlap

        self.structural = StructuralStrategy(headers_to_split_on)
        self.semantic = SemanticStrategy(
            chunk_size=max_chunk_tokens * 4,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, content: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """Split using hybrid approach."""
        structural_chunks = self.structural.chunk(content, metadata)
        final_chunks = []

        for chunk in structural_chunks:
            token_count = self.count_tokens(chunk.content)

            if token_count <= self.max_chunk_tokens:
                final_chunks.append(chunk)
            else:
                sub_chunks = self.semantic.chunk(chunk.content, chunk.metadata)
                final_chunks.extend(sub_chunks)

        return final_chunks


class DocumentTypeStrategy(ChunkingStrategy):
    """
    Strategy that adapts based on document content type.

    Uses different chunk sizes based on detected content type.
    """

    CHUNK_SIZES: dict[str, int] = {
        "business_rule": 800,
        "api_spec": 1500,
        "db_schema": 2500,
        "use_case": 2000,
        "architecture": 3500,
        "default": 2000,
    }

    def __init__(self, content_type: str = "default"):
        """
        Initialize with content type.

        Args:
            content_type: Type of content being chunked
        """
        self.content_type = content_type
        chunk_size = self.CHUNK_SIZES.get(content_type, self.CHUNK_SIZES["default"])

        self.inner_strategy = HybridStrategy(
            max_chunk_tokens=chunk_size,
            chunk_overlap=int(chunk_size * 0.15),
        )

    def chunk(self, content: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """Chunk using type-specific settings."""
        return self.inner_strategy.chunk(content, metadata)
