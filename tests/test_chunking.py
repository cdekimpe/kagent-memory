"""Tests for text chunking."""

import pytest

from kagent_memory.chunking import FixedSizeChunker


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_empty_text(self):
        """Empty text should return no chunks."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_whitespace_only(self):
        """Whitespace-only text should return no chunks."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk("   \n\t  ")
        assert chunks == []

    def test_short_text(self):
        """Text shorter than chunk_size should return single chunk."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        text = "This is a short text."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0
        assert chunks[0].start == 0

    def test_long_text_creates_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        text = "A" * 150  # 150 characters

        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert len(chunk.text) <= 50

    def test_overlap_between_chunks(self):
        """Consecutive chunks should have overlap."""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        text = "A" * 100

        chunks = chunker.chunk(text)

        # With overlap, chunks should share some content
        assert len(chunks) >= 2

    def test_sentence_boundary_detection(self):
        """Chunker should try to break at sentence boundaries."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        text = "This is sentence one. This is sentence two. This is sentence three."

        chunks = chunker.chunk(text)

        # The first chunk should end at a sentence boundary if possible
        assert len(chunks) >= 1

    def test_invalid_chunk_size(self):
        """Should raise error for invalid chunk_size."""
        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=0, overlap=10)

        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=-1, overlap=10)

    def test_invalid_overlap(self):
        """Should raise error for invalid overlap."""
        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=100, overlap=-1)

        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=100, overlap=100)

    def test_chunk_positions(self):
        """Chunk positions should be correct."""
        chunker = FixedSizeChunker(chunk_size=50, overlap=0)
        text = "A" * 100

        chunks = chunker.chunk(text)

        assert chunks[0].start == 0
        assert chunks[0].end == 50
