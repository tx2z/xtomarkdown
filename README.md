# XtoMarkdown

A cross-platform GUI application for converting documents to Markdown.

## Features

- **Drag & Drop**: Simply drag files into the application
- **Multiple Formats**: Supports DOCX, PDF, PPTX, XLSX, HTML, and more
- **Two Engines**: Uses Pandoc and MarkItDown for best results per format
- **Smart Defaults**: Automatically selects the best engine for each file type
- **Customizable**: Override engine selection per file type in preferences
- **Cross-Platform**: Works on Linux, Windows, and macOS

## Supported Formats

| Format | Default Engine | Description |
|--------|---------------|-------------|
| DOCX | Pandoc | Microsoft Word documents |
| PDF | Pandoc | PDF documents |
| PPTX | MarkItDown | PowerPoint presentations |
| XLSX | MarkItDown | Excel spreadsheets |
| HTML | Pandoc | Web pages |
| RTF | Pandoc | Rich Text Format |
| ODT | Pandoc | OpenDocument Text |
| EPUB | Pandoc | E-books |
| CSV | MarkItDown | Comma-separated values |
| JSON | MarkItDown | JSON data |
| XML | MarkItDown | XML data |

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/xtomarkdown.git
   cd xtomarkdown
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Run the application:
   ```bash
   xtomarkdown
   # or
   python -m xtomarkdown
   ```

### Development

Install with development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Usage

1. **Add Files**: Drag files into the drop zone or click to browse
2. **Select Output**: Choose where to save converted files
   - Same folder as source
   - A specific folder
   - Ask each time
3. **Convert**: Click "Convert to Markdown"

### Preferences

Access preferences to:
- Set default output location
- View installed engines
- Override engine selection per file type
- Reset all settings to defaults

## Configuration

Settings are stored in:
- **Linux**: `~/.config/xtomarkdown/settings.json`
- **macOS**: `~/Library/Application Support/xtomarkdown/settings.json`
- **Windows**: `%LOCALAPPDATA%\xtomarkdown\settings.json`

## Building Standalone Executables

Using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed src/xtomarkdown/app.py --name xtomarkdown
```

## License

MIT License - see LICENSE file for details.

## Credits

- [Pandoc](https://pandoc.org/) - Universal document converter
- [MarkItDown](https://github.com/microsoft/markitdown) - Microsoft's document to Markdown converter
- [PySide6](https://doc.qt.io/qtforpython-6/) - Qt for Python
