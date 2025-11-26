"""MarkItDown conversion engine implementation."""

from pathlib import Path
from typing import ClassVar

from .base import BaseEngine, ConversionResult


class MarkItDownEngine(BaseEngine):
    """Conversion engine using Microsoft's MarkItDown library."""

    name: ClassVar[str] = "markitdown"
    display_name: ClassVar[str] = "MarkItDown"
    supported_formats: ClassVar[set[str]] = {
        "docx",
        "pdf",
        "pptx",
        "xlsx",
        "xls",
        "html",
        "htm",
        "csv",
        "json",
        "xml",
        "epub",
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        "wav",
        "mp3",
        "zip",
    }

    def __init__(self):
        self._markitdown = None
        self._md_instance = None
        self._version: str | None = None

    def _get_markitdown(self):
        """Lazy load markitdown module."""
        if self._markitdown is None:
            try:
                import markitdown

                self._markitdown = markitdown
            except ImportError:
                pass
        return self._markitdown

    def _get_md_instance(self):
        """Get or create MarkItDown instance."""
        if self._md_instance is None:
            markitdown = self._get_markitdown()
            if markitdown is not None:
                self._md_instance = markitdown.MarkItDown()
        return self._md_instance

    def is_available(self) -> bool:
        """Check if MarkItDown library is available."""
        return self._get_markitdown() is not None

    def get_version(self) -> str | None:
        """Get the MarkItDown version string."""
        if self._version is not None:
            return self._version

        if not self.is_available():
            return None

        try:
            import importlib.metadata

            self._version = importlib.metadata.version("markitdown")
            return self._version
        except Exception:
            return "unknown"

    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        """Convert a document to Markdown using MarkItDown."""
        md = self._get_md_instance()
        if md is None:
            return ConversionResult(success=False, error="MarkItDown library is not installed")

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert the file
            result = md.convert(str(input_path))

            # Write the markdown content
            output_path.write_text(result.text_content, encoding="utf-8")

            # Note: MarkItDown doesn't extract media separately
            warnings = None
            ext = input_path.suffix.lower()
            if ext in {".docx", ".pptx"} and "![" in result.text_content:
                warnings = [
                    "Note: MarkItDown may not extract embedded images. "
                    "Consider using Pandoc for better image handling."
                ]

            return ConversionResult(success=True, output_path=output_path, warnings=warnings)

        except Exception as e:
            return ConversionResult(success=False, error=f"MarkItDown conversion failed: {e}")
