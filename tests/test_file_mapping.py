"""Tests for file mapping utilities."""

import pytest

from xtomarkdown.config.defaults import DEFAULT_ENGINE_MAPPING, SUPPORTED_FORMATS
from xtomarkdown.core.file_mapping import (
    get_engine_for_format,
    get_fallback_engine,
    get_supported_extensions,
    is_supported_format,
    normalize_extension,
)


class TestNormalizeExtension:
    """Test extension normalization."""

    def test_lowercase_conversion(self):
        """Should convert extension to lowercase."""
        assert normalize_extension("DOCX") == "docx"
        assert normalize_extension("PDF") == "pdf"
        assert normalize_extension("DocX") == "docx"

    def test_strip_leading_dot(self):
        """Should strip leading dot."""
        assert normalize_extension(".docx") == "docx"
        assert normalize_extension(".PDF") == "pdf"

    def test_no_dot(self):
        """Should handle extension without dot."""
        assert normalize_extension("docx") == "docx"
        assert normalize_extension("pdf") == "pdf"

    def test_empty_string(self):
        """Should handle empty string."""
        assert normalize_extension("") == ""

    def test_dot_only(self):
        """Should handle dot only."""
        assert normalize_extension(".") == ""

    def test_multiple_dots(self):
        """lstrip strips ALL leading dots."""
        # Note: lstrip(".") removes all leading dots, not just one
        assert normalize_extension("..docx") == "docx"


class TestGetEngineForFormat:
    """Test default engine retrieval."""

    def test_docx_default_engine(self):
        """DOCX should default to pandoc."""
        assert get_engine_for_format("docx") == "pandoc"

    def test_xlsx_default_engine(self):
        """XLSX should default to markitdown."""
        assert get_engine_for_format("xlsx") == "markitdown"

    def test_pptx_default_engine(self):
        """PPTX should default to markitdown."""
        assert get_engine_for_format("pptx") == "markitdown"

    def test_pdf_default_engine(self):
        """PDF should default to pandoc."""
        assert get_engine_for_format("pdf") == "pandoc"

    def test_csv_default_engine(self):
        """CSV should default to markitdown."""
        assert get_engine_for_format("csv") == "markitdown"

    def test_normalizes_extension(self):
        """Should normalize extension before lookup."""
        assert get_engine_for_format(".DOCX") == "pandoc"
        assert get_engine_for_format("XLSX") == "markitdown"

    def test_unsupported_format_returns_none(self):
        """Should return None for unsupported formats."""
        assert get_engine_for_format("xyz") is None
        assert get_engine_for_format("unknown") is None

    def test_all_supported_formats_have_default(self):
        """All supported formats should have a default engine."""
        for fmt in SUPPORTED_FORMATS:
            engine = get_engine_for_format(fmt)
            assert engine is not None, f"Format {fmt} has no default engine"
            assert engine in ("pandoc", "markitdown"), f"Format {fmt} has unknown engine: {engine}"


class TestGetFallbackEngine:
    """Test fallback engine retrieval."""

    def test_docx_fallback_engine(self):
        """DOCX should fall back to markitdown."""
        assert get_fallback_engine("docx") == "markitdown"

    def test_pdf_fallback_engine(self):
        """PDF should fall back to markitdown."""
        assert get_fallback_engine("pdf") == "markitdown"

    def test_html_fallback_engine(self):
        """HTML should fall back to markitdown."""
        assert get_fallback_engine("html") == "markitdown"

    def test_rtf_no_fallback(self):
        """RTF should have no fallback (pandoc only)."""
        assert get_fallback_engine("rtf") is None

    def test_csv_no_fallback(self):
        """CSV should have no fallback (markitdown only)."""
        assert get_fallback_engine("csv") is None

    def test_json_no_fallback(self):
        """JSON should have no fallback (markitdown only)."""
        assert get_fallback_engine("json") is None

    def test_normalizes_extension(self):
        """Should normalize extension before lookup."""
        assert get_fallback_engine(".DOCX") == "markitdown"
        assert get_fallback_engine("PDF") == "markitdown"

    def test_unsupported_format_returns_none(self):
        """Should return None for unsupported formats."""
        assert get_fallback_engine("xyz") is None


class TestIsSupportedFormat:
    """Test format support checking."""

    def test_supported_formats(self):
        """Should recognize supported formats."""
        supported = ["docx", "doc", "xlsx", "xls", "pptx", "ppt", "pdf", "rtf",
                     "odt", "html", "htm", "epub", "csv", "json", "xml"]
        for fmt in supported:
            assert is_supported_format(fmt), f"{fmt} should be supported"

    def test_unsupported_formats(self):
        """Should reject unsupported formats."""
        unsupported = ["txt", "mp4", "avi", "exe", "zip", "tar"]
        for fmt in unsupported:
            assert not is_supported_format(fmt), f"{fmt} should not be supported"

    def test_normalizes_extension(self):
        """Should normalize extension before checking."""
        assert is_supported_format(".DOCX")
        assert is_supported_format("PDF")
        assert is_supported_format(".xlsx")

    def test_empty_string(self):
        """Empty string should not be supported."""
        assert not is_supported_format("")

    def test_all_default_mappings_supported(self):
        """All formats in default mapping should be supported."""
        for fmt in DEFAULT_ENGINE_MAPPING.keys():
            assert is_supported_format(fmt), f"{fmt} in mapping but not supported"


class TestGetSupportedExtensions:
    """Test supported extensions list."""

    def test_returns_list(self):
        """Should return a list."""
        extensions = get_supported_extensions()
        assert isinstance(extensions, list)

    def test_returns_sorted(self):
        """Should return sorted list."""
        extensions = get_supported_extensions()
        assert extensions == sorted(extensions)

    def test_no_duplicates(self):
        """Should have no duplicate extensions."""
        extensions = get_supported_extensions()
        assert len(extensions) == len(set(extensions))

    def test_no_dots(self):
        """Extensions should not have leading dots."""
        extensions = get_supported_extensions()
        for ext in extensions:
            assert not ext.startswith("."), f"Extension {ext} has leading dot"

    def test_lowercase(self):
        """Extensions should be lowercase."""
        extensions = get_supported_extensions()
        for ext in extensions:
            assert ext == ext.lower(), f"Extension {ext} is not lowercase"

    def test_contains_expected_formats(self):
        """Should contain expected formats."""
        extensions = get_supported_extensions()
        expected = ["docx", "pdf", "xlsx", "pptx", "html", "csv"]
        for fmt in expected:
            assert fmt in extensions, f"{fmt} not in supported extensions"

    def test_matches_supported_formats_set(self):
        """Should match SUPPORTED_FORMATS set."""
        extensions = get_supported_extensions()
        assert set(extensions) == SUPPORTED_FORMATS


class TestDefaultEngineMappingIntegrity:
    """Test the integrity of DEFAULT_ENGINE_MAPPING."""

    def test_mapping_structure(self):
        """Each mapping should be a tuple of (default, fallback)."""
        for ext, mapping in DEFAULT_ENGINE_MAPPING.items():
            assert isinstance(mapping, tuple), f"{ext} mapping is not a tuple"
            assert len(mapping) == 2, f"{ext} mapping doesn't have 2 elements"
            assert mapping[0] in ("pandoc", "markitdown"), f"{ext} has unknown default: {mapping[0]}"
            assert mapping[1] is None or mapping[1] in ("pandoc", "markitdown"), \
                f"{ext} has unknown fallback: {mapping[1]}"

    def test_fallback_differs_from_default(self):
        """When fallback exists, it should differ from default."""
        for ext, mapping in DEFAULT_ENGINE_MAPPING.items():
            if mapping[1] is not None:
                assert mapping[0] != mapping[1], \
                    f"{ext} has same default and fallback: {mapping[0]}"

    def test_office_formats_use_expected_engines(self):
        """Office formats should use expected engines by default."""
        # Documents favor pandoc (better structure)
        assert DEFAULT_ENGINE_MAPPING["docx"][0] == "pandoc"
        assert DEFAULT_ENGINE_MAPPING["pdf"][0] == "pandoc"
        # Spreadsheets and presentations favor markitdown
        assert DEFAULT_ENGINE_MAPPING["xlsx"][0] == "markitdown"
        assert DEFAULT_ENGINE_MAPPING["pptx"][0] == "markitdown"
