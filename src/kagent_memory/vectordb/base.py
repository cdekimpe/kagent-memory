"""Base class for vector store implementations."""

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """Abstract base class for vector store implementations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store (create collections, indexes, etc.)."""
        pass

    @abstractmethod
    async def add(
        self,
        vectors: list[list[float]],
        documents: list[str],
        metadata: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add vectors with documents and metadata to the store.

        Args:
            vectors: List of embedding vectors.
            documents: List of document texts.
            metadata: List of metadata dicts for each vector.
            ids: Optional list of IDs for the vectors.

        Returns:
            List of assigned IDs for the stored vectors.
        """
        pass

    @abstractmethod
    async def search(
        self,
        vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            vector: Query vector.
            top_k: Number of results to return.
            filters: Optional filters for metadata fields.
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of results with id, score, content, and metadata.
        """
        pass

    @abstractmethod
    async def delete(
        self,
        ids: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Delete vectors by IDs or filters.

        Args:
            ids: Optional list of IDs to delete.
            filters: Optional filters for metadata fields.

        Returns:
            Number of deleted vectors.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the vector store is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass
