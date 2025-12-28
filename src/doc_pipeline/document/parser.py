"""Multi-format document parser."""

import re
from pathlib import Path
from typing import Any

from doc_pipeline.document.models import (
    DocumentChunk,
    DocumentMetadata,
    ParsedDocument,
)


class DocumentParser:
    """Parser for multiple document formats (Word, Excel, Markdown, PDF)."""

    SUPPORTED_EXTENSIONS = {".docx", ".xlsx", ".md", ".markdown", ".pdf", ".txt"}

    def __init__(self) -> None:
        """Initialize the document parser."""
        pass

    def parse(self, file_path: str | Path) -> ParsedDocument:
        """
        Parse a document file and return structured content.

        Args:
            file_path: Path to the document file

        Returns:
            ParsedDocument containing parsed content and metadata
        """
        file_path = Path(file_path)
        self._validate_file(file_path)

        ext = file_path.suffix.lower()

        if ext in {".md", ".markdown", ".txt"}:
            elements = self._parse_markdown(file_path)
        elif ext == ".docx":
            elements = self._parse_docx(file_path)
        elif ext == ".xlsx":
            elements = self._parse_xlsx(file_path)
        elif ext == ".pdf":
            elements = self._parse_pdf(file_path)
        else:
            elements = []

        chunks = self._create_chunks(elements, file_path)

        title = ""
        for elem in elements:
            if elem.get("type") == "Title":
                title = elem.get("text", "")
                break

        return ParsedDocument(
            source_file=file_path,
            file_type=file_path.suffix.lstrip("."),
            title=title,
            chunks=chunks,
            raw_elements=elements,
        )

    def _parse_markdown(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse markdown file."""
        content = file_path.read_text(encoding="utf-8")
        elements = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("# "):
                elements.append({"type": "Title", "text": line[2:]})
            elif line.startswith("## "):
                elements.append({"type": "Header", "text": line[3:]})
            elif line.startswith("### "):
                elements.append({"type": "Header", "text": line[4:]})
            elif line.startswith("- ") or line.startswith("* "):
                elements.append({"type": "ListItem", "text": line[2:]})
            elif re.match(r"^\d+\.", line):
                elements.append({"type": "ListItem", "text": re.sub(r"^\d+\.\s*", "", line)})
            elif line.startswith("|"):
                elements.append({"type": "Table", "text": line})
            elif line.startswith("```"):
                elements.append({"type": "CodeBlock", "text": line})
            else:
                elements.append({"type": "NarrativeText", "text": line})

        return elements

    def _parse_docx(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse Word document."""
        try:
            from docx import Document
        except ImportError:
            return [{"type": "Error", "text": "python-docx not installed"}]

        doc = Document(file_path)
        elements = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style = para.style.name if para.style else ""

            if "Heading 1" in style or "Title" in style:
                elements.append({"type": "Title", "text": text})
            elif "Heading" in style:
                elements.append({"type": "Header", "text": text})
            else:
                elements.append({"type": "NarrativeText", "text": text})

        return elements

    def _parse_xlsx(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse Excel file."""
        try:
            from openpyxl import load_workbook
        except ImportError:
            return [{"type": "Error", "text": "openpyxl not installed"}]

        wb = load_workbook(file_path, read_only=True)
        elements = []

        for sheet in wb.sheetnames:
            ws = wb[sheet]
            elements.append({"type": "Title", "text": f"Sheet: {sheet}"})

            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                if row_text.strip(" |"):
                    elements.append({"type": "Table", "text": row_text})

        return elements

    def _parse_pdf(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse PDF file."""
        try:
            import pdfplumber
        except ImportError:
            return [{"type": "Error", "text": "pdfplumber not installed"}]

        elements = []

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    elements.append({
                        "type": "NarrativeText",
                        "text": text,
                        "metadata": {"page_number": i + 1},
                    })

        return elements

    def parse_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
    ) -> list[ParsedDocument]:
        """
        Parse all supported documents in a directory.

        Args:
            directory: Path to the directory
            recursive: Whether to search recursively

        Returns:
            List of ParsedDocument objects
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        documents = []
        pattern = "**/*" if recursive else "*"

        for file_path in directory.glob(pattern):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    doc = self.parse(file_path)
                    documents.append(doc)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

        return documents

    def _validate_file(self, file_path: Path) -> None:
        """Validate the file exists and is supported."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Supported: {self.SUPPORTED_EXTENSIONS}"
            )

    def _create_chunks(
        self,
        elements: list[dict[str, Any]],
        source_file: Path,
    ) -> list[DocumentChunk]:
        """Create document chunks from parsed elements."""
        chunks = []
        current_section = ""
        current_chapter = ""

        for elem in elements:
            elem_type = elem.get("type", "")
            text = elem.get("text", "").strip()

            if not text:
                continue

            if elem_type == "Title":
                current_chapter = text
                current_section = ""
            elif elem_type == "Header":
                current_section = text

            metadata = DocumentMetadata(
                source_file=source_file,
                chapter=current_chapter,
                section=current_section,
            )

            if "metadata" in elem and "page_number" in elem["metadata"]:
                metadata.page_or_section = f"page_{elem['metadata']['page_number']}"
                metadata.extra["page_number"] = elem["metadata"]["page_number"]

            chunk = DocumentChunk(
                content=text,
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks


def parse_file(file_path: str | Path) -> ParsedDocument:
    """Convenience function to parse a single file."""
    parser = DocumentParser()
    return parser.parse(file_path)


def parse_directory(
    directory: str | Path,
    recursive: bool = True,
) -> list[ParsedDocument]:
    """Convenience function to parse a directory."""
    parser = DocumentParser()
    return parser.parse_directory(directory, recursive)
