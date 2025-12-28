"""OpenAPI 3.0 exporter for API specifications."""

from pathlib import Path
from typing import Any

import yaml


class OpenAPIExporter:
    """Export API specifications to OpenAPI 3.0 format."""

    def __init__(self, output_dir: str | Path):
        """
        Initialize the OpenAPI exporter.

        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        api_specs: list[dict[str, Any]],
        title: str = "API Specification",
        version: str = "1.0.0",
        filename: str = "openapi.yaml",
    ) -> Path:
        """
        Export API specifications to OpenAPI 3.0 format.

        Args:
            api_specs: List of API specification dictionaries
            title: API title
            version: API version
            filename: Output filename

        Returns:
            Path to the generated file
        """
        openapi_doc = self._build_openapi_doc(api_specs, title, version)

        file_path = self.output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(
                openapi_doc,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        return file_path

    def _build_openapi_doc(
        self,
        api_specs: list[dict[str, Any]],
        title: str,
        version: str,
    ) -> dict[str, Any]:
        """Build OpenAPI 3.0 document structure."""
        doc = {
            "openapi": "3.0.3",
            "info": {
                "title": title,
                "version": version,
                "description": "Auto-generated API specification",
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Development server"},
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                },
            },
        }

        for spec in api_specs:
            path = spec.get("path", "/")
            method = spec.get("method", "get").lower()

            if path not in doc["paths"]:
                doc["paths"][path] = {}

            doc["paths"][path][method] = self._build_operation(spec)

            # Add schemas from request/response
            self._extract_schemas(spec, doc["components"]["schemas"])

        return doc

    def _build_operation(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Build OpenAPI operation object."""
        operation = {
            "operationId": spec.get("id", "operation"),
            "summary": spec.get("name", ""),
            "description": spec.get("description", ""),
            "tags": [spec.get("version", "v1")],
        }

        # Request body
        request = spec.get("request", {})
        if request:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    request.get("content_type", "application/json"): {
                        "schema": self._convert_schema(request.get("body", {}))
                    }
                },
            }

        # Responses
        response = spec.get("response", {})
        operation["responses"] = {}

        # Success response
        success = response.get("success", {})
        if success:
            status = str(success.get("status", 200))
            operation["responses"][status] = {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": self._convert_schema(success.get("body", {}))
                    }
                },
            }

        # Error responses
        for error in response.get("errors", []):
            status = str(error.get("status", 400))
            operation["responses"][status] = {
                "description": error.get("message", "Error"),
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "code": {
                                    "type": "string",
                                    "example": error.get("code", "ERROR"),
                                },
                                "message": {
                                    "type": "string",
                                    "example": error.get("message", ""),
                                },
                            },
                        }
                    }
                },
            }

        # Security
        security = spec.get("security", {})
        if security.get("authentication") and security["authentication"] != "none":
            operation["security"] = [{"bearerAuth": []}]

        return operation

    def _convert_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert internal schema format to OpenAPI schema."""
        if not schema:
            return {"type": "object"}

        # If it's already in a compatible format
        if "type" in schema:
            result = {"type": schema["type"]}

            if schema["type"] == "object":
                result["properties"] = {}
                result["required"] = schema.get("required", [])

                for prop_name, prop_def in schema.get("properties", {}).items():
                    if isinstance(prop_def, dict):
                        result["properties"][prop_name] = prop_def
                    else:
                        # Simple string definition like "string (UUID)"
                        result["properties"][prop_name] = self._parse_simple_type(
                            str(prop_def)
                        )

            return result

        # Convert simple key-value definitions
        result = {"type": "object", "properties": {}}
        for key, value in schema.items():
            result["properties"][key] = self._parse_simple_type(str(value))

        return result

    def _parse_simple_type(self, type_str: str) -> dict[str, Any]:
        """Parse simple type string like 'string (UUID)'."""
        type_str = type_str.lower()

        if "uuid" in type_str:
            return {"type": "string", "format": "uuid"}
        elif "datetime" in type_str or "timestamp" in type_str:
            return {"type": "string", "format": "date-time"}
        elif "email" in type_str:
            return {"type": "string", "format": "email"}
        elif "int" in type_str or "number" in type_str:
            return {"type": "integer"}
        elif "bool" in type_str:
            return {"type": "boolean"}
        else:
            return {"type": "string"}

    def _extract_schemas(
        self,
        spec: dict[str, Any],
        schemas: dict[str, Any],
    ) -> None:
        """Extract reusable schemas from spec."""
        # This could be enhanced to create and reference shared schemas
        pass
