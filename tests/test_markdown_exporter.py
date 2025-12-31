"""Tests for Markdown exporter."""

import tempfile
from pathlib import Path

import pytest

from doc_pipeline.generation.exporters import MarkdownExporter


class TestMarkdownExporter:
    """Test suite for MarkdownExporter."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def exporter(self, output_dir: Path) -> MarkdownExporter:
        """Create MarkdownExporter instance."""
        return MarkdownExporter(output_dir)

    @pytest.fixture
    def sample_requirements(self) -> dict:
        """Sample requirements data."""
        return {
            "business_requirements": [
                {
                    "id": "BR-001",
                    "title": "用戶註冊功能",
                    "description": "系統需提供用戶自助註冊功能",
                    "priority": "P0",
                    "source": "系統設計文件",
                    "acceptance_criteria": [
                        "用戶可透過 Email 註冊",
                        "註冊後需 Email 驗證",
                    ],
                }
            ],
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "Email 註冊",
                    "parent_br": "BR-001",
                    "description": "用戶輸入 Email 和密碼完成註冊",
                    "actor": "訪客",
                    "preconditions": ["用戶未登入"],
                    "postconditions": ["用戶帳號建立"],
                    "business_rules": ["BRule-001"],
                }
            ],
            "business_rules": [
                {
                    "id": "BRule-001",
                    "title": "Email 格式驗證",
                    "description": "Email 必須符合 RFC 5322 格式",
                    "type": "validation",
                    "error_message": "請輸入有效的 Email 格式",
                }
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "category": "performance",
                    "title": "API 回應時間",
                    "requirement": "95% 的 API 請求需在 200ms 內回應",
                }
            ],
        }

    @pytest.fixture
    def sample_api_specs(self) -> dict:
        """Sample API specifications data."""
        return {
            "api_specifications": [
                {
                    "id": "API-001",
                    "name": "用戶註冊",
                    "method": "POST",
                    "path": "/api/v1/users/register",
                    "version": "v1",
                    "related_fr": "FR-001",
                    "description": "註冊新用戶帳號",
                    "request": {
                        "content_type": "application/json",
                        "body": {
                            "type": "object",
                            "required": ["email", "password"],
                            "properties": {
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "用戶 Email",
                                },
                                "password": {
                                    "type": "string",
                                    "min_length": 8,
                                    "description": "密碼，至少8字元",
                                },
                            },
                        },
                    },
                    "response": {
                        "success": {
                            "status": 201,
                            "body": {
                                "user_id": "string (UUID)",
                                "email": "string",
                            },
                        },
                        "errors": [
                            {
                                "status": 400,
                                "code": "INVALID_EMAIL",
                                "message": "Email 格式不正確",
                            },
                            {
                                "status": 409,
                                "code": "EMAIL_EXISTS",
                                "message": "Email 已被使用",
                            },
                        ],
                    },
                    "security": {
                        "authentication": "none",
                        "rate_limit": "10 requests/minute per IP",
                    },
                }
            ]
        }

    @pytest.fixture
    def sample_dev_tasks(self) -> dict:
        """Sample development tasks data."""
        return {
            "epics": [
                {
                    "id": "EPIC-001",
                    "title": "用戶管理模組",
                    "description": "實作用戶註冊、登入、權限管理",
                    "related_brs": ["BR-001", "BR-002"],
                }
            ],
            "stories": [
                {
                    "id": "STORY-001",
                    "title": "用戶 Email 註冊",
                    "epic": "EPIC-001",
                    "related_fr": "FR-001",
                    "description": "身為訪客\n我想要透過 Email 註冊帳號\n以便使用系統功能",
                    "acceptance_criteria": [
                        "輸入有效 Email 和密碼可完成註冊",
                        "重複 Email 顯示錯誤訊息",
                    ],
                    "story_points": 5,
                }
            ],
            "tasks": [
                {
                    "id": "TASK-001",
                    "story": "STORY-001",
                    "title": "實作 User Entity",
                    "type": "backend",
                    "description": "建立 User 領域模型",
                    "technical_details": {
                        "file_path": "src/domain/user.py",
                        "references": [
                            {"domain_model": "DM-001"},
                            {"business_rules": ["BRule-001"]},
                        ],
                    },
                    "dependencies": [],
                    "estimated_hours": 2,
                    "checklist": [
                        "建立 User Entity class",
                        "實作 Email Value Object",
                        "撰寫單元測試",
                    ],
                },
                {
                    "id": "TASK-002",
                    "story": "STORY-001",
                    "title": "API 整合測試",
                    "type": "testing",
                    "description": "撰寫註冊 API 整合測試",
                    "dependencies": ["TASK-001"],
                    "estimated_hours": 2,
                    "test_scenarios": [
                        "成功註冊",
                        "Email 格式錯誤",
                    ],
                },
            ],
        }


class TestExportRequirements(TestMarkdownExporter):
    """Test export_requirements method."""

    def test_export_requirements_creates_file(
        self, exporter: MarkdownExporter, output_dir: Path, sample_requirements: dict
    ):
        """Test that export_requirements creates a markdown file."""
        result = exporter.export_requirements(sample_requirements)

        assert result.exists()
        assert result.suffix == ".md"
        assert result.name == "requirements-list.md"

    def test_export_requirements_content_has_title(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test that exported file has correct title."""
        result = exporter.export_requirements(sample_requirements)
        content = result.read_text(encoding="utf-8")

        assert "# 📋 需求規格清單" in content

    def test_export_requirements_has_business_requirements(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test that business requirements are included."""
        result = exporter.export_requirements(sample_requirements)
        content = result.read_text(encoding="utf-8")

        assert "## 📌 業務需求" in content
        assert "BR-001" in content
        assert "用戶註冊功能" in content
        assert "`P0`" in content

    def test_export_requirements_has_functional_requirements(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test that functional requirements are included."""
        result = exporter.export_requirements(sample_requirements)
        content = result.read_text(encoding="utf-8")

        assert "## ⚙️ 功能需求" in content
        assert "FR-001" in content
        assert "`BR-001`" in content
        assert "訪客" in content

    def test_export_requirements_has_business_rules(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test that business rules are included."""
        result = exporter.export_requirements(sample_requirements)
        content = result.read_text(encoding="utf-8")

        assert "## 📏 業務規則" in content
        assert "BRule-001" in content
        assert "validation" in content

    def test_export_requirements_has_nfr(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test that non-functional requirements are included."""
        result = exporter.export_requirements(sample_requirements)
        content = result.read_text(encoding="utf-8")

        assert "## 🛡️ 非功能需求" in content
        assert "NFR-001" in content
        assert "performance" in content

    def test_export_requirements_has_summary_table(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test that summary statistics table is included."""
        result = exporter.export_requirements(sample_requirements)
        content = result.read_text(encoding="utf-8")

        assert "## 📊 需求統計" in content
        assert "| 業務需求 (BR) | 1 |" in content
        assert "| 功能需求 (FR) | 1 |" in content

    def test_export_requirements_empty_data(
        self, exporter: MarkdownExporter
    ):
        """Test export with empty requirements."""
        result = exporter.export_requirements({})
        content = result.read_text(encoding="utf-8")

        assert "# 📋 需求規格清單" in content
        assert "| **總計** | **0** |" in content

    def test_export_requirements_custom_filename(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test export with custom filename."""
        result = exporter.export_requirements(
            sample_requirements, filename="custom-reqs.md"
        )

        assert result.name == "custom-reqs.md"


class TestExportApiSpec(TestMarkdownExporter):
    """Test export_api_spec method."""

    def test_export_api_spec_creates_file(
        self, exporter: MarkdownExporter, output_dir: Path, sample_api_specs: dict
    ):
        """Test that export_api_spec creates a markdown file."""
        result = exporter.export_api_spec(sample_api_specs)

        assert result.exists()
        assert result.suffix == ".md"
        assert result.name == "api-spec.md"

    def test_export_api_spec_has_title(
        self, exporter: MarkdownExporter, sample_api_specs: dict
    ):
        """Test that exported file has correct title."""
        result = exporter.export_api_spec(sample_api_specs)
        content = result.read_text(encoding="utf-8")

        assert "# 🔌 API 規格文件" in content

    def test_export_api_spec_has_overview_table(
        self, exporter: MarkdownExporter, sample_api_specs: dict
    ):
        """Test that API overview table is included."""
        result = exporter.export_api_spec(sample_api_specs)
        content = result.read_text(encoding="utf-8")

        assert "## 📑 API 總覽" in content
        assert "| 方法 | 路徑 | 名稱 | 認證 |" in content
        assert "🟡 POST" in content
        assert "`/api/v1/users/register`" in content

    def test_export_api_spec_has_request_details(
        self, exporter: MarkdownExporter, sample_api_specs: dict
    ):
        """Test that request details are included."""
        result = exporter.export_api_spec(sample_api_specs)
        content = result.read_text(encoding="utf-8")

        assert "#### 📤 Request" in content
        assert "application/json" in content
        assert "`email`" in content
        assert "`password`" in content

    def test_export_api_spec_has_response_details(
        self, exporter: MarkdownExporter, sample_api_specs: dict
    ):
        """Test that response details are included."""
        result = exporter.export_api_spec(sample_api_specs)
        content = result.read_text(encoding="utf-8")

        assert "#### 📥 Response" in content
        assert "201" in content
        assert "`INVALID_EMAIL`" in content
        assert "`EMAIL_EXISTS`" in content

    def test_export_api_spec_has_security(
        self, exporter: MarkdownExporter, sample_api_specs: dict
    ):
        """Test that security section is included."""
        result = exporter.export_api_spec(sample_api_specs)
        content = result.read_text(encoding="utf-8")

        assert "#### 🔐 安全性" in content
        assert "10 requests/minute per IP" in content

    def test_export_api_spec_empty_data(self, exporter: MarkdownExporter):
        """Test export with empty API specs."""
        result = exporter.export_api_spec({"api_specifications": []})
        content = result.read_text(encoding="utf-8")

        assert "# 🔌 API 規格文件" in content
        assert "_尚無 API 規格_" in content

    def test_export_api_spec_method_badges(
        self, exporter: MarkdownExporter
    ):
        """Test that different HTTP methods get correct badges."""
        api_specs = {
            "api_specifications": [
                {"id": "API-001", "name": "Get", "method": "GET", "path": "/get"},
                {"id": "API-002", "name": "Post", "method": "POST", "path": "/post"},
                {"id": "API-003", "name": "Put", "method": "PUT", "path": "/put"},
                {"id": "API-004", "name": "Delete", "method": "DELETE", "path": "/del"},
            ]
        }
        result = exporter.export_api_spec(api_specs)
        content = result.read_text(encoding="utf-8")

        assert "🟢 GET" in content
        assert "🟡 POST" in content
        assert "🔵 PUT" in content
        assert "🔴 DELETE" in content


class TestExportDevTasks(TestMarkdownExporter):
    """Test export_dev_tasks method."""

    def test_export_dev_tasks_creates_file(
        self, exporter: MarkdownExporter, output_dir: Path, sample_dev_tasks: dict
    ):
        """Test that export_dev_tasks creates a markdown file."""
        result = exporter.export_dev_tasks(sample_dev_tasks)

        assert result.exists()
        assert result.suffix == ".md"
        assert result.name == "dev-tasks.md"

    def test_export_dev_tasks_has_title(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that exported file has correct title."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "# 📝 開發任務清單" in content

    def test_export_dev_tasks_has_epics(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that epics are included."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "## 🎯 Epics" in content
        assert "EPIC-001" in content
        assert "用戶管理模組" in content

    def test_export_dev_tasks_has_stories(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that user stories are included."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "## 📖 User Stories" in content
        assert "STORY-001" in content
        assert "Story Points" in content

    def test_export_dev_tasks_has_tasks(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that tasks are included."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "## ✅ Tasks" in content
        assert "TASK-001" in content
        assert "TASK-002" in content

    def test_export_dev_tasks_has_checklist(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that task checklists are included."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "**開發 Checklist**:" in content
        assert "- [ ] 建立 User Entity class" in content

    def test_export_dev_tasks_has_test_scenarios(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that test scenarios are included."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "**測試場景**:" in content
        assert "- [ ] 成功註冊" in content

    def test_export_dev_tasks_has_summary(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that task summary is included."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "## 📊 任務統計" in content
        assert "| Epics | 1 |" in content
        assert "| Stories | 1 |" in content
        assert "| Tasks | 2 |" in content
        assert "| **總預估時數** | **4 小時** |" in content

    def test_export_dev_tasks_type_icons(
        self, exporter: MarkdownExporter, sample_dev_tasks: dict
    ):
        """Test that task types have correct icons."""
        result = exporter.export_dev_tasks(sample_dev_tasks)
        content = result.read_text(encoding="utf-8")

        assert "### ⚙️ TASK-001" in content  # backend
        assert "### 🧪 TASK-002" in content  # testing

    def test_export_dev_tasks_empty_data(self, exporter: MarkdownExporter):
        """Test export with empty tasks."""
        result = exporter.export_dev_tasks({})
        content = result.read_text(encoding="utf-8")

        assert "# 📝 開發任務清單" in content
        assert "| **總預估時數** | **0 小時** |" in content


class TestExportAll(TestMarkdownExporter):
    """Test export_all method."""

    def test_export_all_creates_all_files(
        self,
        exporter: MarkdownExporter,
        output_dir: Path,
        sample_requirements: dict,
        sample_api_specs: dict,
        sample_dev_tasks: dict,
    ):
        """Test that export_all creates all markdown files."""
        specs = {
            "requirements": sample_requirements,
            "api_specifications": sample_api_specs["api_specifications"],
            "development_tasks": sample_dev_tasks,
        }

        result = exporter.export_all(specs)

        assert "requirements" in result
        assert "api_spec" in result
        assert "dev_tasks" in result
        assert all(path.exists() for path in result.values())

    def test_export_all_handles_nested_api_specs(
        self,
        exporter: MarkdownExporter,
        sample_requirements: dict,
        sample_api_specs: dict,
        sample_dev_tasks: dict,
    ):
        """Test that export_all handles nested api_specifications structure."""
        # Simulate the structure from generate_all()
        specs = {
            "requirements": sample_requirements,
            "api_specifications": sample_api_specs,  # Nested structure
            "development_tasks": sample_dev_tasks,
        }

        result = exporter.export_all(specs)

        assert "api_spec" in result
        content = result["api_spec"].read_text(encoding="utf-8")
        assert "API-001" in content

    def test_export_all_partial_specs(
        self, exporter: MarkdownExporter, sample_requirements: dict
    ):
        """Test export_all with only some specs present."""
        specs = {
            "requirements": sample_requirements,
        }

        result = exporter.export_all(specs)

        assert "requirements" in result
        assert "api_spec" not in result
        assert "dev_tasks" not in result

    def test_export_all_empty_specs(self, exporter: MarkdownExporter):
        """Test export_all with empty specs."""
        result = exporter.export_all({})

        assert len(result) == 0
