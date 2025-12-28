# Doc-Pipeline

**Document-to-Code Pipeline** - AI-driven document processing and specification generation system.

將原始系統設計文件（Word、Excel、Markdown、PDF）轉換為 AI 可處理的結構化規格。

## Features

- **Multi-format Parsing**: 支援 Word、Excel、Markdown、PDF 等格式
- **Smart Chunking**: 基於結構和語意的智能切分
- **LLM Classification**: 使用 LLM 自動分類文件內容
- **Knowledge Base**: ChromaDB 向量儲存與相似度搜尋
- **Specification Generation**: 自動產出需求清單、API 規格、DB Schema、開發任務
- **Multiple Exporters**: YAML、OpenAPI 3.0、SQL DDL 等格式輸出

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd smart-sdlc

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure your API keys in `.env`:
   ```
   OPENAI_API_KEY=sk-your-key
   # or
   ANTHROPIC_API_KEY=sk-ant-your-key
   LLM_PROVIDER=anthropic
   ```

## Quick Start

```bash
# Initialize project structure
doc-pipeline init

# Process documents
doc-pipeline process ./your-docs --name "My Project"

# Generate specific specs
doc-pipeline generate requirements
doc-pipeline generate api
doc-pipeline generate tasks

# Search knowledge base
doc-pipeline search "user registration"

# Show configuration
doc-pipeline info
```

## Pipeline Stages

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Ingest  │───▶│  Parse   │───▶│ Chunking │───▶│ Classify │
│  收集文件  │    │  解析轉換  │    │  智能切分  │    │  文件分類  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Export  │◀───│ Generate │◀───│   Store  │◀───│  Enrich  │
│  格式輸出  │    │  規格產出  │    │  知識庫存  │    │  語意增強  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Output Files

After running the pipeline, you'll get:

- `requirements-list.yaml` - 需求清單 (BR, FR, BRule, NFR)
- `api-spec.yaml` - API 規格
- `database-spec.yaml` - 資料庫規格
- `dev-tasks.yaml` - 開發任務清單
- `openapi.yaml` - OpenAPI 3.0 文件
- `schema.sql` - DDL 資料庫腳本
- `ai-ready-specs/` - AI 工具可直接使用的規格

## Project Structure

```
src/doc_pipeline/
├── cli.py              # CLI 入口
├── config.py           # 配置管理
├── document/           # 文件處理
│   ├── models.py       # 資料模型
│   └── parser.py       # 多格式解析器
├── chunking/           # 智能切分
│   ├── strategies.py   # 切分策略
│   └── chunker.py      # 切分器
├── classification/     # 文件分類
│   ├── taxonomy.py     # 分類體系
│   └── classifier.py   # LLM 分類器
├── knowledge_base/     # 知識庫
│   ├── embeddings.py   # 向量化
│   └── vectorstore.py  # 向量儲存
├── generation/         # 規格產出
│   ├── generator.py    # 規格產生器
│   ├── prompts/        # Prompt 模板
│   └── exporters/      # 格式匯出器
└── pipeline/           # 流程編排
    └── orchestrator.py # Pipeline 編排器
```

## Development

```bash
# Run tests
pytest

# Type checking
mypy src

# Linting
ruff check src
```

## License

MIT
