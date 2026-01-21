"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from kagent_memory.chunking import FixedSizeChunker
from kagent_memory.embeddings.base import EmbeddingProvider
from kagent_memory.service import MemoryService
from kagent_memory.vectordb.base import VectorStore


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    def __init__(self, dimension: int = 1536):
        self._dimension = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return mock embeddings (same vector for simplicity)."""
        return [[0.1] * self._dimension for _ in texts]

    def get_dimension(self) -> int:
        return self._dimension

    async def close(self) -> None:
        pass


class MockVectorStore(VectorStore):
    """Mock vector store for testing."""

    def __init__(self):
        self._data: dict[str, dict] = {}
        self._counter = 0

    async def initialize(self) -> None:
        pass

    async def add(
        self,
        vectors: list[list[float]],
        documents: list[str],
        metadata: list[dict],
        ids: list[str] | None = None,
    ) -> list[str]:
        result_ids = []
        for i, (vector, doc, meta) in enumerate(zip(vectors, documents, metadata)):
            id_ = ids[i] if ids else f"mock-{self._counter}"
            self._counter += 1
            self._data[id_] = {
                "vector": vector,
                "content": doc,
                "metadata": meta,
            }
            result_ids.append(id_)
        return result_ids

    async def search(
        self,
        vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
        score_threshold: float | None = None,
    ) -> list[dict]:
        results = []
        for id_, data in self._data.items():
            # Simple filter matching
            if filters:
                match = all(
                    data["metadata"].get(k) == v
                    for k, v in filters.items()
                    if v is not None
                )
                if not match:
                    continue

            results.append({
                "id": id_,
                "score": 0.9,  # Mock score
                "content": data["content"],
                "metadata": data["metadata"],
            })

        return results[:top_k]

    async def delete(
        self,
        ids: list[str] | None = None,
        filters: dict | None = None,
    ) -> int:
        count = 0
        if ids:
            for id_ in ids:
                if id_ in self._data:
                    del self._data[id_]
                    count += 1
        elif filters:
            to_delete = []
            for id_, data in self._data.items():
                match = all(
                    data["metadata"].get(k) == v
                    for k, v in filters.items()
                    if v is not None
                )
                if match:
                    to_delete.append(id_)
            for id_ in to_delete:
                del self._data[id_]
                count += 1
        return count

    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        pass


@pytest.fixture
def mock_embedding_provider() -> MockEmbeddingProvider:
    """Create a mock embedding provider."""
    return MockEmbeddingProvider()


@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    """Create a mock vector store."""
    return MockVectorStore()


@pytest.fixture
def chunker() -> FixedSizeChunker:
    """Create a fixed-size chunker."""
    return FixedSizeChunker(chunk_size=100, overlap=20)


@pytest_asyncio.fixture
async def memory_service(
    mock_embedding_provider: MockEmbeddingProvider,
    mock_vector_store: MockVectorStore,
    chunker: FixedSizeChunker,
) -> AsyncGenerator[MemoryService, None]:
    """Create a memory service with mocked dependencies."""
    service = MemoryService(
        embedding_provider=mock_embedding_provider,
        vector_store=mock_vector_store,
        chunker=chunker,
    )
    await service.initialize()
    yield service
    await service.close()
