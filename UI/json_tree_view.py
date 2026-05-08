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
JSON Tree View Widget

A graphical tree-based JSON viewer similar to XML Spy,
displaying JSON structure with icons, expandable nodes,
and value editing capabilities.
"""

from typing import Any

from i18n import t
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class JSONTreeItem(QTreeWidgetItem):
    """Custom tree item for JSON data."""

    # Item types
    TYPE_OBJECT = 0
    TYPE_ARRAY = 1
    TYPE_STRING = 2
    TYPE_NUMBER = 3
    TYPE_BOOLEAN = 4
    TYPE_NULL = 5

    def __init__(self, key: str = "", value: Any = None, json_type: int = TYPE_STRING,
                 parent: QTreeWidgetItem | None = None, palette: dict = None):
        if parent:
            super().__init__(parent)
        else:
            super().__init__()

        self.key = key
        self.json_value = value
        self.json_type = json_type
        self.palette = palette
        self.json_path = ""

        self._setup_display()

    def _setup_display(self):
        """Setup item display based on type."""
        # Column 0: Key/Index
        self.setText(0, self.key)

        # Column 1: Type indicator
        type_labels = {
            self.TYPE_OBJECT: "{ }",
            self.TYPE_ARRAY: "[ ]",
            self.TYPE_STRING: "str",
            self.TYPE_NUMBER: "num",
            self.TYPE_BOOLEAN: "bool",
            self.TYPE_NULL: "null"
        }
        self.setText(1, type_labels.get(self.json_type, "?"))

        # Column 2: Value (for primitives)
        if self.json_type == self.TYPE_OBJECT:
            self.setText(2, f"{{...}} ({self._count_children()} properties)")
        elif self.json_type == self.TYPE_ARRAY:
            self.setText(2, f"[...] ({self._count_children()} items)")
        elif self.json_type == self.TYPE_STRING:
            # Show truncated string
            display_val = str(self.json_value)
            if len(display_val) > 100:
                display_val = display_val[:97] + "..."
            self.setText(2, f'"{display_val}"')
        elif self.json_type == self.TYPE_BOOLEAN:
            self.setText(2, "true" if self.json_value else "false")
        elif self.json_type == self.TYPE_NULL:
            self.setText(2, "null")
        else:
            self.setText(2, str(self.json_value))

        # Apply styling based on type
        self._apply_type_styling()

    def _count_children(self) -> int:
        """Count how many children this value has."""
        if isinstance(self.json_value, dict):
            return len(self.json_value)
        elif isinstance(self.json_value, list):
            return len(self.json_value)
        return 0

    def _apply_type_styling(self):
        """Apply color styling based on JSON type."""
        color_map = {
            self.TYPE_OBJECT: self.palette.tree_object,
            self.TYPE_ARRAY: self.palette.tree_array,
            self.TYPE_STRING: self.palette.tree_string,
            self.TYPE_NUMBER: self.palette.tree_number,
            self.TYPE_BOOLEAN: self.palette.tree_boolean,
            self.TYPE_NULL: self.palette.tree_null,
        }
        color = color_map.get(self.json_type, QColor("#000000"))

        # Apply color to value column
        self.setForeground(2, QBrush(color))

        # Bold for keys
        font = self.font(0)
        font.setBold(True)
        self.setFont(0, font)

        # Italic for type column
        type_font = self.font(1)
        type_font.setItalic(True)
        self.setFont(1, type_font)


class JSONTreeWidget(QTreeWidget):
    """Tree widget for displaying JSON data graphically."""

    # Signals
    pathSelected = Signal(str)  # Emitted when a path is selected
    valueChanged = Signal(str, object)  # Emitted when a value is changed (path, new_value)

    def __init__(self, parent: QWidget | None = None, palette: dict = None):
        super().__init__(parent)
        self.palette = palette
        self._setup_ui()
        self._json_data: dict | None = None

    def set_theme(self, palette: dict):
        """Update the theme for the tree view."""
        self.palette = palette
        self.load_json(self._json_data)  # Reload data to apply new colors

    def _setup_ui(self):
        """Setup the tree widget UI."""
        # Setup columns
        self.setColumnCount(3)
        self.setHeaderLabels(["Key / Index", "Type", "Value"])

        # Configure header
        header = self.header()
        if header:
            header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Set column widths
        self.setColumnWidth(0, 250)
        self.setColumnWidth(1, 60)

        # Selection behavior
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Enable alternating row colors
        self.setAlternatingRowColors(True)

        # Enable animations
        self.setAnimated(True)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def load_json(self, data: Any) -> None:
        """Load JSON data into the tree."""
        self.clear()
        self._json_data = data

        if data is None:
            return

        # Create root item
        root = self._create_item_for_value("root", data, "")
        if root:
            self.addTopLevelItem(root)
            root.setExpanded(True)

            # Expand first level
            for i in range(root.childCount()):
                child = root.child(i)
                if child:
                    child.setExpanded(True)

    def _create_item_for_value(self, key: str, value: Any, parent_path: str) -> JSONTreeItem:
        """Create a tree item for a JSON value."""
        # Determine path
        if parent_path:
            if key.isdigit():
                path = f"{parent_path}[{key}]"
            else:
                path = f"{parent_path}.{key}"
        else:
            path = key

        # Determine type
        if isinstance(value, dict):
            item = JSONTreeItem(key, value, JSONTreeItem.TYPE_OBJECT, palette=self.palette)
            item.json_path = path

            # Add children
            for child_key, child_value in value.items():
                child_item = self._create_item_for_value(child_key, child_value, path)
                item.addChild(child_item)

        elif isinstance(value, list):
            item = JSONTreeItem(key, value, JSONTreeItem.TYPE_ARRAY, palette=self.palette)
            item.json_path = path

            # Add children with index as key
            for i, child_value in enumerate(value):
                child_item = self._create_item_for_value(str(i), child_value, path)
                item.addChild(child_item)

        elif isinstance(value, str):
            item = JSONTreeItem(key, value, JSONTreeItem.TYPE_STRING, palette=self.palette)
            item.json_path = path

        elif isinstance(value, bool):  # Must check before int/float!
            item = JSONTreeItem(key, value, JSONTreeItem.TYPE_BOOLEAN, palette=self.palette)
            item.json_path = path

        elif isinstance(value, (int, float)):
            item = JSONTreeItem(key, value, JSONTreeItem.TYPE_NUMBER, palette=self.palette)
            item.json_path = path

        elif value is None:
            item = JSONTreeItem(key, value, JSONTreeItem.TYPE_NULL, palette=self.palette)
            item.json_path = path
        else:
            # Unknown type, treat as string
            item = JSONTreeItem(key, str(value), JSONTreeItem.TYPE_STRING, palette=self.palette)
            item.json_path = path

        return item

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click."""
        if isinstance(item, JSONTreeItem):
            self.pathSelected.emit(item.json_path)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double-click (for editing in future)."""
        pass

    def _show_context_menu(self, position):
        """Show context menu."""
        item = self.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Copy Path
        copy_path_action = QAction(t("copy_path"), self)
        copy_path_action.triggered.connect(self._copy_path)
        menu.addAction(copy_path_action)

        # Copy Value
        copy_value_action = QAction(t("copy_value"), self)
        copy_value_action.triggered.connect(self._copy_value)
        menu.addAction(copy_value_action)

        menu.addSeparator()

        # Expand/Collapse
        expand_action = QAction(t("expand_all"), self)
        expand_action.triggered.connect(self.expandAll)
        menu.addAction(expand_action)

        collapse_action = QAction(t("collapse_all"), self)
        collapse_action.triggered.connect(self.collapseAll)
        menu.addAction(collapse_action)

        viewport = self.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(position))

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)

    def _copy_value(self, item: QTreeWidgetItem):
        """Copy item value to clipboard."""
        if isinstance(item, JSONTreeItem):
            import json
            if item.json_type in (JSONTreeItem.TYPE_OBJECT, JSONTreeItem.TYPE_ARRAY):
                text = json.dumps(item.json_value, indent=2, ensure_ascii=False)
            elif item.json_type == JSONTreeItem.TYPE_STRING:
                text = item.json_value
            elif item.json_type == JSONTreeItem.TYPE_NULL:
                text = "null"
            else:
                text = str(item.json_value)
            self._copy_to_clipboard(text)

    def _expand_item(self, item: QTreeWidgetItem, expand: bool):
        """Expand or collapse item and all children."""
        item.setExpanded(expand)
        for i in range(item.childCount()):
            child = item.child(i)
            if child:
                self._expand_item(child, expand)

    def expand_to_path(self, path: str):
        """Expand tree to show the given path."""
        # Parse path into parts
        parts = []
        current = ""
        in_bracket = False

        for char in path:
            if char == '[':
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = True
            elif char == ']':
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = False
            elif char == '.' and not in_bracket:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char

        if current:
            parts.append(current)

        # Navigate through tree
        if not parts:
            return

        # Start from root
        if self.topLevelItemCount() == 0:
            return

        current_item = self.topLevelItem(0)
        if not current_item:
            return
        current_item.setExpanded(True)

        # Skip "root" if it's first part
        if parts[0] == "root":
            parts = parts[1:]

        for part in parts:
            found = False
            if not current_item:
                break
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if child and isinstance(child, JSONTreeItem) and child.key == part:
                    child.setExpanded(True)
                    current_item = child
                    found = True
                    break

            if not found:
                break

        # Select final item
        if current_item:
            self.setCurrentItem(current_item)
            self.scrollToItem(current_item)


class JSONTreeView(QWidget):
    """Complete JSON Tree View widget with toolbar."""

    # Signals
    pathSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None, palette: dict = None):
        super().__init__(parent)
        self.palette = palette or {}
        self._setup_ui()

    def set_theme(self, palette: dict):
        """Update the theme for the tree view."""
        self.palette = palette
        self.tree.set_theme(palette)

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)

        # Expand all button
        self.btn_expand_all = QPushButton("▼ Expand All")
        self.btn_expand_all.setFixedWidth(100)
        self.btn_expand_all.clicked.connect(self._expand_all)
        toolbar.addWidget(self.btn_expand_all)

        # Collapse all button
        self.btn_collapse_all = QPushButton("▶ Collapse All")
        self.btn_collapse_all.setFixedWidth(100)
        self.btn_collapse_all.clicked.connect(self._collapse_all)
        toolbar.addWidget(self.btn_collapse_all)

        toolbar.addStretch()

        # Search field
        self.search_label = QLabel("Search:")
        toolbar.addWidget(self.search_label)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Enter key or value...")
        self.search_field.setFixedWidth(200)
        self.search_field.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_field)

        # Stats label
        self.stats_label = QLabel("")
        toolbar.addWidget(self.stats_label)

        layout.addLayout(toolbar)

        # Tree widget
        self.tree = JSONTreeWidget(palette=self.palette)
        self.tree.pathSelected.connect(self.pathSelected.emit)
        layout.addWidget(self.tree)

    def load_json(self, data: Any) -> None:
        """Load JSON data."""
        self.tree.load_json(data)
        self._update_stats(data)

    def _update_stats(self, data: Any):
        """Update statistics label."""
        if data is None:
            self.stats_label.setText("")
            return

        def count_items(obj):
            if isinstance(obj, dict):
                count = len(obj)
                for v in obj.values():
                    count += count_items(v)
                return count
            elif isinstance(obj, list):
                count = len(obj)
                for item in obj:
                    count += count_items(item)
                return count
            return 0

        total = count_items(data)
        self.stats_label.setText(f"Total: {total} items")

    def _expand_all(self):
        """Expand all items."""
        self.tree.expandAll()

    def _collapse_all(self):
        """Collapse all items."""
        self.tree.collapseAll()
        # Keep root expanded
        if self.tree.topLevelItemCount() > 0:
            root = self.tree.topLevelItem(0)
            if root:
                root.setExpanded(True)

    def _on_search(self, text: str):
        """Handle search input."""
        if not text:
            # Reset all items visibility
            self._show_all_items()
            return

        text_lower = text.lower()
        root = self.tree.invisibleRootItem()
        if root:
            self._search_and_highlight(root, text_lower)

    def _show_all_items(self):
        """Show all items."""

        def show_recursive(item: QTreeWidgetItem):
            item.setHidden(False)
            for i in range(item.childCount()):
                child = item.child(i)
                if child:
                    show_recursive(child)

        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            if top_item:
                show_recursive(top_item)

    def _search_and_highlight(self, parent: QTreeWidgetItem, search_text: str) -> bool:
        """Search and highlight matching items. Returns True if any child matches."""
        any_match = False

        for i in range(parent.childCount()):
            child = parent.child(i)
            if not child:
                continue

            # Check if this item matches
            matches = False
            if isinstance(child, JSONTreeItem):
                if search_text in child.key.lower():
                    matches = True
                elif child.json_type == JSONTreeItem.TYPE_STRING and search_text in str(child.json_value).lower():
                    matches = True
                elif search_text in str(child.json_value).lower():
                    matches = True

            # Check children
            child_matches = self._search_and_highlight(child, search_text)

            if matches or child_matches:
                child.setHidden(False)
                if matches:
                    child.setExpanded(True)
                any_match = True
            else:
                child.setHidden(True)

        return any_match

    def expand_to_path(self, path: str):
        """Expand tree to show the given path."""
        self.tree.expand_to_path(path)

    def update_texts(self, expand_text: str, collapse_text: str, search_text: str):
        """Update UI texts for localization."""
        self.btn_expand_all.setText(f"▼ {expand_text}")
        self.btn_collapse_all.setText(f"▶ {collapse_text}")
        self.search_label.setText(f"{search_text}:")
