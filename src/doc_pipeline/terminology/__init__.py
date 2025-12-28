"""Terminology consistency checking module."""

from doc_pipeline.terminology.checker import TerminologyChecker
from doc_pipeline.terminology.models import (
    Glossary,
    GlossaryTerm,
    TerminologyIssue,
    TerminologyReport,
)

__all__ = [
    "TerminologyChecker",
    "Glossary",
    "GlossaryTerm",
    "TerminologyIssue",
    "TerminologyReport",
]
