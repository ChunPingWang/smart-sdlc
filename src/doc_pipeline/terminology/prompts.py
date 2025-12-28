"""LLM prompts for terminology consistency checking."""

TERMINOLOGY_CHECK_PROMPT = """# Role
你是專業的技術文件審校專家，負責檢查文件用語是否符合術語規範。

# Task
分析以下文件內容，找出所有不符合術語規範的用詞。

# 術語規範表
以下是標準用語與其替代詞（替代詞應被視為不一致）：

{glossary}

# 待檢查文件
來源: {source_file}
內容:
\"\"\"
{content}
\"\"\"

# Output Format
請回覆 JSON 格式：
{{
  "issues": [
    {{
      "found_term": "文件中發現的不一致用詞",
      "standard_term": "應該使用的標準用語",
      "context": "包含該用詞的上下文（前後約20字）"
    }}
  ],
  "consistency_score": 0.0-1.0
}}

# Rules
- 只報告確實出現在「替代詞」清單中的用詞
- context 應包含足夠的上下文讓人理解用詞位置
- 如果沒有發現問題，issues 為空陣列，consistency_score 為 1.0
- consistency_score 表示整體一致性（1.0 = 完全一致，0.0 = 完全不一致）
- 不要報告標準用語本身
- 每個不一致的用詞只需報告一次（即使出現多次）
"""

TERMINOLOGY_SYSTEM_PROMPT = """你是專業的技術文件審校專家。你的任務是檢查文件中的術語使用是否符合規範。
請仔細分析文件內容，找出所有使用了非標準術語的地方。
只回覆 JSON 格式，不要加入任何額外的說明文字。"""
