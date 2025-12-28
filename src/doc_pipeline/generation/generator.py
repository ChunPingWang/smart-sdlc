"""Specification generator using LLM."""

import re
from typing import Any

import yaml

from doc_pipeline.classification.classifier import LLMClient
from doc_pipeline.document.models import ChunkType, DocumentChunk
from doc_pipeline.generation.prompts import (
    API_SPEC_PROMPT,
    DB_SCHEMA_PROMPT,
    DEV_TASKS_PROMPT,
    REQUIREMENTS_PROMPT,
)


class SpecificationGenerator:
    """
    Generate structured specifications from document chunks using LLM.

    Supports generating:
    - Requirements (BR, FR, BRule, NFR)
    - API Specifications
    - Database Schemas
    - Development Tasks
    """

    def __init__(
        self,
        project_name: str = "Project",
    ):
        """
        Initialize the generator.

        Args:
            project_name: Name of the project for generated specs
        """
        self.llm = LLMClient()
        self.project_name = project_name

    def generate_requirements(
        self,
        chunks: list[DocumentChunk],
    ) -> dict[str, Any]:
        """
        Generate requirements from document chunks.

        Args:
            chunks: List of document chunks to process

        Returns:
            Dictionary with requirements data
        """
        content = self._combine_chunks(
            chunks,
            types=[ChunkType.REQUIREMENT, ChunkType.USE_CASE, ChunkType.BUSINESS_RULE],
        )

        if not content:
            content = self._combine_chunks(chunks)

        prompt = REQUIREMENTS_PROMPT.format(
            document_content=content,
            source_file=self._get_sources(chunks),
            content_type="requirements",
        )

        result = self._invoke_llm(prompt)
        return self._parse_yaml(result)

    def generate_api_spec(
        self,
        chunks: list[DocumentChunk],
        related_requirements: str = "",
    ) -> dict[str, Any]:
        """
        Generate API specifications from document chunks.

        Args:
            chunks: List of document chunks
            related_requirements: String of related requirement IDs

        Returns:
            Dictionary with API spec data
        """
        content = self._combine_chunks(
            chunks,
            types=[ChunkType.API_SPEC, ChunkType.USE_CASE],
        )

        if not content:
            content = self._combine_chunks(chunks)

        prompt = API_SPEC_PROMPT.format(
            document_content=content,
            source_file=self._get_sources(chunks),
            related_requirements=related_requirements or "N/A",
        )

        result = self._invoke_llm(prompt)
        return self._parse_yaml(result)

    def generate_db_schema(
        self,
        chunks: list[DocumentChunk],
        related_apis: str = "",
    ) -> dict[str, Any]:
        """
        Generate database schema from document chunks.

        Args:
            chunks: List of document chunks
            related_apis: String of related API IDs

        Returns:
            Dictionary with DB schema and domain model data
        """
        content = self._combine_chunks(
            chunks,
            types=[ChunkType.DB_SCHEMA, ChunkType.DOMAIN_MODEL],
        )

        if not content:
            content = self._combine_chunks(chunks)

        prompt = DB_SCHEMA_PROMPT.format(
            document_content=content,
            source_file=self._get_sources(chunks),
            related_apis=related_apis or "N/A",
        )

        result = self._invoke_llm(prompt)
        return self._parse_yaml(result)

    def generate_dev_tasks(
        self,
        specs: dict[str, Any],
        tech_stack: str = "Python + FastAPI + PostgreSQL",
    ) -> dict[str, Any]:
        """
        Generate development tasks from specifications.

        Args:
            specs: Combined specifications dict
            tech_stack: Technology stack description

        Returns:
            Dictionary with epics, stories, and tasks
        """
        specs_str = yaml.dump(specs, allow_unicode=True, default_flow_style=False)

        prompt = DEV_TASKS_PROMPT.format(
            specifications=specs_str,
            project_name=self.project_name,
            tech_stack=tech_stack,
        )

        result = self._invoke_llm(prompt)
        return self._parse_yaml(result)

    def generate_all(
        self,
        chunks: list[DocumentChunk],
        tech_stack: str = "Python + FastAPI + PostgreSQL",
    ) -> dict[str, Any]:
        """
        Generate all specifications from document chunks.

        Args:
            chunks: List of document chunks
            tech_stack: Technology stack description

        Returns:
            Dictionary with all generated specifications
        """
        requirements = self.generate_requirements(chunks)
        api_specs = self.generate_api_spec(chunks)
        db_schema = self.generate_db_schema(chunks)

        combined_specs = {
            **requirements,
            **api_specs,
            **db_schema,
        }

        dev_tasks = self.generate_dev_tasks(combined_specs, tech_stack)

        return {
            "project": self.project_name,
            "requirements": requirements,
            "api_specifications": api_specs,
            "database": db_schema,
            "development_tasks": dev_tasks,
        }

    def _invoke_llm(self, prompt: str) -> str:
        """Invoke LLM with the prompt."""
        system_prompt = "你是專業的系統分析師和架構師。請根據提供的文件內容，產出結構化的規格文件。"
        return self.llm.complete(system_prompt, prompt)

    def _combine_chunks(
        self,
        chunks: list[DocumentChunk],
        types: list[ChunkType] | None = None,
    ) -> str:
        """Combine chunk contents, optionally filtered by type."""
        if types:
            filtered = [c for c in chunks if c.chunk_type in types]
            if filtered:
                chunks = filtered

        return "\n\n---\n\n".join(c.content for c in chunks)

    def _get_sources(self, chunks: list[DocumentChunk]) -> str:
        """Get unique source files from chunks."""
        sources = set(str(c.metadata.source_file) for c in chunks)
        return ", ".join(sources)

    def _parse_yaml(self, content: str) -> dict[str, Any]:
        """Parse YAML from LLM response."""
        content = re.sub(r"```ya?ml\s*", "", content)
        content = re.sub(r"```\s*$", "", content)
        content = content.strip()

        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            return {"raw_content": content, "parse_error": True}


class AIReadySpecGenerator:
    """
    Generate AI-Ready specifications for Claude Code / GitHub Copilot.

    These specs are designed to be directly consumable by AI coding assistants.
    """

    def __init__(
        self,
        generator: SpecificationGenerator | None = None,
    ):
        """
        Initialize the AI-Ready spec generator.

        Args:
            generator: Base specification generator
        """
        self.generator = generator or SpecificationGenerator()

    def generate_feature_spec(
        self,
        feature_id: str,
        chunks: list[DocumentChunk],
    ) -> dict[str, Any]:
        """
        Generate a complete AI-Ready spec for a single feature.

        Args:
            feature_id: Feature identifier (e.g., "FR-001")
            chunks: Related document chunks

        Returns:
            AI-Ready specification dictionary
        """
        requirements = self.generator.generate_requirements(chunks)
        api_spec = self.generator.generate_api_spec(chunks)
        db_schema = self.generator.generate_db_schema(chunks)

        feature = None
        for fr in requirements.get("functional_requirements", []):
            if fr.get("id") == feature_id:
                feature = fr
                break

        if not feature:
            feature = {
                "id": feature_id,
                "name": "Feature",
                "description": "Generated from document analysis",
            }

        ai_ready_spec = {
            "spec_version": "1.0",
            "spec_type": "feature",
            "feature": {
                "id": feature_id,
                "name": feature.get("title", feature_id),
                "description": feature.get("description", ""),
            },
            "business_rules": requirements.get("business_rules", []),
            "api": api_spec.get("api_specifications", [{}])[0]
            if api_spec.get("api_specifications")
            else {},
            "database": db_schema.get("database_schemas", [{}])[0]
            if db_schema.get("database_schemas")
            else {},
            "domain": {
                "models": db_schema.get("domain_models", []),
                "events": db_schema.get("domain_events", []),
            },
            "test_cases": self._generate_test_cases(feature, requirements),
            "implementation_guide": self._generate_impl_guide(),
        }

        return ai_ready_spec

    def _generate_test_cases(
        self,
        feature: dict,
        requirements: dict,
    ) -> list[dict]:
        """Generate test case templates."""
        test_cases = []

        for criterion in feature.get("acceptance_criteria", []):
            test_cases.append(
                {
                    "scenario": criterion,
                    "given": "前置條件已滿足",
                    "when": "執行相關操作",
                    "then": criterion,
                }
            )

        for rule in requirements.get("business_rules", []):
            test_cases.append(
                {
                    "scenario": f"驗證: {rule.get('title', 'Rule')}",
                    "given": "輸入資料",
                    "when": "觸發驗證",
                    "then": rule.get("description", "驗證通過"),
                }
            )

        return test_cases

    def _generate_impl_guide(self) -> dict:
        """Generate implementation guide template."""
        return {
            "architecture": "hexagonal",
            "layers": [
                {"name": "adapter_in", "description": "REST Controller / GraphQL"},
                {"name": "application", "description": "Use Cases"},
                {"name": "domain", "description": "Aggregates, Entities, Value Objects"},
                {"name": "adapter_out", "description": "Repository Implementations"},
            ],
            "patterns": [
                "依賴注入 (Dependency Injection)",
                "領域事件 (Domain Events)",
                "值物件驗證 (Value Object Validation)",
            ],
        }
