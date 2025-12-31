"""Command-line interface for doc-pipeline."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from doc_pipeline import __version__
from doc_pipeline.config import settings

app = typer.Typer(
    name="doc-pipeline",
    help="Document-to-Code Pipeline - AI-driven document processing and specification generation",
    add_completion=False,
)
console = Console()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
) -> None:
    """Doc-Pipeline: Transform documents into structured specifications."""
    if version:
        console.print(f"doc-pipeline version {__version__}")
        raise typer.Exit()


@app.command()
def init(
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory for generated files",
    ),
) -> None:
    """Initialize the project structure."""
    console.print(Panel.fit("[bold blue]Initializing doc-pipeline[/bold blue]"))

    # Create directories
    dirs = [
        output_dir,
        output_dir / "ai-ready-specs",
        Path("./data"),
        Path("./data/chromadb"),
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"  [green]Created[/green] {d}")

    # Create .env if not exists
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            console.print("  [green]Created[/green] .env from .env.example")
        else:
            console.print("  [yellow]Warning[/yellow] .env.example not found")

    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Configure your API keys in .env")
    console.print("  2. Place your documents in a directory")
    console.print("  3. Run: doc-pipeline process ./your-docs")


@app.command()
def process(
    input_dir: Path = typer.Argument(
        ...,
        help="Directory containing input documents",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory",
    ),
    project_name: str = typer.Option(
        "Project",
        "--name",
        "-n",
        help="Project name for generated specs",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Skip LLM-based classification (use rules only)",
    ),
    no_kb: bool = typer.Option(
        False,
        "--no-kb",
        help="Skip storing in knowledge base",
    ),
    no_generate: bool = typer.Option(
        False,
        "--no-generate",
        help="Skip specification generation",
    ),
) -> None:
    """Process documents through the complete pipeline."""
    console.print(
        Panel.fit(
            f"[bold blue]Processing documents from {input_dir}[/bold blue]"
        )
    )

    from doc_pipeline.pipeline import PipelineOrchestrator

    orchestrator = PipelineOrchestrator(
        project_name=project_name,
        output_dir=output_dir,
    )

    result = orchestrator.run(
        input_dir=input_dir,
        generate_specs=not no_generate,
        use_llm_classifier=not no_llm,
        store_in_kb=not no_kb,
    )

    # Display results
    console.print("\n[bold]Pipeline Results:[/bold]")
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Documents processed", str(result.documents_processed))
    table.add_row("Chunks created", str(result.chunks_created))
    table.add_row("Chunks classified", str(result.chunks_classified))
    table.add_row("Specs generated", "Yes" if result.specs_generated else "No")

    console.print(table)

    if result.output_files:
        console.print("\n[bold]Generated files:[/bold]")
        for name, path in result.output_files.items():
            console.print(f"  [green]{name}[/green]: {path}")

    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  [red]{error}[/red]")


@app.command()
def generate(
    spec_type: str = typer.Argument(
        ...,
        help="Type of spec to generate: requirements, api, db, tasks, all",
    ),
    input_dir: Path = typer.Option(
        None,
        "--from",
        "-f",
        help="Directory with processed chunks (uses knowledge base if not specified)",
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory",
    ),
    format_type: str = typer.Option(
        "all",
        "--format",
        help="Output format: yaml, markdown, all",
    ),
) -> None:
    """Generate specific specification types."""
    console.print(f"[blue]Generating {spec_type} specifications...[/blue]")

    from doc_pipeline.generation import SpecificationGenerator
    from doc_pipeline.knowledge_base import KnowledgeBase

    # Get chunks
    if input_dir:
        from doc_pipeline.chunking import SmartChunker
        from doc_pipeline.document import DocumentParser

        parser = DocumentParser()
        chunker = SmartChunker()

        documents = parser.parse_directory(input_dir)
        chunks = []
        for doc in documents:
            chunks.extend(chunker.chunk_document(doc))
    else:
        # Load from knowledge base
        kb = KnowledgeBase()
        chunks = kb.get_all()

    if not chunks:
        console.print("[red]No chunks found to process[/red]")
        raise typer.Exit(1)

    generator = SpecificationGenerator()

    if spec_type == "requirements":
        specs = generator.generate_requirements(chunks)
    elif spec_type == "api":
        specs = generator.generate_api_spec(chunks)
    elif spec_type == "db":
        specs = generator.generate_db_schema(chunks)
    elif spec_type == "tasks":
        reqs = generator.generate_requirements(chunks)
        api = generator.generate_api_spec(chunks)
        db = generator.generate_db_schema(chunks)
        combined = {**reqs, **api, **db}
        specs = generator.generate_dev_tasks(combined)
    elif spec_type == "all":
        specs = generator.generate_all(chunks)
    else:
        console.print(f"[red]Unknown spec type: {spec_type}[/red]")
        raise typer.Exit(1)

    # Export based on format
    from doc_pipeline.generation.exporters import MarkdownExporter, YAMLExporter

    output_paths = []

    # YAML export
    if format_type in ("yaml", "all"):
        yaml_exporter = YAMLExporter(output_dir)
        yaml_path = yaml_exporter._write_yaml(specs, f"{spec_type}-spec.yaml")
        output_paths.append(yaml_path)

    # Markdown export (except for db)
    if format_type in ("markdown", "all") and spec_type != "db":
        md_exporter = MarkdownExporter(output_dir)
        if spec_type == "requirements":
            md_path = md_exporter.export_requirements(specs)
        elif spec_type == "api":
            api_specs = specs.get("api_specifications", [])
            md_path = md_exporter.export_api_spec({"api_specifications": api_specs})
        elif spec_type == "tasks":
            md_path = md_exporter.export_dev_tasks(specs)
        elif spec_type == "all":
            md_files = md_exporter.export_all(specs)
            output_paths.extend(md_files.values())
            md_path = None
        else:
            md_path = None

        if md_path:
            output_paths.append(md_path)

    console.print("\n[bold]Generated files:[/bold]")
    for path in output_paths:
        console.print(f"  [green]{path}[/green]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum results"),
    type_filter: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by chunk type (e.g., api_specification, business_rule)",
    ),
) -> None:
    """Search the knowledge base."""
    from doc_pipeline.document.models import ChunkType
    from doc_pipeline.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()

    chunk_type = None
    if type_filter:
        try:
            chunk_type = ChunkType(type_filter)
        except ValueError:
            console.print(f"[yellow]Warning: Unknown type '{type_filter}'[/yellow]")

    results = kb.search(query, k=limit, filter_type=chunk_type)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")

    for i, chunk in enumerate(results, 1):
        console.print(f"[bold cyan]Result {i}[/bold cyan]")
        console.print(f"  Type: {chunk.chunk_type.value}")
        console.print(f"  Source: {chunk.metadata.source_file}")
        console.print(f"  Content: {chunk.content[:200]}...")
        console.print()


@app.command()
def convert(
    input_dir: Path = typer.Argument(
        ...,
        help="Directory containing input documents",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory for converted files",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Search directories recursively",
    ),
    use_docling: bool = typer.Option(
        False,
        "--use-docling",
        help="Use Docling AI-powered conversion for better accuracy",
    ),
    generate_ddl: bool = typer.Option(
        True,
        "--ddl/--no-ddl",
        help="Generate DDL SQL files for database-related content",
    ),
) -> None:
    """Convert documents to Markdown format (1:1 conversion, no modification).

    Features:
    - Word (.docx): Preserves heading hierarchy (H1-H9), lists, tables → output/word/
    - Excel (.xlsx): Each sheet outputs as separate file → output/excel/
    - PDF: Page-by-page conversion → output/pdf/
    - Markdown/Text: Copy as-is → output/markdown/
    - DDL: Auto-generates .sql files when database/table keywords detected

    Output is organized by source format in subdirectories.
    Use --use-docling for AI-powered conversion with better accuracy (requires docling package).
    """
    console.print(
        Panel.fit(
            f"[bold blue]Converting documents from {input_dir}[/bold blue]"
        )
    )

    from doc_pipeline.document.parser import (
        DocumentParser,
        _docx_to_markdown,
        _pdf_to_markdown,
        _xlsx_to_markdown_sheets,
        contains_ddl_keywords,
        convert_to_markdown,
        generate_ddl_from_markdown,
    )

    parser = DocumentParser()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create format-specific subdirectories
    format_dirs = {
        ".docx": "word",
        ".xlsx": "excel",
        ".pdf": "pdf",
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "markdown",
    }

    def get_format_subdir(ext: str) -> str:
        """Get the subdirectory name for a file extension."""
        return format_dirs.get(ext.lower(), "other")

    # Find all supported files
    pattern = "**/*" if recursive else "*"
    converted_files: list[tuple[Path, Path]] = []
    ddl_files: list[Path] = []
    errors: list[tuple[Path, str]] = []

    for file_path in input_dir.glob(pattern):
        if file_path.suffix.lower() not in parser.SUPPORTED_EXTENSIONS:
            continue

        try:
            ext = file_path.suffix.lower()
            relative_path = file_path.relative_to(input_dir)
            base_name = file_path.stem
            format_subdir = get_format_subdir(ext)

            # Handle Excel files: each sheet as separate file
            if ext == ".xlsx":
                if use_docling:
                    # Docling converts entire file
                    md_content = convert_to_markdown(file_path, use_docling=True)
                    output_path = output_dir / format_subdir / relative_path.with_suffix(".md")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(md_content, encoding="utf-8")
                    converted_files.append((file_path, output_path))
                    console.print(f"  [green]✓[/green] {file_path.name} → {format_subdir}/{output_path.name}")

                    # Check for DDL keywords
                    if generate_ddl and contains_ddl_keywords(md_content):
                        ddl_content = generate_ddl_from_markdown(md_content, base_name)
                        if ddl_content:
                            ddl_path = output_dir / format_subdir / relative_path.with_suffix(".sql")
                            ddl_path.write_text(ddl_content, encoding="utf-8")
                            ddl_files.append(ddl_path)
                            console.print(f"  [cyan]📊[/cyan] {file_path.name} → {format_subdir}/{ddl_path.name} (DDL)")
                else:
                    # Convert each sheet separately
                    sheets = _xlsx_to_markdown_sheets(file_path)
                    for sheet_name, md_content in sheets.items():
                        # Clean sheet name for filename
                        safe_sheet_name = "".join(
                            c if c.isalnum() or c in "-_ " else "_" for c in sheet_name
                        ).strip()
                        output_name = f"{base_name}_{safe_sheet_name}.md"
                        output_path = output_dir / format_subdir / relative_path.parent / output_name
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_text(md_content, encoding="utf-8")
                        converted_files.append((file_path, output_path))
                        console.print(f"  [green]✓[/green] {file_path.name} [{sheet_name}] → {format_subdir}/{output_name}")

                        # Check for DDL keywords in each sheet
                        if generate_ddl and contains_ddl_keywords(md_content):
                            ddl_content = generate_ddl_from_markdown(md_content, f"{base_name}_{safe_sheet_name}")
                            if ddl_content:
                                ddl_name = f"{base_name}_{safe_sheet_name}.sql"
                                ddl_path = output_dir / format_subdir / relative_path.parent / ddl_name
                                ddl_path.write_text(ddl_content, encoding="utf-8")
                                ddl_files.append(ddl_path)
                                console.print(f"  [cyan]📊[/cyan] {file_path.name} [{sheet_name}] → {format_subdir}/{ddl_name} (DDL)")

            # Handle Word files
            elif ext == ".docx":
                if use_docling:
                    md_content = convert_to_markdown(file_path, use_docling=True)
                else:
                    md_content = _docx_to_markdown(file_path)

                output_path = output_dir / format_subdir / relative_path.with_suffix(".md")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(md_content, encoding="utf-8")
                converted_files.append((file_path, output_path))
                console.print(f"  [green]✓[/green] {file_path.name} → {format_subdir}/{output_path.name}")

                # Check for DDL keywords
                if generate_ddl and contains_ddl_keywords(md_content):
                    ddl_content = generate_ddl_from_markdown(md_content, base_name)
                    if ddl_content:
                        ddl_path = output_dir / format_subdir / relative_path.with_suffix(".sql")
                        ddl_path.write_text(ddl_content, encoding="utf-8")
                        ddl_files.append(ddl_path)
                        console.print(f"  [cyan]📊[/cyan] {file_path.name} → {format_subdir}/{ddl_path.name} (DDL)")

            # Handle PDF files
            elif ext == ".pdf":
                if use_docling:
                    md_content = convert_to_markdown(file_path, use_docling=True)
                else:
                    md_content = _pdf_to_markdown(file_path)

                output_path = output_dir / format_subdir / relative_path.with_suffix(".md")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(md_content, encoding="utf-8")
                converted_files.append((file_path, output_path))
                console.print(f"  [green]✓[/green] {file_path.name} → {format_subdir}/{output_path.name}")

            # Handle Markdown/Text files (copy as-is)
            elif ext in {".md", ".markdown", ".txt"}:
                md_content = file_path.read_text(encoding="utf-8")
                output_path = output_dir / format_subdir / relative_path.with_suffix(".md")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(md_content, encoding="utf-8")
                converted_files.append((file_path, output_path))
                console.print(f"  [green]✓[/green] {file_path.name} → {format_subdir}/{output_path.name}")

        except Exception as e:
            errors.append((file_path, str(e)))
            console.print(f"  [red]✗[/red] {file_path.name}: {e}")

    # Summary
    console.print()
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Files converted", str(len(converted_files)))
    table.add_row("DDL files generated", str(len(ddl_files)))
    table.add_row("Errors", str(len(errors)))
    table.add_row("Output directory", str(output_dir))

    console.print(table)

    if converted_files:
        console.print("\n[bold]Converted files:[/bold]")
        for src, dst in converted_files:
            console.print(f"  [green]{dst}[/green]")

    if ddl_files:
        console.print("\n[bold]DDL files:[/bold]")
        for ddl_path in ddl_files:
            console.print(f"  [cyan]{ddl_path}[/cyan]")


@app.command()
def info() -> None:
    """Show configuration and status information."""
    console.print(Panel.fit("[bold blue]Doc-Pipeline Configuration[/bold blue]"))

    table = Table(show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("LLM Provider", settings.llm_provider.value)

    # Show model based on provider
    if settings.llm_provider.value == "openai":
        llm_model = settings.openai_model
    elif settings.llm_provider.value == "anthropic":
        llm_model = settings.anthropic_model
    else:  # ollama
        llm_model = f"{settings.ollama_model} @ {settings.ollama_base_url}"
    table.add_row("LLM Model", llm_model)
    table.add_row("Embedding Model", settings.embedding_model)
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Output Directory", str(settings.output_dir))
    table.add_row("ChromaDB Path", str(settings.chroma_persist_dir))

    console.print(table)

    # Check knowledge base
    try:
        from doc_pipeline.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        count = kb.count()
        console.print(f"\n[green]Knowledge base: {count} documents[/green]")
    except Exception:
        console.print("\n[yellow]Knowledge base: Not initialized[/yellow]")


@app.command()
def clear_kb() -> None:
    """Clear the knowledge base."""
    if typer.confirm("Are you sure you want to clear the knowledge base?"):
        from doc_pipeline.knowledge_base import KnowledgeBase

        kb = KnowledgeBase()
        kb.clear()
        console.print("[green]Knowledge base cleared[/green]")
    else:
        console.print("[yellow]Cancelled[/yellow]")


@app.command("check-terms")
def check_terminology(
    glossary: Path = typer.Option(
        ...,
        "--glossary",
        "-g",
        help="Path to terminology glossary file (YAML)",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Output directory for the report",
    ),
    type_filter: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by chunk type (e.g., api_specification)",
    ),
) -> None:
    """Check document terminology consistency against a glossary."""
    console.print(
        Panel.fit("[bold blue]Terminology Consistency Check[/bold blue]")
    )

    from doc_pipeline.document.models import ChunkType
    from doc_pipeline.knowledge_base import KnowledgeBase
    from doc_pipeline.terminology import TerminologyChecker

    # Load chunks from knowledge base
    kb = KnowledgeBase()

    if type_filter:
        try:
            chunk_type = ChunkType(type_filter)
            chunks = kb.get_by_type(chunk_type)
        except ValueError:
            console.print(f"[red]Unknown type: {type_filter}[/red]")
            raise typer.Exit(1)
    else:
        chunks = kb.get_all()

    if not chunks:
        console.print("[yellow]No documents found in knowledge base.[/yellow]")
        console.print("Run 'doc-pipeline process' first to add documents.")
        raise typer.Exit(1)

    console.print(f"Checking {len(chunks)} document chunks...")

    # Run terminology check
    try:
        checker = TerminologyChecker(glossary)
        report = checker.check_all(chunks)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Display summary
    console.print("\n[bold]Check Summary:[/bold]")
    summary_table = Table(show_header=False)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Documents checked", str(report.summary["total_chunks"]))
    summary_table.add_row("Issues found", str(report.summary["issues_found"]))
    score_pct = int(report.summary["consistency_score"] * 100)
    score_color = "green" if score_pct >= 80 else "yellow" if score_pct >= 60 else "red"
    summary_table.add_row("Consistency score", f"[{score_color}]{score_pct}%[/{score_color}]")

    console.print(summary_table)

    # Display issues if any
    if report.issues:
        console.print("\n[bold]Issues Found:[/bold]")
        issues_table = Table()
        issues_table.add_column("Source", style="cyan")
        issues_table.add_column("Found", style="red")
        issues_table.add_column("Should Be", style="green")
        issues_table.add_column("Context", style="dim")

        for issue in report.issues:
            # Truncate source file name
            source = Path(issue.source_file).name
            # Truncate context
            context = issue.context[:40] + "..." if len(issue.context) > 40 else issue.context
            issues_table.add_row(
                source,
                issue.found_term,
                issue.standard_term,
                context,
            )

        console.print(issues_table)

    # Export reports
    report_path = checker.export_report(report, output_dir)
    readable_path = checker.export_readable_report(report, output_dir)

    console.print("\n[bold]Reports saved:[/bold]")
    console.print(f"  [green]Technical:[/green] {report_path}")
    console.print(f"  [green]Readable:[/green]  {readable_path}")


if __name__ == "__main__":
    app()
