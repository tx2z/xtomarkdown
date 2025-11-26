"""Main application entry point."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .gui.main_window import MainWindow


def main():
    """Run the XtoMarkdown application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("XtoMarkdown")
    app.setOrganizationName("xtomarkdown")
    app.setApplicationVersion("1.0.0")
    app.setDesktopFileName("xtomarkdown")  # For GNOME/Wayland icon matching

    # Set application icon
    icon_path = Path(__file__).parent / "gui" / "resources" / "icons" / "app-icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Load and apply stylesheet
    style_path = Path(__file__).parent / "gui" / "resources" / "style.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
