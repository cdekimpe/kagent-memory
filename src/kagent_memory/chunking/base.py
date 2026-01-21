"""Base class for text chunking strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk with position information."""

    text: str
    start: int
    end: int
    index: int


class Chunker(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]:
        """Split text into chunks.

        Args:
            text: The text to chunk.

        Returns:
            List of Chunk objects with text and position info.
        """
        pass
