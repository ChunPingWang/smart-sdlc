"""Multi-format document parser."""

import re
import warnings
from pathlib import Path
from typing import Any

from doc_pipeline.document.models import (
    DocumentChunk,
    DocumentMetadata,
    ParsedDocument,
)


# DDL 相關關鍵字
DDL_KEYWORDS = {
    "資料庫", "資料表", "數據庫", "數據表", "database", "table", "schema",
    "欄位", "字段", "column", "field", "primary key", "foreign key",
    "pk", "fk", "index", "constraint", "資料型別", "資料類型", "data type",
}


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

        doc = Document(str(file_path))
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


# =============================================================================
# Conversion Functions
# =============================================================================


def convert_to_markdown(file_path: str | Path, use_docling: bool = False) -> str:
    """
    Convert a document file directly to Markdown format without any modification.

    Args:
        file_path: Path to the document file
        use_docling: Use Docling for AI-powered conversion (more accurate)

    Returns:
        Markdown string representation of the document
    """
    parser = DocumentParser()
    file_path = Path(file_path)
    parser._validate_file(file_path)

    ext = file_path.suffix.lower()

    if use_docling:
        return _convert_with_docling(file_path)

    if ext in {".md", ".markdown", ".txt"}:
        return file_path.read_text(encoding="utf-8")
    elif ext == ".docx":
        return _docx_to_markdown(file_path)
    elif ext == ".xlsx":
        # For single file conversion, combine all sheets
        sheets = _xlsx_to_markdown_sheets(file_path)
        return "\n\n---\n\n".join(sheets.values())
    elif ext == ".pdf":
        return _pdf_to_markdown(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _convert_with_docling(file_path: Path) -> str:
    """Convert document using Docling AI-powered converter."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise ImportError(
            "Docling not installed. Run: pip install docling\n"
            "Docling provides AI-powered document conversion with better accuracy."
        )

    converter = DocumentConverter()
    result = converter.convert(str(file_path))
    return result.document.export_to_markdown()


def _docx_to_markdown(file_path: Path) -> str:
    """Convert Word document to Markdown with proper heading hierarchy."""
    try:
        from docx import Document
        from docx.table import Table as DocxTable
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

    doc = Document(str(file_path))
    lines: list[str] = []
    list_counter = 0
    in_list = False

    def get_heading_level(style_name: str) -> int | None:
        """Extract heading level from style name."""
        if not style_name:
            return None
        if "Title" in style_name:
            return 1
        match = re.search(r"Heading\s*(\d+)", style_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        if "Heading" in style_name:
            return 2
        return None

    def format_table(table: DocxTable) -> list[str]:
        """Convert Word table to Markdown table."""
        table_lines = []
        rows_data = []

        for row in table.rows:
            row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            rows_data.append(row_cells)

        if not rows_data:
            return []

        # Determine column count
        max_cols = max(len(row) for row in rows_data)

        # Header row
        header = rows_data[0]
        header.extend([""] * (max_cols - len(header)))
        table_lines.append("| " + " | ".join(header) + " |")
        table_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

        # Data rows
        for row in rows_data[1:]:
            row.extend([""] * (max_cols - len(row)))
            table_lines.append("| " + " | ".join(row) + " |")

        return table_lines

    # Process document body (paragraphs and tables in order)
    for element in doc.element.body:
        # Check if it's a paragraph
        if element.tag.endswith("p"):
            for para in doc.paragraphs:
                if para._element is element:
                    text = para.text.strip()
                    style_name = para.style.name if para.style else ""

                    # Handle empty paragraphs
                    if not text:
                        if lines and lines[-1] != "":
                            lines.append("")
                        in_list = False
                        list_counter = 0
                        continue

                    # Check heading level
                    heading_level = get_heading_level(style_name)
                    if heading_level:
                        if lines and lines[-1] != "":
                            lines.append("")
                        lines.append("#" * heading_level + " " + text)
                        lines.append("")
                        in_list = False
                        list_counter = 0
                        continue

                    # Check for list items
                    if "List" in style_name:
                        if "Number" in style_name or "Ordered" in style_name:
                            list_counter += 1
                            lines.append(f"{list_counter}. {text}")
                        else:
                            lines.append(f"- {text}")
                        in_list = True
                        continue

                    # Check for indented text (TOC or nested content)
                    if "TOC" in style_name:
                        # Table of contents - add as indented list
                        indent_level = 0
                        if para.paragraph_format.left_indent:
                            indent_level = int(para.paragraph_format.left_indent.pt / 36)
                        lines.append("  " * indent_level + "- " + text)
                        continue

                    # Regular paragraph
                    if in_list:
                        lines.append("")
                        in_list = False
                        list_counter = 0

                    lines.append(text)
                    lines.append("")
                    break

        # Check if it's a table
        elif element.tag.endswith("tbl"):
            for table in doc.tables:
                if table._element is element:
                    if lines and lines[-1] != "":
                        lines.append("")
                    table_lines = format_table(table)
                    lines.extend(table_lines)
                    lines.append("")
                    break

    return "\n".join(lines)


def _xlsx_to_markdown_sheets(file_path: Path) -> dict[str, str]:
    """
    Convert Excel file to Markdown, one file per sheet.

    Returns:
        Dictionary mapping sheet names to their Markdown content
    """
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ImportError("openpyxl not installed. Run: pip install openpyxl")

    sheets_content: dict[str, str] = {}

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        wb = load_workbook(file_path, read_only=True, data_only=True)

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            lines = [f"# {sheet_name}", ""]

            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                sheets_content[sheet_name] = "\n".join(lines)
                continue

            # Filter out completely empty rows
            non_empty_rows = [row for row in rows if any(cell is not None for cell in row)]
            if not non_empty_rows:
                sheets_content[sheet_name] = "\n".join(lines)
                continue

            # Determine max columns
            max_cols = max(len(row) for row in non_empty_rows)

            # Create table header from first row
            header_row = non_empty_rows[0]
            header_cells = [str(cell) if cell is not None else "" for cell in header_row]
            header_cells.extend([""] * (max_cols - len(header_cells)))

            lines.append("| " + " | ".join(header_cells) + " |")
            lines.append("| " + " | ".join(["---"] * max_cols) + " |")

            # Data rows
            for row in non_empty_rows[1:]:
                cells = [str(cell) if cell is not None else "" for cell in row]
                cells.extend([""] * (max_cols - len(cells)))
                lines.append("| " + " | ".join(cells) + " |")

            lines.append("")
            sheets_content[sheet_name] = "\n".join(lines)

    return sheets_content


def _xlsx_to_markdown(file_path: Path) -> str:
    """Convert Excel file to single Markdown (legacy, combines all sheets)."""
    sheets = _xlsx_to_markdown_sheets(file_path)
    return "\n\n---\n\n".join(sheets.values())


def _pdf_to_markdown(file_path: Path) -> str:
    """Convert PDF to Markdown."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")

    lines = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i > 0:
                lines.append("")
                lines.append("---")
                lines.append("")

            lines.append(f"## Page {i + 1}")
            lines.append("")

            text = page.extract_text()
            if text:
                lines.append(text)

    return "\n".join(lines)


# =============================================================================
# DDL Generation Functions
# =============================================================================


def contains_ddl_keywords(content: str) -> bool:
    """Check if content contains DDL-related keywords."""
    content_lower = content.lower()
    return any(keyword.lower() in content_lower for keyword in DDL_KEYWORDS)


def extract_table_definitions(markdown_content: str) -> list[dict[str, Any]]:
    """
    Extract table definitions from Markdown content.

    Returns list of table definitions with columns and types.
    """
    tables = []
    lines = markdown_content.split("\n")
    current_table_name = None
    current_columns = []
    in_table = False

    for i, line in enumerate(lines):
        line = line.strip()

        # Look for table name in headers or text
        if line.startswith("#"):
            header_text = re.sub(r"^#+\s*", "", line)
            # Check if header contains table-related keywords
            if any(kw in header_text.lower() for kw in ["table", "資料表", "數據表"]):
                # Extract table name
                match = re.search(r"[:\s]([A-Za-z_][A-Za-z0-9_]*)", header_text)
                if match:
                    if current_table_name and current_columns:
                        tables.append({
                            "name": current_table_name,
                            "columns": current_columns
                        })
                    current_table_name = match.group(1)
                    current_columns = []
                    in_table = False

        # Detect markdown table start
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 2:
                # Check if this looks like a column definition row
                # Common patterns: 欄位名稱, Column Name, Field, 資料型別, Type, etc.
                first_cell_lower = cells[0].lower() if cells else ""

                if in_table:
                    # This is a data row in an existing table
                    if len(cells) >= 2:
                        col_info = _parse_column_row(cells)
                        if col_info:
                            current_columns.append(col_info)
                else:
                    # Check if this is a header row for column definitions
                    header_keywords = ["欄位", "column", "field", "名稱", "name", "型別", "type"]
                    if any(kw in first_cell_lower for kw in header_keywords):
                        in_table = True

        elif line.startswith("|") and "---" in line:
            # Separator line, continue
            pass
        elif not line.startswith("|") and in_table:
            # End of table
            in_table = False

    # Don't forget the last table
    if current_table_name and current_columns:
        tables.append({
            "name": current_table_name,
            "columns": current_columns
        })

    return tables


def _parse_column_row(cells: list[str]) -> dict[str, str] | None:
    """Parse a table row as a column definition."""
    if len(cells) < 2:
        return None

    # Try to identify column name and type
    col_name = cells[0].strip()
    col_type = cells[1].strip() if len(cells) > 1 else "VARCHAR(255)"

    # Skip if looks like a header row
    if col_name.lower() in ["欄位", "column", "field", "名稱", "name", ""]:
        return None

    # Clean column name
    col_name = re.sub(r"[^\w]", "_", col_name)
    if not col_name or col_name[0].isdigit():
        return None

    # Map common type names to SQL types
    type_mapping = {
        "string": "VARCHAR(255)",
        "字串": "VARCHAR(255)",
        "text": "TEXT",
        "文字": "TEXT",
        "int": "INTEGER",
        "integer": "INTEGER",
        "整數": "INTEGER",
        "number": "DECIMAL(18,2)",
        "數字": "DECIMAL(18,2)",
        "decimal": "DECIMAL(18,2)",
        "float": "FLOAT",
        "double": "DOUBLE",
        "date": "DATE",
        "日期": "DATE",
        "datetime": "DATETIME",
        "時間": "DATETIME",
        "timestamp": "TIMESTAMP",
        "boolean": "BOOLEAN",
        "bool": "BOOLEAN",
        "布林": "BOOLEAN",
    }

    col_type_lower = col_type.lower()
    for key, sql_type in type_mapping.items():
        if key in col_type_lower:
            col_type = sql_type
            break

    # Check for constraints
    constraints = []
    full_text = " ".join(cells).lower()
    if "primary" in full_text or "pk" in full_text or "主鍵" in full_text:
        constraints.append("PRIMARY KEY")
    if "not null" in full_text or "必填" in full_text or "required" in full_text:
        constraints.append("NOT NULL")
    if "unique" in full_text or "唯一" in full_text:
        constraints.append("UNIQUE")

    return {
        "name": col_name,
        "type": col_type,
        "constraints": constraints,
        "comment": cells[-1] if len(cells) > 2 else "",
    }


def generate_ddl_from_markdown(markdown_content: str, table_name: str | None = None) -> str:
    """
    Generate DDL SQL from Markdown content.

    Args:
        markdown_content: Markdown content containing table definitions
        table_name: Optional override for table name

    Returns:
        DDL SQL statements
    """
    tables = extract_table_definitions(markdown_content)

    if not tables:
        # Try to generate a simple DDL from any markdown table found
        tables = _extract_simple_tables(markdown_content, table_name)

    if not tables:
        return ""

    ddl_statements = []
    ddl_statements.append("-- Auto-generated DDL from document conversion")
    ddl_statements.append(f"-- Source: {table_name or 'unknown'}")
    ddl_statements.append("")

    for table in tables:
        tbl_name = table["name"]
        columns = table["columns"]

        if not columns:
            continue

        ddl_statements.append(f"CREATE TABLE {tbl_name} (")

        col_defs = []
        for col in columns:
            col_def = f"    {col['name']} {col['type']}"
            if col.get("constraints"):
                col_def += " " + " ".join(col["constraints"])
            if col.get("comment"):
                col_def += f"  -- {col['comment']}"
            col_defs.append(col_def)

        ddl_statements.append(",\n".join(col_defs))
        ddl_statements.append(");")
        ddl_statements.append("")

    return "\n".join(ddl_statements)


def _extract_simple_tables(markdown_content: str, default_name: str | None = None) -> list[dict]:
    """Extract table structure from any markdown table."""
    tables = []
    lines = markdown_content.split("\n")

    current_headers: list[str] = []
    current_rows: list[list[str]] = []
    table_count = 0

    for line in lines:
        line = line.strip()

        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if not current_headers:
                current_headers = cells
            else:
                current_rows.append(cells)

        elif line.startswith("|") and "---" in line:
            continue

        elif not line.startswith("|") and current_headers:
            # End of table
            if current_headers and current_rows:
                table_count += 1
                name = default_name or f"table_{table_count}"
                name = re.sub(r"[^\w]", "_", name)

                columns = []
                for i, header in enumerate(current_headers):
                    col_name = re.sub(r"[^\w]", "_", header) or f"col_{i}"
                    # Infer type from first row data
                    sample = current_rows[0][i] if i < len(current_rows[0]) else ""
                    col_type = _infer_sql_type(sample)
                    columns.append({
                        "name": col_name,
                        "type": col_type,
                        "constraints": [],
                        "comment": header,
                    })

                tables.append({"name": name, "columns": columns})

            current_headers = []
            current_rows = []

    return tables


def _infer_sql_type(sample: str) -> str:
    """Infer SQL type from sample data."""
    if not sample:
        return "VARCHAR(255)"

    sample = sample.strip()

    # Check for numbers
    if re.match(r"^-?\d+$", sample):
        return "INTEGER"
    if re.match(r"^-?\d+\.\d+$", sample):
        return "DECIMAL(18,2)"

    # Check for dates
    if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}", sample):
        return "DATE"

    # Check for boolean
    if sample.lower() in ["true", "false", "yes", "no", "是", "否", "y", "n"]:
        return "BOOLEAN"

    # Default to varchar with reasonable length
    length = max(255, len(sample) * 2)
    return f"VARCHAR({min(length, 4000)})"
