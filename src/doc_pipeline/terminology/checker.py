"""Terminology consistency checker using LLM."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from doc_pipeline.classification.classifier import LLMClient
from doc_pipeline.document.models import DocumentChunk
from doc_pipeline.terminology.models import (
    Glossary,
    GlossaryTerm,
    TerminologyIssue,
    TerminologyReport,
)
from doc_pipeline.terminology.prompts import (
    TERMINOLOGY_CHECK_PROMPT,
    TERMINOLOGY_SYSTEM_PROMPT,
)


class TerminologyChecker:
    """
    Check document terminology consistency against a glossary.

    Uses LLM to analyze document chunks and find terminology
    that doesn't match the standard terms defined in the glossary.
    """

    def __init__(self, glossary_path: Path | str):
        """
        Initialize the terminology checker.

        Args:
            glossary_path: Path to the YAML glossary file
        """
        self.glossary_path = Path(glossary_path)
        self.glossary = self._load_glossary(self.glossary_path)
        self.llm = LLMClient()
        self._issue_counter = 0

    def _load_glossary(self, path: Path) -> Glossary:
        """
        Load glossary from YAML file.

        Args:
            path: Path to the glossary file

        Returns:
            Glossary object

        Raises:
            FileNotFoundError: If glossary file doesn't exist
            ValueError: If glossary format is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Glossary file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty or invalid glossary file: {path}")

        terms = []
        for term_data in data.get("terms", []):
            terms.append(
                GlossaryTerm(
                    standard=term_data.get("standard", ""),
                    alternatives=term_data.get("alternatives", []),
                    description=term_data.get("description", ""),
                )
            )

        return Glossary(
            project_name=data.get("project_name", ""),
            terms=terms,
        )

    def _format_glossary_for_prompt(self) -> str:
        """
        Format glossary as text for LLM prompt.

        Returns:
            Formatted glossary string
        """
        lines = []
        for term in self.glossary.terms:
            alts = ", ".join(f'"{a}"' for a in term.alternatives)
            lines.append(f'- 標準用語: "{term.standard}"')
            if alts:
                lines.append(f"  替代詞（視為不一致）: {alts}")
            if term.description:
                lines.append(f"  說明: {term.description}")
        return "\n".join(lines)

    def _generate_issue_id(self) -> str:
        """Generate a unique issue ID."""
        self._issue_counter += 1
        return f"TERM-{self._issue_counter:03d}"

    def check_chunk(self, chunk: DocumentChunk) -> list[TerminologyIssue]:
        """
        Check a single chunk for terminology issues.

        Args:
            chunk: The document chunk to check

        Returns:
            List of terminology issues found
        """
        # Format the prompt
        user_prompt = TERMINOLOGY_CHECK_PROMPT.format(
            glossary=self._format_glossary_for_prompt(),
            source_file=str(chunk.metadata.source_file),
            content=chunk.content,
        )

        # Call LLM
        try:
            response = self.llm.complete(TERMINOLOGY_SYSTEM_PROMPT, user_prompt)
            result = self._parse_llm_response(response)
        except Exception as e:
            print(f"Warning: LLM error for chunk {chunk.id}: {e}")
            return []

        # Convert to TerminologyIssue objects
        issues = []
        for issue_data in result.get("issues", []):
            issue = TerminologyIssue(
                id=self._generate_issue_id(),
                source_file=str(chunk.metadata.source_file),
                chunk_id=chunk.id,
                found_term=issue_data.get("found_term", ""),
                standard_term=issue_data.get("standard_term", ""),
                context=issue_data.get("context", ""),
                severity="warning",
            )
            issues.append(issue)

        return issues

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM JSON response.

        Args:
            response: Raw LLM response

        Returns:
            Parsed result dict
        """
        # Try to find JSON in response
        json_match = re.search(r"\{[\s\S]*\}", response)

        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "issues": data.get("issues", []),
                    "consistency_score": float(data.get("consistency_score", 1.0)),
                }
            except json.JSONDecodeError:
                pass

        return {"issues": [], "consistency_score": 1.0}

    def check_all(self, chunks: list[DocumentChunk]) -> TerminologyReport:
        """
        Check all chunks for terminology issues.

        Args:
            chunks: List of document chunks to check

        Returns:
            Complete terminology report
        """
        self._issue_counter = 0  # Reset counter
        all_issues: list[TerminologyIssue] = []
        total_score = 0.0

        for chunk in chunks:
            issues = self.check_chunk(chunk)
            all_issues.extend(issues)

            # Estimate score based on issues found
            if issues:
                # More issues = lower score
                chunk_score = max(0.0, 1.0 - (len(issues) * 0.1))
            else:
                chunk_score = 1.0
            total_score += chunk_score

        # Calculate average consistency score
        avg_score = total_score / len(chunks) if chunks else 1.0

        return TerminologyReport(
            generated_at=datetime.now().isoformat(),
            glossary_file=str(self.glossary_path),
            summary={
                "total_chunks": len(chunks),
                "issues_found": len(all_issues),
                "consistency_score": round(avg_score, 2),
            },
            issues=all_issues,
        )

    def export_report(self, report: TerminologyReport, output_path: Path) -> Path:
        """
        Export report to YAML file.

        Args:
            report: The terminology report
            output_path: Directory to save the report

        Returns:
            Path to the saved report file
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / "terminology-report.yaml"

        # Convert to dict for YAML export
        report_dict = {
            "report": {
                "generated_at": report.generated_at,
                "glossary_file": report.glossary_file,
                "summary": report.summary,
            },
            "issues": [
                {
                    "id": issue.id,
                    "source_file": issue.source_file,
                    "chunk_id": issue.chunk_id,
                    "found_term": issue.found_term,
                    "standard_term": issue.standard_term,
                    "context": issue.context,
                    "severity": issue.severity,
                }
                for issue in report.issues
            ],
        }

        with open(report_file, "w", encoding="utf-8") as f:
            yaml.dump(report_dict, f, allow_unicode=True, sort_keys=False)

        return report_file
