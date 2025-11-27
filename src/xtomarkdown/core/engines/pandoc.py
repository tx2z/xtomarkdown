"""Pandoc conversion engine implementation."""

import os
import sys
from pathlib import Path
from typing import ClassVar

from .base import BaseEngine, ConversionResult


def _get_bundled_pandoc_path() -> str | None:
    """Get the path to bundled pandoc binary in PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]

        # Check multiple possible locations
        # PyInstaller windowed apps on macOS put binaries in Frameworks
        possible_paths = [
            base_path / "pandoc",  # Standard location
            base_path / ".." / "Frameworks" / "pandoc",  # macOS app bundle
        ]

        for pandoc_path in possible_paths:
            pandoc_path = pandoc_path.resolve()
            if pandoc_path.exists():
                return str(pandoc_path)
    return None


class PandocEngine(BaseEngine):
    """Conversion engine using Pandoc via pypandoc."""

    name: ClassVar[str] = "pandoc"
    display_name: ClassVar[str] = "Pandoc"
    supported_formats: ClassVar[set[str]] = {
        "docx",
        "doc",
        "pdf",
        "html",
        "htm",
        "rtf",
        "odt",
        "epub",
        "pptx",
        "xlsx",
        "tex",
        "latex",
        "rst",
        "org",
    }

    def __init__(self):
        self._pypandoc = None
        self._version: str | None = None
        self._configure_bundled_pandoc()

    def _configure_bundled_pandoc(self):
        """Configure pypandoc to use bundled pandoc if available."""
        bundled_path = _get_bundled_pandoc_path()
        if bundled_path:
            # Set environment variable that pypandoc checks
            os.environ["PYPANDOC_PANDOC"] = bundled_path

    def _get_pypandoc(self):
        """Lazy load pypandoc module."""
        if self._pypandoc is None:
            try:
                import pypandoc

                self._pypandoc = pypandoc
            except ImportError:
                pass
        return self._pypandoc

    def is_available(self) -> bool:
        """Check if Pandoc is available via pypandoc."""
        pypandoc = self._get_pypandoc()
        if pypandoc is None:
            return False
        try:
            pypandoc.get_pandoc_version()
            return True
        except Exception:
            return False

    def get_version(self) -> str | None:
        """Get the Pandoc version string."""
        if self._version is not None:
            return self._version

        pypandoc = self._get_pypandoc()
        if pypandoc is None:
            return None

        try:
            self._version = pypandoc.get_pandoc_version()
            return self._version
        except Exception:
            return None

    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        """Convert a document to Markdown using Pandoc."""
        pypandoc = self._get_pypandoc()
        if pypandoc is None:
            return ConversionResult(success=False, error="pypandoc is not installed")

        if not self.is_available():
            return ConversionResult(success=False, error="Pandoc is not available")

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create media directory for extracted images
            media_dir = output_path.parent / f"{output_path.stem}_media"

            # Build extra arguments for pandoc
            extra_args = [
                "--wrap=none",  # Don't wrap lines
                f"--extract-media={media_dir}",  # Extract images
            ]

            # Convert the file
            pypandoc.convert_file(
                str(input_path),
                "gfm",  # GitHub Flavored Markdown
                outputfile=str(output_path),
                extra_args=extra_args,
            )

            # Check if media was extracted
            warnings = []
            if media_dir.exists() and any(media_dir.iterdir()):
                warnings.append(f"Media files extracted to: {media_dir}")

            return ConversionResult(
                success=True, output_path=output_path, warnings=warnings if warnings else None
            )

        except Exception as e:
            return ConversionResult(success=False, error=f"Pandoc conversion failed: {e}")
