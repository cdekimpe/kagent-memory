"""Base class for embedding providers."""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the dimension of the embedding vectors.

        Returns:
            The dimensionality of the embedding space.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass
