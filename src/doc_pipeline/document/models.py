"""Core data models for document processing."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ChunkType(str, Enum):
    """Document chunk classification types."""

    BUSINESS_RULE = "business_rule"
    USE_CASE = "use_case"
    API_SPEC = "api_specification"
    DB_SCHEMA = "database_schema"
    DOMAIN_MODEL = "domain_model"
    SEQUENCE = "sequence_diagram"
    ARCHITECTURE = "architecture"
    GLOSSARY = "glossary"
    REQUIREMENT = "requirement"
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """Metadata for a document or chunk."""

    source_file: Path
    page_or_section: str = ""
    chapter: str = ""
    section: str = ""
    subsection: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    extra: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """A chunk of document content with metadata."""

    id: str = Field(default="", description="Unique identifier for the chunk")
    content: str = Field(description="The text content of the chunk")
    metadata: DocumentMetadata
    chunk_type: ChunkType = Field(default=ChunkType.UNKNOWN)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Generate ID if not provided."""
        if not self.id:
            import hashlib

            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            source_name = self.metadata.source_file.stem
            self.id = f"{source_name}_{content_hash}"


class ParsedDocument(BaseModel):
    """A fully parsed document with its chunks."""

    source_file: Path
    file_type: str = Field(description="File extension without dot")
    title: str = ""
    chunks: list[DocumentChunk] = Field(default_factory=list)
    raw_elements: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Raw elements from parser",
    )
    parsed_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_chunks(self) -> int:
        """Return total number of chunks."""
        return len(self.chunks)

    def get_chunks_by_type(self, chunk_type: ChunkType) -> list[DocumentChunk]:
        """Filter chunks by type."""
        return [c for c in self.chunks if c.chunk_type == chunk_type]


# Specification output models


class RequirementItem(BaseModel):
    """A single requirement item."""

    id: str
    title: str
    description: str
    priority: str = "P1"
    source: str = ""
    stakeholder: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    related_items: list[str] = Field(default_factory=list)


class BusinessRequirement(RequirementItem):
    """Business requirement (BR)."""

    type: str = "BR"


class FunctionalRequirement(RequirementItem):
    """Functional requirement (FR)."""

    type: str = "FR"
    parent_br: str = ""
    actor: str = ""
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    api_endpoints: list[str] = Field(default_factory=list)


class BusinessRule(BaseModel):
    """Business rule definition."""

    id: str
    title: str
    description: str
    type: str = "validation"  # validation, calculation, decision
    logic: str = ""
    error_message: str = ""


class NonFunctionalRequirement(RequirementItem):
    """Non-functional requirement (NFR)."""

    type: str = "NFR"
    category: str = ""  # performance, security, availability, etc.
    measurement: str = ""


class RequirementsList(BaseModel):
    """Complete requirements list."""

    project: str
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "draft"
    business_requirements: list[BusinessRequirement] = Field(default_factory=list)
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(
        default_factory=list
    )


class APIEndpoint(BaseModel):
    """API endpoint specification."""

    id: str
    name: str
    method: str
    path: str
    version: str = "v1"
    related_fr: str = ""
    description: str = ""
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)
    security: dict[str, Any] = Field(default_factory=dict)


class DatabaseTable(BaseModel):
    """Database table definition."""

    id: str
    name: str
    description: str = ""
    related_api: list[str] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    indexes: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[dict[str, Any]] = Field(default_factory=list)


class DomainModel(BaseModel):
    """Domain model definition."""

    id: str
    name: str
    type: str = "entity"  # aggregate_root, entity, value_object
    bounded_context: str = ""
    properties: list[dict[str, Any]] = Field(default_factory=list)
    behaviors: list[dict[str, Any]] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)


class DomainEvent(BaseModel):
    """Domain event definition."""

    id: str
    name: str
    producer: str = ""
    description: str = ""
    payload: dict[str, str] = Field(default_factory=dict)
    consumers: list[dict[str, str]] = Field(default_factory=list)


class TechnicalSpec(BaseModel):
    """Complete technical specification."""

    project: str
    version: str = "1.0.0"
    architecture_style: str = "hexagonal"
    api_specifications: list[APIEndpoint] = Field(default_factory=list)
    database_schemas: list[DatabaseTable] = Field(default_factory=list)
    domain_models: list[DomainModel] = Field(default_factory=list)
    domain_events: list[DomainEvent] = Field(default_factory=list)


class DevTask(BaseModel):
    """Development task."""

    id: str
    title: str
    type: str = "backend"  # backend, frontend, testing, devops
    story: str = ""
    description: str = ""
    technical_details: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    estimated_hours: float = 0


class UserStory(BaseModel):
    """User story."""

    id: str
    title: str
    epic: str = ""
    related_fr: str = ""
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    story_points: int = 0
    tasks: list[DevTask] = Field(default_factory=list)


class Epic(BaseModel):
    """Epic (large feature)."""

    id: str
    title: str
    description: str = ""
    related_brs: list[str] = Field(default_factory=list)
    stories: list[UserStory] = Field(default_factory=list)


class DevTaskList(BaseModel):
    """Complete development task list."""

    sprint: str = ""
    start_date: str = ""
    end_date: str = ""
    epics: list[Epic] = Field(default_factory=list)
