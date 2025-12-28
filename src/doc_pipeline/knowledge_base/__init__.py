"""Knowledge base module for vector storage and retrieval."""

from doc_pipeline.knowledge_base.embeddings import EmbeddingService
from doc_pipeline.knowledge_base.vectorstore import KnowledgeBase

__all__ = [
    "EmbeddingService",
    "KnowledgeBase",
]
