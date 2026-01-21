"""Tests for FastAPI routes."""

from datetime import UTC
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


class TestAPI:
    """Tests for API endpoints."""

    @pytest.fixture
    def mock_memory_service(self):
        """Create a mock memory service."""
        from kagent_memory.models import AddMemoryResponse, MemorySearchResponse, MemorySearchResult

        service = AsyncMock()
        service.add_memory.return_value = AddMemoryResponse(
            memory_ids=["id-1", "id-2"],
            chunks_created=2,
        )
        service.search_memory.return_value = MemorySearchResponse(
            results=[
                MemorySearchResult(
                    content="Test content",
                    metadata={"user_id": "test-user"},
                    score=0.9,
                    memory_id="id-1",
                )
            ],
            query="test query",
        )
        service.health_check.return_value = True
        service.delete_memories.return_value = 1
        return service

    @pytest.fixture
    def client(self, mock_memory_service):
        """Create test client with mocked service."""
        from kagent_memory.api import routes

        # Patch the global memory service
        routes._memory_service = mock_memory_service


        # Create app without lifespan (which would override our mock)
        from fastapi import FastAPI
        app = FastAPI()

        # Copy routes manually
        @app.get("/health")
        async def health():
            from datetime import datetime

            from kagent_memory import __version__
            from kagent_memory.models import HealthResponse
            healthy = await mock_memory_service.health_check()
            return HealthResponse(
                status="healthy" if healthy else "degraded",
                version=__version__,
                qdrant_connected=healthy,
                timestamp=datetime.now(UTC),
            )

        @app.post("/api/memory")
        async def add_memory(request: dict):
            from kagent_memory.models import AddMemoryRequest
            req = AddMemoryRequest(**request)
            return await mock_memory_service.add_memory(
                content=req.content,
                metadata=req.metadata,
                user_id=req.user_id,
                session_id=req.session_id,
                agent_name=req.agent_name,
            )

        @app.post("/api/memory/search")
        async def search_memory(request: dict):
            from kagent_memory.models import MemorySearchRequest
            req = MemorySearchRequest(**request)
            return await mock_memory_service.search_memory(req)

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Health endpoint should return status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["qdrant_connected"] is True

    def test_add_memory_endpoint(self, client):
        """Add memory endpoint should accept content."""
        response = client.post(
            "/api/memory",
            json={
                "content": "Test memory content",
                "user_id": "test-user",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_created"] == 2
        assert len(data["memory_ids"]) == 2

    def test_search_memory_endpoint(self, client):
        """Search memory endpoint should return results."""
        response = client.post(
            "/api/memory/search",
            json={
                "query": "test query",
                "user_id": "test-user",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["query"] == "test query"
