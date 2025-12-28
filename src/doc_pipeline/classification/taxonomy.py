"""Document classification taxonomy and definitions."""

from dataclasses import dataclass

from doc_pipeline.document.models import ChunkType


@dataclass
class ChunkTypeInfo:
    """Information about a chunk type."""

    type: ChunkType
    name: str
    name_zh: str
    description: str
    keywords: list[str]
    examples: list[str]


# Taxonomy definition with Chinese and English descriptions
TAXONOMY: dict[ChunkType, ChunkTypeInfo] = {
    ChunkType.BUSINESS_RULE: ChunkTypeInfo(
        type=ChunkType.BUSINESS_RULE,
        name="Business Rule",
        name_zh="業務規則",
        description="Validation rules, calculation logic, or decision rules for business operations",
        keywords=[
            "must", "should", "validate", "verify", "check",
            "必須", "應該", "驗證", "檢查", "規則",
            "if-then", "when", "constraint", "限制", "條件",
        ],
        examples=[
            "Email must be in valid RFC 5322 format",
            "Password must be at least 8 characters with mixed case",
            "Age must be between 18 and 120",
        ],
    ),
    ChunkType.USE_CASE: ChunkTypeInfo(
        type=ChunkType.USE_CASE,
        name="Use Case",
        name_zh="使用案例",
        description="User stories, use case descriptions, or user workflow scenarios",
        keywords=[
            "user", "actor", "scenario", "story", "flow",
            "用戶", "使用者", "情境", "場景", "流程",
            "as a", "I want", "so that", "given", "when", "then",
        ],
        examples=[
            "As a user, I want to register with my email",
            "The customer can view their order history",
            "When user clicks login, the system validates credentials",
        ],
    ),
    ChunkType.API_SPEC: ChunkTypeInfo(
        type=ChunkType.API_SPEC,
        name="API Specification",
        name_zh="API 規格",
        description="REST API endpoints, request/response formats, HTTP methods",
        keywords=[
            "api", "endpoint", "request", "response", "http",
            "get", "post", "put", "delete", "patch",
            "json", "path", "parameter", "body", "header",
            "接口", "請求", "回應", "端點",
        ],
        examples=[
            "POST /api/v1/users - Create new user",
            "Request body: { email: string, password: string }",
            "Response 201: { id: uuid, created_at: datetime }",
        ],
    ),
    ChunkType.DB_SCHEMA: ChunkTypeInfo(
        type=ChunkType.DB_SCHEMA,
        name="Database Schema",
        name_zh="資料庫結構",
        description="Database table definitions, columns, indexes, constraints",
        keywords=[
            "table", "column", "field", "index", "constraint",
            "primary key", "foreign key", "unique", "nullable",
            "varchar", "int", "boolean", "timestamp", "uuid",
            "表格", "欄位", "索引", "約束", "主鍵", "外鍵",
        ],
        examples=[
            "Table: users (id UUID PK, email VARCHAR UNIQUE)",
            "CREATE TABLE orders (order_id SERIAL PRIMARY KEY)",
            "Index: idx_users_email ON users(email)",
        ],
    ),
    ChunkType.DOMAIN_MODEL: ChunkTypeInfo(
        type=ChunkType.DOMAIN_MODEL,
        name="Domain Model",
        name_zh="領域模型",
        description="Domain entities, value objects, aggregates in DDD style",
        keywords=[
            "entity", "aggregate", "value object", "domain",
            "bounded context", "repository", "factory",
            "實體", "聚合", "值物件", "領域", "倉儲",
            "property", "behavior", "invariant",
        ],
        examples=[
            "User Aggregate Root with Email value object",
            "Order entity belongs to Customer aggregate",
            "Invariant: Order total must equal sum of line items",
        ],
    ),
    ChunkType.SEQUENCE: ChunkTypeInfo(
        type=ChunkType.SEQUENCE,
        name="Sequence Diagram",
        name_zh="時序圖",
        description="Interaction flows, sequence diagrams, process steps",
        keywords=[
            "sequence", "flow", "step", "then", "next",
            "call", "return", "async", "sync",
            "時序", "步驟", "呼叫", "返回", "流程",
            "→", "->", "1.", "2.", "3.",
        ],
        examples=[
            "1. User submits form → 2. Server validates → 3. Database saves",
            "Client calls AuthService.login() → returns JWT token",
            "Step 1: Parse input, Step 2: Transform data",
        ],
    ),
    ChunkType.ARCHITECTURE: ChunkTypeInfo(
        type=ChunkType.ARCHITECTURE,
        name="Architecture",
        name_zh="架構設計",
        description="System architecture, components, infrastructure design",
        keywords=[
            "architecture", "component", "layer", "module",
            "microservice", "monolith", "infrastructure",
            "架構", "元件", "層", "模組", "基礎設施",
            "container", "deployment", "scale", "load balancer",
        ],
        examples=[
            "Hexagonal architecture with ports and adapters",
            "Microservices: User Service, Order Service, Payment Service",
            "Deploy to Kubernetes with 3 replicas",
        ],
    ),
    ChunkType.GLOSSARY: ChunkTypeInfo(
        type=ChunkType.GLOSSARY,
        name="Glossary",
        name_zh="術語表",
        description="Term definitions, domain vocabulary, acronyms",
        keywords=[
            "term", "definition", "meaning", "acronym",
            "術語", "定義", "縮寫", "詞彙",
            "refers to", "means", "is defined as",
        ],
        examples=[
            "SKU: Stock Keeping Unit - unique product identifier",
            "JWT: JSON Web Token for authentication",
            "PO refers to Purchase Order",
        ],
    ),
    ChunkType.REQUIREMENT: ChunkTypeInfo(
        type=ChunkType.REQUIREMENT,
        name="Requirement",
        name_zh="需求",
        description="General requirements, feature requests, specifications",
        keywords=[
            "requirement", "feature", "shall", "need",
            "需求", "功能", "特性", "規格",
            "priority", "stakeholder", "acceptance",
        ],
        examples=[
            "The system shall support 1000 concurrent users",
            "Feature: Multi-language support for 5 languages",
            "Requirement: 99.9% uptime SLA",
        ],
    ),
    ChunkType.UNKNOWN: ChunkTypeInfo(
        type=ChunkType.UNKNOWN,
        name="Unknown",
        name_zh="未知",
        description="Content that doesn't fit other categories",
        keywords=[],
        examples=[],
    ),
}


def get_classification_prompt() -> str:
    """Generate the classification prompt for LLM."""
    types_desc = []
    for chunk_type, info in TAXONOMY.items():
        if chunk_type == ChunkType.UNKNOWN:
            continue
        types_desc.append(f"- {info.type.value}: {info.name_zh} - {info.description}")

    types_str = "\n".join(types_desc)

    return f"""你是文件分類專家。請分析以下文件片段，判斷其類型。

可能的類型：
{types_str}

請回覆 JSON 格式：
{{
  "type": "類型值",
  "confidence": 0.0-1.0,
  "entities": ["識別出的實體名稱"],
  "dependencies": ["相依的其他文件/概念"]
}}

注意：
- type 必須是上述類型值之一
- confidence 表示分類信心度
- entities 列出文件中提到的重要實體（如用戶、訂單等）
- dependencies 列出此內容依賴的其他概念或文件"""
