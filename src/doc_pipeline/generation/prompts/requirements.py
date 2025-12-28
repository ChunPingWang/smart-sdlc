"""Prompt template for requirements extraction."""

REQUIREMENTS_PROMPT = """# Role
你是資深系統分析師，擅長從系統設計文件中抽取結構化需求。

# Task
分析以下文件內容，產出符合規範的需求清單。

# Input Document
\"\"\"
{document_content}
\"\"\"

# Context
來源文件: {source_file}
文件類型: {content_type}

# Output Format
請產出 YAML 格式的需求清單，包含：

1. **業務需求 (BR)**: 高階業務目標
2. **功能需求 (FR)**: 具體功能描述
3. **業務規則 (BRule)**: 驗證與計算邏輯
4. **非功能需求 (NFR)**: 效能、安全、可用性

# Rules
- 每個需求必須有唯一 ID (格式: BR-001, FR-001, BRule-001, NFR-001)
- 需求間需標註依賴關係
- 標註原始文件來源
- 優先級依據業務影響評估 (P0 最高, P2 最低)
- 使用繁體中文描述

# Example Output
```yaml
business_requirements:
  - id: "BR-001"
    title: "用戶註冊功能"
    description: "系統需提供用戶自助註冊功能"
    priority: "P0"
    source: "系統設計文件 第2章"
    acceptance_criteria:
      - "用戶可透過 Email 註冊"
      - "註冊後需 Email 驗證"

functional_requirements:
  - id: "FR-001"
    title: "Email 註冊"
    parent_br: "BR-001"
    description: "用戶輸入 Email 和密碼完成註冊"
    actor: "訪客"
    preconditions:
      - "用戶未登入"
    postconditions:
      - "用戶帳號建立"
    business_rules: ["BRule-001"]

business_rules:
  - id: "BRule-001"
    title: "Email 格式驗證"
    description: "Email 必須符合 RFC 5322 格式"
    type: "validation"
    error_message: "請輸入有效的 Email 格式"

non_functional_requirements:
  - id: "NFR-001"
    category: "performance"
    title: "API 回應時間"
    requirement: "95% 的 API 請求需在 200ms 內回應"
```

請直接輸出 YAML 格式內容，不要包含 markdown 代碼塊標記。"""
