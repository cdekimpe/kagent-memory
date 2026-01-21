"""OpenAI embedding provider implementation."""

import logging
from typing import Any, Literal

from openai import AsyncOpenAI

from kagent_memory.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

# Model dimensions mapping
MODEL_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}

EmbeddingModel = Literal["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding models."""

    def __init__(
        self,
        api_key: str,
        model: EmbeddingModel = "text-embedding-3-small",
        dimensions: int | None = None,
    ):
        """Initialize the OpenAI embedding provider.

        Args:
            api_key: OpenAI API key.
            model: Embedding model to use.
            dimensions: Custom dimensions (only for text-embedding-3-* models).
        """
        self.model = model
        self._dimensions = dimensions
        self._client = AsyncOpenAI(api_key=api_key)

        # Validate dimensions for text-embedding-3-* models
        if dimensions is not None and "text-embedding-3" not in model:
            logger.warning(f"Custom dimensions not supported for model {model}, using default")
            self._dimensions = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using OpenAI API.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        # Build request kwargs
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": texts,
        }

        # Add dimensions for text-embedding-3-* models
        if self._dimensions is not None and "text-embedding-3" in self.model:
            kwargs["dimensions"] = self._dimensions

        logger.debug(f"Embedding {len(texts)} texts with model {self.model}")
        response = await self._client.embeddings.create(**kwargs)

        return [item.embedding for item in response.data]

    def get_dimension(self) -> int:
        """Return the embedding dimension.

        Returns:
            The dimensionality of embeddings.
        """
        if self._dimensions is not None:
            return self._dimensions
        return MODEL_DIMENSIONS.get(self.model, 1536)

    async def close(self) -> None:
        """Clean up the OpenAI client."""
        await self._client.close()
