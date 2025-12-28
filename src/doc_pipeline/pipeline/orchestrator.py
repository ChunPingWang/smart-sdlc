"""Pipeline orchestrator for document-to-code workflow."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from doc_pipeline.chunking import SmartChunker
from doc_pipeline.classification import DocumentClassifier
from doc_pipeline.classification.classifier import RuleBasedClassifier
from doc_pipeline.config import settings
from doc_pipeline.document import DocumentParser, ParsedDocument
from doc_pipeline.document.models import DocumentChunk
from doc_pipeline.generation import SpecificationGenerator
from doc_pipeline.generation.exporters import OpenAPIExporter, SQLExporter, YAMLExporter
from doc_pipeline.knowledge_base import KnowledgeBase

console = Console()


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    documents_processed: int = 0
    chunks_created: int = 0
    chunks_classified: int = 0
    specs_generated: bool = False
    output_files: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class PipelineOrchestrator:
    """
    Orchestrate the complete document-to-code pipeline.

    Pipeline stages:
    1. Ingest - Collect documents from input directory
    2. Parse - Parse documents into structured elements
    3. Chunk - Split documents into semantic chunks
    4. Classify - Classify chunks by type
    5. Store - Store chunks in knowledge base
    6. Generate - Generate specifications from chunks
    7. Export - Export specifications to various formats
    """

    def __init__(
        self,
        project_name: str = "Project",
        output_dir: str | Path | None = None,
    ):
        """
        Initialize the pipeline orchestrator.

        Args:
            project_name: Name of the project
            output_dir: Directory for output files
        """
        self.project_name = project_name
        self.output_dir = Path(output_dir or settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.parser = DocumentParser()
        self.chunker = SmartChunker()
        self.classifier: DocumentClassifier | RuleBasedClassifier | None = None
        self.knowledge_base: KnowledgeBase | None = None
        self.generator: SpecificationGenerator | None = None

    def run(
        self,
        input_dir: str | Path,
        generate_specs: bool = True,
        use_llm_classifier: bool = True,
        store_in_kb: bool = True,
    ) -> PipelineResult:
        """
        Run the complete pipeline.

        Args:
            input_dir: Directory containing input documents
            generate_specs: Whether to generate specifications
            use_llm_classifier: Whether to use LLM for classification
            store_in_kb: Whether to store in knowledge base

        Returns:
            PipelineResult with execution details
        """
        result = PipelineResult()
        input_path = Path(input_dir)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Stage 1: Ingest
            task = progress.add_task("Ingesting documents...", total=None)
            documents = self._ingest(input_path)
            result.documents_processed = len(documents)
            progress.update(task, completed=True)

            if not documents:
                result.errors.append("No documents found")
                return result

            # Stage 2 & 3: Parse and Chunk
            task = progress.add_task("Parsing and chunking...", total=None)
            all_chunks = self._parse_and_chunk(documents)
            result.chunks_created = len(all_chunks)
            progress.update(task, completed=True)

            # Stage 4: Classify
            task = progress.add_task("Classifying chunks...", total=None)
            if use_llm_classifier:
                try:
                    self.classifier = DocumentClassifier()
                    all_chunks = self.classifier.batch_classify(all_chunks)
                except Exception as e:
                    console.print(f"[yellow]LLM classifier failed, using rules: {e}[/yellow]")
                    rule_classifier = RuleBasedClassifier()
                    all_chunks = [rule_classifier.classify(c) for c in all_chunks]
            else:
                rule_classifier = RuleBasedClassifier()
                all_chunks = [rule_classifier.classify(c) for c in all_chunks]
            result.chunks_classified = len(all_chunks)
            progress.update(task, completed=True)

            # Stage 5: Store in Knowledge Base
            if store_in_kb:
                task = progress.add_task("Storing in knowledge base...", total=None)
                self.knowledge_base = KnowledgeBase()
                self.knowledge_base.add_chunks(all_chunks)
                progress.update(task, completed=True)

            # Stage 6 & 7: Generate and Export
            if generate_specs:
                task = progress.add_task("Generating specifications...", total=None)
                try:
                    self.generator = SpecificationGenerator(project_name=self.project_name)
                    specs = self.generator.generate_all(all_chunks)
                    result.specs_generated = True
                    result.output_files = self._export_all(specs)
                except Exception as e:
                    result.errors.append(f"Spec generation failed: {e}")
                    # Still export what we have
                    result.output_files = self._export_chunks(all_chunks)
                progress.update(task, completed=True)

        return result

    def run_stage(
        self,
        stage: str,
        input_data: Any,
    ) -> Any:
        """
        Run a single pipeline stage.

        Args:
            stage: Stage name (ingest, parse, chunk, classify, store, generate)
            input_data: Input for the stage

        Returns:
            Output from the stage
        """
        stages = {
            "ingest": self._ingest,
            "parse": lambda docs: self._parse_and_chunk(docs),
            "classify": self._classify,
            "store": self._store,
            "generate": self._generate,
        }

        if stage not in stages:
            raise ValueError(f"Unknown stage: {stage}")

        return stages[stage](input_data)

    def _ingest(self, input_dir: Path) -> list[ParsedDocument]:
        """Ingest documents from directory."""
        console.print(f"[blue]Scanning directory: {input_dir}[/blue]")
        documents = self.parser.parse_directory(input_dir)
        console.print(f"[green]Found {len(documents)} documents[/green]")
        return documents

    def _parse_and_chunk(
        self,
        documents: list[ParsedDocument],
    ) -> list[DocumentChunk]:
        """Parse and chunk all documents."""
        all_chunks = []

        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            console.print(
                f"  [dim]{doc.source_file.name}: {len(chunks)} chunks[/dim]"
            )

        return all_chunks

    def _classify(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Classify all chunks."""
        if not self.classifier:
            self.classifier = RuleBasedClassifier()
        if isinstance(self.classifier, DocumentClassifier):
            return self.classifier.batch_classify(chunks)
        else:
            return [self.classifier.classify(c) for c in chunks]

    def _store(self, chunks: list[DocumentChunk]) -> int:
        """Store chunks in knowledge base."""
        if not self.knowledge_base:
            self.knowledge_base = KnowledgeBase()
        ids = self.knowledge_base.add_chunks(chunks)
        return len(ids)

    def _generate(self, chunks: list[DocumentChunk]) -> dict[str, Any]:
        """Generate all specifications."""
        if not self.generator:
            self.generator = SpecificationGenerator(project_name=self.project_name)
        return self.generator.generate_all(chunks)

    def _export_all(self, specs: dict[str, Any]) -> dict[str, Path]:
        """Export all specifications to files."""
        exported = {}

        # YAML export
        yaml_exporter = YAMLExporter(self.output_dir)
        yaml_files = yaml_exporter.export_all(specs)
        exported.update(yaml_files)

        # OpenAPI export
        if specs.get("api_specifications"):
            api_specs = specs["api_specifications"]
            if isinstance(api_specs, dict):
                api_list = api_specs.get("api_specifications", [])
            else:
                api_list = api_specs

            if api_list:
                openapi_exporter = OpenAPIExporter(self.output_dir)
                exported["openapi"] = openapi_exporter.export(
                    api_list,
                    title=f"{self.project_name} API",
                )

        # SQL export
        if specs.get("database"):
            db_schemas = specs["database"]
            if isinstance(db_schemas, dict):
                schema_list = db_schemas.get("database_schemas", [])
            else:
                schema_list = db_schemas

            if schema_list:
                sql_exporter = SQLExporter(self.output_dir)
                exported["sql"] = sql_exporter.export(schema_list)

        return exported

    def _export_chunks(self, chunks: list[DocumentChunk]) -> dict[str, Path]:
        """Export chunks when spec generation fails."""
        yaml_exporter = YAMLExporter(self.output_dir)

        chunk_data = {
            "chunks": [
                {
                    "id": c.id,
                    "content": c.content[:500],  # Truncate for readability
                    "type": c.chunk_type.value,
                    "source": str(c.metadata.source_file),
                }
                for c in chunks
            ]
        }

        return {"chunks": yaml_exporter._write_yaml(chunk_data, "chunks.yaml")}


def run_pipeline(
    input_dir: str | Path,
    output_dir: str | Path | None = None,
    project_name: str = "Project",
) -> PipelineResult:
    """
    Convenience function to run the complete pipeline.

    Args:
        input_dir: Directory containing input documents
        output_dir: Directory for output files
        project_name: Name of the project

    Returns:
        PipelineResult with execution details
    """
    orchestrator = PipelineOrchestrator(
        project_name=project_name,
        output_dir=output_dir,
    )
    return orchestrator.run(input_dir)
