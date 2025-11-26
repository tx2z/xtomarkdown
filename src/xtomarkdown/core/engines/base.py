"""Abstract base class for conversion engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass
class ConversionResult:
    """Result of a document conversion operation."""

    success: bool
    output_path: Path | None = None
    error: str | None = None
    warnings: list[str] | None = None


class BaseEngine(ABC):
    """Abstract base class for all conversion engines."""

    # Engine identifier (e.g., "pandoc", "markitdown")
    name: ClassVar[str] = "base"

    # Human-readable display name
    display_name: ClassVar[str] = "Base Engine"

    # Set of supported file extensions (without dots)
    supported_formats: ClassVar[set[str]] = set()

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is installed and available."""
        pass

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        """
        Convert a document to Markdown.

        Args:
            input_path: Path to the input document
            output_path: Path for the output Markdown file

        Returns:
            ConversionResult with success status and any errors
        """
        pass

    def supports_format(self, extension: str) -> bool:
        """Check if this engine supports a given file extension."""
        return extension.lower().lstrip(".") in self.supported_formats

    def get_version(self) -> str | None:
        """Get the engine version string, if available."""
        return None
