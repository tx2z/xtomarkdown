"""Default configuration values."""

# Default engine for each file format
# Format: extension -> (default_engine, fallback_engine or None)
DEFAULT_ENGINE_MAPPING: dict[str, tuple[str, str | None]] = {
    # Office documents
    "docx": ("pandoc", "markitdown"),
    "doc": ("pandoc", None),
    "xlsx": ("markitdown", "pandoc"),
    "xls": ("markitdown", None),
    "pptx": ("markitdown", "pandoc"),
    "ppt": ("markitdown", None),
    # PDF
    "pdf": ("pandoc", "markitdown"),
    # Rich text
    "rtf": ("pandoc", None),
    "odt": ("pandoc", None),
    # Web
    "html": ("pandoc", "markitdown"),
    "htm": ("pandoc", "markitdown"),
    # eBooks
    "epub": ("pandoc", "markitdown"),
    # Data formats
    "csv": ("markitdown", None),
    "json": ("markitdown", None),
    "xml": ("markitdown", None),
}

# All supported file extensions
SUPPORTED_FORMATS: set[str] = set(DEFAULT_ENGINE_MAPPING.keys())

# File filter string for Qt file dialogs
FILE_FILTER = "Documents (*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf *.rtf *.odt *.html *.htm *.epub *.csv *.json *.xml);;All Files (*)"

# Display names for engines
ENGINE_DISPLAY_NAMES: dict[str, str] = {
    "pandoc": "Pandoc",
    "markitdown": "MarkItDown",
}

# Format display names
FORMAT_DISPLAY_NAMES: dict[str, str] = {
    "docx": "Word Document",
    "doc": "Word Document (Legacy)",
    "xlsx": "Excel Spreadsheet",
    "xls": "Excel Spreadsheet (Legacy)",
    "pptx": "PowerPoint Presentation",
    "ppt": "PowerPoint (Legacy)",
    "pdf": "PDF Document",
    "rtf": "Rich Text Format",
    "odt": "OpenDocument Text",
    "html": "HTML Document",
    "htm": "HTML Document",
    "epub": "EPUB eBook",
    "csv": "CSV Data",
    "json": "JSON Data",
    "xml": "XML Data",
}
