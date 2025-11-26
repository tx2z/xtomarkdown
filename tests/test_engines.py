"""Tests for the conversion engine implementations."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xtomarkdown.core.engines.base import BaseEngine, ConversionResult
from xtomarkdown.core.engines.markitdown import MarkItDownEngine
from xtomarkdown.core.engines.pandoc import PandocEngine


class TestConversionResult:
    """Test the ConversionResult dataclass."""

    def test_success_result(self):
        """Should create a success result."""
        result = ConversionResult(success=True, output_path=Path("/output.md"))
        assert result.success
        assert result.output_path == Path("/output.md")
        assert result.error is None
        assert result.warnings is None

    def test_failure_result(self):
        """Should create a failure result."""
        result = ConversionResult(success=False, error="Something went wrong")
        assert not result.success
        assert result.error == "Something went wrong"
        assert result.output_path is None

    def test_result_with_warnings(self):
        """Should store warnings."""
        result = ConversionResult(
            success=True,
            output_path=Path("/output.md"),
            warnings=["Warning 1", "Warning 2"]
        )
        assert result.warnings == ["Warning 1", "Warning 2"]


class TestBaseEngine:
    """Test the abstract BaseEngine class."""

    def test_supports_format_in_set(self):
        """supports_format should return True for formats in supported_formats."""
        # Create a concrete implementation for testing
        class TestEngine(BaseEngine):
            name = "test"
            display_name = "Test"
            supported_formats = {"docx", "pdf"}

            def is_available(self):
                return True

            def convert(self, input_path, output_path):
                return ConversionResult(success=True, output_path=output_path)

        engine = TestEngine()
        assert engine.supports_format("docx")
        assert engine.supports_format("pdf")
        assert not engine.supports_format("xlsx")

    def test_supports_format_normalizes(self):
        """supports_format should normalize extension."""
        class TestEngine(BaseEngine):
            name = "test"
            display_name = "Test"
            supported_formats = {"docx"}

            def is_available(self):
                return True

            def convert(self, input_path, output_path):
                return ConversionResult(success=True, output_path=output_path)

        engine = TestEngine()
        assert engine.supports_format(".DOCX")
        assert engine.supports_format("DOCX")
        assert engine.supports_format(".docx")

    def test_get_version_default(self):
        """Default get_version should return None."""
        class TestEngine(BaseEngine):
            name = "test"
            display_name = "Test"
            supported_formats = set()

            def is_available(self):
                return True

            def convert(self, input_path, output_path):
                return ConversionResult(success=True, output_path=output_path)

        engine = TestEngine()
        assert engine.get_version() is None


class TestPandocEngine:
    """Test the Pandoc engine implementation."""

    def test_class_attributes(self):
        """Should have correct class attributes."""
        assert PandocEngine.name == "pandoc"
        assert PandocEngine.display_name == "Pandoc"
        assert "docx" in PandocEngine.supported_formats
        assert "pdf" in PandocEngine.supported_formats

    def test_supported_formats(self):
        """Should support expected formats."""
        expected = {"docx", "doc", "pdf", "html", "htm", "rtf", "odt", "epub"}
        for fmt in expected:
            assert fmt in PandocEngine.supported_formats

    def test_lazy_load_pypandoc(self):
        """Should lazy load pypandoc module."""
        engine = PandocEngine()
        assert engine._pypandoc is None
        # After calling _get_pypandoc, it should be loaded (if available)
        engine._get_pypandoc()
        # Result depends on whether pypandoc is installed

    def test_is_available_without_pypandoc(self):
        """Should return False if pypandoc not installed."""
        engine = PandocEngine()
        with patch.object(engine, "_get_pypandoc", return_value=None):
            assert not engine.is_available()

    def test_is_available_with_pypandoc(self):
        """Should return True if pypandoc and pandoc are available."""
        engine = PandocEngine()
        mock_pypandoc = MagicMock()
        mock_pypandoc.get_pandoc_version.return_value = "3.0.0"
        with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
            assert engine.is_available()

    def test_is_available_pandoc_error(self):
        """Should return False if pandoc not installed."""
        engine = PandocEngine()
        mock_pypandoc = MagicMock()
        mock_pypandoc.get_pandoc_version.side_effect = Exception("Pandoc not found")
        with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
            assert not engine.is_available()

    def test_get_version_without_pypandoc(self):
        """Should return None if pypandoc not installed."""
        engine = PandocEngine()
        with patch.object(engine, "_get_pypandoc", return_value=None):
            assert engine.get_version() is None

    def test_get_version_with_pypandoc(self):
        """Should return version string."""
        engine = PandocEngine()
        mock_pypandoc = MagicMock()
        mock_pypandoc.get_pandoc_version.return_value = "3.1.2"
        with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
            version = engine.get_version()
            assert version == "3.1.2"

    def test_get_version_caches_result(self):
        """Should cache version after first call."""
        engine = PandocEngine()
        engine._version = "cached_version"
        # Should return cached version without calling pypandoc
        assert engine.get_version() == "cached_version"

    def test_convert_without_pypandoc(self):
        """Should return error if pypandoc not installed."""
        engine = PandocEngine()
        with patch.object(engine, "_get_pypandoc", return_value=None):
            result = engine.convert(Path("/input.docx"), Path("/output.md"))
            assert not result.success
            assert "not installed" in result.error.lower()

    def test_convert_without_pandoc(self):
        """Should return error if pandoc not available."""
        engine = PandocEngine()
        mock_pypandoc = MagicMock()
        mock_pypandoc.get_pandoc_version.side_effect = Exception("Not found")
        with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
            result = engine.convert(Path("/input.docx"), Path("/output.md"))
            assert not result.success
            assert "not available" in result.error.lower()

    def test_convert_creates_output_dir(self):
        """Should create output directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "subdir" / "output.md"

            engine = PandocEngine()
            mock_pypandoc = MagicMock()
            mock_pypandoc.get_pandoc_version.return_value = "3.0.0"
            mock_pypandoc.convert_file = MagicMock()

            with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
                engine.convert(input_file, output_file)
                # Should have created the subdir
                assert output_file.parent.exists()

    def test_convert_success(self):
        """Should return success result on successful conversion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"

            engine = PandocEngine()
            mock_pypandoc = MagicMock()
            mock_pypandoc.get_pandoc_version.return_value = "3.0.0"
            mock_pypandoc.convert_file = MagicMock()

            with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
                result = engine.convert(input_file, output_file)
                assert result.success
                assert result.output_path == output_file

    def test_convert_with_media_extraction(self):
        """Should report media extraction in warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"
            media_dir = Path(tmpdir) / "output_media"
            media_dir.mkdir()
            (media_dir / "image.png").touch()  # Simulate extracted media

            engine = PandocEngine()
            mock_pypandoc = MagicMock()
            mock_pypandoc.get_pandoc_version.return_value = "3.0.0"
            mock_pypandoc.convert_file = MagicMock()

            with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
                result = engine.convert(input_file, output_file)
                assert result.success
                if result.warnings:
                    assert any("media" in w.lower() for w in result.warnings)

    def test_convert_exception_handling(self):
        """Should handle conversion exceptions gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"

            engine = PandocEngine()
            mock_pypandoc = MagicMock()
            mock_pypandoc.get_pandoc_version.return_value = "3.0.0"
            mock_pypandoc.convert_file.side_effect = RuntimeError("Conversion failed")

            with patch.object(engine, "_get_pypandoc", return_value=mock_pypandoc):
                result = engine.convert(input_file, output_file)
                assert not result.success
                assert "failed" in result.error.lower()


class TestMarkItDownEngine:
    """Test the MarkItDown engine implementation."""

    def test_class_attributes(self):
        """Should have correct class attributes."""
        assert MarkItDownEngine.name == "markitdown"
        assert MarkItDownEngine.display_name == "MarkItDown"
        assert "docx" in MarkItDownEngine.supported_formats
        assert "xlsx" in MarkItDownEngine.supported_formats

    def test_supported_formats(self):
        """Should support expected formats."""
        expected = {"docx", "pdf", "pptx", "xlsx", "xls", "html", "csv", "json", "xml"}
        for fmt in expected:
            assert fmt in MarkItDownEngine.supported_formats

    def test_lazy_load_markitdown(self):
        """Should lazy load markitdown module."""
        engine = MarkItDownEngine()
        assert engine._markitdown is None
        # After calling _get_markitdown, it should be loaded (if available)
        engine._get_markitdown()

    def test_is_available_without_module(self):
        """Should return False if markitdown not installed."""
        engine = MarkItDownEngine()
        with patch.object(engine, "_get_markitdown", return_value=None):
            assert not engine.is_available()

    def test_is_available_with_module(self):
        """Should return True if markitdown is available."""
        engine = MarkItDownEngine()
        mock_markitdown = MagicMock()
        with patch.object(engine, "_get_markitdown", return_value=mock_markitdown):
            assert engine.is_available()

    def test_get_version_without_module(self):
        """Should return None if markitdown not installed."""
        engine = MarkItDownEngine()
        with patch.object(engine, "is_available", return_value=False):
            assert engine.get_version() is None

    def test_get_version_caches_result(self):
        """Should cache version after first call."""
        engine = MarkItDownEngine()
        engine._version = "0.1.0"
        assert engine.get_version() == "0.1.0"

    def test_convert_without_module(self):
        """Should return error if markitdown not installed."""
        engine = MarkItDownEngine()
        with patch.object(engine, "_get_md_instance", return_value=None):
            result = engine.convert(Path("/input.docx"), Path("/output.md"))
            assert not result.success
            assert "not installed" in result.error.lower()

    def test_convert_creates_output_dir(self):
        """Should create output directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "subdir" / "output.md"

            engine = MarkItDownEngine()
            mock_md = MagicMock()
            mock_result = MagicMock()
            mock_result.text_content = "# Test"
            mock_md.convert.return_value = mock_result

            with patch.object(engine, "_get_md_instance", return_value=mock_md):
                engine.convert(input_file, output_file)
                assert output_file.parent.exists()

    def test_convert_success(self):
        """Should return success result on successful conversion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"

            engine = MarkItDownEngine()
            mock_md = MagicMock()
            mock_result = MagicMock()
            mock_result.text_content = "# Converted Document\n\nContent here."
            mock_md.convert.return_value = mock_result

            with patch.object(engine, "_get_md_instance", return_value=mock_md):
                result = engine.convert(input_file, output_file)
                assert result.success
                assert result.output_path == output_file
                # Should have written the file
                assert output_file.read_text() == "# Converted Document\n\nContent here."

    def test_convert_with_embedded_images_warning(self):
        """Should warn about embedded images in docx/pptx."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"

            engine = MarkItDownEngine()
            mock_md = MagicMock()
            mock_result = MagicMock()
            mock_result.text_content = "# Doc\n\n![image](path/to/image.png)"  # Contains image
            mock_md.convert.return_value = mock_result

            with patch.object(engine, "_get_md_instance", return_value=mock_md):
                result = engine.convert(input_file, output_file)
                assert result.success
                assert result.warnings is not None
                assert any("image" in w.lower() for w in result.warnings)

    def test_convert_pptx_with_images_warning(self):
        """Should warn about embedded images in pptx."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.pptx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"

            engine = MarkItDownEngine()
            mock_md = MagicMock()
            mock_result = MagicMock()
            mock_result.text_content = "# Slide\n\n![chart](embedded)"
            mock_md.convert.return_value = mock_result

            with patch.object(engine, "_get_md_instance", return_value=mock_md):
                result = engine.convert(input_file, output_file)
                assert result.success
                if "![" in mock_result.text_content:
                    assert result.warnings is not None

    def test_convert_exception_handling(self):
        """Should handle conversion exceptions gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.docx"
            input_file.touch()
            output_file = Path(tmpdir) / "output.md"

            engine = MarkItDownEngine()
            mock_md = MagicMock()
            mock_md.convert.side_effect = RuntimeError("Conversion failed")

            with patch.object(engine, "_get_md_instance", return_value=mock_md):
                result = engine.convert(input_file, output_file)
                assert not result.success
                assert "failed" in result.error.lower()


class TestEngineComparison:
    """Compare behavior between engines."""

    def test_both_support_docx(self):
        """Both engines should support DOCX."""
        assert "docx" in PandocEngine.supported_formats
        assert "docx" in MarkItDownEngine.supported_formats

    def test_both_support_pdf(self):
        """Both engines should support PDF."""
        assert "pdf" in PandocEngine.supported_formats
        assert "pdf" in MarkItDownEngine.supported_formats

    def test_markitdown_has_more_spreadsheet_formats(self):
        """MarkItDown should support more spreadsheet formats."""
        assert "csv" in MarkItDownEngine.supported_formats
        assert "xlsx" in MarkItDownEngine.supported_formats
        assert "xls" in MarkItDownEngine.supported_formats

    def test_pandoc_has_more_document_formats(self):
        """Pandoc should support more document formats."""
        assert "rtf" in PandocEngine.supported_formats
        assert "odt" in PandocEngine.supported_formats
        assert "tex" in PandocEngine.supported_formats

    def test_engines_have_unique_names(self):
        """Engine names should be unique."""
        assert PandocEngine.name != MarkItDownEngine.name

    def test_engines_have_display_names(self):
        """Both engines should have display names."""
        assert PandocEngine.display_name
        assert MarkItDownEngine.display_name
