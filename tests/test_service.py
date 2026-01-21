"""Tests for MemoryService."""

import pytest

from kagent_memory.models import MemorySearchRequest
from kagent_memory.service import MemoryService


class TestMemoryService:
    """Tests for MemoryService."""

    @pytest.mark.asyncio
    async def test_add_memory(self, memory_service: MemoryService):
        """Should add memory and return chunk IDs."""
        response = await memory_service.add_memory(
            content="This is a test memory content.",
            user_id="test-user",
            session_id="test-session",
        )

        assert response.chunks_created >= 1
        assert len(response.memory_ids) == response.chunks_created

    @pytest.mark.asyncio
    async def test_add_memory_with_metadata(self, memory_service: MemoryService):
        """Should store custom metadata with memory."""
        response = await memory_service.add_memory(
            content="Memory with metadata.",
            metadata={"category": "test", "priority": "high"},
            user_id="test-user",
        )

        assert response.chunks_created >= 1

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_service: MemoryService):
        """Should find stored memories."""
        # Add memory first
        await memory_service.add_memory(
            content="The user prefers dark mode.",
            user_id="user-1",
        )

        # Search
        request = MemorySearchRequest(
            query="dark mode preference",
            user_id="user-1",
        )
        response = await memory_service.search_memory(request)

        assert len(response.results) >= 1
        assert response.query == "dark mode preference"

    @pytest.mark.asyncio
    async def test_search_memory_with_filter(self, memory_service: MemoryService):
        """Should filter results by user_id."""
        # Add memories for different users
        await memory_service.add_memory(
            content="User 1 preference",
            user_id="user-1",
        )
        await memory_service.add_memory(
            content="User 2 preference",
            user_id="user-2",
        )

        # Search for user-1 only
        request = MemorySearchRequest(
            query="preference",
            user_id="user-1",
        )
        response = await memory_service.search_memory(request)

        # All results should be for user-1
        for result in response.results:
            assert result.metadata.get("user_id") == "user-1"

    @pytest.mark.asyncio
    async def test_add_session_to_memory(self, memory_service: MemoryService):
        """Should extract text from session events."""
        events = [
            {"author": "user", "content": "Hello, how are you?"},
            {"author": "assistant", "content": "I'm doing well, thank you!"},
        ]

        response = await memory_service.add_session_to_memory(
            session_id="session-123",
            user_id="user-1",
            events=events,
            app_name="test-agent",
        )

        assert response.chunks_created >= 1

    @pytest.mark.asyncio
    async def test_add_session_with_adk_format(self, memory_service: MemoryService):
        """Should handle ADK-style event format."""
        events = [
            {
                "author": "user",
                "content": {"parts": [{"text": "What is the weather?"}]},
            },
            {
                "author": "assistant",
                "content": {"parts": [{"text": "It's sunny today."}]},
            },
        ]

        response = await memory_service.add_session_to_memory(
            session_id="session-456",
            user_id="user-1",
            events=events,
        )

        assert response.chunks_created >= 1

    @pytest.mark.asyncio
    async def test_delete_memories(self, memory_service: MemoryService):
        """Should delete memories by filter."""
        # Add memory
        await memory_service.add_memory(
            content="Memory to delete",
            user_id="delete-user",
        )

        # Delete
        deleted = await memory_service.delete_memories(user_id="delete-user")
        assert deleted >= 1

        # Verify deleted
        request = MemorySearchRequest(query="delete", user_id="delete-user")
        response = await memory_service.search_memory(request)
        assert len(response.results) == 0

    @pytest.mark.asyncio
    async def test_health_check(self, memory_service: MemoryService):
        """Should return health status."""
        healthy = await memory_service.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_empty_content(self, memory_service: MemoryService):
        """Should handle empty content gracefully."""
        response = await memory_service.add_memory(
            content="",
            user_id="test-user",
        )

        assert response.chunks_created == 0
        assert response.memory_ids == []
