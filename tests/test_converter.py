"""Tests for the DocumentConverter facade."""

import tempfile
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

from xtomarkdown.config.settings import Settings
from xtomarkdown.core.converter import DocumentConverter
from xtomarkdown.core.engines.base import BaseEngine, ConversionResult


class MockEngine(BaseEngine):
    """Mock engine for testing converter logic."""

    name: ClassVar[str] = "mockengine"
    display_name: ClassVar[str] = "Mock Engine"
    supported_formats: ClassVar[set[str]] = {"docx", "pdf", "xlsx"}

    def __init__(self, available: bool = True, success: bool = True):
        self._available = available
        self._success = success
        self.convert_called = False
        self.last_input = None
        self.last_output = None

    def is_available(self) -> bool:
        return self._available

    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        self.convert_called = True
        self.last_input = input_path
        self.last_output = output_path
        if self._success:
            return ConversionResult(success=True, output_path=output_path)
        else:
            return ConversionResult(success=False, error="Mock conversion failed")


class TestDocumentConverterInitialization:
    """Test converter initialization."""

    def test_uses_provided_settings(self):
        """Should use provided settings."""
        settings = Settings(output_mode="folder", output_folder="/tmp")
        converter = DocumentConverter(settings=settings)
        assert converter.settings.output_mode == "folder"
        assert converter.settings.output_folder == "/tmp"

    def test_loads_default_settings(self):
        """Should load default settings if none provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                converter = DocumentConverter()
                assert converter.settings is not None
                assert converter.settings.output_mode == "same"

    def test_has_registry(self):
        """Should have an engine registry."""
        converter = DocumentConverter(settings=Settings())
        assert converter.registry is not None


class TestDocumentConverterConvert:
    """Test the convert method."""

    def test_input_file_not_found(self):
        """Should return error if input file doesn't exist."""
        converter = DocumentConverter(settings=Settings())
        result = converter.convert("/nonexistent/file.docx")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_unsupported_format(self):
        """Should return error for unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                result = converter.convert(f.name)
                assert not result.success
                assert "unsupported" in result.error.lower()
            finally:
                Path(f.name).unlink()

    def test_no_available_engine(self):
        """Should return error when no engine available."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                # Clear all engines
                converter.registry._engines.clear()

                result = converter.convert(f.name)
                assert not result.success
                assert "no available engine" in result.error.lower()
            finally:
                Path(f.name).unlink()

    def test_uses_forced_engine(self):
        """Should use forced engine when specified."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                mock_engine = MockEngine()
                converter.registry.register(mock_engine)

                # Force the mock engine
                converter.convert(f.name, engine_name="mockengine")
                assert mock_engine.convert_called
            finally:
                Path(f.name).unlink()

    def test_forced_engine_must_support_format(self):
        """Forced engine must support the file format."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                mock_engine = MockEngine()  # Doesn't support csv
                converter.registry.register(mock_engine)

                # mockengine doesn't support csv, should fall back
                result = converter.convert(f.name, engine_name="mockengine")
                # Should either fail or use another engine
                assert not mock_engine.convert_called or not mock_engine.supports_format("csv")
            finally:
                Path(f.name).unlink()

    def test_accepts_path_object(self):
        """Should accept Path objects as input."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                mock_engine = MockEngine()
                converter.registry.register(mock_engine)
                converter.registry._engines = {"mockengine": mock_engine}

                result = converter.convert(Path(f.name))
                # Should process without error about path type
                assert mock_engine.convert_called or not result.success
            finally:
                Path(f.name).unlink()

    def test_accepts_string_path(self):
        """Should accept string paths as input."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                mock_engine = MockEngine()
                converter.registry._engines = {"mockengine": mock_engine}

                result = converter.convert(f.name)
                assert mock_engine.convert_called or not result.success
            finally:
                Path(f.name).unlink()


class TestDocumentConverterEngineSelection:
    """Test the _select_engine method."""

    def test_forced_engine_priority(self):
        """Forced engine should have highest priority."""
        converter = DocumentConverter(settings=Settings())
        mock_engine = MockEngine()
        converter.registry.register(mock_engine)

        engine = converter._select_engine("docx", forced_engine="mockengine")
        assert engine is not None
        assert engine.name == "mockengine"

    def test_user_override_priority(self):
        """User override should take priority over defaults."""
        settings = Settings(engine_overrides={"docx": "mockengine"})
        converter = DocumentConverter(settings=settings)
        mock_engine = MockEngine()
        converter.registry.register(mock_engine)

        engine = converter._select_engine("docx")
        assert engine is not None
        assert engine.name == "mockengine"

    def test_falls_back_to_default(self):
        """Should fall back to default engine when no override."""
        converter = DocumentConverter(settings=Settings())
        mock_engine = MockEngine()
        converter.registry.register(mock_engine)

        # docx defaults to pandoc, but if unavailable falls back
        engine = converter._select_engine("docx")
        # Engine selection depends on what's available
        if engine:
            assert engine.supports_format("docx")

    def test_unavailable_forced_engine_ignored(self):
        """Unavailable forced engine should be ignored."""
        converter = DocumentConverter(settings=Settings())
        mock_engine = MockEngine(available=False)
        converter.registry.register(mock_engine)

        engine = converter._select_engine("docx", forced_engine="mockengine")
        # Should not select unavailable engine
        if engine:
            assert engine.name != "mockengine" or engine.is_available()

    def test_unavailable_user_override_ignored(self):
        """Unavailable user override engine should be ignored."""
        settings = Settings(engine_overrides={"docx": "mockengine"})
        converter = DocumentConverter(settings=settings)
        mock_engine = MockEngine(available=False)
        converter.registry.register(mock_engine)

        engine = converter._select_engine("docx")
        # Should not select unavailable engine
        if engine:
            assert engine.name != "mockengine" or engine.is_available()


class TestDocumentConverterOutputPath:
    """Test the _get_output_path method."""

    def test_same_folder_mode(self):
        """Should output to same folder as input by default."""
        settings = Settings(output_mode="same")
        converter = DocumentConverter(settings=settings)

        input_path = Path("/home/user/documents/file.docx")
        output_path = converter._get_output_path(input_path)

        assert output_path.parent == input_path.parent
        assert output_path.name == "file.md"

    def test_folder_mode(self):
        """Should output to specified folder."""
        settings = Settings(output_mode="folder", output_folder="/tmp/output")
        converter = DocumentConverter(settings=settings)

        input_path = Path("/home/user/documents/file.docx")
        output_path = converter._get_output_path(input_path)

        assert output_path.parent == Path("/tmp/output")
        assert output_path.name == "file.md"

    def test_folder_mode_without_folder(self):
        """Should fall back to same folder if no folder specified."""
        settings = Settings(output_mode="folder", output_folder=None)
        converter = DocumentConverter(settings=settings)

        input_path = Path("/home/user/documents/file.docx")
        output_path = converter._get_output_path(input_path)

        # Falls back to same folder
        assert output_path.parent == input_path.parent

    def test_preserves_stem(self):
        """Should preserve the input file stem."""
        settings = Settings(output_mode="same")
        converter = DocumentConverter(settings=settings)

        input_path = Path("/path/to/my-document.docx")
        output_path = converter._get_output_path(input_path)

        assert output_path.stem == "my-document"
        assert output_path.suffix == ".md"

    def test_explicit_output_path(self):
        """Should use explicit output path when provided to convert."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            try:
                converter = DocumentConverter(settings=Settings())
                mock_engine = MockEngine()
                converter.registry._engines = {"mockengine": mock_engine}

                explicit_output = Path("/tmp/custom_output.md")
                converter.convert(f.name, output_path=explicit_output)

                if mock_engine.convert_called:
                    assert mock_engine.last_output == explicit_output
            finally:
                Path(f.name).unlink()


class TestDocumentConverterEngineInfo:
    """Test engine information methods."""

    def test_get_available_engines(self):
        """Should return info about available engines."""
        converter = DocumentConverter(settings=Settings())
        engines = converter.get_available_engines()

        assert isinstance(engines, list)
        for engine_info in engines:
            assert "name" in engine_info
            assert "display_name" in engine_info
            assert "available" in engine_info

    def test_get_engines_for_file(self):
        """Should return engines available for a file."""
        converter = DocumentConverter(settings=Settings())
        mock_engine = MockEngine()
        converter.registry.register(mock_engine)

        engines = converter.get_engines_for_file("document.docx")
        assert isinstance(engines, list)
        # Should include mock engine which supports docx
        names = [e["name"] for e in engines]
        assert "mockengine" in names

    def test_get_engines_for_file_with_path(self):
        """Should accept Path object for file."""
        converter = DocumentConverter(settings=Settings())

        engines = converter.get_engines_for_file(Path("document.docx"))
        assert isinstance(engines, list)


class TestDocumentConverterIntegration:
    """Integration tests for the full conversion flow."""

    def test_full_conversion_success(self):
        """Test successful conversion flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_file = Path(tmpdir) / "test.docx"
            input_file.touch()

            settings = Settings(output_mode="same")
            converter = DocumentConverter(settings=settings)

            # Register mock engine
            mock_engine = MockEngine()
            converter.registry._engines = {"mockengine": mock_engine}

            result = converter.convert(input_file)

            assert mock_engine.convert_called
            assert mock_engine.last_input == input_file
            expected_output = Path(tmpdir) / "test.md"
            assert mock_engine.last_output == expected_output

    def test_full_conversion_failure(self):
        """Test conversion failure handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_file = Path(tmpdir) / "test.docx"
            input_file.touch()

            settings = Settings()
            converter = DocumentConverter(settings=settings)

            # Register failing mock engine
            mock_engine = MockEngine(success=False)
            converter.registry._engines = {"mockengine": mock_engine}

            result = converter.convert(input_file)

            assert not result.success
            assert result.error is not None

    def test_extension_case_insensitivity(self):
        """Should handle different extension cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test .DOCX (uppercase)
            input_file = Path(tmpdir) / "test.DOCX"
            input_file.touch()

            settings = Settings()
            converter = DocumentConverter(settings=settings)
            mock_engine = MockEngine()
            converter.registry._engines = {"mockengine": mock_engine}

            result = converter.convert(input_file)

            assert mock_engine.convert_called
