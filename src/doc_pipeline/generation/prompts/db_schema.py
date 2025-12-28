"""Prompt template for database schema extraction."""

DB_SCHEMA_PROMPT = """# Role
你是資深資料庫架構師，擅長從系統設計文件中抽取資料庫結構定義。

# Task
分析以下文件內容，產出資料庫 Schema 規格。

# Input Document
\"\"\"
{document_content}
\"\"\"

# Context
來源文件: {source_file}
資料庫類型: PostgreSQL 15
相關 API: {related_apis}

# Output Format
請產出 YAML 格式的資料庫規格：

# Rules
- 表格名稱使用 snake_case (複數形式)
- 欄位名稱使用 snake_case
- 包含適當的索引定義
- 定義外鍵關聯
- 使用 UUID 作為主鍵類型

# Example Output
```yaml
database_schemas:
  - id: "TBL-001"
    name: "users"
    description: "用戶主表"
    related_api: ["API-001", "API-002"]
    columns:
      - name: "id"
        type: "UUID"
        primary_key: true
        description: "主鍵"
      - name: "email"
        type: "VARCHAR(255)"
        nullable: false
        unique: true
        description: "用戶 Email"
      - name: "password_hash"
        type: "VARCHAR(255)"
        nullable: false
        description: "密碼雜湊值"
      - name: "status"
        type: "VARCHAR(20)"
        default: "'pending'"
        description: "帳號狀態: pending, active, suspended"
      - name: "created_at"
        type: "TIMESTAMP"
        default: "NOW()"
      - name: "updated_at"
        type: "TIMESTAMP"
        on_update: "NOW()"
    indexes:
      - name: "idx_users_email"
        columns: ["email"]
        unique: true
      - name: "idx_users_status"
        columns: ["status"]
    constraints:
      - type: "check"
        name: "chk_email_format"
        expression: "email ~* '^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$'"

domain_models:
  - id: "DM-001"
    name: "User"
    type: "aggregate_root"
    bounded_context: "Identity"
    properties:
      - name: "id"
        type: "UserId"
      - name: "email"
        type: "Email"
      - name: "status"
        type: "UserStatus"
    behaviors:
      - name: "register"
        description: "註冊新用戶"
        events: ["UserRegistered"]
    invariants:
      - "Email 必須唯一"

domain_events:
  - id: "EVT-001"
    name: "UserRegistered"
    producer: "User Aggregate"
    description: "用戶完成註冊時發布"
    payload:
      user_id: "UUID"
      email: "string"
      registered_at: "datetime"
    consumers:
      - service: "Notification Service"
        action: "發送驗證信"
```

請直接輸出 YAML 格式內容，不要包含 markdown 代碼塊標記。"""
