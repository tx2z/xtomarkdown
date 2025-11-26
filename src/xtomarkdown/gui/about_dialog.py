"""About dialog with license information."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class AboutDialog(QDialog):
    """About dialog showing application info and licenses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About XtoMarkdown")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # App title and version
        title_label = QLabel("<h2>XtoMarkdown</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        description = QLabel(
            "A cross-platform GUI application for converting\n"
            "documents (DOCX, PDF, PPTX, etc.) to Markdown."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        # Tab widget for licenses
        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)

        # License tab
        license_tab = self._create_license_tab()
        tabs.addTab(license_tab, "License")

        # Third-party tab
        third_party_tab = self._create_third_party_tab()
        tabs.addTab(third_party_tab, "Third-Party Licenses")

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def _create_license_tab(self) -> QWidget:
        """Create the license tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        license_text = """
<p><b>XtoMarkdown</b> is licensed under the <b>GNU General Public License v3.0</b> (GPL-3.0-or-later).</p>

<p>This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.</p>

<p>This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.</p>

<p>You should have received a copy of the GNU General Public License along with this program. If not, see <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.</p>

<p>Source code: <a href="https://github.com/tx2z/xtomarkdown">https://github.com/tx2z/xtomarkdown</a></p>
"""

        label = QLabel(license_text)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        label.setTextFormat(Qt.TextFormat.RichText)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return widget

    def _create_third_party_tab(self) -> QWidget:
        """Create the third-party licenses tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        third_party_text = """
<p>XtoMarkdown uses the following open source software:</p>

<h3>Pandoc (GPL v2+)</h3>
<p>Pandoc is a universal document converter.<br>
Website: <a href="https://pandoc.org/">https://pandoc.org/</a><br>
Source: <a href="https://github.com/jgm/pandoc">https://github.com/jgm/pandoc</a><br>
License: GNU General Public License v2 or later</p>

<h3>pypandoc (MIT)</h3>
<p>Python wrapper for Pandoc.<br>
Source: <a href="https://github.com/JessicaTegner/pypandoc">https://github.com/JessicaTegner/pypandoc</a><br>
License: MIT License</p>

<h3>MarkItDown (MIT)</h3>
<p>Microsoft's library for converting documents to Markdown.<br>
Source: <a href="https://github.com/microsoft/markitdown">https://github.com/microsoft/markitdown</a><br>
License: MIT License<br>
Copyright (c) Microsoft Corporation</p>

<h3>PySide6 (LGPL v3)</h3>
<p>Qt for Python - Official Python bindings for Qt.<br>
Website: <a href="https://www.qt.io/qt-for-python">https://www.qt.io/qt-for-python</a><br>
License: GNU Lesser General Public License v3</p>

<h3>platformdirs (MIT)</h3>
<p>Cross-platform directories for application data.<br>
Source: <a href="https://github.com/platformdirs/platformdirs">https://github.com/platformdirs/platformdirs</a><br>
License: MIT License</p>

<hr>
<p><i>Full license texts are available in the LICENSES/ directory of the source distribution.</i></p>
"""

        label = QLabel(third_party_text)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        label.setTextFormat(Qt.TextFormat.RichText)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return widget
