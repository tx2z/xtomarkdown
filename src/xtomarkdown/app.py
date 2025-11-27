"""Main application entry point."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import __version__
from .gui.main_window import MainWindow


def _get_resource_path(relative_path: str) -> Path:
    """Get the path to a resource file, handling PyInstaller bundles."""
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base_path / "xtomarkdown" / "gui" / "resources" / relative_path
    else:
        # Running in normal Python environment
        return Path(__file__).parent / "gui" / "resources" / relative_path


def main():
    """Run the XtoMarkdown application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Consistent look across all platforms
    app.setApplicationName("XtoMarkdown")
    app.setOrganizationName("xtomarkdown")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("xtomarkdown")  # For GNOME/Wayland icon matching

    # Set application icon
    icon_path = _get_resource_path("icons/app-icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Load and apply stylesheet
    style_path = _get_resource_path("style.qss")
    if style_path.exists():
        app.setStyleSheet(style_path.read_text())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
