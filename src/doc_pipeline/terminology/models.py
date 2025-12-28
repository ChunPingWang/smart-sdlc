"""Data models for terminology consistency checking."""

from pydantic import BaseModel, Field


class GlossaryTerm(BaseModel):
    """A single term definition in the glossary."""

    standard: str = Field(description="The standard/preferred term to use")
    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternative terms that should be replaced with the standard term",
    )
    description: str = Field(default="", description="Description of the term")


class Glossary(BaseModel):
    """A glossary containing terminology standards."""

    project_name: str = Field(default="", description="Project name")
    terms: list[GlossaryTerm] = Field(
        default_factory=list, description="List of term definitions"
    )


class TerminologyIssue(BaseModel):
    """A single terminology inconsistency issue."""

    id: str = Field(description="Issue ID (e.g., TERM-001)")
    source_file: str = Field(description="Source file where the issue was found")
    chunk_id: str = Field(description="ID of the chunk containing the issue")
    found_term: str = Field(description="The non-standard term found in the document")
    standard_term: str = Field(description="The standard term that should be used")
    context: str = Field(description="Context around the found term")
    severity: str = Field(default="warning", description="Issue severity")


class TerminologyReport(BaseModel):
    """Complete terminology consistency check report."""

    generated_at: str = Field(description="Report generation timestamp")
    glossary_file: str = Field(description="Path to the glossary file used")
    summary: dict = Field(description="Summary statistics")
    issues: list[TerminologyIssue] = Field(
        default_factory=list, description="List of found issues"
    )
