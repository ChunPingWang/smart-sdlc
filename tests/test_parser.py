"""Tests for document parser."""

from pathlib import Path

import pytest

from doc_pipeline.document.parser import DocumentParser


class TestDocumentParser:
    """Test suite for DocumentParser."""

    def test_init(self):
        """Test parser initialization."""
        parser = DocumentParser()
        assert parser is not None

    def test_supported_extensions(self):
        """Test supported file extensions."""
        parser = DocumentParser()
        expected = {".docx", ".xlsx", ".md", ".markdown", ".pdf", ".txt"}
        assert parser.SUPPORTED_EXTENSIONS == expected

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises error."""
        parser = DocumentParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.md")

    def test_parse_unsupported_extension(self, tmp_path: Path):
        """Test parsing unsupported file type raises error."""
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("content")

        parser = DocumentParser()
        with pytest.raises(ValueError, match="Unsupported file type"):
            parser.parse(unsupported_file)

    def test_parse_markdown_file(self, tmp_path: Path):
        """Test parsing a markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title\n\nSome content here.")

        parser = DocumentParser()
        result = parser.parse(md_file)

        assert result.source_file == md_file
        assert result.file_type == "md"
        assert len(result.chunks) > 0

    def test_parse_directory(self, tmp_path: Path):
        """Test parsing a directory of files."""
        # Create test files
        (tmp_path / "file1.md").write_text("# File 1\n\nContent 1")
        (tmp_path / "file2.md").write_text("# File 2\n\nContent 2")
        (tmp_path / "ignored.xyz").write_text("Ignored")

        parser = DocumentParser()
        results = parser.parse_directory(tmp_path)

        assert len(results) == 2
        filenames = [r.source_file.name for r in results]
        assert "file1.md" in filenames
        assert "file2.md" in filenames
