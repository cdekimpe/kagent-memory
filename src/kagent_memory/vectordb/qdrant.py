"""Qdrant vector store implementation."""

import logging
import uuid
from typing import Any, Sequence, cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from kagent_memory.vectordb.base import VectorStore

logger = logging.getLogger(__name__)

# Type alias for filter conditions
FilterCondition = (
    qdrant_models.FieldCondition
    | qdrant_models.IsEmptyCondition
    | qdrant_models.IsNullCondition
    | qdrant_models.HasIdCondition
    | qdrant_models.HasVectorCondition
    | qdrant_models.NestedCondition
    | qdrant_models.Filter
)


class QdrantVectorStore(VectorStore):
    """Qdrant vector store implementation."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        dimension: int,
        api_key: str | None = None,
    ):
        """Initialize the Qdrant vector store.

        Args:
            url: Qdrant server URL.
            collection_name: Name of the collection to use.
            dimension: Dimension of the embedding vectors.
            api_key: Optional API key for Qdrant Cloud.
        """
        self.url = url
        self.collection_name = collection_name
        self.dimension = dimension
        self._client = AsyncQdrantClient(url=url, api_key=api_key)

    async def initialize(self) -> None:
        """Initialize the collection if it doesn't exist."""
        try:
            collections = await self._client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)

            if not exists:
                logger.info(f"Creating collection {self.collection_name} with dimension {self.dimension}")
                await self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.dimension,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )

                # Create payload indexes for common filter fields
                for field in ["user_id", "session_id", "agent_name"]:
                    await self._client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                    )
                logger.info(f"Collection {self.collection_name} created with indexes")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    async def add(
        self,
        vectors: list[list[float]],
        documents: list[str],
        metadata: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add vectors to Qdrant.

        Args:
            vectors: List of embedding vectors.
            documents: List of document texts.
            metadata: List of metadata dicts.
            ids: Optional list of IDs.

        Returns:
            List of assigned IDs.
        """
        if not vectors:
            return []

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]

        # Build points
        points = [
            qdrant_models.PointStruct(
                id=id_,
                vector=vector,
                payload={"content": doc, **meta},
            )
            for id_, vector, doc, meta in zip(ids, vectors, documents, metadata)
        ]

        logger.debug(f"Upserting {len(points)} points to {self.collection_name}")
        await self._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return ids

    async def search(
        self,
        vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in Qdrant.

        Args:
            vector: Query vector.
            top_k: Number of results to return.
            filters: Optional filters for metadata fields.
            score_threshold: Minimum similarity score.

        Returns:
            List of results with id, score, content, and metadata.
        """
        # Build filter if provided
        qdrant_filter = None
        if filters:
            conditions: list[FilterCondition] = []
            for key, value in filters.items():
                if value is not None:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=value),
                        )
                    )
            if conditions:
                qdrant_filter = qdrant_models.Filter(must=conditions)

        logger.debug(f"Searching {self.collection_name} with top_k={top_k}, filter={filters}")
        results = await self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            query_filter=qdrant_filter,
            score_threshold=score_threshold,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score if r.score is not None else 0.0,
                "content": r.payload.get("content", "") if r.payload else "",
                "metadata": {k: v for k, v in (r.payload or {}).items() if k != "content"},
            }
            for r in results.points
        ]

    async def delete(
        self,
        ids: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Delete vectors from Qdrant.

        Args:
            ids: Optional list of IDs to delete.
            filters: Optional filters for metadata fields.

        Returns:
            Number of deleted vectors (estimated).
        """
        if ids:
            logger.debug(f"Deleting {len(ids)} points by ID from {self.collection_name}")
            # Cast to the expected type for PointIdsList
            point_ids: Sequence[int | str] = cast(Sequence[int | str], ids)
            await self._client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(points=point_ids),
            )
            return len(ids)
        elif filters:
            # Build filter conditions
            conditions: list[FilterCondition] = []
            for key, value in filters.items():
                if value is not None:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=value),
                        )
                    )

            if conditions:
                qdrant_filter = qdrant_models.Filter(must=conditions)
                logger.debug(f"Deleting points by filter from {self.collection_name}")

                # Count before deletion for return value
                count_result = await self._client.count(
                    collection_name=self.collection_name,
                    count_filter=qdrant_filter,
                )

                await self._client.delete(
                    collection_name=self.collection_name,
                    points_selector=qdrant_models.FilterSelector(filter=qdrant_filter),
                )
                return count_result.count

        return 0

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            await self._client.get_collections()
            return True
        except (UnexpectedResponse, Exception) as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the Qdrant client."""
        await self._client.close()
