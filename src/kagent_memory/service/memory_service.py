"""Core memory service implementation."""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from kagent_memory.chunking.base import Chunker
from kagent_memory.embeddings.base import EmbeddingProvider
from kagent_memory.models import (
    AddMemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
)
from kagent_memory.vectordb.base import VectorStore

logger = logging.getLogger(__name__)


class MemoryService:
    """Core memory service that orchestrates embedding, chunking, and storage."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        chunker: Chunker,
    ):
        """Initialize the memory service.

        Args:
            embedding_provider: Provider for text embeddings.
            vector_store: Vector database for storage.
            chunker: Text chunking strategy.
        """
        self.embeddings = embedding_provider
        self.store = vector_store
        self.chunker = chunker

    async def initialize(self) -> None:
        """Initialize the memory service and underlying stores."""
        await self.store.initialize()
        logger.info("Memory service initialized")

    async def add_memory(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        agent_name: str | None = None,
    ) -> AddMemoryResponse:
        """Add a memory entry with chunking and embedding.

        Args:
            content: The content to store.
            metadata: Optional additional metadata.
            user_id: User identifier for isolation.
            session_id: Session identifier for grouping.
            agent_name: Agent name for filtering.

        Returns:
            Response with created memory IDs and chunk count.
        """
        metadata = metadata or {}

        # Create content hash for deduplication tracking
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Build base metadata
        base_metadata: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "content_hash": content_hash,
        }

        # Add optional fields if provided
        if user_id:
            base_metadata["user_id"] = user_id
        if session_id:
            base_metadata["session_id"] = session_id
        if agent_name:
            base_metadata["agent_name"] = agent_name

        # Chunk the content
        chunks = self.chunker.chunk(content)

        if not chunks:
            logger.warning("No chunks created from content")
            return AddMemoryResponse(memory_ids=[], chunks_created=0)

        logger.debug(f"Created {len(chunks)} chunks from content")

        # Embed all chunks
        chunk_texts = [c.text for c in chunks]
        vectors = await self.embeddings.embed(chunk_texts)

        # Prepare metadata for each chunk
        chunk_metadata = []
        for chunk in chunks:
            chunk_meta = {
                **base_metadata,
                **metadata,
                "chunk_index": chunk.index,
                "chunk_start": chunk.start,
                "chunk_end": chunk.end,
                "total_chunks": len(chunks),
            }
            chunk_metadata.append(chunk_meta)

        # Store in vector DB
        memory_ids = await self.store.add(
            vectors=vectors,
            documents=chunk_texts,
            metadata=chunk_metadata,
        )

        logger.info(f"Stored {len(memory_ids)} memory chunks for user={user_id}, session={session_id}")
        return AddMemoryResponse(
            memory_ids=memory_ids,
            chunks_created=len(chunks),
        )

    async def search_memory(self, request: MemorySearchRequest) -> MemorySearchResponse:
        """Search memories by semantic similarity.

        Args:
            request: Search request with query and filters.

        Returns:
            Search response with ranked results.
        """
        # Embed the query
        query_vectors = await self.embeddings.embed([request.query])
        query_vector = query_vectors[0]

        # Build filters
        filters: dict[str, Any] = dict(request.filters)
        if request.user_id:
            filters["user_id"] = request.user_id
        if request.session_id:
            filters["session_id"] = request.session_id
        if request.agent_name:
            filters["agent_name"] = request.agent_name

        # Search
        results = await self.store.search(
            vector=query_vector,
            top_k=request.top_k,
            filters=filters if filters else None,
            score_threshold=request.score_threshold,
        )

        logger.debug(f"Found {len(results)} results for query: {request.query[:50]}...")
        return MemorySearchResponse(
            results=[
                MemorySearchResult(
                    content=r["content"],
                    metadata=r["metadata"],
                    score=r["score"],
                    memory_id=r["id"],
                )
                for r in results
            ],
            query=request.query,
        )

    async def add_session_to_memory(
        self,
        session_id: str,
        user_id: str,
        events: list[dict[str, Any]],
        app_name: str | None = None,
    ) -> AddMemoryResponse:
        """Add session events to memory (ADK compatibility).

        Extracts text content from session events and stores as memory.

        Args:
            session_id: Session identifier.
            user_id: User identifier.
            events: List of session events.
            app_name: Optional application/agent name.

        Returns:
            Response with created memory IDs.
        """
        # Extract text content from events
        content_parts: list[str] = []

        for event in events:
            if not isinstance(event, dict):
                continue

            author = event.get("author", "unknown")

            # Handle different content formats
            content = event.get("content")
            if content is None:
                continue

            if isinstance(content, str):
                content_parts.append(f"{author}: {content}")
            elif isinstance(content, dict):
                # ADK-style content with parts
                parts = content.get("parts", [])
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        content_parts.append(f"{author}: {part['text']}")
                    elif isinstance(part, str):
                        content_parts.append(f"{author}: {part}")

        if not content_parts:
            logger.debug("No text content found in session events")
            return AddMemoryResponse(memory_ids=[], chunks_created=0)

        full_content = "\n".join(content_parts)

        return await self.add_memory(
            content=full_content,
            metadata={"source": "session"},
            user_id=user_id,
            session_id=session_id,
            agent_name=app_name,
        )

    async def delete_memories(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_name: str | None = None,
    ) -> int:
        """Delete memories by user and optional filters.

        Args:
            user_id: User identifier (required).
            session_id: Optional session filter.
            agent_name: Optional agent filter.

        Returns:
            Number of deleted memories.
        """
        filters: dict[str, Any] = {"user_id": user_id}
        if session_id:
            filters["session_id"] = session_id
        if agent_name:
            filters["agent_name"] = agent_name

        deleted = await self.store.delete(filters=filters)
        logger.info(f"Deleted {deleted} memories for user={user_id}, session={session_id}")
        return deleted

    async def health_check(self) -> bool:
        """Check if the memory service is healthy.

        Returns:
            True if all components are healthy.
        """
        return await self.store.health_check()

    async def close(self) -> None:
        """Clean up resources."""
        await self.embeddings.close()
        await self.store.close()
        logger.info("Memory service closed")
