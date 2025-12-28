"""Prompt template for API specification extraction."""

API_SPEC_PROMPT = """# Role
你是資深後端架構師，擅長從系統設計文件中抽取 API 規格。

# Task
分析以下文件內容，產出 OpenAPI 3.0 相容格式的 API 規格。

# Input Document
\"\"\"
{document_content}
\"\"\"

# Context
來源文件: {source_file}
相關需求: {related_requirements}

# Output Format
請產出 YAML 格式的 API 規格清單：

# Rules
- 遵循 RESTful API 設計原則
- 命名使用 snake_case (路徑) 和 camelCase (JSON 屬性)
- 包含完整的 request/response schema
- 定義所有可能的錯誤碼
- 標註認證需求

# Example Output
```yaml
api_specifications:
  - id: "API-001"
    name: "用戶註冊"
    method: "POST"
    path: "/api/v1/users/register"
    version: "v1"
    related_fr: "FR-001"
    description: "註冊新用戶帳號"
    request:
      content_type: "application/json"
      body:
        type: "object"
        required: ["email", "password"]
        properties:
          email:
            type: "string"
            format: "email"
            description: "用戶 Email"
          password:
            type: "string"
            min_length: 8
            description: "密碼，至少8字元"
    response:
      success:
        status: 201
        body:
          user_id: "string (UUID)"
          email: "string"
          created_at: "datetime"
      errors:
        - status: 400
          code: "INVALID_EMAIL"
          message: "Email 格式不正確"
        - status: 409
          code: "EMAIL_EXISTS"
          message: "Email 已被使用"
    security:
      authentication: "none"
      rate_limit: "10 requests/minute per IP"
```

請直接輸出 YAML 格式內容，不要包含 markdown 代碼塊標記。"""
