"""FastAPI routes for Kagent Memory service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException

from kagent_memory import __version__
from kagent_memory.chunking import FixedSizeChunker
from kagent_memory.config import Settings, get_openai_settings, get_settings
from kagent_memory.embeddings import OpenAIEmbeddingProvider
from kagent_memory.models import (
    AddMemoryRequest,
    AddMemoryResponse,
    DeleteMemoryResponse,
    HealthResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    SessionMemoryRequest,
)
from kagent_memory.service import MemoryService
from kagent_memory.vectordb import QdrantVectorStore

logger = logging.getLogger(__name__)

# Global memory service instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Dependency to get the memory service instance."""
    if _memory_service is None:
        raise HTTPException(status_code=503, detail="Memory service not initialized")
    return _memory_service


async def create_memory_service(settings: Settings) -> MemoryService:
    """Create and initialize the memory service."""
    openai_settings = get_openai_settings()

    if not openai_settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # Create embedding provider
    embedding_provider = OpenAIEmbeddingProvider(
        api_key=openai_settings.openai_api_key,
        model=settings.embedding_model,  # type: ignore
        dimensions=settings.embedding_dimensions,
    )

    # Create vector store
    vector_store = QdrantVectorStore(
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        dimension=embedding_provider.get_dimension(),
        api_key=settings.qdrant_api_key,
    )

    # Create chunker
    chunker = FixedSizeChunker(
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )

    # Create service
    service = MemoryService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        chunker=chunker,
    )

    # Initialize
    await service.initialize()

    return service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global _memory_service

    settings = get_settings()
    logger.info(f"Starting Kagent Memory service v{__version__}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Collection: {settings.qdrant_collection}")
    logger.info(f"Embedding model: {settings.embedding_model}")

    # Initialize memory service
    _memory_service = await create_memory_service(settings)

    yield

    # Cleanup
    if _memory_service:
        await _memory_service.close()
        _memory_service = None

    logger.info("Kagent Memory service stopped")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="Kagent Memory",
        description="Long-term memory service for Kagent platform",
        version=__version__,
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check(
        service: MemoryService = Depends(get_memory_service),
    ) -> HealthResponse:
        """Health check endpoint."""
        qdrant_healthy = await service.health_check()
        return HealthResponse(
            status="healthy" if qdrant_healthy else "degraded",
            version=__version__,
            qdrant_connected=qdrant_healthy,
            timestamp=datetime.utcnow(),
        )

    @app.post("/api/memory", response_model=AddMemoryResponse, tags=["Memory"])
    async def add_memory(
        request: AddMemoryRequest,
        x_user_id: str | None = Header(default=None),
        service: MemoryService = Depends(get_memory_service),
    ) -> AddMemoryResponse:
        """Add a memory entry."""
        user_id = request.user_id or x_user_id

        return await service.add_memory(
            content=request.content,
            metadata=request.metadata,
            user_id=user_id,
            session_id=request.session_id,
            agent_name=request.agent_name,
        )

    @app.post("/api/memory/search", response_model=MemorySearchResponse, tags=["Memory"])
    async def search_memory(
        request: MemorySearchRequest,
        x_user_id: str | None = Header(default=None),
        service: MemoryService = Depends(get_memory_service),
    ) -> MemorySearchResponse:
        """Search memories by semantic similarity."""
        # Use header user_id if not provided in request
        if x_user_id and not request.user_id:
            request.user_id = x_user_id

        return await service.search_memory(request)

    @app.post("/api/memory/session", response_model=AddMemoryResponse, tags=["Memory"])
    async def add_session_memory(
        request: SessionMemoryRequest,
        service: MemoryService = Depends(get_memory_service),
    ) -> AddMemoryResponse:
        """Add session events to memory (ADK compatibility)."""
        return await service.add_session_to_memory(
            session_id=request.session_id,
            user_id=request.user_id,
            events=request.events,
            app_name=request.app_name,
        )

    @app.delete("/api/memory/{user_id}", response_model=DeleteMemoryResponse, tags=["Memory"])
    async def delete_user_memories(
        user_id: str,
        session_id: str | None = None,
        agent_name: str | None = None,
        service: MemoryService = Depends(get_memory_service),
    ) -> DeleteMemoryResponse:
        """Delete memories for a user."""
        deleted_count = await service.delete_memories(
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name,
        )
        return DeleteMemoryResponse(deleted_count=deleted_count)

    return app
