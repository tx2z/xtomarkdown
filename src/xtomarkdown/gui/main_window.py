"""Main application window."""

import time
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import Settings
from ..core.converter import DocumentConverter
from .about_dialog import AboutDialog
from .drop_zone import DropZone, DropZoneState
from .preferences import PreferencesDialog
from .resources.icons import get_icon


class ConversionWorker(QThread):
    """Worker thread for file conversions."""

    MIN_DURATION = 2.0  # Minimum seconds to show spinner

    progress = Signal(int, int, str)  # current, total, filename
    file_completed = Signal(str, bool, str)  # path, success, message
    conversion_done = Signal(int, int)  # success_count, fail_count

    def __init__(self, converter: DocumentConverter, files: list[str], output_func):
        super().__init__()
        self.converter = converter
        self.files = files
        self.output_func = output_func

    def run(self):
        """Run conversions."""
        start_time = time.monotonic()
        total = len(self.files)
        success_count = 0
        fail_count = 0

        for i, file_path in enumerate(self.files):
            filename = Path(file_path).name
            self.progress.emit(i + 1, total, filename)

            output_path = self.output_func(file_path)
            result = self.converter.convert(file_path, output_path)

            if result.success:
                success_count += 1
                self.file_completed.emit(file_path, True, str(result.output_path))
            else:
                fail_count += 1
                self.file_completed.emit(file_path, False, result.error or "Unknown error")

        # Ensure minimum duration so spinner is visible
        elapsed = time.monotonic() - start_time
        if elapsed < self.MIN_DURATION:
            time.sleep(self.MIN_DURATION - elapsed)

        self.conversion_done.emit(success_count, fail_count)


class MainWindow(QMainWindow):
    """Main application window."""

    SUCCESS_DISPLAY_TIME = 5000  # 5 seconds

    def __init__(self):
        super().__init__()
        self.settings = Settings.load()
        self.converter = DocumentConverter(self.settings)
        self._worker: ConversionWorker | None = None
        self._ask_output_paths: dict[str, str] = {}  # For "ask" mode
        self._setup_ui()
        self._restore_geometry()

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("XtoMarkdown")
        self.setMinimumSize(400, 300)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Drop zone (main UI element)
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_zone, stretch=1)

        # Bottom row with about and preferences buttons
        bottom_row = QHBoxLayout()

        self.about_btn = QPushButton("About")
        self.about_btn.setIcon(get_icon("info"))
        self.about_btn.clicked.connect(self._show_about)
        bottom_row.addWidget(self.about_btn)

        bottom_row.addStretch()

        self.prefs_btn = QPushButton("Preferences")
        self.prefs_btn.setIcon(get_icon("settings"))
        self.prefs_btn.clicked.connect(self._show_preferences)
        bottom_row.addWidget(self.prefs_btn)

        layout.addLayout(bottom_row)

        # Timer for returning to idle state after success
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._reset_to_idle)

    def _show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def _show_preferences(self):
        """Show preferences dialog."""
        dialog = PreferencesDialog(self.settings, self)
        if dialog.exec():
            # Refresh converter with updated settings
            self.converter = DocumentConverter(self.settings)

    def _get_output_path(self, input_path: str) -> str | None:
        """Get output path for a file based on settings."""
        input_file = Path(input_path)
        output_name = input_file.stem + ".md"

        if self.settings.output_mode == "ask":
            # Check if we already have a path for this file (from pre-prompt)
            if input_path in self._ask_output_paths:
                return self._ask_output_paths[input_path]
            # Shouldn't happen, but fallback to same folder
            return str(input_file.parent / output_name)
        elif self.settings.output_mode == "folder" and self.settings.output_folder:
            return str(Path(self.settings.output_folder) / output_name)
        else:
            # Default to same folder as source
            return str(input_file.parent / output_name)

    def _on_files_dropped(self, files: list[str]):
        """Handle files dropped - start conversion immediately."""
        if self._worker is not None:
            return  # Already converting

        # Stop any pending reset timer
        self._reset_timer.stop()

        # Clear previous ask paths
        self._ask_output_paths.clear()

        # If "ask" mode, prompt for each file's output location first
        if self.settings.output_mode == "ask":
            for file_path in files:
                input_file = Path(file_path)
                output_name = input_file.stem + ".md"
                default_path = str(input_file.parent / output_name)

                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    f"Save '{input_file.name}' as",
                    default_path,
                    "Markdown Files (*.md)",
                )

                if save_path:
                    self._ask_output_paths[file_path] = save_path
                else:
                    # User cancelled - abort all
                    self._ask_output_paths.clear()
                    return

        # Start conversion
        self._start_conversion(files)

    def _start_conversion(self, files: list[str]):
        """Start converting files."""
        if not files:
            return

        # Update UI state
        self.drop_zone.set_state(DropZoneState.PROCESSING)
        self.prefs_btn.setEnabled(False)

        # Start worker thread
        self._worker = ConversionWorker(self.converter, files, self._get_output_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.conversion_done.connect(self._on_conversion_done)
        self._worker.start()

    def _on_progress(self, current: int, total: int, filename: str):
        """Handle progress updates."""
        if total == 1:
            self.drop_zone.set_state(DropZoneState.PROCESSING, filename)
        else:
            self.drop_zone.set_state(DropZoneState.PROCESSING, f"{filename} ({current}/{total})")

    def _on_conversion_done(self, success_count: int, fail_count: int):
        """Handle conversion completion."""
        self._worker = None
        self.prefs_btn.setEnabled(True)

        if fail_count == 0:
            # All succeeded
            if success_count == 1:
                message = "File converted successfully"
            else:
                message = f"{success_count} files converted"
            self.drop_zone.set_state(DropZoneState.SUCCESS, message)
        elif success_count == 0:
            # All failed
            if fail_count == 1:
                message = "Conversion failed"
            else:
                message = f"All {fail_count} files failed"
            self.drop_zone.set_state(DropZoneState.ERROR, message)
        else:
            # Mixed results
            message = f"{success_count} converted, {fail_count} failed"
            self.drop_zone.set_state(DropZoneState.SUCCESS, message)

        # Start timer to return to idle state
        self._reset_timer.start(self.SUCCESS_DISPLAY_TIME)

    def _reset_to_idle(self):
        """Reset drop zone to idle state."""
        self.drop_zone.set_state(DropZoneState.IDLE)

    def _restore_geometry(self):
        """Restore window geometry from settings."""
        self.resize(self.settings.window_width, self.settings.window_height)
        if self.settings.window_x is not None and self.settings.window_y is not None:
            self.move(self.settings.window_x, self.settings.window_y)

    def closeEvent(self, event):
        """Handle window close - save geometry."""
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings.window_x = self.x()
        self.settings.window_y = self.y()
        self.settings.save()
        event.accept()
