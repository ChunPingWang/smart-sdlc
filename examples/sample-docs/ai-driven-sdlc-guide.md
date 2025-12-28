# 文件智能化處理與 AI 驅動開發完整指南

> 本文件提供從原始系統分析文件到 AI 可處理規格的完整方法論與工具鏈

---

## 目錄

1. [整體流程架構](#一整體流程架構)
2. [文件預處理工具鏈](#二文件預處理工具鏈)
3. [智能切分策略](#三智能切分策略)
4. [文件分類與標註](#四文件分類與標註)
5. [需求清單規格](#五需求清單規格)
6. [技術清單規格](#六技術清單規格)
7. [開發任務清單](#七開發任務清單)
8. [AI-Ready 規格格式](#八ai-ready-規格格式)
9. [完整 SDLC 流程](#九完整-sdlc-流程)
10. [工具總覽與建議](#十工具總覽與建議)
11. [範例模板](#十一範例模板)

---

## 一、整體流程架構

### Document-to-Code Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Document-to-Code Pipeline                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  Ingest  │───▶│  Parse   │───▶│ Chunking │───▶│  Enrich  │          │
│  │  收集文件  │    │  解析轉換  │    │  智能切分  │    │  語意增強  │          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│       │                                                │                │
│       ▼                                                ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  Store   │◀───│ Generate │◀───│  Review  │◀───│ Classify │          │
│  │ 知識庫儲存 │    │  規格產出  │    │  人工審查  │    │  文件分類  │          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 產出物架構

```
原始文件                     LLM 處理                    產出物
─────────                   ─────────                   ─────────

┌─────────┐                ┌─────────┐                ┌─────────────────┐
│  Word   │───┐            │         │           ┌───▶│ 需求清單 (BRD)   │
│  Excel  │───┼───────────▶│   LLM   │───────────┼───▶│ 功能清單 (FRD)   │
│Markdown │───┘            │ Pipeline│           ├───▶│ API 規格         │
└─────────┘                │         │           ├───▶│ DB Schema        │
                           └─────────┘           ├───▶│ 測試案例         │
                                                 └───▶│ 開發任務         │
                                                      └─────────────────┘
```

---

## 二、文件預處理工具鏈

### 2.1 文件解析工具對照表

| 文件類型 | 推薦工具 | 說明 |
|---------|---------|------|
| **Word (.docx)** | `python-docx`, `mammoth`, `pandoc` | mammoth 保留語意結構較佳 |
| **Excel (.xlsx)** | `openpyxl`, `pandas` | 處理 Schema 定義表格 |
| **Markdown** | `markdown-it`, `remark` | 保持原生格式最佳 |
| **PDF** | `PyMuPDF`, `pdfplumber` | 表格提取用 pdfplumber |
| **混合格式** | `unstructured.io` | 一站式解決方案 |

### 2.2 核心工具安裝

```bash
# 推薦的開源工具組合
pip install unstructured python-docx openpyxl pandas
pip install langchain-text-splitters tiktoken
pip install chromadb  # 向量儲存
```

### 2.3 Unstructured.io 使用範例

```python
from unstructured.partition.auto import partition

# 自動識別並解析各種格式
elements = partition(filename="system_design.docx")

# 元素類型包含：Title, NarrativeText, Table, ListItem 等
for element in elements:
    print(f"Type: {type(element).__name__}")
    print(f"Text: {element.text[:100]}...")
```

---

## 三、智能切分策略

### 3.1 切分原則

```
┌─────────────────────────────────────────────────────────┐
│                    文件切分策略                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 依文件結構 (Structural)                              │
│     ├── 章節標題為邊界                                   │
│     ├── API 定義為獨立單元                               │
│     └── Table Schema 為獨立單元                          │
│                                                         │
│  2. 依語意關聯 (Semantic)                                │
│     ├── Use Case 完整保留                               │
│     ├── 業務規則不拆分                                   │
│     └── 關聯實體群組處理                                  │
│                                                         │
│  3. 依 Token 限制 (Technical)                            │
│     ├── 單一 Chunk 控制在 2000-4000 tokens              │
│     ├── 保留上下文重疊 (10-20%)                          │
│     └── 附加 metadata 標註來源                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 切分尺寸建議

| 文件類型 | 建議 Token 數 | 原因 |
|---------|--------------|------|
| 業務規則 | 500-1000 | 保持規則完整性 |
| API 定義 | 1000-2000 | 單一 endpoint 完整 |
| DB Schema | 2000-3000 | 相關表格群組 |
| Use Case | 1500-2500 | 完整流程描述 |
| 架構說明 | 3000-4000 | 需要較多上下文 |

### 3.3 實作範例

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 依 Markdown 標題結構切分
headers_to_split_on = [
    ("#", "chapter"),
    ("##", "section"),
    ("###", "subsection"),
]

splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
chunks = splitter.split_text(markdown_content)

# 每個 chunk 自動帶有階層 metadata
for chunk in chunks:
    print(chunk.metadata)  # {'chapter': 'API設計', 'section': '用戶管理'}
```

---

## 四、文件分類與標註

### 4.1 系統文件分類體系

```
Documents/
├── requirements/           # 需求規格
│   ├── business-rules/     # 業務規則
│   ├── use-cases/          # 使用案例
│   └── constraints/        # 限制條件
│
├── technical/              # 技術規格
│   ├── api-specs/          # API 規格 (OpenAPI)
│   ├── data-models/        # 資料模型
│   ├── database-schemas/   # DB Schema
│   └── sequence-diagrams/  # 時序圖
│
├── architecture/           # 架構設計
│   ├── context/            # 系統脈絡
│   ├── containers/         # 容器圖
│   └── components/         # 元件圖
│
└── glossary/               # 術語表 (Domain Language)
```

### 4.2 自動分類 Prompt

```markdown
你是文件分類專家。請分析以下文件片段，判斷其類型：

可能的類型：
- BUSINESS_RULE: 業務規則描述
- USE_CASE: 使用案例/用戶故事
- API_SPEC: API 介面規格
- DATA_MODEL: 資料模型/ER 圖
- DB_SCHEMA: 資料庫表格定義
- SEQUENCE: 流程/時序說明
- ARCHITECTURE: 架構設計
- GLOSSARY: 術語定義

請回覆 JSON 格式：
{
  "type": "類型",
  "confidence": 0.0-1.0,
  "entities": ["識別出的實體名稱"],
  "dependencies": ["相依的其他文件/概念"]
}
```

---

## 五、需求清單規格

### 5.1 需求清單結構定義

```yaml
# requirements-list.yaml
metadata:
  project: "專案名稱"
  version: "1.0.0"
  created_at: "2024-12-28"
  author: "系統分析師"
  status: "draft | review | approved"

# 業務需求 (Business Requirements)
business_requirements:
  - id: "BR-001"
    title: "用戶註冊功能"
    description: "系統需提供用戶自助註冊功能"
    priority: "P0 | P1 | P2"
    source: "原始文件位置/頁碼"
    stakeholder: "產品經理"
    acceptance_criteria:
      - "用戶可透過 Email 註冊"
      - "註冊後需 Email 驗證"
    dependencies: []
    related_frs: ["FR-001", "FR-002"]

# 功能需求 (Functional Requirements)  
functional_requirements:
  - id: "FR-001"
    title: "Email 註冊"
    parent_br: "BR-001"
    description: "用戶輸入 Email 和密碼完成註冊"
    actor: "訪客"
    preconditions:
      - "用戶未登入"
      - "Email 未被使用"
    postconditions:
      - "用戶帳號建立"
      - "驗證信發送"
    business_rules: ["BRule-001", "BRule-002"]
    ui_mockup: "link-to-figma"
    api_endpoints: ["POST /api/v1/users/register"]
    
# 業務規則 (Business Rules)
business_rules:
  - id: "BRule-001"
    title: "Email 格式驗證"
    description: "Email 必須符合 RFC 5322 格式"
    type: "validation"
    logic: "regex: ^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
    error_message: "請輸入有效的 Email 格式"

# 非功能需求 (Non-Functional Requirements)
non_functional_requirements:
  - id: "NFR-001"
    category: "performance"
    title: "API 回應時間"
    requirement: "95% 的 API 請求需在 200ms 內回應"
    measurement: "P95 latency < 200ms"
```

### 5.2 需求抽取 Prompt

```markdown
# Role
你是資深系統分析師，擅長從系統設計文件中抽取結構化需求。

# Task
分析以下文件內容，產出符合規範的需求清單。

# Input Document
"""
{document_chunk}
"""

# Output Format
請產出 YAML 格式的需求清單，包含：

1. **業務需求 (BR)**: 高階業務目標
2. **功能需求 (FR)**: 具體功能描述
3. **業務規則 (BRule)**: 驗證與計算邏輯
4. **非功能需求 (NFR)**: 效能、安全、可用性

# Rules
- 每個需求必須有唯一 ID
- 需求間需標註依賴關係
- 標註原始文件來源
- 優先級依據業務影響評估
- 使用繁體中文

# Example Output
business_requirements:
  - id: "BR-001"
    title: "..."
    priority: "P0"
    ...
```

---

## 六、技術清單規格

### 6.1 技術清單結構定義

```yaml
# technical-spec-list.yaml
metadata:
  project: "專案名稱"
  version: "1.0.0"
  architecture_style: "microservices | monolith | modular-monolith"
  
# API 規格清單
api_specifications:
  - id: "API-001"
    name: "用戶註冊"
    method: "POST"
    path: "/api/v1/users/register"
    version: "v1"
    related_fr: "FR-001"
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
    
# 資料庫 Schema 清單
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
        type: "ENUM('pending', 'active', 'suspended')"
        default: "pending"
        description: "帳號狀態"
      - name: "created_at"
        type: "TIMESTAMP"
        default: "CURRENT_TIMESTAMP"
      - name: "updated_at"
        type: "TIMESTAMP"
        on_update: "CURRENT_TIMESTAMP"
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

# 領域模型清單
domain_models:
  - id: "DM-001"
    name: "User"
    type: "aggregate_root"
    bounded_context: "Identity"
    properties:
      - name: "id"
        type: "UserId"
        description: "用戶識別碼"
      - name: "email"
        type: "Email"
        description: "Email 值物件"
      - name: "status"
        type: "UserStatus"
        description: "狀態列舉"
    behaviors:
      - name: "register"
        description: "註冊新用戶"
        params: ["email", "password"]
        events: ["UserRegistered"]
      - name: "activate"
        description: "啟用帳號"
        events: ["UserActivated"]
    invariants:
      - "Email 必須唯一"
      - "密碼必須符合強度規則"

# 事件清單 (Event-Driven Architecture)
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
      - service: "Analytics Service"
        action: "記錄註冊事件"

# 整合介面清單
integrations:
  - id: "INT-001"
    name: "Email Service"
    type: "external"
    protocol: "REST"
    provider: "SendGrid"
    endpoints:
      - action: "send_email"
        method: "POST"
        url: "https://api.sendgrid.com/v3/mail/send"
    authentication: "API Key"
    retry_policy:
      max_attempts: 3
      backoff: "exponential"
    circuit_breaker:
      failure_threshold: 5
      timeout: 30s
```

### 6.2 技術規格抽取 Prompt

```markdown
# Role
你是資深架構師，擅長從系統設計文件中抽取技術規格。

# Context
專案採用以下技術棧：
- 後端: Java 21 + Spring Boot 3.x
- 資料庫: PostgreSQL 15
- 架構風格: Hexagonal Architecture
- API 風格: RESTful

# Task
分析以下文件內容，產出結構化技術清單。

# Input Document
"""
{document_chunk}
"""

# Output Sections

## 1. API 規格
產出 OpenAPI 3.0 相容格式，包含：
- HTTP Method + Path
- Request/Response Schema
- Error Codes
- 認證需求

## 2. 資料庫 Schema
產出包含：
- 表格名稱與欄位定義
- 資料型別與約束
- 索引設計
- 關聯關係

## 3. 領域模型
依 DDD 原則產出：
- Aggregate Root
- Entity
- Value Object
- Domain Event

## 4. 業務規則實作
產出可執行的規則描述：
- 驗證規則 (Validation)
- 計算規則 (Calculation)
- 決策規則 (Decision)

# Rules
- 遵循專案命名慣例 (snake_case for DB, camelCase for API)
- 標註原始需求來源
- 識別跨服務依賴
- 使用繁體中文描述，英文命名
```

---

## 七、開發任務清單

### 7.1 任務清單結構

```yaml
# dev-tasks.yaml
metadata:
  sprint: "Sprint 1"
  start_date: "2024-01-08"
  end_date: "2024-01-19"

epics:
  - id: "EPIC-001"
    title: "用戶管理模組"
    description: "實作用戶註冊、登入、權限管理"
    related_brs: ["BR-001", "BR-002"]
    
stories:
  - id: "STORY-001"
    title: "用戶 Email 註冊"
    epic: "EPIC-001"
    related_fr: "FR-001"
    description: |
      身為訪客
      我想要透過 Email 註冊帳號
      以便使用系統功能
    acceptance_criteria:
      - "輸入有效 Email 和密碼可完成註冊"
      - "重複 Email 顯示錯誤訊息"
      - "註冊後收到驗證信"
    story_points: 5
    
tasks:
  - id: "TASK-001"
    story: "STORY-001"
    title: "實作 User Entity"
    type: "backend"
    description: "建立 User 領域模型"
    technical_details:
      file_path: "src/main/java/com/example/domain/user/User.java"
      references:
        - domain_model: "DM-001"
        - business_rules: ["BRule-001", "BRule-002"]
    estimated_hours: 2
    assignee: null
    checklist:
      - "建立 User Entity class"
      - "實作 Email Value Object"
      - "加入驗證邏輯"
      - "撰寫單元測試"
      
  - id: "TASK-002"
    story: "STORY-001"
    title: "實作 UserRepository"
    type: "backend"
    description: "建立用戶資料存取層"
    technical_details:
      file_path: "src/main/java/com/example/infrastructure/persistence/"
      references:
        - table: "TBL-001"
    dependencies: ["TASK-001"]
    estimated_hours: 3
    
  - id: "TASK-003"
    story: "STORY-001"
    title: "實作註冊 API"
    type: "backend"
    description: "建立 POST /api/v1/users/register endpoint"
    technical_details:
      references:
        - api: "API-001"
    dependencies: ["TASK-001", "TASK-002"]
    estimated_hours: 4
    
  - id: "TASK-004"
    story: "STORY-001"
    title: "API 整合測試"
    type: "testing"
    description: "撰寫註冊 API 整合測試"
    test_scenarios:
      - "成功註冊"
      - "Email 格式錯誤"
      - "Email 已存在"
    dependencies: ["TASK-003"]
    estimated_hours: 2
```

### 7.2 任務產生 Prompt

```markdown
# Role
你是 Scrum Master，擅長將技術規格轉換為可執行的開發任務。

# Input
以下是技術規格：
"""
{technical_spec}
"""

# Task
請產出開發任務清單，包含：

1. **Epic**: 大型功能模組
2. **Story**: 用戶故事 (As a... I want... So that...)
3. **Task**: 具體開發任務

# Rules
- 任務粒度控制在 2-8 小時
- 標註任務依賴關係
- 包含測試任務
- 參照原始技術規格
- 提供 checklist
```

---

## 八、AI-Ready 規格格式

### 8.1 單一功能完整規格

此格式專門設計給 AI 輔助開發工具 (Claude Code / GitHub Copilot) 使用：

```yaml
# ai-ready-spec/FR-001-user-registration.yaml
spec_version: "1.0"
spec_type: "feature"

# === 功能概述 ===
feature:
  id: "FR-001"
  name: "用戶 Email 註冊"
  description: "允許訪客透過 Email 註冊成為系統用戶"

# === 業務規則 ===
business_rules:
  - id: "BR-001"
    rule: "Email 必須符合 RFC 5322 格式"
    validation: "regex: ^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
    
  - id: "BR-002"  
    rule: "密碼至少 8 字元，包含大小寫和數字"
    validation: "regex: ^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}$"
    
  - id: "BR-003"
    rule: "同一 Email 不可重複註冊"
    check: "SELECT COUNT(*) FROM users WHERE email = ?"

# === API 規格 ===
api:
  method: "POST"
  path: "/api/v1/users/register"
  request:
    body:
      email: { type: "string", format: "email", required: true }
      password: { type: "string", minLength: 8, required: true }
      name: { type: "string", maxLength: 100, required: false }
  response:
    201:
      body:
        id: "uuid"
        email: "string"
        created_at: "datetime"
    400:
      errors:
        - code: "INVALID_EMAIL"
        - code: "WEAK_PASSWORD"
    409:
      errors:
        - code: "EMAIL_EXISTS"

# === 資料庫 ===
database:
  table: "users"
  columns:
    - { name: "id", type: "UUID", pk: true }
    - { name: "email", type: "VARCHAR(255)", unique: true, not_null: true }
    - { name: "password_hash", type: "VARCHAR(255)", not_null: true }
    - { name: "name", type: "VARCHAR(100)" }
    - { name: "status", type: "VARCHAR(20)", default: "'pending'" }
    - { name: "created_at", type: "TIMESTAMP", default: "NOW()" }

# === 領域模型 ===
domain:
  aggregate: "User"
  entities:
    - name: "User"
      properties:
        - { name: "id", type: "UserId" }
        - { name: "email", type: "Email" }
        - { name: "passwordHash", type: "PasswordHash" }
        - { name: "status", type: "UserStatus" }
  value_objects:
    - name: "Email"
      validation: "BR-001"
    - name: "Password"
      validation: "BR-002"
  events:
    - name: "UserRegistered"
      payload: ["userId", "email", "registeredAt"]

# === 測試案例 ===
test_cases:
  - scenario: "成功註冊"
    given: "用戶輸入有效 Email 和密碼"
    when: "呼叫註冊 API"
    then: "回傳 201 和用戶資訊"
    
  - scenario: "Email 已存在"
    given: "Email 已被註冊"
    when: "使用相同 Email 註冊"
    then: "回傳 409 EMAIL_EXISTS"
    
  - scenario: "密碼太弱"
    given: "密碼只有數字"
    when: "呼叫註冊 API"
    then: "回傳 400 WEAK_PASSWORD"

# === 實作指引 ===
implementation_guide:
  architecture: "hexagonal"
  layers:
    - adapter_in: "REST Controller"
    - application: "RegisterUserUseCase"
    - domain: "User Aggregate"
    - adapter_out: "JPA Repository"
  
  file_structure:
    - "adapter/in/web/UserController.java"
    - "application/usecase/RegisterUserUseCase.java"
    - "application/port/in/RegisterUserCommand.java"
    - "application/port/out/UserRepository.java"
    - "domain/user/User.java"
    - "domain/user/Email.java"
    - "adapter/out/persistence/UserJpaRepository.java"
```

### 8.2 給 Claude Code 的 Prompt Template

```markdown
# Context
你正在開發一個 Spring Boot 專案，採用 Hexagonal Architecture。

# Specification
以下是功能規格：

{ai_ready_spec}

# Task
請依據規格實作以下部分：
1. Domain Layer - User Aggregate 和 Value Objects
2. Application Layer - RegisterUserUseCase
3. Adapter Layer - REST Controller

# Constraints
- 使用 Java 21 Record 定義 Command/Query
- 遵循 SOLID 原則
- 包含完整 JavaDoc
- 產生對應的單元測試

# Output
請依序產出各檔案內容。
```

---

## 九、完整 SDLC 流程

### AI-Assisted SDLC Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI-Assisted SDLC Pipeline                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1: Document Ingestion (文件收集)                                      │
│  ────────────────────────────────────────                                   │
│  • 收集所有 Word/Excel/Markdown 文件                                         │
│  • 統一轉換為 Markdown + YAML metadata                                       │
│  • 建立文件版本控管 (Git)                                                    │
│                                                                             │
│  Phase 2: Parsing & Chunking (解析切分)                                      │
│  ────────────────────────────────────────                                   │
│  • Unstructured.io 解析各格式                                                │
│  • 語意感知切分 (保持業務完整性)                                              │
│  • 自動分類與標籤                                                            │
│                                                                             │
│  Phase 3: Knowledge Base (知識庫建立)                                        │
│  ────────────────────────────────────────                                   │
│  • Embedding 向量化 (text-embedding-3-small)                                │
│  • 儲存至 ChromaDB / Qdrant                                                 │
│  • 建立關聯索引                                                              │
│                                                                             │
│  Phase 4: Specification Generation (規格產出)                                │
│  ────────────────────────────────────────                                   │
│  • LLM 抽取 → 需求規格 (SRS)                                                 │
│  • LLM 抽取 → API 規格 (OpenAPI)                                            │
│  • LLM 抽取 → 資料規格 (Schema)                                              │
│  • LLM 抽取 → 測試案例 (Gherkin)                                             │
│                                                                             │
│  Phase 5: Human Review (人工審查)                                            │
│  ────────────────────────────────────────                                   │
│  • 架構師審查技術規格                                                         │
│  • BA 審查需求規格                                                           │
│  • 標註修正與回饋                                                            │
│                                                                             │
│  Phase 6: AI Development (AI 輔助開發)                                       │
│  ────────────────────────────────────────                                   │
│  • 規格餵入 Claude Code / GitHub Copilot                                    │
│  • 依 chunk 逐步產生程式碼                                                   │
│  • 自動產生單元測試                                                          │
│                                                                             │
│  Phase 7: Continuous Refinement (持續優化)                                   │
│  ────────────────────────────────────────                                   │
│  • 程式碼變更反向更新文件                                                     │
│  • 知識庫持續學習                                                            │
│  • 文件-程式碼一致性檢查                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LLM 文件梳理 Pipeline

```
┌────────────────────────────────────────────────────────────────────┐
│                     LLM 文件梳理 Pipeline                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   Raw Chunks ──┬──▶ [分類] ──▶ [關聯分析] ──▶ [知識圖譜]            │
│                │                                                   │
│                ├──▶ [抽取 API] ──▶ OpenAPI YAML                    │
│                │                                                   │
│                ├──▶ [抽取 Schema] ──▶ DDL / Prisma Schema          │
│                │                                                   │
│                ├──▶ [抽取規則] ──▶ Gherkin / Decision Table        │
│                │                                                   │
│                └──▶ [產生測試] ──▶ Test Cases                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 十、工具總覽與建議

### 10.1 推薦工具對照表

| 階段 | 工具 | 用途 |
|------|------|------|
| **文件解析** | Unstructured.io | 多格式統一處理 |
| **文件轉換** | Pandoc | 格式互轉 |
| **智能切分** | LangChain Text Splitters | 語意感知切分 |
| **向量儲存** | ChromaDB / Qdrant | 本地向量資料庫 |
| **知識圖譜** | Neo4j | 關聯查詢 |
| **規格產出** | Claude API / OpenAI | LLM 抽取轉換 |
| **API 規格** | Swagger Editor | OpenAPI 編輯驗證 |
| **Schema 管理** | Prisma / Drizzle | 資料模型定義 |
| **測試規格** | Cucumber / Gherkin | BDD 測試案例 |
| **流程編排** | LangGraph / Prefect | Pipeline 管理 |

### 10.2 工具整合輸出格式

| 用途 | 工具 | 輸出格式 |
|------|------|----------|
| 需求管理 | Jira / Azure DevOps | 可匯入 CSV/JSON |
| API 文件 | Swagger UI / Redoc | OpenAPI YAML |
| DB 文件 | DBDocs / SchemaSpy | DDL / Prisma |
| 測試管理 | TestRail / Zephyr | Gherkin / CSV |
| AI 開發 | Claude Code / Copilot | AI-Ready YAML |

### 10.3 快速開始方案

```bash
# 1. 建立專案結構
mkdir doc-intelligence && cd doc-intelligence

# 2. 安裝核心套件
pip install unstructured langchain chromadb openai

# 3. 文件處理腳本
python ingest.py --source ./raw-docs --output ./processed

# 4. 啟動知識庫
python build_kb.py --chunks ./processed --db ./vectordb

# 5. 規格產生
python generate_specs.py --query "產生用戶管理 API 規格"
```

---

## 十一、範例模板

### 11.1 處理流程程式碼

```python
# spec_generator.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import yaml
import json

class SpecType(Enum):
    BUSINESS_REQ = "business_requirement"
    FUNCTIONAL_REQ = "functional_requirement"
    API_SPEC = "api_specification"
    DB_SCHEMA = "database_schema"
    DOMAIN_MODEL = "domain_model"
    DEV_TASK = "development_task"

@dataclass
class DocumentChunk:
    content: str
    source_file: str
    page_or_section: str
    chunk_type: Optional[SpecType] = None

class SpecificationGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.prompts = self._load_prompts()
    
    def process_document(self, chunks: List[DocumentChunk]) -> dict:
        """處理文件 chunks 並產出所有規格"""
        results = {
            "requirements": [],
            "api_specs": [],
            "db_schemas": [],
            "domain_models": [],
            "dev_tasks": []
        }
        
        for chunk in chunks:
            # 1. 分類 chunk
            chunk_type = self._classify_chunk(chunk)
            
            # 2. 依類型抽取規格
            if chunk_type == SpecType.BUSINESS_REQ:
                reqs = self._extract_requirements(chunk)
                results["requirements"].extend(reqs)
                
            elif chunk_type == SpecType.API_SPEC:
                apis = self._extract_api_specs(chunk)
                results["api_specs"].extend(apis)
                
            elif chunk_type == SpecType.DB_SCHEMA:
                schemas = self._extract_db_schemas(chunk)
                results["db_schemas"].extend(schemas)
        
        # 3. 建立關聯
        self._link_specifications(results)
        
        # 4. 產生開發任務
        results["dev_tasks"] = self._generate_dev_tasks(results)
        
        return results
    
    def _classify_chunk(self, chunk: DocumentChunk) -> SpecType:
        """使用 LLM 分類 chunk 類型"""
        prompt = f"""
        分析以下文件片段，判斷其主要類型：
        
        {chunk.content}
        
        可能類型：
        - business_requirement: 業務需求描述
        - functional_requirement: 功能需求
        - api_specification: API 介面規格
        - database_schema: 資料庫表格定義
        - domain_model: 領域模型描述
        
        回覆 JSON: {{"type": "類型", "confidence": 0.0-1.0}}
        """
        response = self.llm.complete(prompt)
        result = json.loads(response)
        return SpecType(result["type"])
    
    def _extract_requirements(self, chunk: DocumentChunk) -> List[dict]:
        """抽取需求規格"""
        prompt = self.prompts["requirements"].format(
            document_chunk=chunk.content,
            source=f"{chunk.source_file}:{chunk.page_or_section}"
        )
        response = self.llm.complete(prompt)
        return yaml.safe_load(response)
    
    def _extract_api_specs(self, chunk: DocumentChunk) -> List[dict]:
        """抽取 API 規格"""
        prompt = self.prompts["api_spec"].format(
            document_chunk=chunk.content
        )
        response = self.llm.complete(prompt)
        return yaml.safe_load(response)
    
    def _generate_dev_tasks(self, specs: dict) -> List[dict]:
        """從規格產生開發任務"""
        tasks = []
        
        # 為每個 API 產生任務
        for api in specs["api_specs"]:
            tasks.extend(self._api_to_tasks(api))
        
        # 為每個 DB Schema 產生任務
        for schema in specs["db_schemas"]:
            tasks.extend(self._schema_to_tasks(schema))
        
        return tasks
    
    def export_all(self, results: dict, output_dir: str):
        """匯出所有規格文件"""
        # 需求清單
        with open(f"{output_dir}/requirements-list.yaml", "w") as f:
            yaml.dump(results["requirements"], f, allow_unicode=True)
        
        # API 規格 (OpenAPI 格式)
        openapi_spec = self._to_openapi(results["api_specs"])
        with open(f"{output_dir}/api-spec.yaml", "w") as f:
            yaml.dump(openapi_spec, f, allow_unicode=True)
        
        # DB Schema (DDL)
        ddl = self._to_ddl(results["db_schemas"])
        with open(f"{output_dir}/schema.sql", "w") as f:
            f.write(ddl)
        
        # 開發任務 (可匯入 Jira)
        with open(f"{output_dir}/dev-tasks.yaml", "w") as f:
            yaml.dump(results["dev_tasks"], f, allow_unicode=True)
```

---

## 附錄 A：Checklist

### 文件預處理 Checklist

- [ ] 收集所有原始文件 (Word/Excel/Markdown/PDF)
- [ ] 建立文件清單與版本記錄
- [ ] 選擇適當的解析工具
- [ ] 定義切分策略與粒度
- [ ] 建立分類標籤體系
- [ ] 設計 metadata schema

### 規格產出 Checklist

- [ ] 定義需求 ID 命名規則
- [ ] 建立需求模板
- [ ] 定義 API 規格格式 (OpenAPI)
- [ ] 定義 DB Schema 格式
- [ ] 建立關聯追溯矩陣
- [ ] 設計審查流程

### AI 開發 Checklist

- [ ] 準備 AI-Ready 規格格式
- [ ] 定義 Prompt Template
- [ ] 建立程式碼審查標準
- [ ] 設計測試策略
- [ ] 建立 CI/CD 流程

---

## 附錄 B：參考資源

### 開源工具連結

| 工具 | 連結 |
|------|------|
| Unstructured.io | https://github.com/Unstructured-IO/unstructured |
| LangChain | https://github.com/langchain-ai/langchain |
| ChromaDB | https://github.com/chroma-core/chroma |
| Pandoc | https://pandoc.org/ |

### 相關文章

- LangChain Text Splitters 文件
- OpenAPI Specification 3.0
- Domain-Driven Design Reference
- Hexagonal Architecture 指南

---

*文件版本: 1.0.0*  
*最後更新: 2024-12-28*
