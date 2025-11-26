"""Drag-and-drop zone widget for file input with state management."""

from enum import Enum, auto
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..config.defaults import SUPPORTED_FORMATS
from .resources.icons import get_icon


class DropZoneState(Enum):
    """States for the drop zone."""

    IDLE = auto()
    PROCESSING = auto()
    SUCCESS = auto()
    ERROR = auto()


class DropZone(QWidget):
    """
    A widget that accepts file drops and shows conversion state.

    Signals:
        files_dropped: Emitted with a list of file paths when files are dropped
    """

    files_dropped = Signal(list)

    ANIMATION_DURATION = 250  # milliseconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drag_active = False
        self._state = DropZoneState.IDLE
        self._rotation = 0
        self._pending_state = None
        self._pending_message = None
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 32, 20, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Content container - holds icon and labels for animation
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon label - fixed size to prevent layout shifts
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(64, 64)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Main text - fixed height to prevent layout shifts
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedHeight(24)
        font = self.label.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        self.label.setFont(font)
        content_layout.addWidget(self.label)

        # Subtext - fixed height to prevent layout shifts
        self.sublabel = QLabel()
        self.sublabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sublabel.setFixedHeight(20)
        content_layout.addWidget(self.sublabel)

        layout.addWidget(self.content)

        # Opacity effect for fade animation
        self.opacity_effect = QGraphicsOpacityEffect(self.content)
        self.opacity_effect.setOpacity(1.0)
        self.content.setGraphicsEffect(self.opacity_effect)

        # Style
        self.setObjectName("DropZone")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set initial state (no animation)
        self._update_content_for_state(DropZoneState.IDLE, "")
        self._update_style()

    def _setup_animations(self):
        """Set up the transition animations."""
        # Spinner rotation timer
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._rotate_spinner)

        # Fade out animation
        self._fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_out.setDuration(self.ANIMATION_DURATION)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Fade in animation
        self._fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_in.setDuration(self.ANIMATION_DURATION)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.InCubic)

        # Sequential: fade out -> update content -> fade in
        self._transition = QSequentialAnimationGroup()
        self._transition.addAnimation(self._fade_out)
        self._transition.addAnimation(self._fade_in)

        # Connect to update content between animations
        self._fade_out.finished.connect(self._on_fade_out_finished)

    def _rotate_spinner(self):
        """Rotate the spinner icon."""
        self._rotation = (self._rotation + 30) % 360
        pixmap = get_icon("spinner").pixmap(QSize(48, 48))
        from PySide6.QtGui import QTransform

        transform = QTransform().rotate(self._rotation)
        rotated = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.icon_label.setPixmap(rotated)

    def set_state(self, state: DropZoneState, message: str = ""):
        """Set the current state of the drop zone with animation."""
        if state == self._state and not message:
            return

        # Store pending state for after animation
        self._pending_state = state
        self._pending_message = message

        # Stop any running transition
        self._transition.stop()

        # Reset opacity before starting
        self.opacity_effect.setOpacity(1.0)

        # Start transition
        self._transition.start()

    def _on_fade_out_finished(self):
        """Called when fade out completes - update content before fade in."""
        if self._pending_state is not None:
            self._state = self._pending_state

            # Update content
            self._update_content_for_state(self._pending_state, self._pending_message or "")
            self._update_style()

            # Handle spinner
            if self._pending_state == DropZoneState.PROCESSING:
                self._rotation = 0
                self._spinner_timer.start(50)
                self.setAcceptDrops(False)
                self.setCursor(Qt.CursorShape.WaitCursor)
            else:
                self._spinner_timer.stop()
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                self.setAcceptDrops(True)

            self._pending_state = None
            self._pending_message = None

    def _update_content_for_state(self, state: DropZoneState, message: str):
        """Update UI elements based on state."""
        if state == DropZoneState.IDLE:
            self.icon_label.setPixmap(get_icon("upload").pixmap(QSize(48, 48)))
            self.label.setText("Drop files here")
            self.sublabel.setText("or click to browse")

        elif state == DropZoneState.PROCESSING:
            self.icon_label.setPixmap(get_icon("spinner").pixmap(QSize(48, 48)))
            self.label.setText("Converting...")
            self.sublabel.setText(message or " ")

        elif state == DropZoneState.SUCCESS:
            self.icon_label.setPixmap(get_icon("success").pixmap(QSize(48, 48)))
            self.label.setText("Conversion complete!")
            self.sublabel.setText(message if message else "Files saved successfully")

        elif state == DropZoneState.ERROR:
            self.icon_label.setPixmap(get_icon("error").pixmap(QSize(48, 48)))
            self.label.setText("Conversion failed")
            self.sublabel.setText(message or " ")

    def _update_style(self):
        """Update the widget style based on drag state."""
        palette = self.palette()

        if self._state == DropZoneState.SUCCESS:
            border_color = "#2ec27e"  # Green for success
            bg_color = palette.base().color().name()
        elif self._state == DropZoneState.ERROR:
            border_color = "#e01b24"  # Red for error
            bg_color = palette.base().color().name()
        elif self._drag_active:
            border_color = palette.highlight().color().name()
            bg_color = palette.alternateBase().color().name()
        else:
            border_color = palette.mid().color().name()
            bg_color = palette.base().color().name()

        highlight_color = palette.highlight().color().name()
        alt_bg = palette.alternateBase().color().name()

        # Only show hover effect in idle state
        if self._state == DropZoneState.IDLE:
            hover_style = f"""
                #DropZone:hover {{
                    border-color: {highlight_color};
                    background-color: {alt_bg};
                }}
            """
        else:
            hover_style = ""

        self.setStyleSheet(f"""
            #DropZone {{
                border: 2px dashed {border_color};
                border-radius: 12px;
                background-color: {bg_color};
                min-height: 180px;
            }}
            {hover_style}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if self._state != DropZoneState.IDLE:
            event.ignore()
            return

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    ext = Path(url.toLocalFile()).suffix.lower().lstrip(".")
                    if ext in SUPPORTED_FORMATS:
                        event.acceptProposedAction()
                        self._drag_active = True
                        self._update_style()
                        return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self._drag_active = False
        self._update_style()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        self._drag_active = False
        self._update_style()

        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                ext = Path(path).suffix.lower().lstrip(".")
                if ext in SUPPORTED_FORMATS:
                    files.append(path)

        if files:
            self.files_dropped.emit(files)

    def mousePressEvent(self, event):
        """Handle mouse clicks to open file browser."""
        if self._state != DropZoneState.IDLE:
            return

        from PySide6.QtWidgets import QFileDialog

        from ..config.defaults import FILE_FILTER

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Convert", "", FILE_FILTER
        )
        if files:
            self.files_dropped.emit(files)
