"""LLM-based document classifier."""

import json
import re
from typing import Any

from doc_pipeline.classification.taxonomy import TAXONOMY, get_classification_prompt
from doc_pipeline.config import settings
from doc_pipeline.document.models import ChunkType, DocumentChunk


class LLMClient:
    """Simple LLM client wrapper for OpenAI, Anthropic, and Ollama."""

    def __init__(self) -> None:
        """Initialize based on settings."""
        self.config = settings.get_llm_config()
        self.provider = self.config["provider"]

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Complete a prompt using the configured LLM."""
        if self.provider == "openai":
            return self._openai_complete(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return self._anthropic_complete(system_prompt, user_prompt)
        else:  # ollama
            return self._ollama_complete(system_prompt, user_prompt)

    def _openai_complete(self, system_prompt: str, user_prompt: str) -> str:
        """Use OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.config["api_key"])
            model = self.config["model"]

            # o1/o3/o4 系列推理模型不支援 temperature 和 system message
            is_reasoning_model = any(
                model.startswith(prefix) for prefix in ("o1", "o3", "o4")
            )

            if is_reasoning_model:
                # 推理模型：合併 prompt，不設定 temperature
                combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": combined_prompt},
                    ],
                )
            else:
                # 標準模型：使用 system message 和 temperature=0
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0,
                    )
                except Exception as temp_error:
                    # 若 temperature 不支援，則不帶 temperature 重試
                    if "temperature" in str(temp_error).lower():
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                        )
                    else:
                        raise
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error: {e}"

    def _anthropic_complete(self, system_prompt: str, user_prompt: str) -> str:
        """Use Anthropic API."""
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.config["api_key"])
            response = client.messages.create(
                model=self.config["model"],
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if response.content and hasattr(response.content[0], "text"):
                return str(response.content[0].text)
            return ""
        except Exception as e:
            return f"Error: {e}"

    def _ollama_complete(self, system_prompt: str, user_prompt: str) -> str:
        """Use Ollama API."""
        try:
            import urllib.error
            import urllib.request

            url = f"{self.config['base_url']}/api/chat"
            payload = {
                "model": self.config["model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                content: str = result.get("message", {}).get("content", "")
                return content
        except urllib.error.URLError as e:
            return f"Error: Ollama connection failed - {e.reason}. Is Ollama running?"
        except Exception as e:
            return f"Error: {e}"


class DocumentClassifier:
    """
    LLM-based document chunk classifier.

    Supports both OpenAI and Anthropic as backends.
    """

    def __init__(
        self,
        use_keywords: bool = True,
    ):
        """
        Initialize the classifier.

        Args:
            use_keywords: Whether to use keyword-based pre-classification
        """
        self.llm = LLMClient()
        self.use_keywords = use_keywords
        self.system_prompt = get_classification_prompt()

    def classify(self, chunk: DocumentChunk) -> DocumentChunk:
        """
        Classify a single document chunk.

        Args:
            chunk: The chunk to classify

        Returns:
            The chunk with updated classification
        """
        # Try keyword-based classification first
        if self.use_keywords:
            keyword_result = self._classify_by_keywords(chunk.content)
            if keyword_result and keyword_result[1] > 0.8:
                chunk.chunk_type = keyword_result[0]
                chunk.confidence = keyword_result[1]
                return chunk

        # Use LLM for classification
        result = self._classify_with_llm(chunk.content)

        chunk.chunk_type = result.get("type", ChunkType.UNKNOWN)
        chunk.confidence = result.get("confidence", 0.0)
        chunk.entities = result.get("entities", [])
        chunk.dependencies = result.get("dependencies", [])

        return chunk

    def batch_classify(
        self,
        chunks: list[DocumentChunk],
        batch_size: int = 10,
    ) -> list[DocumentChunk]:
        """
        Classify multiple chunks.

        Args:
            chunks: List of chunks to classify
            batch_size: Number of chunks to process at once

        Returns:
            List of classified chunks
        """
        classified = []

        for chunk in chunks:
            classified_chunk = self.classify(chunk)
            classified.append(classified_chunk)

        return classified

    def _classify_by_keywords(
        self,
        content: str,
    ) -> tuple[ChunkType, float] | None:
        """
        Attempt classification using keywords.

        Args:
            content: The content to classify

        Returns:
            Tuple of (ChunkType, confidence) or None
        """
        content_lower = content.lower()
        scores: dict[ChunkType, float] = {}

        for chunk_type, info in TAXONOMY.items():
            if chunk_type == ChunkType.UNKNOWN:
                continue

            matches = sum(1 for kw in info.keywords if kw.lower() in content_lower)
            if matches > 0:
                scores[chunk_type] = min(matches / 5.0, 1.0)

        if not scores:
            return None

        best_type = max(scores, key=lambda k: scores[k])
        return (best_type, scores[best_type])

    def _classify_with_llm(self, content: str) -> dict[str, Any]:
        """
        Classify content using LLM.

        Args:
            content: The content to classify

        Returns:
            Classification result dict
        """
        user_prompt = f"請分類以下內容：\n\n{content}"

        try:
            response = self.llm.complete(self.system_prompt, user_prompt)
            result = self._parse_llm_response(response)
            return result
        except Exception as e:
            return {
                "type": ChunkType.UNKNOWN,
                "confidence": 0.0,
                "error": str(e),
            }

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse LLM JSON response."""
        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group())

                type_str = data.get("type", "unknown")
                try:
                    chunk_type = ChunkType(type_str)
                except ValueError:
                    chunk_type = ChunkType.UNKNOWN

                return {
                    "type": chunk_type,
                    "confidence": float(data.get("confidence", 0.5)),
                    "entities": data.get("entities", []),
                    "dependencies": data.get("dependencies", []),
                }
            except json.JSONDecodeError:
                pass

        return {"type": ChunkType.UNKNOWN, "confidence": 0.0}


class RuleBasedClassifier:
    """
    Rule-based classifier using patterns and keywords.

    Faster than LLM but less accurate.
    """

    def classify(self, chunk: DocumentChunk) -> DocumentChunk:
        """Classify using rules and patterns."""
        content = chunk.content
        content_lower = content.lower()

        if self._is_api_spec(content):
            chunk.chunk_type = ChunkType.API_SPEC
            chunk.confidence = 0.9
            return chunk

        if self._is_db_schema(content):
            chunk.chunk_type = ChunkType.DB_SCHEMA
            chunk.confidence = 0.9
            return chunk

        if self._is_use_case(content_lower):
            chunk.chunk_type = ChunkType.USE_CASE
            chunk.confidence = 0.8
            return chunk

        if self._is_business_rule(content_lower):
            chunk.chunk_type = ChunkType.BUSINESS_RULE
            chunk.confidence = 0.8
            return chunk

        for chunk_type, info in TAXONOMY.items():
            if chunk_type == ChunkType.UNKNOWN:
                continue
            matches = sum(1 for kw in info.keywords if kw.lower() in content_lower)
            if matches >= 3:
                chunk.chunk_type = chunk_type
                chunk.confidence = min(matches / 5.0, 0.8)
                return chunk

        chunk.chunk_type = ChunkType.UNKNOWN
        chunk.confidence = 0.0
        return chunk

    def _is_api_spec(self, content: str) -> bool:
        """Check if content is API specification."""
        patterns = [
            r"(GET|POST|PUT|DELETE|PATCH)\s+/",
            r"endpoint\s*:",
            r"request\s*:\s*\{",
            r"response\s*:\s*\{",
            r"/api/v\d+/",
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)

    def _is_db_schema(self, content: str) -> bool:
        """Check if content is database schema."""
        patterns = [
            r"CREATE\s+TABLE",
            r"(VARCHAR|INT|BOOLEAN|TIMESTAMP|UUID)\s*\(",
            r"PRIMARY\s+KEY",
            r"FOREIGN\s+KEY",
            r"表格\s*[:：]",
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)

    def _is_use_case(self, content: str) -> bool:
        """Check if content is a use case."""
        patterns = [
            r"as\s+a\s+\w+",
            r"i\s+want\s+to",
            r"so\s+that",
            r"given\s+.+when\s+.+then",
            r"身為.+我想要.+以便",
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)

    def _is_business_rule(self, content: str) -> bool:
        """Check if content is a business rule."""
        patterns = [
            r"(must|shall|should)\s+(be|have|contain)",
            r"(必須|應該|需要)\s*(是|有|包含)",
            r"if\s+.+then",
            r"驗證.+規則",
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)
