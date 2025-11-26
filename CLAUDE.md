# XtoMarkdown - Project Context

## Overview

XtoMarkdown is a cross-platform GUI application for converting documents (DOCX, PDF, PPTX, etc.) to Markdown. It uses Python with PySide6 for the GUI and supports two conversion engines: Pandoc and MarkItDown.

## Technology Stack

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python)
- **Conversion Engines**:
  - `pypandoc-binary` - Bundles Pandoc for document conversion
  - `markitdown` - Microsoft's document to Markdown library
- **Config Storage**: `platformdirs` for cross-platform config paths
- **Packaging**: PyInstaller for standalone executables

## Project Structure

```
src/xtomarkdown/
├── app.py                 # Main entry point, QApplication setup
├── __main__.py            # Module runner
├── config/
│   ├── settings.py        # Settings model with JSON persistence
│   └── defaults.py        # Default engine mappings, format lists
├── core/
│   ├── converter.py       # Main conversion facade
│   ├── file_mapping.py    # Format to engine mapping utilities
│   └── engines/
│       ├── base.py        # Abstract BaseEngine class
│       ├── pandoc.py      # Pandoc engine implementation
│       ├── markitdown.py  # MarkItDown engine implementation
│       └── registry.py    # Engine discovery and selection
└── gui/
    ├── main_window.py     # Main application window
    ├── drop_zone.py       # Drag-and-drop file input widget
    ├── file_list.py       # File queue widget with engine selection
    ├── preferences.py     # Preferences dialog
    └── resources/
        └── style.qss      # Qt stylesheet
```

## Key Design Decisions

### Engine Selection Logic
1. User override (from settings) takes priority
2. Default engine from `DEFAULT_ENGINE_MAPPING` in `config/defaults.py`
3. Fallback engine if default is unavailable
4. Any available engine that supports the format

### Default Engine Mapping
- **Pandoc**: DOCX, PDF, HTML, RTF, ODT, EPUB (better image extraction, structure)
- **MarkItDown**: PPTX, XLSX, CSV, JSON, XML (native Python support)

### Settings Storage
- Linux: `~/.config/xtomarkdown/settings.json`
- macOS: `~/Library/Application Support/xtomarkdown/settings.json`
- Windows: `%LOCALAPPDATA%\xtomarkdown\settings.json`

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the application
python -m xtomarkdown

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/xtomarkdown --cov-report=html

# Lint code (check for issues)
ruff check src/

# Lint and auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/

# Type check
mypy src/

# Setup pre-commit hooks (run once after clone)
pre-commit install

# Run all pre-commit checks manually
pre-commit run --all-files

# Build standalone executable
pyinstaller --onefile --windowed src/xtomarkdown/app.py --name xtomarkdown
```

## Code Conventions

- Type hints used throughout (Python 3.10+ syntax)
- PySide6 signals/slots for GUI communication
- Dataclasses for data structures (Settings, ConversionResult)
- Abstract base class pattern for engines
- Lazy loading for optional dependencies (pypandoc, markitdown)

## Adding New Engines

1. Create a new file in `core/engines/` (e.g., `new_engine.py`)
2. Inherit from `BaseEngine` and implement:
   - `name`, `display_name`, `supported_formats` class attributes
   - `is_available()` method
   - `convert(input_path, output_path)` method
3. Register in `registry.py` `_register_default_engines()`
4. Add format mappings in `config/defaults.py`

## Adding New Formats

1. Add extension to `DEFAULT_ENGINE_MAPPING` in `config/defaults.py`
2. Add display name to `FORMAT_DISPLAY_NAMES`
3. Update `FILE_FILTER` string for file dialogs
4. Ensure at least one engine supports it in `supported_formats`
