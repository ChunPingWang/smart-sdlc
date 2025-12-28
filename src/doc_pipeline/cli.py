"""Command-line interface for doc-pipeline."""

from pathlib import Path
from typing import Optional

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
) -> None:
    """Generate specific specification types."""
    console.print(f"[blue]Generating {spec_type} specifications...[/blue]")

    from doc_pipeline.generation import SpecificationGenerator
    from doc_pipeline.knowledge_base import KnowledgeBase

    # Get chunks
    if input_dir:
        from doc_pipeline.document import DocumentParser
        from doc_pipeline.chunking import SmartChunker

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

    # Export
    from doc_pipeline.generation.exporters import YAMLExporter

    exporter = YAMLExporter(output_dir)
    output_path = exporter._write_yaml(specs, f"{spec_type}-spec.yaml")

    console.print(f"[green]Generated: {output_path}[/green]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum results"),
    type_filter: Optional[str] = typer.Option(
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
def info() -> None:
    """Show configuration and status information."""
    console.print(Panel.fit("[bold blue]Doc-Pipeline Configuration[/bold blue]"))

    table = Table(show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("LLM Provider", settings.llm_provider.value)
    table.add_row("LLM Model", settings.openai_model if settings.llm_provider.value == "openai" else settings.anthropic_model)
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


if __name__ == "__main__":
    app()
