"""Prompt templates for specification generation."""

from doc_pipeline.generation.prompts.requirements import REQUIREMENTS_PROMPT
from doc_pipeline.generation.prompts.api_spec import API_SPEC_PROMPT
from doc_pipeline.generation.prompts.db_schema import DB_SCHEMA_PROMPT
from doc_pipeline.generation.prompts.dev_tasks import DEV_TASKS_PROMPT

__all__ = [
    "REQUIREMENTS_PROMPT",
    "API_SPEC_PROMPT",
    "DB_SCHEMA_PROMPT",
    "DEV_TASKS_PROMPT",
]
