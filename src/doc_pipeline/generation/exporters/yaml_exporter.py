"""YAML exporter for specifications."""

from pathlib import Path
from typing import Any

import yaml


class YAMLExporter:
    """Export specifications to YAML format."""

    def __init__(self, output_dir: str | Path):
        """
        Initialize the YAML exporter.

        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_requirements(
        self,
        data: dict[str, Any],
        filename: str = "requirements-list.yaml",
    ) -> Path:
        """Export requirements to YAML."""
        return self._write_yaml(data, filename)

    def export_technical_spec(
        self,
        data: dict[str, Any],
        filename: str = "technical-spec.yaml",
    ) -> Path:
        """Export technical specifications to YAML."""
        return self._write_yaml(data, filename)

    def export_dev_tasks(
        self,
        data: dict[str, Any],
        filename: str = "dev-tasks.yaml",
    ) -> Path:
        """Export development tasks to YAML."""
        return self._write_yaml(data, filename)

    def export_ai_ready_spec(
        self,
        data: dict[str, Any],
        feature_id: str,
    ) -> Path:
        """Export AI-Ready specification for a feature."""
        filename = f"ai-ready-spec/{feature_id}.yaml"
        return self._write_yaml(data, filename)

    def export_all(
        self,
        specs: dict[str, Any],
    ) -> dict[str, Path]:
        """
        Export all specifications to separate files.

        Args:
            specs: Dictionary with all specifications

        Returns:
            Dictionary mapping spec type to file path
        """
        exported = {}

        if "requirements" in specs:
            exported["requirements"] = self.export_requirements(specs["requirements"])

        if "api_specifications" in specs:
            exported["api_spec"] = self._write_yaml(
                specs["api_specifications"],
                "api-spec.yaml",
            )

        if "database" in specs:
            exported["database"] = self._write_yaml(
                specs["database"],
                "database-spec.yaml",
            )

        if "development_tasks" in specs:
            exported["dev_tasks"] = self.export_dev_tasks(specs["development_tasks"])

        # Export combined spec
        exported["combined"] = self._write_yaml(specs, "all-specs.yaml")

        return exported

    def _write_yaml(
        self,
        data: dict[str, Any],
        filename: str,
    ) -> Path:
        """Write data to YAML file."""
        file_path = self.output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        return file_path
