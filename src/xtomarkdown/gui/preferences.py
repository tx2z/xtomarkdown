"""Preferences dialog for application settings."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..config import DEFAULT_ENGINE_MAPPING, Settings
from ..config.defaults import ENGINE_DISPLAY_NAMES, FORMAT_DISPLAY_NAMES
from ..core.engines import EngineRegistry
from .resources.icons import get_icon


class PreferencesDialog(QDialog):
    """Dialog for editing application preferences."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.registry = EngineRegistry()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Output location section
        output_group = QGroupBox("Output Location")
        output_layout = QVBoxLayout(output_group)

        self.output_button_group = QButtonGroup(self)

        # Same as source option
        self.same_radio = QRadioButton("Same folder as source file")
        self.output_button_group.addButton(self.same_radio)
        output_layout.addWidget(self.same_radio)

        # Specific folder option
        folder_row = QHBoxLayout()
        self.folder_radio = QRadioButton("Specific folder:")
        self.output_button_group.addButton(self.folder_radio)
        folder_row.addWidget(self.folder_radio)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Select a folder...")
        self.folder_edit.setReadOnly(True)
        folder_row.addWidget(self.folder_edit, stretch=1)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setIcon(get_icon("folder"))
        self.browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.browse_btn)
        output_layout.addLayout(folder_row)

        # Always ask option
        self.ask_radio = QRadioButton("Always ask where to save")
        self.output_button_group.addButton(self.ask_radio)
        output_layout.addWidget(self.ask_radio)

        layout.addWidget(output_group)

        # Engine status section
        status_group = QGroupBox("Installed Engines")
        status_layout = QVBoxLayout(status_group)

        for engine in self.registry.get_all():
            row = QHBoxLayout()
            row.setSpacing(8)

            name_label = QLabel(f"<b>{engine.display_name}</b>")
            row.addWidget(name_label)

            if engine.is_available():
                version = engine.get_version() or "installed"
                icon_label = QLabel()
                icon_label.setPixmap(get_icon("check").pixmap(QSize(16, 16)))
                row.addWidget(icon_label)
                status_label = QLabel(version)
            else:
                icon_label = QLabel()
                icon_label.setPixmap(get_icon("error").pixmap(QSize(16, 16)))
                row.addWidget(icon_label)
                status_label = QLabel("Not installed")
                status_label.setEnabled(False)  # Grayed out for disabled look
            row.addWidget(status_label)
            row.addStretch()
            status_layout.addLayout(row)

        layout.addWidget(status_group)

        # Engine preferences section
        engine_group = QGroupBox("Engine Preferences by File Type")
        engine_layout = QVBoxLayout(engine_group)

        self.engine_table = QTableWidget()
        self.engine_table.setColumnCount(3)
        self.engine_table.setHorizontalHeaderLabels(["Format", "Engine", "Status"])
        self.engine_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.engine_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.engine_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.engine_table.setColumnWidth(1, 120)
        self.engine_table.setColumnWidth(2, 80)
        self.engine_table.verticalHeader().setVisible(False)
        self.engine_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._populate_engine_table()
        engine_layout.addWidget(self.engine_table)

        # Reset buttons
        reset_row = QHBoxLayout()
        reset_row.addStretch()

        self.reset_selected_btn = QPushButton("Reset Selected")
        self.reset_selected_btn.clicked.connect(self._reset_selected)
        reset_row.addWidget(self.reset_selected_btn)

        self.reset_all_btn = QPushButton("Reset All to Defaults")
        self.reset_all_btn.clicked.connect(self._reset_all)
        reset_row.addWidget(self.reset_all_btn)

        engine_layout.addLayout(reset_row)
        layout.addWidget(engine_group)

        # Dialog buttons
        button_row = QHBoxLayout()
        button_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save_and_close)
        button_row.addWidget(self.save_btn)

        layout.addLayout(button_row)

    def _populate_engine_table(self):
        """Populate the engine preferences table."""
        formats = sorted(DEFAULT_ENGINE_MAPPING.keys())
        self.engine_table.setRowCount(len(formats))
        self._engine_combos: dict[str, QComboBox] = {}

        for row, ext in enumerate(formats):
            default_engine, _fallback = DEFAULT_ENGINE_MAPPING[ext]

            # Format name
            format_name = FORMAT_DISPLAY_NAMES.get(ext, f".{ext}")
            format_item = QTableWidgetItem(f".{ext} - {format_name}")
            format_item.setData(Qt.ItemDataRole.UserRole, ext)
            format_item.setFlags(format_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.engine_table.setItem(row, 0, format_item)

            # Engine combo
            combo = QComboBox()
            combo.addItem(f"Auto ({ENGINE_DISPLAY_NAMES.get(default_engine, default_engine)})", "")

            # Add available engines
            engines = self.registry.get_engines_for_extension(ext)
            for engine in engines:
                display_name = ENGINE_DISPLAY_NAMES.get(engine.name, engine.name)
                combo.addItem(display_name, engine.name)

            # Set current value from settings
            user_override = self.settings.get_engine_for_extension(ext)
            if user_override:
                index = combo.findData(user_override)
                if index >= 0:
                    combo.setCurrentIndex(index)

            self._engine_combos[ext] = combo
            self.engine_table.setCellWidget(row, 1, combo)

            # Status
            status = "Default" if not user_override else "Modified"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if user_override:
                status_item.setForeground(Qt.GlobalColor.blue)
            self.engine_table.setItem(row, 2, status_item)

    def _load_settings(self):
        """Load current settings into the UI."""
        # Output mode
        if self.settings.output_mode == "same":
            self.same_radio.setChecked(True)
        elif self.settings.output_mode == "folder":
            self.folder_radio.setChecked(True)
        else:
            self.ask_radio.setChecked(True)

        # Output folder
        if self.settings.output_folder:
            self.folder_edit.setText(self.settings.output_folder)

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.folder_edit.text() or str(Path.home())
        )
        if folder:
            self.folder_edit.setText(folder)
            self.folder_radio.setChecked(True)

    def _reset_selected(self):
        """Reset selected rows to default engine."""
        selected_rows = {index.row() for index in self.engine_table.selectedIndexes()}
        if not selected_rows:
            return

        for row in selected_rows:
            ext_item = self.engine_table.item(row, 0)
            if ext_item is None:
                continue
            ext = ext_item.data(Qt.ItemDataRole.UserRole)
            combo = self._engine_combos.get(ext)
            if combo:
                combo.setCurrentIndex(0)  # Auto
                status_item = self.engine_table.item(row, 2)
                if status_item is not None:
                    status_item.setText("Default")
                    status_item.setForeground(Qt.GlobalColor.black)

    def _reset_all(self):
        """Reset all engines to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset All",
            "Reset all engine preferences to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for combo in self._engine_combos.values():
                combo.setCurrentIndex(0)
            for row in range(self.engine_table.rowCount()):
                status_item = self.engine_table.item(row, 2)
                if status_item is not None:
                    status_item.setText("Default")
                    status_item.setForeground(Qt.GlobalColor.black)

    def _save_and_close(self):
        """Save settings and close dialog."""
        # Save output mode
        if self.same_radio.isChecked():
            self.settings.output_mode = "same"
        elif self.folder_radio.isChecked():
            self.settings.output_mode = "folder"
        else:
            self.settings.output_mode = "ask"

        # Save output folder
        self.settings.output_folder = self.folder_edit.text() or None

        # Save engine preferences
        self.settings.engine_overrides.clear()
        for ext, combo in self._engine_combos.items():
            engine = combo.currentData()
            if engine:  # Not "Auto"
                self.settings.engine_overrides[ext] = engine

        self.settings.save()
        self.accept()
