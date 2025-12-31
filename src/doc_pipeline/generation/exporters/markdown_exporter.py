"""Markdown exporter for specifications."""

from datetime import datetime
from pathlib import Path
from typing import Any


class MarkdownExporter:
    """Export specifications to Markdown format."""

    def __init__(self, output_dir: str | Path):
        """
        Initialize the Markdown exporter.

        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_requirements(
        self,
        data: dict[str, Any],
        filename: str = "requirements-list.md",
    ) -> Path:
        """Export requirements to Markdown."""
        lines = [
            "# 📋 需求規格清單",
            "",
            f"> 產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # Business Requirements
        brs = data.get("business_requirements", [])
        if brs:
            lines.extend([
                "## 📌 業務需求 (Business Requirements)",
                "",
            ])
            for br in brs:
                lines.extend(self._format_business_requirement(br))

        # Functional Requirements
        frs = data.get("functional_requirements", [])
        if frs:
            lines.extend([
                "## ⚙️ 功能需求 (Functional Requirements)",
                "",
            ])
            for fr in frs:
                lines.extend(self._format_functional_requirement(fr))

        # Business Rules
        brules = data.get("business_rules", [])
        if brules:
            lines.extend([
                "## 📏 業務規則 (Business Rules)",
                "",
            ])
            for brule in brules:
                lines.extend(self._format_business_rule(brule))

        # Non-Functional Requirements
        nfrs = data.get("non_functional_requirements", [])
        if nfrs:
            lines.extend([
                "## 🛡️ 非功能需求 (Non-Functional Requirements)",
                "",
            ])
            for nfr in nfrs:
                lines.extend(self._format_nfr(nfr))

        # Summary table
        lines.extend(self._format_requirements_summary(data))

        return self._write_markdown(lines, filename)

    def _format_business_requirement(self, br: dict) -> list[str]:
        """Format a single business requirement."""
        lines = [
            f"### {br.get('id', 'N/A')}: {br.get('title', '未命名')}",
            "",
            f"**優先級**: `{br.get('priority', 'N/A')}`",
            f"**來源**: {br.get('source', 'N/A')}",
            "",
            f"> {br.get('description', '')}",
            "",
        ]

        criteria = br.get("acceptance_criteria", [])
        if criteria:
            lines.append("**驗收條件**:")
            for c in criteria:
                lines.append(f"- [ ] {c}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_functional_requirement(self, fr: dict) -> list[str]:
        """Format a single functional requirement."""
        lines = [
            f"### {fr.get('id', 'N/A')}: {fr.get('title', fr.get('description', '未命名')[:30])}",
            "",
        ]

        if fr.get("parent_br"):
            lines.append(f"**關聯業務需求**: `{fr['parent_br']}`")
        if fr.get("actor"):
            lines.append(f"**執行者**: {fr['actor']}")
        lines.append("")

        if fr.get("description"):
            lines.append(f"> {fr['description']}")
            lines.append("")

        preconditions = fr.get("preconditions", [])
        if preconditions:
            lines.append("**前置條件**:")
            for p in preconditions:
                lines.append(f"- {p}")
            lines.append("")

        postconditions = fr.get("postconditions", [])
        if postconditions:
            lines.append("**後置條件**:")
            for p in postconditions:
                lines.append(f"- {p}")
            lines.append("")

        brules = fr.get("business_rules", [])
        if brules:
            lines.append(f"**相關業務規則**: {', '.join(f'`{b}`' for b in brules)}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_business_rule(self, brule: dict) -> list[str]:
        """Format a single business rule."""
        lines = [
            f"### {brule.get('id', 'N/A')}: {brule.get('title', '未命名')}",
            "",
        ]

        if brule.get("type"):
            lines.append(f"**類型**: `{brule['type']}`")
            lines.append("")

        if brule.get("description"):
            lines.append(f"> {brule['description']}")
            lines.append("")

        if brule.get("error_message"):
            lines.append(f"**錯誤訊息**: _{brule['error_message']}_")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_nfr(self, nfr: dict) -> list[str]:
        """Format a single non-functional requirement."""
        lines = [
            f"### {nfr.get('id', 'N/A')}: {nfr.get('title', nfr.get('requirement', '未命名')[:30])}",
            "",
            f"**類別**: `{nfr.get('category', 'N/A')}`",
            "",
        ]

        if nfr.get("requirement"):
            lines.append(f"> {nfr['requirement']}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_requirements_summary(self, data: dict) -> list[str]:
        """Format requirements summary table."""
        brs = len(data.get("business_requirements", []))
        frs = len(data.get("functional_requirements", []))
        brules = len(data.get("business_rules", []))
        nfrs = len(data.get("non_functional_requirements", []))
        total = brs + frs + brules + nfrs

        return [
            "",
            "## 📊 需求統計",
            "",
            "| 類型 | 數量 |",
            "|------|------|",
            f"| 業務需求 (BR) | {brs} |",
            f"| 功能需求 (FR) | {frs} |",
            f"| 業務規則 (BRule) | {brules} |",
            f"| 非功能需求 (NFR) | {nfrs} |",
            f"| **總計** | **{total}** |",
            "",
        ]

    def export_api_spec(
        self,
        data: dict[str, Any],
        filename: str = "api-spec.md",
    ) -> Path:
        """Export API specifications to Markdown."""
        lines = [
            "# 🔌 API 規格文件",
            "",
            f"> 產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        apis = data.get("api_specifications", [])
        if not apis:
            lines.append("_尚無 API 規格_")
        else:
            # API Summary Table
            lines.extend([
                "## 📑 API 總覽",
                "",
                "| 方法 | 路徑 | 名稱 | 認證 |",
                "|------|------|------|------|",
            ])
            for api in apis:
                method = api.get("method", "GET")
                path = api.get("path", "N/A")
                name = api.get("name", "未命名")
                auth = api.get("security", {}).get("authentication", "required")
                method_badge = self._get_method_badge(method)
                lines.append(f"| {method_badge} | `{path}` | {name} | {auth} |")

            lines.extend(["", "---", ""])

            # API Details
            lines.append("## 📖 API 詳細規格")
            lines.append("")

            for api in apis:
                lines.extend(self._format_api(api))

        return self._write_markdown(lines, filename)

    def _get_method_badge(self, method: str) -> str:
        """Get colored badge for HTTP method."""
        badges = {
            "GET": "🟢 GET",
            "POST": "🟡 POST",
            "PUT": "🔵 PUT",
            "PATCH": "🟣 PATCH",
            "DELETE": "🔴 DELETE",
        }
        return badges.get(method.upper(), method)

    def _format_api(self, api: dict) -> list[str]:
        """Format a single API specification."""
        api_id = api.get("id", "N/A")
        name = api.get("name", "未命名")
        method = api.get("method", "GET")
        path = api.get("path", "N/A")

        lines = [
            f"### {api_id}: {name}",
            "",
            f"**{self._get_method_badge(method)}** `{path}`",
            "",
        ]

        if api.get("version"):
            lines.append(f"**版本**: {api['version']}")
        if api.get("related_fr"):
            lines.append(f"**關聯功能需求**: `{api['related_fr']}`")

        lines.append("")

        if api.get("description"):
            lines.append(f"> {api['description']}")
            lines.append("")

        # Request
        request = api.get("request", {})
        if request:
            lines.extend(self._format_request(request))

        # Response
        response = api.get("response", {})
        if response:
            lines.extend(self._format_response(response))

        # Security
        security = api.get("security", {})
        if security:
            lines.extend([
                "#### 🔐 安全性",
                "",
                f"- **認證**: {security.get('authentication', 'N/A')}",
            ])
            if security.get("rate_limit"):
                lines.append(f"- **速率限制**: {security['rate_limit']}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_request(self, request: dict) -> list[str]:
        """Format API request specification."""
        lines = [
            "#### 📤 Request",
            "",
        ]

        if request.get("content_type"):
            lines.append(f"**Content-Type**: `{request['content_type']}`")
            lines.append("")

        body = request.get("body", {})
        if body:
            properties = body.get("properties", {})
            required = body.get("required", [])

            if properties:
                lines.append("**Request Body**:")
                lines.append("")
                lines.append("| 欄位 | 類型 | 必填 | 說明 |")
                lines.append("|------|------|------|------|")

                for field, spec in properties.items():
                    field_type = spec.get("type", "string")
                    if spec.get("format"):
                        field_type += f" ({spec['format']})"
                    is_required = "✅" if field in required else ""
                    desc = spec.get("description", "")
                    lines.append(f"| `{field}` | {field_type} | {is_required} | {desc} |")

                lines.append("")

        return lines

    def _format_response(self, response: dict) -> list[str]:
        """Format API response specification."""
        lines = [
            "#### 📥 Response",
            "",
        ]

        success = response.get("success", {})
        if success:
            status = success.get("status", 200)
            lines.append(f"**成功回應** (`{status}`):")
            lines.append("")
            lines.append("```json")

            body = success.get("body", {})
            if isinstance(body, dict):
                for key, value in body.items():
                    lines.append(f'  "{key}": "{value}"')
            lines.append("```")
            lines.append("")

        errors = response.get("errors", [])
        if errors:
            lines.append("**錯誤回應**:")
            lines.append("")
            lines.append("| 狀態碼 | 錯誤碼 | 說明 |")
            lines.append("|--------|--------|------|")

            for error in errors:
                status = error.get("status", "N/A")
                code = error.get("code", "N/A")
                message = error.get("message", "")
                lines.append(f"| {status} | `{code}` | {message} |")

            lines.append("")

        return lines

    def export_dev_tasks(
        self,
        data: dict[str, Any],
        filename: str = "dev-tasks.md",
    ) -> Path:
        """Export development tasks to Markdown."""
        lines = [
            "# 📝 開發任務清單",
            "",
            f"> 產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # Epics
        epics = data.get("epics", [])
        if epics:
            lines.extend([
                "## 🎯 Epics",
                "",
            ])
            for epic in epics:
                lines.extend(self._format_epic(epic))

        # Stories
        stories = data.get("stories", [])
        if stories:
            lines.extend([
                "## 📖 User Stories",
                "",
            ])
            for story in stories:
                lines.extend(self._format_story(story))

        # Tasks
        tasks = data.get("tasks", [])
        if tasks:
            lines.extend([
                "## ✅ Tasks",
                "",
            ])
            for task in tasks:
                lines.extend(self._format_task(task))

        # Summary
        lines.extend(self._format_tasks_summary(data))

        return self._write_markdown(lines, filename)

    def _format_epic(self, epic: dict) -> list[str]:
        """Format a single epic."""
        lines = [
            f"### {epic.get('id', 'N/A')}: {epic.get('title', '未命名')}",
            "",
        ]

        if epic.get("description"):
            lines.append(f"> {epic['description']}")
            lines.append("")

        related_brs = epic.get("related_brs", [])
        if related_brs:
            lines.append(f"**關聯業務需求**: {', '.join(f'`{br}`' for br in related_brs)}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_story(self, story: dict) -> list[str]:
        """Format a single user story."""
        lines = [
            f"### {story.get('id', 'N/A')}: {story.get('title', '未命名')}",
            "",
        ]

        if story.get("epic"):
            lines.append(f"**Epic**: `{story['epic']}`")
        if story.get("related_fr"):
            lines.append(f"**功能需求**: `{story['related_fr']}`")
        if story.get("story_points"):
            lines.append(f"**Story Points**: {story['story_points']}")

        lines.append("")

        if story.get("description"):
            lines.append("**User Story**:")
            lines.append("")
            lines.append("```")
            lines.append(story["description"].strip())
            lines.append("```")
            lines.append("")

        criteria = story.get("acceptance_criteria", [])
        if criteria:
            lines.append("**驗收條件**:")
            for c in criteria:
                lines.append(f"- [ ] {c}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_task(self, task: dict) -> list[str]:
        """Format a single development task."""
        task_id = task.get("id", "N/A")
        title = task.get("title", "未命名")
        task_type = task.get("type", "development")

        type_icons = {
            "backend": "⚙️",
            "frontend": "🖥️",
            "testing": "🧪",
            "infrastructure": "🏗️",
            "documentation": "📚",
        }
        icon = type_icons.get(task_type, "📌")

        lines = [
            f"### {icon} {task_id}: {title}",
            "",
        ]

        if task.get("story"):
            lines.append(f"**Story**: `{task['story']}`")
        if task.get("type"):
            lines.append(f"**類型**: `{task['type']}`")
        if task.get("estimated_hours"):
            lines.append(f"**預估時數**: {task['estimated_hours']} 小時")

        lines.append("")

        if task.get("description"):
            lines.append(f"> {task['description']}")
            lines.append("")

        # Dependencies
        deps = task.get("dependencies", [])
        if deps:
            lines.append(f"**依賴任務**: {', '.join(f'`{d}`' for d in deps)}")
            lines.append("")

        # Technical Details
        tech = task.get("technical_details", {})
        if tech:
            lines.append("**技術細節**:")
            if tech.get("file_path"):
                lines.append(f"- 檔案路徑: `{tech['file_path']}`")
            refs = tech.get("references", [])
            if refs:
                for ref in refs:
                    if isinstance(ref, dict):
                        for key, value in ref.items():
                            if isinstance(value, list):
                                lines.append(f"- {key}: {', '.join(f'`{v}`' for v in value)}")
                            else:
                                lines.append(f"- {key}: `{value}`")
            lines.append("")

        # Test Scenarios
        scenarios = task.get("test_scenarios", [])
        if scenarios:
            lines.append("**測試場景**:")
            for s in scenarios:
                lines.append(f"- [ ] {s}")
            lines.append("")

        # Checklist
        checklist = task.get("checklist", [])
        if checklist:
            lines.append("**開發 Checklist**:")
            for item in checklist:
                lines.append(f"- [ ] {item}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _format_tasks_summary(self, data: dict) -> list[str]:
        """Format tasks summary."""
        epics = len(data.get("epics", []))
        stories = len(data.get("stories", []))
        tasks = data.get("tasks", [])
        task_count = len(tasks)

        total_hours = sum(t.get("estimated_hours", 0) for t in tasks)

        # Count by type
        type_counts: dict[str, int] = {}
        for task in tasks:
            t = task.get("type", "other")
            type_counts[t] = type_counts.get(t, 0) + 1

        lines = [
            "",
            "## 📊 任務統計",
            "",
            "| 項目 | 數量 |",
            "|------|------|",
            f"| Epics | {epics} |",
            f"| Stories | {stories} |",
            f"| Tasks | {task_count} |",
            f"| **總預估時數** | **{total_hours} 小時** |",
            "",
        ]

        if type_counts:
            lines.extend([
                "### 任務類型分布",
                "",
                "| 類型 | 數量 |",
                "|------|------|",
            ])
            for t, count in sorted(type_counts.items()):
                lines.append(f"| {t} | {count} |")
            lines.append("")

        return lines

    def export_all(
        self,
        specs: dict[str, Any],
    ) -> dict[str, Path]:
        """
        Export all specifications to separate Markdown files.

        Args:
            specs: Dictionary with all specifications

        Returns:
            Dictionary mapping spec type to file path
        """
        exported = {}

        if "requirements" in specs:
            exported["requirements"] = self.export_requirements(specs["requirements"])

        if "api_specifications" in specs:
            api_specs = specs["api_specifications"]
            # Handle nested structure from generate_all()
            if isinstance(api_specs, dict) and "api_specifications" in api_specs:
                api_list = api_specs["api_specifications"]
            elif isinstance(api_specs, list):
                api_list = api_specs
            else:
                api_list = []
            exported["api_spec"] = self.export_api_spec({"api_specifications": api_list})

        if "development_tasks" in specs:
            exported["dev_tasks"] = self.export_dev_tasks(specs["development_tasks"])

        return exported

    def _write_markdown(
        self,
        lines: list[str],
        filename: str,
    ) -> Path:
        """Write lines to Markdown file."""
        file_path = self.output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = "\n".join(lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path
