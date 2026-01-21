"""Fixed-size text chunking implementation."""

import logging

from kagent_memory.chunking.base import Chunk, Chunker

logger = logging.getLogger(__name__)

# Sentence separators in order of preference
SENTENCE_SEPARATORS = [". ", ".\n", "\n\n", "\n", " "]


class FixedSizeChunker(Chunker):
    """Fixed-size chunking with overlap and smart boundary detection."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize the fixed-size chunker.

        Args:
            chunk_size: Target size of each chunk in characters.
            overlap: Number of overlapping characters between chunks.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into fixed-size chunks with overlap.

        Attempts to break at sentence boundaries when possible.

        Args:
            text: The text to chunk.

        Returns:
            List of Chunk objects.
        """
        if not text or not text.strip():
            return []

        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            # Calculate initial end position
            end = min(start + self.chunk_size, len(text))

            # If we're not at the end of text, try to find a good break point
            if end < len(text):
                end = self._find_break_point(text, start, end)

            # Extract and clean the chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        start=start,
                        end=end,
                        index=index,
                    )
                )
                index += 1

            # If we've reached the end of text, stop
            if end >= len(text):
                break

            # Move start position with overlap
            new_start = end - self.overlap

            # Ensure we make progress
            if new_start <= start:
                new_start = end

            start = new_start

        logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find the best break point near the end position.

        Looks for sentence boundaries working backwards from end.

        Args:
            text: The full text.
            start: Start position of current chunk.
            end: Initial end position.

        Returns:
            Adjusted end position at a good break point.
        """
        search_region = text[start:end]
        min_chunk_size = self.chunk_size // 2

        # Try each separator in order of preference
        for sep in SENTENCE_SEPARATORS:
            last_sep = search_region.rfind(sep)

            # Accept if found and results in reasonable chunk size
            if last_sep > min_chunk_size:
                return start + last_sep + len(sep)

        # No good break point found, use original end
        return end
