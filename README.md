# Doc-Pipeline

**Document-to-Code Pipeline** - AI 驅動的文件處理與規格產出系統

將原始系統設計文件（Word、Excel、Markdown、PDF）轉換為 AI 可處理的結構化規格。

## 專案狀態

| 項目 | 狀態 |
|------|------|
| 核心功能 | ✅ 完成 |
| 多格式解析 | ✅ 支援 .docx, .xlsx, .md, .pdf, .txt |
| 智能切分 | ✅ 結構/語意/混合策略 |
| 文件分類 | ✅ LLM + 規則雙模式 |
| 知識庫 | ✅ 向量儲存 + 語意搜尋 |
| 規格產出 | ✅ 需求/API/DB/任務 |
| LLM 支援 | ✅ OpenAI / Anthropic / Ollama |
| Embedding 支援 | ✅ OpenAI / Ollama (本地) |
| 測試覆蓋 | ✅ 14 個測試通過 |

## 功能特色

- **多格式解析**: 支援 Word、Excel、Markdown、PDF、純文字
- **智能切分**: 基於結構（標題層級）和語意（段落邊界）的切分策略
- **LLM 分類**: 使用 LLM 或規則自動分類文件內容類型
- **向量語意搜尋**: 使用 Embedding 模型進行語意相似度搜尋
- **知識庫**: 本地檔案式儲存，支援向量搜尋與關鍵字搜尋
- **規格產出**: 自動產出需求清單、API 規格、DB Schema、開發任務
- **多種匯出**: YAML、OpenAPI 3.0、SQL DDL 格式輸出
- **完全本地運行**: 使用 Ollama 可完全離線運行，無需 API Key

## 安裝

### 使用 uv（推薦）

```bash
# Clone 專案
git clone https://github.com/ChunPingWang/smart-sdlc.git
cd smart-sdlc

# 使用 uv 安裝（自動建立虛擬環境）
uv sync

# 執行 CLI
uv run doc-pipeline --help
```

### 使用 pip

```bash
# Clone 專案
git clone https://github.com/ChunPingWang/smart-sdlc.git
cd smart-sdlc

# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安裝套件
pip install -e ".[dev]"

# 執行 CLI
doc-pipeline --help
```

---

## Ollama 設定（推薦 - 完全本地運行）

使用 Ollama 可以完全在本地運行 LLM 和 Embedding，無需 API Key。

### 1. 安裝 Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 從 https://ollama.com/download 下載安裝程式
```

### 2. 啟動 Ollama 服務

```bash
ollama serve
```

### 3. 下載模型

```bash
# LLM 模型 (用於分類和規格產出)
ollama pull llama3.2        # 2.0 GB - 推薦，平衡效能與品質

# Embedding 模型 (用於向量語意搜尋)
ollama pull nomic-embed-text  # 274 MB - 768 維向量
```

**可選的 LLM 模型：**
| 模型 | 大小 | 說明 |
|------|------|------|
| `llama3.2` | 2.0 GB | 推薦，平衡效能與品質 |
| `llama3.2:1b` | 1.3 GB | 輕量版，速度更快 |
| `mistral` | 4.1 GB | 效能優秀 |
| `qwen2.5` | 4.7 GB | 中文支援佳 |
| `codellama` | 3.8 GB | 程式碼專用 |

### 4. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`：
```env
# LLM 設定
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Embedding 設定
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### 5. 驗證設定

```bash
# 檢查設定
uv run doc-pipeline info

# 預期輸出：
# LLM Provider: ollama
# LLM Model: llama3.2 @ http://localhost:11434
```

---

## 其他 LLM 設定

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

### Anthropic Claude

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Embedding 仍需使用 OpenAI 或 Ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

---

## 使用方式

### 快速開始

```bash
# 1. 初始化專案結構
uv run doc-pipeline init

# 2. 處理文件（使用規則分類 + 向量儲存）
uv run doc-pipeline process ./your-docs --no-llm --no-generate

# 3. 語意搜尋
uv run doc-pipeline search "用戶註冊 API"

# 4. 完整 pipeline（需要 LLM）
uv run doc-pipeline process ./your-docs --name "專案名稱"
```

### CLI 命令

```bash
# 完整處理 pipeline
uv run doc-pipeline process <文件目錄> [選項]

選項:
  --output, -o    輸出目錄 (預設: ./output)
  --name, -n      專案名稱
  --no-llm        跳過 LLM 分類，使用規則分類
  --no-kb         跳過知識庫儲存
  --no-generate   跳過規格產出（僅解析、切分、分類）

# 範例
uv run doc-pipeline process ./docs --name "電商系統" --output ./specs
uv run doc-pipeline process ./docs --no-llm --no-generate  # 僅處理不產出
```

```bash
# 產出特定規格
uv run doc-pipeline generate <類型> [選項]

類型: requirements, api, db, tasks, all

# 範例
uv run doc-pipeline generate requirements
uv run doc-pipeline generate api --from ./docs
uv run doc-pipeline generate all
```

```bash
# 搜尋知識庫（支援語意搜尋）
uv run doc-pipeline search <關鍵字> [選項]

選項:
  --limit, -l     結果數量限制 (預設: 5)
  --type, -t      篩選類型 (api_specification, business_rule, use_case 等)

# 範例 - 語意搜尋會找到相關但不完全匹配的結果
uv run doc-pipeline search "用戶登入驗證"
uv run doc-pipeline search "API 設計" --type api_specification --limit 10
```

```bash
# 其他命令
uv run doc-pipeline info      # 顯示設定資訊
uv run doc-pipeline clear-kb  # 清空知識庫
uv run doc-pipeline --version # 顯示版本
```

---

## 向量語意搜尋

本專案支援向量語意搜尋，使用 Embedding 模型將文件內容轉換為向量，進行相似度比對。

### 工作原理

```
查詢文字 ──▶ Embedding 模型 ──▶ 查詢向量 (768維)
                                    │
                                    ▼ cosine similarity
知識庫文件 ──▶ Embedding 模型 ──▶ 文件向量 ──▶ 排序結果
```

### 優點

| 傳統關鍵字搜尋 | 向量語意搜尋 |
|--------------|------------|
| 只能匹配完全相同的詞 | 理解語意相似性 |
| "登入" 找不到 "認證" | "登入" 可找到 "認證"、"驗證" |
| 對錯字敏感 | 對錯字容錯 |

### 使用範例

```bash
# 語意搜尋 - 會找到相關概念
uv run doc-pipeline search "使用者身份驗證"
# 可能找到: "用戶登入"、"OAuth 認證"、"JWT Token" 等相關內容

# 傳統搜尋只會精確匹配
uv run doc-pipeline search "使用者身份驗證" --no-semantic
```

---

## Pipeline 流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Ingest  │───▶│  Parse   │───▶│ Chunking │───▶│ Classify │
│  收集文件  │    │  解析轉換  │    │  智能切分  │    │  文件分類  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Export  │◀───│ Generate │◀───│  Store   │◀───│ Embedding│
│  格式輸出  │    │  規格產出  │    │ 向量儲存  │    │  向量化   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 各階段說明

| 階段 | 功能 | 輸出 |
|------|------|------|
| Ingest | 掃描目錄收集支援格式文件 | 文件清單 |
| Parse | 解析文件內容，提取結構化元素 | ParsedDocument |
| Chunking | 按標題/段落智能切分 | DocumentChunk[] |
| Classify | LLM/規則分類文件類型 | 標註類型的 Chunk |
| Embedding | 計算向量嵌入 | 768 維向量 |
| Store | 儲存至知識庫供後續查詢 | JSON + 向量索引 |
| Generate | LLM 產出結構化規格 | YAML 規格檔 |
| Export | 轉換為各種格式輸出 | OpenAPI/SQL/YAML |

---

## 輸出檔案

執行完整 pipeline 後產出：

```
output/
├── requirements-list.yaml  # 需求清單 (BR, FR, BRule, NFR)
├── api-spec.yaml           # API 規格
├── database-spec.yaml      # 資料庫規格
├── dev-tasks.yaml          # 開發任務清單 (Epic/Story/Task)
├── all-specs.yaml          # 合併所有規格
├── openapi.yaml            # OpenAPI 3.0 文件 (若有 API)
├── schema.sql              # DDL 資料庫腳本 (若有 DB)
└── ai-ready-specs/         # AI 工具可直接使用的規格
```

## 文件分類類型

| 類型 | 說明 | 範例 |
|------|------|------|
| `requirement` | 功能需求 | FR-001 用戶註冊功能 |
| `business_rule` | 商業規則 | 密碼長度至少 8 字元 |
| `use_case` | 使用案例 | 身為用戶，我想要... |
| `api_specification` | API 規格 | POST /api/v1/users |
| `db_schema` | 資料庫結構 | CREATE TABLE users |
| `domain_model` | 領域模型 | User Entity 定義 |
| `ui_spec` | UI 規格 | 登入頁面設計 |
| `sequence_diagram` | 時序圖 | 註冊流程圖 |
| `architecture` | 架構設計 | 系統架構圖 |

---

## 專案結構

```
smart-sdlc/
├── pyproject.toml              # 專案配置
├── README.md                   # 說明文件
├── .env.example                # 環境變數範例
├── src/doc_pipeline/           # 主套件
│   ├── __init__.py
│   ├── cli.py                  # CLI 入口
│   ├── config.py               # 配置管理
│   ├── document/               # 文件處理
│   │   ├── models.py           # 資料模型
│   │   └── parser.py           # 多格式解析器
│   ├── chunking/               # 智能切分
│   │   ├── strategies.py       # 切分策略
│   │   └── chunker.py          # 切分器
│   ├── classification/         # 文件分類
│   │   ├── taxonomy.py         # 分類體系
│   │   └── classifier.py       # LLM/規則分類器
│   ├── knowledge_base/         # 知識庫
│   │   ├── embeddings.py       # 向量嵌入服務
│   │   └── vectorstore.py      # 向量儲存與搜尋
│   ├── generation/             # 規格產出
│   │   ├── generator.py        # 規格產生器
│   │   ├── prompts/            # Prompt 模板
│   │   └── exporters/          # 格式匯出器
│   └── pipeline/               # 流程編排
│       └── orchestrator.py     # Pipeline 編排器
├── tests/                      # 測試
│   ├── test_parser.py
│   └── test_chunker.py
└── examples/                   # 範例
    └── sample-docs/
```

---

## 開發

```bash
# 執行測試
uv run pytest

# 執行測試（詳細輸出）
uv run pytest -v

# 型別檢查
uv run mypy src

# 程式碼檢查
uv run ruff check src
```

## 系統需求

- Python 3.11+
- 選擇一種 LLM:
  - OpenAI API Key，或
  - Anthropic API Key，或
  - Ollama（本地安裝，推薦）

## 疑難排解

### Ollama 連線失敗

```bash
# 確認 Ollama 服務運行中
ollama serve

# 確認模型已下載
ollama list

# 測試 API
curl http://localhost:11434/api/tags
```

### Embedding 失敗

```bash
# 確認 embedding 模型已下載
ollama pull nomic-embed-text

# 測試 embedding API
curl http://localhost:11434/api/embed -d '{"model": "nomic-embed-text", "input": "test"}'
```

### 長文件處理

長文件（超過 4000 字元）會自動截斷以符合模型限制。這是正常行為，不影響搜尋品質。

---

## 授權

MIT License
