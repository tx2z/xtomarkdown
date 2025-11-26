"""Main document converter facade."""

from pathlib import Path

from ..config import Settings
from .engines import ConversionResult, EngineRegistry
from .file_mapping import is_supported_format


class DocumentConverter:
    """
    Main facade for document conversion.

    Handles engine selection based on user preferences and defaults,
    and coordinates the conversion process.
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize the converter.

        Args:
            settings: Application settings (uses defaults if not provided)
        """
        self.settings = settings or Settings.load()
        self.registry = EngineRegistry()

    def convert(
        self,
        input_path: Path | str,
        output_path: Path | str | None = None,
        engine_name: str | None = None,
    ) -> ConversionResult:
        """
        Convert a document to Markdown.

        Args:
            input_path: Path to the input document
            output_path: Path for output (defaults to same name with .md)
            engine_name: Force a specific engine (overrides user settings)

        Returns:
            ConversionResult with success status and output path
        """
        input_path = Path(input_path)

        # Validate input file
        if not input_path.exists():
            return ConversionResult(success=False, error=f"Input file not found: {input_path}")

        ext = input_path.suffix.lower().lstrip(".")
        if not is_supported_format(ext):
            return ConversionResult(success=False, error=f"Unsupported file format: .{ext}")

        # Determine output path
        if output_path is None:
            output_path = self._get_output_path(input_path)
        else:
            output_path = Path(output_path)

        # Select engine
        engine = self._select_engine(ext, engine_name)
        if engine is None:
            return ConversionResult(success=False, error=f"No available engine for .{ext} files")

        # Perform conversion
        result: ConversionResult = engine.convert(input_path, output_path)
        return result

    def _select_engine(self, ext: str, forced_engine: str | None = None):
        """
        Select the best engine for a file extension.

        Priority:
        1. Forced engine (if specified and available)
        2. User override from settings
        3. Default engine from mapping
        4. Fallback engine
        """
        # Check forced engine
        if forced_engine:
            engine = self.registry.get(forced_engine)
            if engine and engine.is_available() and engine.supports_format(ext):
                return engine

        # Check user override
        user_engine = self.settings.get_engine_for_extension(ext)
        if user_engine:
            engine = self.registry.get(user_engine)
            if engine and engine.is_available() and engine.supports_format(ext):
                return engine

        # Use default/fallback from registry
        return self.registry.get_for_extension(ext)

    def _get_output_path(self, input_path: Path) -> Path:
        """
        Determine the output path based on settings.

        Note: For "ask" mode, the GUI should prompt before calling convert().
        This method handles "same" and "folder" modes.
        """
        output_name = input_path.stem + ".md"

        if self.settings.output_mode == "folder" and self.settings.output_folder:
            return Path(self.settings.output_folder) / output_name

        # Default: same folder as input
        return input_path.parent / output_name

    def get_available_engines(self) -> list[dict]:
        """Get information about all available engines."""
        return [
            {
                "name": engine.name,
                "display_name": engine.display_name,
                "version": engine.get_version(),
                "available": engine.is_available(),
            }
            for engine in self.registry.get_all()
        ]

    def get_engines_for_file(self, file_path: Path | str) -> list[dict]:
        """Get available engines for a specific file."""
        ext = Path(file_path).suffix.lower().lstrip(".")
        engines = self.registry.get_engines_for_extension(ext)
        return [
            {
                "name": engine.name,
                "display_name": engine.display_name,
            }
            for engine in engines
        ]
