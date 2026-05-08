#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
VDV463 JSON Validator - Local Python UI

A PySide6-based GUI for validating VDV463 JSON messages.
Supports multiple files, rule configuration, and multilingual interface.

This is the refactored version with separated concerns.
"""

import json
import sys
import time
from collections import namedtuple
from pathlib import Path

# Add src directory to path to import validator
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Also add UI directory for imports when running from different locations
sys.path.insert(0, str(Path(__file__).parent))

from i18n import get_i18n, set_language, t
from managers import FileManager, ValidationManager
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from splash_screen import CustomSplashScreen
from theme import get_palette, get_stylesheet, get_validate_button_style, is_dark_mode
from utils import get_base_path
from widgets import ConfigPanel, EditorPanel, FilePanel, ResultsPanel

from vdv463_validator import SchemaVersion, VDV463Validator

# Base path for all resources
BASE_PATH = get_base_path()

# Named tuple for toolbar action configuration
# Fields:
#   attr_name: Name of the instance attribute to store the action (e.g., 'toolbar_open_action')
#   icon: Icon/emoji to display before the text (e.g., "📂 ")
#   text_key: Translation key for the action text (e.g., 'open_files')
#   tooltip_key: Translation key for the tooltip text (e.g., 'tooltip_add_files')
#   handler: Callback function to execute when the action is triggered
ToolbarAction = namedtuple('ToolbarAction', ['attr_name', 'icon', 'text_key', 'tooltip_key', 'handler'])


class VDV463ValidatorUI(QMainWindow):
    """Main UI application with refactored architecture."""

    def __init__(self, dark_mode: bool = False):
        super().__init__()
        self.i18n = get_i18n()
        self.dark_mode = dark_mode
        self.palette = get_palette(self.dark_mode)
        self.schema_dir = BASE_PATH / "schemas"
        self.config_path: Path | None = None
        self.schema_version = "auto"
        self.current_schema_version: str | None = None  # Track current detected version
        self.validator: VDV463Validator | None = None

        # Initialize settings
        self.settings = QSettings("VDV463", "Validator")

        # Load saved settings
        self._load_settings()

        # Initialize managers
        self.file_manager = FileManager(parent=self)
        self.validation_manager = ValidationManager()

        # Set up validation timer
        self.validation_manager.validation_timer.timeout.connect(self._trigger_live_validation)

        # Initialize validator
        self._init_validator()

        # Setup UI
        self._setup_window()
        self._create_menu()
        self._create_toolbar()
        self._create_widgets()
        self._create_statusbar()
        self._setup_shortcuts()
        self._update_ui_texts()

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Apply saved settings to UI
        self._apply_settings()

    def _init_validator(self) -> None:
        """Initialize VDV463 validator."""
        try:
            self.validator = VDV463Validator(
                schema_dir=self.schema_dir,
                config_path=self.config_path,
                schema_version=self.schema_version
            )
            self.validation_manager.set_validator(self.validator)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize validator: {e}")
            sys.exit(1)

    def _load_settings(self) -> None:
        """Load saved settings from QSettings."""
        # Load language preference
        saved_language = self.settings.value("language", "en")
        if saved_language in ["de", "en"]:
            set_language(saved_language)
            # Sync the instance language with global
            self.i18n.language = saved_language

        # Load validation mode (schema-only checkbox)
        self.saved_schema_only = self.settings.value("schema_only_mode", False, type=bool)

        # Load last selected schema version
        saved_schema_version = self.settings.value("schema_version", "auto")
        if saved_schema_version in SchemaVersion.SUPPORTED_VERSIONS + ["auto"]:
            self.schema_version = saved_schema_version

        # Load last selected rule set path
        saved_rules_path = self.settings.value("rules_path", "")
        if saved_rules_path and Path(saved_rules_path).exists():
            self.config_path = Path(saved_rules_path)

    def _apply_settings(self) -> None:
        """Apply loaded settings to UI components."""
        # Block signals to prevent triggering validation during setup
        self.config_panel.schema_version_combo.blockSignals(True)
        self.config_panel.schema_only_checkbox.blockSignals(True)

        # Apply schema version to combo box
        self.config_panel.schema_version_combo.setCurrentText(self.schema_version)

        # Apply schema-only mode to checkbox
        self.config_panel.schema_only_checkbox.setChecked(self.saved_schema_only)

        # Unblock signals
        self.config_panel.schema_version_combo.blockSignals(False)
        self.config_panel.schema_only_checkbox.blockSignals(False)

        # Update rule config display if rules were loaded
        if self.config_path:
            self.config_panel.config_label.setText(self.config_path.name)
            self._update_ruleset_display(self.config_path.name)

    def _save_settings(self) -> None:
        """Save current settings to QSettings."""
        # Save language preference from global i18n instance
        current_i18n = get_i18n()
        self.settings.setValue("language", current_i18n.language)

        # Save validation mode
        self.settings.setValue("schema_only_mode", self.config_panel.is_schema_only_mode())

        # Save schema version
        self.settings.setValue("schema_version", self.schema_version)

        # Save rule set path
        if self.config_path:
            self.settings.setValue("rules_path", str(self.config_path))
        else:
            self.settings.setValue("rules_path", "")

    def _setup_window(self) -> None:
        """Setup main window."""
        self.setWindowTitle(t("app_title"))
        self.setGeometry(100, 100, 1200, 800)

    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()
        assert menubar is not None

        # File menu
        file_menu = menubar.addMenu(t("file"))
        assert file_menu is not None
        file_menu.addAction(t("open_files"), self.open_files)

        # Recent files submenu
        self.recent_menu = file_menu.addMenu(t("recent_files"))
        assert self.recent_menu is not None
        self._update_recent_files_menu()

        file_menu.addAction(t("close_selected"), self.close_selected_file)
        file_menu.addAction(t("close_all"), self.close_all_files)
        file_menu.addSeparator()
        file_menu.addAction(t("save_json"), self.save_json)
        file_menu.addAction(t("save_as"), self.save_json_as)
        file_menu.addAction(t("export_results"), self.export_results)
        file_menu.addSeparator()
        file_menu.addAction(t("exit"), self.close)

        # Edit menu
        edit_menu = menubar.addMenu(t("edit"))
        assert edit_menu is not None
        edit_menu.addAction(t("undo"), self._undo)
        edit_menu.addAction(t("redo"), self._redo)
        edit_menu.addSeparator()
        edit_menu.addAction(t("cut"), self._cut)
        edit_menu.addAction(t("copy"), self._copy)
        edit_menu.addAction(t("paste"), self._paste)
        edit_menu.addSeparator()
        edit_menu.addAction(t("format_json"), self.format_json)
        edit_menu.addAction(t("minify_json"), self.minify_json)

        # Language menu
        lang_menu = menubar.addMenu(t("language"))
        assert lang_menu is not None
        lang_menu.addAction("Deutsch", lambda: self.change_language("de"))
        lang_menu.addAction("English", lambda: self.change_language("en"))

        # Help menu
        help_menu = menubar.addMenu(t("help"))
        assert help_menu is not None
        help_menu.addAction(t("keyboard_shortcuts"), self.show_shortcuts)
        help_menu.addSeparator()
        help_menu.addAction(t("about"), self.show_about)

    def _create_toolbar(self) -> None:
        """Create toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Define toolbar actions using named tuples for clarity
        self.toolbar_actions_config = [
            ToolbarAction('toolbar_open_action', "📂 ", "open_files", "tooltip_add_files", self.open_files),
            ToolbarAction('toolbar_save_action', "💾 ", "save_json", "tooltip_save", self.save_json),
            None,  # Separator
            ToolbarAction('toolbar_validate_action', "✓ ", "validate", "tooltip_validate", self.validate_current),
            ToolbarAction('toolbar_validate_all_action', "✓✓ ", "validate_all", "tooltip_validate_all",
                          self.validate_all),
            None,  # Separator
            ToolbarAction('toolbar_format_action', "{ } ", "format_json", "tooltip_format_json", self.format_json),
            None,  # Separator
            ToolbarAction('toolbar_goto_error_action', "→ ", "goto_error", "tooltip_goto_error",
                          self.goto_selected_error),
        ]

        # Create toolbar actions
        for config in self.toolbar_actions_config:
            if config is None:
                toolbar.addSeparator()
            else:
                action = toolbar.addAction(config.icon + t(config.text_key))
                action.setToolTip(t(config.tooltip_key))
                action.triggered.connect(config.handler)
                setattr(self, config.attr_name, action)

    def _create_widgets(self) -> None:
        """Create main UI widgets using extracted panel components."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        central_widget.setLayout(main_layout)

        # Horizontal splitter for left/middle/right panels
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Left panel - File list
        self.file_panel = FilePanel(palette=self.palette)
        self.file_panel.file_listbox.itemSelectionChanged.connect(self.on_file_select)
        self.file_panel.btn_add_files.clicked.connect(self.open_files)
        self.file_panel.btn_remove_file.clicked.connect(self.close_selected_file)
        self.main_splitter.addWidget(self.file_panel)

        # Middle panel - JSON editor
        self.editor_panel = EditorPanel(palette=self.palette, schema_dir=self.schema_dir)
        self.editor_panel.json_text.textChanged.connect(self.on_json_modified)
        self.editor_panel.json_text.cursorPositionChanged.connect(self._update_cursor_position)
        self.editor_panel.json_tree_view.pathSelected.connect(self._on_tree_path_selected)
        self.editor_panel.editor_tabs.currentChanged.connect(self._on_editor_tab_changed)
        self.editor_panel.btn_format.clicked.connect(self.format_json)
        self.editor_panel.btn_validate.clicked.connect(self.validate_current)
        self.editor_panel.btn_validate_all.clicked.connect(self.validate_all)
        self.editor_panel.set_validate_button_style(get_validate_button_style(self.dark_mode))
        self.main_splitter.addWidget(self.editor_panel)

        # Right panel - Validation results
        self.results_panel = ResultsPanel(palette=self.palette)
        self.results_panel.results_tree.itemDoubleClicked.connect(self.on_error_double_click)
        self.results_panel.results_tree.itemClicked.connect(self.on_error_click)
        self.results_panel.results_search.textChanged.connect(self.results_panel.filter_results)
        self.results_panel.btn_goto_error.clicked.connect(self.goto_selected_error)
        self.results_panel.btn_clear_results.clicked.connect(self.clear_results)
        self.main_splitter.addWidget(self.results_panel)

        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 2)
        self.main_splitter.setStretchFactor(2, 2)

        for i in range(self.main_splitter.count()):
            self.main_splitter.setCollapsible(i, False)

        # Make splitter take all available vertical space
        main_layout.addWidget(self.main_splitter, stretch=1)

        # Bottom panel - Configuration (fixed height)
        self.config_panel = ConfigPanel()
        self.config_panel.schema_version_combo.currentTextChanged.connect(self.on_schema_version_changed)
        self.config_panel.btn_load_rules.clicked.connect(self.load_rule_config)
        self.config_panel.schema_only_checkbox.stateChanged.connect(self.on_validation_mode_changed)
        self.config_panel.setMaximumHeight(90)  # Increased for two rows
        main_layout.addWidget(self.config_panel, stretch=0)

    def _create_statusbar(self) -> None:
        """Create status bar with live validation status."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Validation status label (left side)
        self.validation_status_label = QLabel("...")
        self.validation_status_label.setObjectName("StatusLabel")
        self.validation_status_label.setToolTip(t("status_no_file"))
        self.statusbar.addWidget(self.validation_status_label)

        # Spacer to push other items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.statusbar.addWidget(spacer, 1)

        # Cursor position label (right side)
        self.cursor_pos_label = QLabel(t("line_column", 1, 1))
        self.statusbar.addPermanentWidget(self.cursor_pos_label)

        # File size label (right side)
        self.file_size_label = QLabel("")
        self.statusbar.addPermanentWidget(self.file_size_label)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # File operations
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_files)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_json)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_json_as)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_selected_file)

        # Editing
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.format_json)
        QShortcut(QKeySequence("Ctrl+Shift+M"), self, self.minify_json)

    def _update_cursor_position(self) -> None:
        """Update cursor position in status bar."""
        line = self.editor_panel.json_text.get_current_line()
        col = self.editor_panel.json_text.get_current_column()
        self.cursor_pos_label.setText(t("line_column", line, col))

    def _update_file_size(self) -> None:
        """Update file size in status bar."""
        if self.file_manager.current_file and self.file_manager.current_file.content:
            size = len(self.file_manager.current_file.content.encode('utf-8'))
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            self.file_size_label.setText(t("file_size", size_str))
        else:
            self.file_size_label.setText("")

    def _update_ui_texts(self) -> None:
        """Update all UI texts (for language changes)."""
        self.setWindowTitle(t("app_title"))

        # Update panel texts
        self.file_panel.update_texts()
        self.editor_panel.update_texts()
        self.results_panel.update_texts()
        self.config_panel.update_texts()

        # Update toolbar action texts
        if hasattr(self, 'toolbar_actions_config'):
            for config in self.toolbar_actions_config:
                if config is not None:  # Skip separators
                    if hasattr(self, config.attr_name):
                        action = getattr(self, config.attr_name)
                        action.setText(config.icon + t(config.text_key))
                        action.setToolTip(t(config.tooltip_key))

    # =========================================================================
    # Recent Files
    # =========================================================================

    def _update_recent_files_menu(self) -> None:
        """Update the recent files submenu."""
        self.recent_menu.clear()

        if not self.file_manager.recent_files:
            action = self.recent_menu.addAction(t("no_recent_files"))
            if action:
                action.setEnabled(False)
        else:
            for filepath in self.file_manager.recent_files:
                path = Path(filepath)
                if path.exists():
                    action = self.recent_menu.addAction(path.name)
                    if action:
                        action.setToolTip(filepath)
                        action.triggered.connect(lambda checked, fp=filepath: self._open_recent_file(fp))

            self.recent_menu.addSeparator()
            self.recent_menu.addAction(t("clear_recent"), self._clear_recent_files)

    def _open_recent_file(self, filepath: str) -> None:
        """Open a file from recent files list."""
        path = Path(filepath)
        if path.exists():
            try:
                self.file_manager.load_file(path, self.file_panel.file_listbox)
                self.on_file_select()
            except Exception as e:
                QMessageBox.warning(self, t("warning"), t("error_loading_file", str(e)))
                if filepath in self.file_manager.recent_files:
                    self.file_manager.recent_files.remove(filepath)
                    self.file_manager._save_recent_files()
                    self._update_recent_files_menu()
        else:
            QMessageBox.warning(self, t("warning"), t("error_loading_file", f"File not found: {filepath}"))
            if filepath in self.file_manager.recent_files:
                self.file_manager.recent_files.remove(filepath)
                self.file_manager._save_recent_files()
                self._update_recent_files_menu()

    def _clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.file_manager.clear_recent_files()
        self._update_recent_files_menu()

    # =========================================================================
    # Drag and Drop
    # =========================================================================

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        mime_data = event.mimeData()
        if mime_data and mime_data.hasUrls():
            for url in mime_data.urls():
                if url.toLocalFile().lower().endswith('.json'):
                    event.acceptProposedAction()
                    self.statusbar.showMessage(t("drop_files_here"), 2000)
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        files_loaded = 0
        mime_data = event.mimeData()
        if not mime_data:
            return
        for url in mime_data.urls():
            filepath = url.toLocalFile()
            if filepath.lower().endswith('.json'):
                try:
                    self.file_manager.load_file(Path(filepath), self.file_panel.file_listbox)
                    self.on_file_select()
                    files_loaded += 1
                except Exception as e:
                    QMessageBox.critical(self, t("error"), t("error_loading_file", str(e)))

        if files_loaded > 0:
            event.acceptProposedAction()
            self.statusbar.showMessage(f"{files_loaded} file(s) loaded", 3000)

    # =========================================================================
    # Editor Tab and View Management
    # =========================================================================

    def _on_editor_tab_changed(self, index: int) -> None:
        """Handle editor tab change - update tree view or schema view when switching."""
        if index == 1:  # Tree view tab
            self._update_tree_view()
        elif index == 2:  # Schema view tab
            self._update_schema_view()

    def _update_tree_view(self) -> None:
        """Update the tree view with current JSON content."""
        try:
            content = self.editor_panel.json_text.toPlainText()
            if content.strip():
                data = json.loads(content)
                self.editor_panel.json_tree_view.load_json(data)
            else:
                self.editor_panel.json_tree_view.load_json(None)
        except json.JSONDecodeError:
            # Don't update tree if JSON is invalid
            pass

    def _update_schema_view(self) -> None:
        """Update schema view based on current file's message type and selected schema version."""
        if not self.file_manager.current_file or not self.file_manager.current_file.data:
            return

        # Detect message type
        data = self.file_manager.current_file.data
        if "depotInfoList" in data:
            msg_type = "ProvideChargingInformationRequest"
        elif "chargingRequestList" in data:
            msg_type = "ProvideChargingRequestsRequest"
        else:
            return

        # Get selected schema version
        selected_version = self.config_panel.schema_version_combo.currentText()

        # If auto, try to detect from validator or use latest
        if selected_version == "auto":
            if self.validator and hasattr(self.validator, '_detected_version'):
                selected_version = self.validator._detected_version  # type: ignore[union-attr]
            else:
                selected_version = SchemaVersion.SUPPORTED_VERSIONS[-1]

        # Build schema file path
        schema_dir = self.editor_panel.schema_view._schema_dir
        if not schema_dir:
            return

        schema_file = schema_dir / selected_version / f"{msg_type}.json"

        if schema_file.exists():
            self.editor_panel.schema_view.load_schema_file(schema_file)
        else:
            # Fallback: try to find any matching schema
            for version_dir in sorted(schema_dir.iterdir(), reverse=True):
                if version_dir.is_dir() and version_dir.name.startswith("v"):
                    fallback_file = version_dir / f"{msg_type}.json"
                    if fallback_file.exists():
                        self.editor_panel.schema_view.load_schema_file(fallback_file)
                        break

    def _on_tree_path_selected(self, path: str) -> None:
        """Handle path selection from tree view - navigate to code."""
        if not path:
            return

        # Switch to code view and highlight the path
        self.editor_panel.editor_tabs.setCurrentIndex(0)

        # Try to find and highlight the path in the JSON
        text = self.editor_panel.json_text.toPlainText()

        # Extract the last key from path
        if '.' in path:
            last_key = path.split('.')[-1]
        elif '[' in path:
            last_key = path.split('[')[0].split('.')[-1] if '.' in path.split('[')[0] else path.split('[')[0]
        else:
            last_key = path

        # Remove array index if present
        if '[' in last_key:
            last_key = last_key.split('[')[0]

        # Search for the key
        search_str = f'"{last_key}"'
        pos = text.find(search_str)

        if pos >= 0:
            line_number = text[:pos].count('\\n') + 1
            self.editor_panel.json_text.goto_line(line_number)

    # =========================================================================
    # JSON Formatting
    # =========================================================================

    def format_json(self) -> None:
        """Format (pretty-print) the JSON content."""
        if not self.file_manager.current_file:
            QMessageBox.warning(self, t("warning"), t("select_file_first"))
            return

        try:
            content = self.editor_panel.json_text.toPlainText()
            data = json.loads(content)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.editor_panel.json_text.setPlainText(formatted)
            self.statusbar.showMessage("JSON formatted", 2000)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, t("error"), f"{t('invalid_json')}: {e}")

    def minify_json(self) -> None:
        """Minify the JSON content."""
        if not self.file_manager.current_file:
            QMessageBox.warning(self, t("warning"), t("select_file_first"))
            return

        try:
            content = self.editor_panel.json_text.toPlainText()
            data = json.loads(content)
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            self.editor_panel.json_text.setPlainText(minified)
            self.statusbar.showMessage("JSON minified", 2000)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, t("error"), f"{t('invalid_json')}: {e}")

    # =========================================================================
    # Edit Menu Actions
    # =========================================================================

    def _undo(self) -> None:
        """Undo action."""
        self.editor_panel.json_text.undo()

    def _redo(self) -> None:
        """Redo action."""
        self.editor_panel.json_text.redo()

    def _cut(self) -> None:
        """Cut action."""
        self.editor_panel.json_text.cut()

    def _copy(self) -> None:
        """Copy action."""
        self.editor_panel.json_text.copy()

    def _paste(self) -> None:
        """Paste action."""
        self.editor_panel.json_text.paste()

    # =========================================================================
    # Error Navigation
    # =========================================================================

    def goto_selected_error(self) -> None:
        """Navigate to the currently selected error in the results tree."""
        current = self.results_panel.results_tree.currentItem()
        if not current or current.childCount() > 0:
            return

        # Switch to code view tab
        self.editor_panel.editor_tabs.setCurrentIndex(0)

        # Highlight the error line
        if self.file_manager.current_file:
            self.validation_manager.highlight_error_line(
                current,
                self.editor_panel.json_text,
                self.file_manager.current_file.content or ""
            )

    def on_error_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on error item - same as single click."""
        self.on_error_click(item, column)

    def on_error_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle single click on error item - highlight in all views."""
        if not isinstance(item, QTreeWidgetItem) or item.childCount() > 0:
            return

        # Use the path from user data if available, otherwise fallback to column 3
        path = item.data(0, Qt.UserRole)
        if not path:
            path = item.text(3)

        if not path:
            return

        # Highlight in code editor (without switching tabs)
        if self.file_manager.current_file:
            self.validation_manager.highlight_error_line(
                item,
                self.editor_panel.json_text,
                self.file_manager.current_file.content or ""
            )

        # Expand tree view to the path
        self.editor_panel.json_tree_view.expand_to_path(path)

        # Highlight in schema view
        self.editor_panel.schema_view.highlight_error_path(path)

    # =========================================================================
    # File Management
    # =========================================================================

    def open_files(self) -> None:
        """Open JSON files."""
        self.file_manager.open_files_dialog(self.file_panel.file_listbox)
        if self.file_manager.loaded_files:
            self._update_recent_files_menu()
            self.on_file_select()

    def close_selected_file(self) -> None:
        """Close selected file."""
        current_row = self.file_panel.file_listbox.currentRow()
        if current_row < 0:
            return

        if self.file_manager.close_file(current_row, self.file_panel.file_listbox):
            if self.file_manager.current_file is None:
                self.editor_panel.json_text.clear()
                self.clear_results()

            if self.file_manager.loaded_files:
                new_idx = min(current_row, len(self.file_manager.loaded_files) - 1)
                self.file_panel.file_listbox.setCurrentRow(new_idx)
                self.on_file_select()

    def close_all_files(self) -> None:
        """Close all files."""
        if self.file_manager.close_all_files(self.file_panel.file_listbox):
            self.editor_panel.json_text.clear()
            self.clear_results()

    def on_file_select(self) -> None:
        """Handle file selection."""
        current_row = self.file_panel.file_listbox.currentRow()
        if current_row < 0:
            return

        self.file_manager.current_file = self.file_manager.loaded_files[current_row]
        self.editor_panel.json_text.setPlainText(self.file_manager.current_file.content or "")
        self._update_file_size()

        # Update tree view if currently visible
        if self.editor_panel.editor_tabs.currentIndex() == 1:
            self._update_tree_view()

        # Update schema view based on the new file's message type
        self._update_schema_view()

        if self.file_manager.current_file.validation_result:
            self.display_validation_results(self.file_manager.current_file.validation_result)
        else:
            self.clear_results()

    def on_json_modified(self) -> None:
        """Handle JSON text modification by starting a timer for live validation."""
        if self.file_manager.current_file:
            self.file_manager.current_file.content = self.editor_panel.json_text.toPlainText()
            self.file_manager.current_file.modified = True

            idx = self.file_manager.loaded_files.index(self.file_manager.current_file)
            item = self.file_panel.file_listbox.item(idx)
            if item:
                item.setText(self.file_manager.current_file.get_display_name())

            # Start the timer to trigger validation after a delay
            self.validation_manager.validation_timer.start()

    def _trigger_live_validation(self) -> None:
        """Perform live validation of the current file's content."""
        if not self.file_manager.current_file or not self.validator:
            return

        content = self.file_manager.current_file.content or ""

        # Don't validate empty content
        if not content.strip():
            self.clear_results()
            return

        try:
            # Check if schema-only mode is enabled
            schema_only = self.config_panel.is_schema_only_mode()

            from managers.validation_manager import ValidationWorker

            # Start validation in a background thread to prevent UI freezing
            self.validation_worker = ValidationWorker(
                self.validator,
                self.file_manager.current_file,
                schema_only
            )
            self.validation_worker._target_file = self.file_manager.current_file
            self.validation_worker.result_ready.connect(self._on_validation_finished)

            self.statusbar.showMessage(t("validating") if hasattr(self, 't') else "Validating...", 2000)
            self.validation_worker.start()
        except Exception as e:
            self.statusbar.showMessage(f"Failed to start validation: {e}", 5000)

    def _on_validation_finished(self, result) -> None:
        """Handle completion of background validation."""
        sender_worker = self.sender()
        if not result or not self.file_manager.current_file or \
           getattr(sender_worker, '_target_file', None) != self.file_manager.current_file:
            return

        try:
            # Update version display
            self._update_version_display(result)

            self.display_validation_results(result)
            self.file_manager.update_file_list_item(
                self.file_manager.current_file,
                self.file_panel.file_listbox
            )
        except Exception as e:
            self.statusbar.showMessage(f"Validation crashed: {e}", 5000)
            if self.validation_status_label:
                self.validation_status_label.setText("🔥")
                self.validation_status_label.setToolTip("FATAL: Validation engine crashed.")

    def save_json(self) -> None:
        """Save current JSON file."""
        if not self.file_manager.current_file:
            QMessageBox.warning(self, t("warning"), t("select_file_first"))
            return

        try:
            self.file_manager.current_file.content = self.editor_panel.json_text.toPlainText()
            self.file_manager.current_file.data = json.loads(self.file_manager.current_file.content)
            self.file_manager.save_file(self.file_manager.current_file)
            QMessageBox.information(self, t("information"),
                                    t("file_saved", self.file_manager.current_file.filepath.name))

            idx = self.file_manager.loaded_files.index(self.file_manager.current_file)
            item = self.file_panel.file_listbox.item(idx)
            if item:
                item.setText(self.file_manager.current_file.get_display_name())

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, t("error"), f"{t('invalid_json')}: {e}")
        except Exception as e:
            QMessageBox.critical(self, t("error"), t("error_saving_file", str(e)))

    def save_json_as(self) -> None:
        """Save current JSON file as new file."""
        if not self.file_manager.current_file:
            QMessageBox.warning(self, t("warning"), t("select_file_first"))
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            t("save_as"),
            self.file_manager.current_file.filepath.name,
            "JSON files (*.json);;All files (*.*)"
        )

        if filepath:
            try:
                self.file_manager.current_file.content = self.editor_panel.json_text.toPlainText()
                self.file_manager.current_file.data = json.loads(self.file_manager.current_file.content)
                self.file_manager.save_file(self.file_manager.current_file, Path(filepath))
                QMessageBox.information(self, t("information"), t("file_saved", filepath))

                idx = self.file_manager.loaded_files.index(self.file_manager.current_file)
                item = self.file_panel.file_listbox.item(idx)
                if item:
                    item.setText(self.file_manager.current_file.get_display_name())

            except json.JSONDecodeError as e:
                QMessageBox.critical(self, t("error"), f"{t('invalid_json')}: {e}")
            except Exception as e:
                QMessageBox.critical(self, t("error"), t("error_saving_file", str(e)))

    def validate_current(self) -> None:
        """Manually trigger validation of the current file."""
        if not self.file_manager.current_file:
            QMessageBox.warning(self, t("warning"), t("select_file_first"))
            return

        # Update content from editor
        self.file_manager.current_file.content = self.editor_panel.json_text.toPlainText()

        # Trigger validation
        self._trigger_live_validation()

    def validate_all(self) -> None:
        """Validate all loaded files."""
        if not self.file_manager.loaded_files:
            QMessageBox.warning(self, t("warning"), t("no_files_loaded"))
            return

        # Store current file
        current = self.file_manager.current_file

        # Validate each file
        for idx in range(len(self.file_manager.loaded_files)):
            # Select the file
            self.file_panel.file_listbox.setCurrentRow(idx)
            self.on_file_select()

            # Trigger validation
            self._trigger_live_validation()

        # Restore original selection
        if current and current in self.file_manager.loaded_files:
            idx = self.file_manager.loaded_files.index(current)
            self.file_panel.file_listbox.setCurrentRow(idx)
            self.on_file_select()

        self.statusbar.showMessage(t("batch_complete"), 3000)

    def display_validation_results(self, result) -> None:
        """Display validation results in tree and update status bar."""

        def set_status_label(text: str, style: str) -> None:
            self.results_panel.status_label.setText(text)
            self.results_panel.status_label.setStyleSheet(style)

        def set_validation_status(text: str, tooltip: str) -> None:
            self.validation_status_label.setText(text)
            self.validation_status_label.setToolTip(tooltip)

        self.validation_manager.display_validation_results(
            result,
            self.results_panel.results_tree,
            set_status_label,
            set_validation_status,
            self.file_manager.current_file.content if self.file_manager.current_file else None
        )

        # Apply current filter if any
        current_filter = self.results_panel.results_search.text()
        if current_filter:
            self.results_panel.filter_results(current_filter)

    def clear_results(self) -> None:
        """Clear validation results."""
        self.results_panel.clear_results()
        # Clear error highlighting in schema view
        self.editor_panel.schema_view.clear_error_highlighting()

    def on_schema_version_changed(self, version: str) -> None:
        """Handle schema version change."""
        self.schema_version = version
        self._init_validator()
        # Update schema view to match selected version
        self._update_schema_view()
        # Re-trigger live validation with the new schema version
        self._trigger_live_validation()
        # Save settings
        self._save_settings()

    def on_validation_mode_changed(self, state: int) -> None:
        """Handle validation mode change (schema-only checkbox)."""
        # Re-trigger validation with new mode
        self._trigger_live_validation()
        # Save settings
        self._save_settings()

    def load_rule_config(self) -> None:
        """Load rule configuration file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            t("load_rules"),
            "",
            "YAML files (*.yaml *.yml);;All files (*.*)"
        )

        if filepath:
            try:
                self.config_path = Path(filepath)
                self._init_validator()
                self.config_panel.config_label.setText(self.config_path.name)

                # Update version display with new ruleset name
                self._update_ruleset_display(self.config_path.name)

                # Save settings
                self._save_settings()

                QMessageBox.information(self, t("information"), t("rules_loaded", self.config_path.name))
            except Exception as e:
                QMessageBox.critical(self, t("error"), t("error_loading_rules", str(e)))

    def _update_version_display(self, result) -> None:
        """Update the version information display based on validation result."""
        if hasattr(result, 'schema_version') and result.schema_version:
            self.current_schema_version = result.schema_version
            self.config_panel.update_version_display(self.current_schema_version)

    def _update_ruleset_display(self, ruleset_name: str | None = None) -> None:
        """Update the ruleset display."""
        self.config_panel.update_version_display(
            self.current_schema_version,
            ruleset_name
        )

    def export_results(self) -> None:
        """Export validation results to JSON."""
        if not self.file_manager.current_file or not self.file_manager.current_file.validation_result:
            QMessageBox.warning(self, t("warning"), t("select_file_first"))
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            t("export_results"),
            f"{self.file_manager.current_file.filepath.stem}_validation.json",
            "JSON files (*.json);;All files (*.*)"
        )

        if filepath:
            try:
                result_dict = self.file_manager.current_file.validation_result.to_dict()
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(result_dict, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, t("information"), t("results_exported", filepath))
            except Exception as e:
                QMessageBox.critical(self, t("error"), f"Export error: {e}")

    def change_language(self, language: str) -> None:
        """Change UI language."""
        set_language(language)
        # Sync instance with global
        self.i18n.language = language

        menubar = self.menuBar()
        if menubar:
            menubar.clear()
        self._create_menu()

        self._update_ui_texts()

        # Save language preference
        self._save_settings()

        if self.file_manager.current_file and self.file_manager.current_file.validation_result:
            self.display_validation_results(self.file_manager.current_file.validation_result)

    def show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        dialog = QMessageBox(self)
        dialog.setWindowTitle(t("shortcuts_title"))
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setText(t("shortcuts_text"))
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()

    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.information(self, t("about"), t("about_text"))

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle application close event."""
        # Save settings before closing
        self._save_settings()
        event.accept()


def main():
    """Main entry point with splash screen."""
    app = QApplication(sys.argv)

    # Apply dark theme if detected
    dark_mode = is_dark_mode()
    app.setStyleSheet(get_stylesheet(dark_mode))

    splash = CustomSplashScreen(timeout_ms=2500)
    splash.show()
    QApplication.processEvents()

    start_time = time.time()

    try:
        window = VDV463ValidatorUI(dark_mode=dark_mode)

        elapsed = (time.time() - start_time) * 1000
        min_display = 800
        if elapsed < min_display:
            delay = int(min_display - elapsed)
            QTimer.singleShot(delay, lambda: finish_startup(app, window, splash))
        else:
            finish_startup(app, window, splash)

    except Exception as e:
        splash.close()
        QMessageBox.critical(None, "Error", f"Failed to initialize application: {e}")
        sys.exit(1)

    sys.exit(app.exec())


def finish_startup(app, window, splash):
    """Complete startup by showing main window and closing splash."""
    window.show()
    app.processEvents()
    splash.close()


if __name__ == "__main__":
    main()
