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

    def export_readable_report(
        self, report: TerminologyReport, output_path: Path
    ) -> Path:
        """
        Export a human-readable Markdown report for non-technical users.

        Args:
            report: The terminology report
            output_path: Directory to save the report

        Returns:
            Path to the saved report file
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / "術語檢查報告.md"

        # Calculate statistics
        total = report.summary["total_chunks"]
        issues_count = report.summary["issues_found"]
        score = report.summary["consistency_score"]
        score_pct = int(score * 100)

        # Determine status emoji and message
        if score_pct >= 90:
            status_emoji = "✅"
            status_msg = "優良"
            status_desc = "文件用語非常一致，符合規範標準。"
        elif score_pct >= 70:
            status_emoji = "⚠️"
            status_msg = "尚可"
            status_desc = "文件用語大致一致，但有些地方需要調整。"
        else:
            status_emoji = "❌"
            status_msg = "需改善"
            status_desc = "文件用語不一致，建議進行統一修訂。"

        # Group issues by source file
        issues_by_file: dict[str, list[TerminologyIssue]] = {}
        for issue in report.issues:
            filename = Path(issue.source_file).name
            if filename not in issues_by_file:
                issues_by_file[filename] = []
            issues_by_file[filename].append(issue)

        # Build Markdown content
        lines = [
            "# 📋 術語一致性檢查報告",
            "",
            f"**產生時間**：{self._format_datetime(report.generated_at)}",
            f"**字典檔案**：{Path(report.glossary_file).name}",
            "",
            "---",
            "",
            "## 📊 檢查結果摘要",
            "",
            f"### {status_emoji} 整體評估：{status_msg}",
            "",
            status_desc,
            "",
            "| 項目 | 數值 |",
            "|------|------|",
            f"| 檢查文件數 | {total} 份 |",
            f"| 發現問題數 | {issues_count} 處 |",
            f"| 一致性分數 | **{score_pct}%** |",
            "",
        ]

        if not report.issues:
            lines.extend([
                "---",
                "",
                "## ✨ 恭喜！",
                "",
                "未發現任何術語不一致的問題。所有文件用語都符合規範！",
                "",
            ])
        else:
            lines.extend([
                "---",
                "",
                "## 📝 需要修正的用語",
                "",
                "以下是發現的術語不一致問題，請參考「建議用語」進行修正：",
                "",
            ])

            # Add issues grouped by file
            for filename, file_issues in issues_by_file.items():
                lines.extend([
                    f"### 📄 {filename}",
                    "",
                    "| 目前用語 | ➡️ | 建議用語 | 出現位置 |",
                    "|----------|:--:|----------|----------|",
                ])

                for issue in file_issues:
                    context = issue.context[:30] + "..." if len(issue.context) > 30 else issue.context
                    # Escape pipe characters in context
                    context = context.replace("|", "\\|")
                    lines.append(
                        f"| **{issue.found_term}** | ➡️ | {issue.standard_term} | {context} |"
                    )

                lines.append("")

            # Add summary by term
            lines.extend([
                "---",
                "",
                "## 📈 問題統計",
                "",
                "以下是各個非標準用語的出現次數：",
                "",
                "| 非標準用語 | 出現次數 | 應改為 |",
                "|------------|----------|--------|",
            ])

            # Count occurrences of each found term
            term_counts: dict[str, tuple[int, str]] = {}
            for issue in report.issues:
                key = issue.found_term
                if key in term_counts:
                    count, std = term_counts[key]
                    term_counts[key] = (count + 1, std)
                else:
                    term_counts[key] = (1, issue.standard_term)

            for found_term, (count, standard_term) in sorted(
                term_counts.items(), key=lambda x: x[1][0], reverse=True
            ):
                lines.append(f"| {found_term} | {count} 次 | {standard_term} |")

            lines.append("")

        # Add glossary reference
        lines.extend([
            "---",
            "",
            "## 📖 術語對照表",
            "",
            "本次檢查使用的標準術語定義：",
            "",
            "| 標準用語 | 說明 | 常見替代詞 |",
            "|----------|------|------------|",
        ])

        for term in self.glossary.terms:
            alts = "、".join(term.alternatives[:3])
            if len(term.alternatives) > 3:
                alts += "..."
            desc = term.description or "-"
            lines.append(f"| **{term.standard}** | {desc} | {alts} |")

        lines.extend([
            "",
            "---",
            "",
            "## 💡 修正建議",
            "",
            "1. **使用編輯器的「尋找並取代」功能**：可快速將非標準用語替換為標準用語",
            "2. **優先處理高頻問題**：從出現次數最多的非標準用語開始修正",
            "3. **更新寫作習慣**：熟記標準術語，避免未來再次使用非標準用語",
            "4. **定期檢查**：建議在文件完成後定期執行術語檢查",
            "",
            "---",
            "",
            f"*報告由 Doc-Pipeline 自動產生 | {self._format_datetime(report.generated_at)}*",
            "",
        ])

        # Write file
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return report_file

    def _format_datetime(self, iso_datetime: str) -> str:
        """Format ISO datetime to readable format."""
        try:
            dt = datetime.fromisoformat(iso_datetime)
            return dt.strftime("%Y 年 %m 月 %d 日 %H:%M")
        except (ValueError, TypeError):
            return iso_datetime
