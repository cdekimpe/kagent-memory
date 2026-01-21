"""Pydantic models for the Kagent Memory API."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


class AddMemoryRequest(BaseModel):
    """Request to add a memory entry."""

    content: str = Field(..., description="The content to store as memory")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    user_id: str | None = Field(default=None, description="User identifier for isolation")
    session_id: str | None = Field(default=None, description="Session identifier for grouping")
    agent_name: str | None = Field(default=None, description="Agent name for filtering")


class AddMemoryResponse(BaseModel):
    """Response after adding memory."""

    memory_ids: list[str] = Field(..., description="IDs of created memory chunks")
    chunks_created: int = Field(..., description="Number of chunks created")


class MemorySearchRequest(BaseModel):
    """Request to search memories."""

    query: str = Field(..., description="Search query")
    user_id: str | None = Field(default=None, description="Filter by user")
    session_id: str | None = Field(default=None, description="Filter by session")
    agent_name: str | None = Field(default=None, description="Filter by agent")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: dict[str, Any] = Field(default_factory=dict, description="Additional filters")


class MemorySearchResult(BaseModel):
    """A single search result."""

    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Memory metadata")
    score: float = Field(..., description="Similarity score")
    memory_id: str = Field(..., description="Memory chunk ID")


class MemorySearchResponse(BaseModel):
    """Response from memory search."""

    results: list[MemorySearchResult] = Field(default_factory=list, description="Search results")
    query: str = Field(..., description="Original query")


class SessionMemoryRequest(BaseModel):
    """Request to add session events to memory (ADK compatibility)."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    events: list[dict[str, Any]] = Field(..., description="Session events to extract memory from")
    app_name: str | None = Field(default=None, description="Application/agent name")


class DeleteMemoryRequest(BaseModel):
    """Request to delete memories."""

    user_id: str = Field(..., description="User identifier")
    session_id: str | None = Field(default=None, description="Optional session filter")
    agent_name: str | None = Field(default=None, description="Optional agent filter")


class DeleteMemoryResponse(BaseModel):
    """Response from deleting memories."""

    deleted_count: int = Field(..., description="Number of memories deleted")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="Service version")
    qdrant_connected: bool = Field(..., description="Qdrant connection status")
    timestamp: datetime = Field(default_factory=_utc_now, description="Check timestamp")
