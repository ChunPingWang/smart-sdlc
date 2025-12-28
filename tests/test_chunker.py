"""Tests for smart chunker."""

from pathlib import Path

import pytest

from doc_pipeline.chunking import SmartChunker
from doc_pipeline.chunking.strategies import (
    HybridStrategy,
    SemanticStrategy,
    StructuralStrategy,
)
from doc_pipeline.document.models import DocumentMetadata


class TestSmartChunker:
    """Test suite for SmartChunker."""

    @pytest.fixture
    def metadata(self) -> DocumentMetadata:
        """Create test metadata."""
        return DocumentMetadata(source_file=Path("test.md"))

    def test_init_default_strategy(self):
        """Test chunker initialization with default strategy."""
        chunker = SmartChunker()
        assert chunker.default_strategy == "hybrid"

    def test_init_custom_strategy(self):
        """Test chunker initialization with custom strategy."""
        chunker = SmartChunker(default_strategy="semantic")
        assert chunker.default_strategy == "semantic"

    def test_chunk_text_simple(self, metadata: DocumentMetadata):
        """Test chunking simple text."""
        chunker = SmartChunker()
        content = "This is a simple paragraph.\n\nThis is another paragraph."

        chunks = chunker.chunk_text(content, metadata)

        assert len(chunks) >= 1
        assert all(c.content for c in chunks)

    def test_chunk_text_with_headers(self, metadata: DocumentMetadata):
        """Test chunking text with markdown headers."""
        chunker = SmartChunker(default_strategy="structural")
        content = """# Chapter 1

Introduction text here.

## Section 1.1

Section content.

## Section 1.2

More content.
"""
        chunks = chunker.chunk_text(content, metadata)

        assert len(chunks) >= 2

    def test_rechunk_large_content(self, metadata: DocumentMetadata):
        """Test rechunking large content."""
        chunker = SmartChunker()

        # Create a large chunk
        large_content = "This is a sentence. " * 1000
        from doc_pipeline.document.models import DocumentChunk

        large_chunk = DocumentChunk(content=large_content, metadata=metadata)

        rechunked = chunker.rechunk([large_chunk], max_tokens=500)

        assert len(rechunked) > 1


class TestStrategies:
    """Test chunking strategies."""

    @pytest.fixture
    def metadata(self) -> DocumentMetadata:
        """Create test metadata."""
        return DocumentMetadata(source_file=Path("test.md"))

    def test_structural_strategy(self, metadata: DocumentMetadata):
        """Test structural chunking strategy."""
        strategy = StructuralStrategy()
        content = "# Header\n\nContent under header.\n\n## Subheader\n\nMore content."

        chunks = strategy.chunk(content, metadata)

        assert len(chunks) >= 1

    def test_semantic_strategy(self, metadata: DocumentMetadata):
        """Test semantic chunking strategy."""
        strategy = SemanticStrategy(chunk_size=100, chunk_overlap=20)
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        chunks = strategy.chunk(content, metadata)

        assert len(chunks) >= 1

    def test_hybrid_strategy(self, metadata: DocumentMetadata):
        """Test hybrid chunking strategy."""
        strategy = HybridStrategy(max_chunk_tokens=100)
        content = "# Title\n\n" + ("Content. " * 100) + "\n\n## Section\n\nMore content."

        chunks = strategy.chunk(content, metadata)

        assert len(chunks) >= 1
