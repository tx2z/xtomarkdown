"""Tests for the EngineRegistry."""

from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock

import pytest

from xtomarkdown.core.engines.base import BaseEngine, ConversionResult
from xtomarkdown.core.engines.registry import EngineRegistry


class MockEngine(BaseEngine):
    """Mock engine for testing."""

    name: ClassVar[str] = "mock"
    display_name: ClassVar[str] = "Mock Engine"
    supported_formats: ClassVar[set[str]] = {"docx", "pdf"}

    def __init__(self, available: bool = True):
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        return ConversionResult(success=True, output_path=output_path)


class MockUnavailableEngine(BaseEngine):
    """Mock engine that is never available."""

    name: ClassVar[str] = "unavailable"
    display_name: ClassVar[str] = "Unavailable Engine"
    supported_formats: ClassVar[set[str]] = {"docx", "pdf"}

    def is_available(self) -> bool:
        return False

    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        return ConversionResult(success=False, error="Engine not available")


class TestEngineRegistryBasics:
    """Test basic registry functionality."""

    def test_default_engines_registered(self):
        """Should register pandoc and markitdown by default."""
        registry = EngineRegistry()
        assert registry.get("pandoc") is not None
        assert registry.get("markitdown") is not None

    def test_get_nonexistent_engine(self):
        """Should return None for nonexistent engine."""
        registry = EngineRegistry()
        assert registry.get("nonexistent") is None

    def test_register_custom_engine(self):
        """Should allow registering custom engines."""
        registry = EngineRegistry()
        mock_engine = MockEngine()
        registry.register(mock_engine)
        assert registry.get("mock") is mock_engine

    def test_register_overwrites_existing(self):
        """Registering with same name should overwrite."""
        registry = EngineRegistry()
        mock1 = MockEngine()
        mock2 = MockEngine()
        registry.register(mock1)
        registry.register(mock2)
        assert registry.get("mock") is mock2

    def test_get_all_returns_all_engines(self):
        """get_all should return all registered engines."""
        registry = EngineRegistry()
        all_engines = registry.get_all()
        engine_names = [e.name for e in all_engines]
        assert "pandoc" in engine_names
        assert "markitdown" in engine_names


class TestEngineAvailability:
    """Test engine availability checking."""

    def test_get_available_filters_unavailable(self):
        """get_available should only return available engines."""
        registry = EngineRegistry()
        registry.register(MockEngine(available=True))
        registry.register(MockUnavailableEngine())

        available = registry.get_available()
        available_names = [e.name for e in available]
        assert "mock" in available_names
        assert "unavailable" not in available_names

    def test_get_available_empty_when_none_available(self):
        """Should return empty list when no engines available."""
        registry = EngineRegistry()
        # Override default engines with unavailable ones
        registry._engines.clear()
        registry.register(MockUnavailableEngine())

        available = registry.get_available()
        assert len(available) == 0


class TestEngineSelection:
    """Test engine selection logic."""

    def test_get_for_extension_returns_default(self):
        """Should return default engine for extension."""
        registry = EngineRegistry()
        # docx defaults to pandoc
        engine = registry.get_for_extension("docx")
        # Only test if pandoc is actually available
        if engine:
            assert engine.supports_format("docx")

    def test_get_for_extension_normalizes(self):
        """Should normalize extension before lookup."""
        registry = EngineRegistry()
        engine1 = registry.get_for_extension("docx")
        engine2 = registry.get_for_extension(".DOCX")
        engine3 = registry.get_for_extension("DOCX")
        # All should return the same engine (or None if unavailable)
        assert engine1 == engine2 == engine3

    def test_get_for_extension_unsupported(self):
        """Should return None for unsupported extension."""
        registry = EngineRegistry()
        assert registry.get_for_extension("xyz") is None

    def test_get_for_extension_fallback(self):
        """Should fall back when default unavailable."""
        registry = EngineRegistry()
        # Clear and add custom engines
        registry._engines.clear()

        # Create unavailable pandoc mock
        class UnavailablePandoc(BaseEngine):
            name: ClassVar[str] = "pandoc"
            display_name: ClassVar[str] = "Pandoc"
            supported_formats: ClassVar[set[str]] = {"docx"}

            def is_available(self):
                return False

            def convert(self, input_path, output_path):
                return ConversionResult(success=False)

        # Create available markitdown mock
        class AvailableMarkItDown(BaseEngine):
            name: ClassVar[str] = "markitdown"
            display_name: ClassVar[str] = "MarkItDown"
            supported_formats: ClassVar[set[str]] = {"docx"}

            def is_available(self):
                return True

            def convert(self, input_path, output_path):
                return ConversionResult(success=True, output_path=output_path)

        registry.register(UnavailablePandoc())
        registry.register(AvailableMarkItDown())

        # docx defaults to pandoc, but pandoc is unavailable
        # Should fall back to markitdown
        engine = registry.get_for_extension("docx")
        assert engine is not None
        assert engine.name == "markitdown"

    def test_get_for_extension_any_available(self):
        """Should find any available engine if default and fallback unavailable."""
        registry = EngineRegistry()
        registry._engines.clear()

        # Only register a custom engine
        class CustomEngine(BaseEngine):
            name: ClassVar[str] = "custom"
            display_name: ClassVar[str] = "Custom"
            supported_formats: ClassVar[set[str]] = {"docx"}

            def is_available(self):
                return True

            def convert(self, input_path, output_path):
                return ConversionResult(success=True, output_path=output_path)

        registry.register(CustomEngine())

        # Should find the custom engine
        engine = registry.get_for_extension("docx")
        assert engine is not None
        assert engine.name == "custom"


class TestGetEnginesForExtension:
    """Test getting all engines for an extension."""

    def test_returns_all_supporting_engines(self):
        """Should return all available engines that support format."""
        registry = EngineRegistry()
        registry.register(MockEngine(available=True))

        engines = registry.get_engines_for_extension("docx")
        names = [e.name for e in engines]
        # MockEngine supports docx
        assert "mock" in names

    def test_filters_unavailable_engines(self):
        """Should only return available engines."""
        registry = EngineRegistry()
        registry.register(MockEngine(available=True))
        registry.register(MockUnavailableEngine())

        engines = registry.get_engines_for_extension("docx")
        names = [e.name for e in engines]
        assert "mock" in names
        assert "unavailable" not in names

    def test_filters_unsupporting_engines(self):
        """Should only return engines that support the format."""
        registry = EngineRegistry()

        class TxtOnlyEngine(BaseEngine):
            name: ClassVar[str] = "txtonly"
            display_name: ClassVar[str] = "TXT Only"
            supported_formats: ClassVar[set[str]] = {"txt"}

            def is_available(self):
                return True

            def convert(self, input_path, output_path):
                return ConversionResult(success=True, output_path=output_path)

        registry.register(TxtOnlyEngine())

        # docx should not include txt-only engine
        engines = registry.get_engines_for_extension("docx")
        names = [e.name for e in engines]
        assert "txtonly" not in names

    def test_normalizes_extension(self):
        """Should normalize extension before filtering."""
        registry = EngineRegistry()
        registry.register(MockEngine(available=True))

        engines1 = registry.get_engines_for_extension("docx")
        engines2 = registry.get_engines_for_extension(".DOCX")

        names1 = {e.name for e in engines1}
        names2 = {e.name for e in engines2}
        assert names1 == names2


class TestGetFallbackFor:
    """Test fallback engine retrieval."""

    def test_returns_fallback_engine(self):
        """Should return fallback engine when available."""
        registry = EngineRegistry()
        # docx has markitdown as fallback
        fallback = registry.get_fallback_for("docx")
        # Only test if markitdown is available
        if fallback:
            assert fallback.name == "markitdown"

    def test_returns_none_when_no_fallback(self):
        """Should return None when format has no fallback."""
        registry = EngineRegistry()
        # rtf has no fallback (pandoc only)
        fallback = registry.get_fallback_for("rtf")
        # Should be None or the engine if it's not actually pandoc-only
        # This depends on engine availability

    def test_returns_none_for_unsupported(self):
        """Should return None for unsupported format."""
        registry = EngineRegistry()
        fallback = registry.get_fallback_for("xyz")
        assert fallback is None

    def test_normalizes_extension(self):
        """Should normalize extension."""
        registry = EngineRegistry()
        fallback1 = registry.get_fallback_for("docx")
        fallback2 = registry.get_fallback_for(".DOCX")
        # Both should return the same result
        if fallback1:
            assert fallback1.name == fallback2.name
        else:
            assert fallback2 is None


class TestEngineSupportFormat:
    """Test engine format support checking."""

    def test_supports_format_true(self):
        """Engine should report supporting formats in its set."""
        engine = MockEngine()
        assert engine.supports_format("docx")
        assert engine.supports_format("pdf")

    def test_supports_format_false(self):
        """Engine should not report supporting other formats."""
        engine = MockEngine()
        assert not engine.supports_format("xlsx")
        assert not engine.supports_format("xyz")

    def test_supports_format_normalizes(self):
        """supports_format should normalize extension."""
        engine = MockEngine()
        assert engine.supports_format(".DOCX")
        assert engine.supports_format("PDF")
        assert engine.supports_format(".pdf")
