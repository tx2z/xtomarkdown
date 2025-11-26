"""Engine registry for discovering and managing conversion engines."""

from ..file_mapping import get_engine_for_format, get_fallback_engine, normalize_extension
from .base import BaseEngine
from .markitdown import MarkItDownEngine
from .pandoc import PandocEngine


class EngineRegistry:
    """Registry for all available conversion engines."""

    def __init__(self):
        self._engines: dict[str, BaseEngine] = {}
        self._register_default_engines()

    def _register_default_engines(self) -> None:
        """Register the built-in engines."""
        self.register(PandocEngine())
        self.register(MarkItDownEngine())

    def register(self, engine: BaseEngine) -> None:
        """Register a conversion engine."""
        self._engines[engine.name] = engine

    def get(self, name: str) -> BaseEngine | None:
        """Get an engine by name."""
        return self._engines.get(name)

    def get_available(self) -> list[BaseEngine]:
        """Get all available (installed) engines."""
        return [e for e in self._engines.values() if e.is_available()]

    def get_all(self) -> list[BaseEngine]:
        """Get all registered engines."""
        return list(self._engines.values())

    def get_for_extension(self, ext: str) -> BaseEngine | None:
        """
        Get the best available engine for a file extension.

        Uses the default mapping, falling back if the primary engine
        is unavailable.
        """
        ext = normalize_extension(ext)

        # Try the default engine
        default_engine_name = get_engine_for_format(ext)
        if default_engine_name:
            engine = self.get(default_engine_name)
            if engine and engine.is_available() and engine.supports_format(ext):
                return engine

        # Try the fallback engine
        fallback_name = get_fallback_engine(ext)
        if fallback_name:
            engine = self.get(fallback_name)
            if engine and engine.is_available() and engine.supports_format(ext):
                return engine

        # Last resort: find any engine that supports this format
        for engine in self.get_available():
            if engine.supports_format(ext):
                return engine

        return None

    def get_engines_for_extension(self, ext: str) -> list[BaseEngine]:
        """Get all available engines that support a file extension."""
        ext = normalize_extension(ext)
        return [engine for engine in self.get_available() if engine.supports_format(ext)]

    def get_fallback_for(self, ext: str) -> BaseEngine | None:
        """Get the fallback engine for an extension."""
        ext = normalize_extension(ext)
        fallback_name = get_fallback_engine(ext)
        if fallback_name:
            engine = self.get(fallback_name)
            if engine and engine.is_available():
                return engine
        return None
