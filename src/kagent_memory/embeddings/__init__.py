"""Embedding providers for Kagent Memory."""

from kagent_memory.embeddings.base import EmbeddingProvider
from kagent_memory.embeddings.openai import OpenAIEmbeddingProvider

__all__ = ["EmbeddingProvider", "OpenAIEmbeddingProvider"]
