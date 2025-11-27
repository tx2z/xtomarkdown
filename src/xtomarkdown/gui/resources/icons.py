"""Icon loading utilities for the application."""

import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def _get_icons_dir() -> Path:
    """Get the icons directory, handling PyInstaller bundles."""
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base_path / "xtomarkdown" / "gui" / "resources" / "icons"
    else:
        # Running in normal Python environment
        return Path(__file__).parent / "icons"


# Path to icons directory
ICONS_DIR = _get_icons_dir()


def get_icon(name: str, color: str | None = None) -> QIcon:
    """
    Load an SVG icon by name.

    Args:
        name: Icon name without extension (e.g., 'close', 'settings')
        color: Optional color to apply (CSS color string)

    Returns:
        QIcon object
    """
    icon_path = ICONS_DIR / f"{name}.svg"
    if not icon_path.exists():
        return QIcon()

    if color:
        # Read and modify SVG content to apply color
        svg_content = icon_path.read_text()
        svg_content = svg_content.replace('fill="currentColor"', f'fill="{color}"')

        # Create icon from modified SVG
        renderer = QSvgRenderer(svg_content.encode())
        sizes = [16, 24, 32, 48]
        icon = QIcon()

        for size in sizes:
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(QApplication.palette().color(QApplication.palette().ColorRole.Window))
            pixmap.fill("#00000000")  # Transparent
            from PySide6.QtGui import QPainter

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            icon.addPixmap(pixmap)

        return icon

    return QIcon(str(icon_path))


def get_icon_path(name: str) -> str:
    """Get the path to an icon file."""
    return str(ICONS_DIR / f"{name}.svg")
