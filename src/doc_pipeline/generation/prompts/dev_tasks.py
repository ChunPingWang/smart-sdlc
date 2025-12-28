"""Prompt template for development task generation."""

DEV_TASKS_PROMPT = """# Role
你是 Scrum Master，擅長將技術規格轉換為可執行的開發任務。

# Task
分析以下技術規格，產出開發任務清單。

# Input Specifications
\"\"\"
{specifications}
\"\"\"

# Context
專案名稱: {project_name}
技術棧: {tech_stack}

# Output Format
請產出 YAML 格式的開發任務清單：

# Rules
- 任務粒度控制在 2-8 小時
- 標註任務依賴關係
- 包含測試任務
- 參照原始技術規格
- 提供 checklist

# Example Output
```yaml
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
    story_points: 5

tasks:
  - id: "TASK-001"
    story: "STORY-001"
    title: "實作 User Entity"
    type: "backend"
    description: "建立 User 領域模型"
    technical_details:
      file_path: "src/domain/user/User.java"
      references:
        - domain_model: "DM-001"
        - business_rules: ["BRule-001"]
    dependencies: []
    estimated_hours: 2
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

請直接輸出 YAML 格式內容，不要包含 markdown 代碼塊標記。"""
