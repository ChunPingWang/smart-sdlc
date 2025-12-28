"""Document classification module."""

from doc_pipeline.classification.classifier import DocumentClassifier
from doc_pipeline.classification.taxonomy import TAXONOMY, ChunkTypeInfo

__all__ = [
    "DocumentClassifier",
    "TAXONOMY",
    "ChunkTypeInfo",
]
