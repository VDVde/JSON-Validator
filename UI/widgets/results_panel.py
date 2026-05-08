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

"""Results panel widget for the VDV463 Validator UI."""

from i18n import t
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)


class ResultsPanel(QFrame):
    """Validation results panel widget."""

    def __init__(self, palette=None, parent=None):
        super().__init__(parent)
        self.palette = palette
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create UI components
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Title / Status Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        self.title_label = QLabel("🔍 " + t("validation_results"))
        accent = self.palette.accent_primary.name() if self.palette else "#1c7ed6"
        self.title_label.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {accent};")
        header_layout.addWidget(self.title_label)

        self.status_label = QLabel(t("no_file"))
        self.status_label.setStyleSheet("font-size: 9pt; font-weight: bold;")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Search box for filtering results
        self.results_search = QLineEdit()
        self.results_search.setPlaceholderText(t("filter_results"))
        self.results_search.setClearButtonEnabled(True)
        self.results_search.setMinimumHeight(30)
        layout.addWidget(self.results_search)

        # Results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(5)
        self.results_tree.setHeaderLabels([t("line"), t("severity"), t("source"), t("path"), t("message")])
        self.results_tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.results_tree.setToolTip(t("tooltip_results_panel"))

        # Configure tree to look like a table
        self.results_tree.setRootIsDecorated(False)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.header().setStretchLastSection(True)

        # Enable multi-selection and context menu
        self.results_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.results_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self._show_context_menu)

        # Improve column widths for better readability
        self.results_tree.setColumnWidth(0, 60)  # Line
        self.results_tree.setColumnWidth(1, 100)  # Severity
        self.results_tree.setColumnWidth(2, 120)  # Source (new)
        self.results_tree.setColumnWidth(3, 200)  # Path
        layout.addWidget(self.results_tree, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.btn_goto_error = QPushButton("→ " + t("goto_error"))
        self.btn_goto_error.setToolTip(t("tooltip_goto_error"))
        self.btn_goto_error.setMinimumHeight(30)
        btn_layout.addWidget(self.btn_goto_error)

        self.btn_clear_results = QPushButton("🗑️")
        self.btn_clear_results.setToolTip(t("tooltip_clear_results"))
        self.btn_clear_results.setMinimumHeight(30)
        self.btn_clear_results.setFixedWidth(40)
        btn_layout.addWidget(self.btn_clear_results)

        layout.addLayout(btn_layout, stretch=0)

    def _show_context_menu(self, position):
        """Show context menu for the results tree."""
        menu = QMenu()

        selected_items = self.results_tree.selectedItems()
        # Filter out category headers
        real_items = [item for item in selected_items if item.childCount() == 0]

        copy_action = QAction(t("copy_selected"), self)
        copy_action.setEnabled(len(real_items) > 0)
        copy_action.triggered.connect(lambda: self._copy_results(real_items))
        menu.addAction(copy_action)

        copy_all_action = QAction(t("copy_all"), self)
        copy_all_action.triggered.connect(lambda: self._copy_results(self._get_all_issues()))
        menu.addAction(copy_all_action)

        menu.addSeparator()

        export_action = QAction(t("export_selected_csv"), self)
        export_action.setEnabled(len(real_items) > 0)
        export_action.triggered.connect(lambda: self._export_results(real_items))
        menu.addAction(export_action)

        export_all_action = QAction(t("export_all_csv"), self)
        export_all_action.triggered.connect(lambda: self._export_results(self._get_all_issues()))
        menu.addAction(export_all_action)

        menu.exec(self.results_tree.viewport().mapToGlobal(position))

    def _get_all_issues(self) -> list[QTreeWidgetItem]:
        """Get all issue items from the tree, excluding headers."""
        issues = []
        for i in range(self.results_tree.topLevelItemCount()):
            parent = self.results_tree.topLevelItem(i)
            for j in range(parent.childCount()):
                issues.append(parent.child(j))
        return issues

    def _format_items_as_text(self, items: list[QTreeWidgetItem]) -> str:
        """Format tree items as tab-separated text."""
        lines = []
        # Header
        lines.append("\t".join([t("line"), t("severity"), t("source"), t("path"), t("message")]))

        for item in items:
            row = [item.text(col) for col in range(5)]
            lines.append("\t".join(row))

        return "\n".join(lines)

    def _copy_results(self, items: list[QTreeWidgetItem]):
        """Copy selected items to clipboard."""
        if not items:
            return
        text = self._format_items_as_text(items)
        QApplication.clipboard().setText(text)

    def _export_results(self, items: list[QTreeWidgetItem]):
        """Export selected items to a CSV file."""
        if not items:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, t("export_results_title"), "", "CSV files (*.csv);;Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            try:
                text = self._format_items_as_text(items)
                # For CSV, replace tabs with semicolons if preferred,
                # but tab-separated is often safer for Excel.
                if file_path.lower().endswith(".csv"):
                    text = text.replace("\t", ";")

                with open(file_path, "w", encoding="utf-8") as f:
                    # Add BOM for Excel UTF-8 compatibility
                    f.write('\ufeff')
                    f.write(text)
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, t("export_error_title"), t("export_error_msg", e))

    def filter_results(self, search_text: str) -> None:
        """Filter validation results based on search text."""
        search_text = search_text.lower()

        # Iterate through all top-level items (severity groups)
        for i in range(self.results_tree.topLevelItemCount()):
            parent = self.results_tree.topLevelItem(i)
            if not parent:
                continue

            visible_children = 0
            # Iterate through all child items (individual errors)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if not child:
                    continue

                # Check if any column contains the search text
                if not search_text:
                    child.setHidden(False)
                    visible_children += 1
                else:
                    matches = False
                    for col in range(5):  # line, severity, source, path, message
                        text = child.text(col).lower()
                        if search_text in text:
                            matches = True
                            break

                    child.setHidden(not matches)
                    if matches:
                        visible_children += 1

            # Hide parent if no visible children
            parent.setHidden(visible_children == 0)

    def clear_results(self) -> None:
        """Clear validation results."""
        self.results_tree.clear()
        self.status_label.setText(t("no_file"))
        self.status_label.setStyleSheet("")
        self.results_search.clear()

    def update_texts(self) -> None:
        """Update all UI texts (for language changes)."""
        self.title_label.setText("🔍 " + t("validation_results"))
        self.btn_goto_error.setText("→ " + t("goto_error"))
        self.btn_goto_error.setToolTip(t("tooltip_goto_error"))
        self.btn_clear_results.setToolTip(t("tooltip_clear_results"))
        self.results_tree.setToolTip(t("tooltip_results_panel"))
        self.results_tree.setHeaderLabels([t("line"), t("severity"), t("source"), t("path"), t("message")])
