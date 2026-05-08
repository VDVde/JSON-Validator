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

"""Editor panel widget for the VDV463 Validator UI."""

from pathlib import Path

from i18n import t
from json_editor import JSONCodeEditor
from json_tree_view import JSONTreeView
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from schema_view import SchemaView


class EditorPanel(QFrame):
    """JSON editor panel widget with tabs for code, tree, and schema views."""

    def __init__(self, palette, schema_dir: Path, parent=None):
        super().__init__(parent)
        self.palette = palette
        self.schema_dir = schema_dir
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create UI components
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Title
        self.title_label = QLabel(t("json_editor"))
        self.title_label.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {self.palette.accent_primary.name()};")
        layout.addWidget(self.title_label, stretch=0)

        # Tab widget for different views
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setDocumentMode(True)

        # Code view tab
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)
        code_layout.setContentsMargins(0, 5, 0, 0)
        code_layout.setSpacing(10)

        # Editor controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.btn_format = QPushButton("{ } " + t("format_json"))
        self.btn_format.setToolTip(t("tooltip_format_json"))
        controls_layout.addWidget(self.btn_format)

        controls_layout.addStretch()

        self.btn_validate = QPushButton("✓ " + t("validate"))
        self.btn_validate.setObjectName("ValidateButton")
        self.btn_validate.setToolTip(t("tooltip_validate"))
        self.btn_validate.setMinimumWidth(120)
        controls_layout.addWidget(self.btn_validate)

        self.btn_validate_all = QPushButton("✓✓ " + t("validate_all"))
        self.btn_validate_all.setObjectName("ValidateAllButton")
        self.btn_validate_all.setToolTip(t("tooltip_validate_all"))
        self.btn_validate_all.setMinimumWidth(120)
        controls_layout.addWidget(self.btn_validate_all)

        code_layout.addLayout(controls_layout)

        # JSON Code Editor
        self.json_text = JSONCodeEditor(palette=self.palette)
        self.json_text.setToolTip(t("tooltip_json_editor"))
        code_layout.addWidget(self.json_text)

        self.editor_tabs.addTab(code_widget, "📝 " + t("code_view"))

        # Tree View tab
        self.json_tree_view = JSONTreeView(palette=self.palette)
        self.editor_tabs.addTab(self.json_tree_view, "🌿 " + t("tree_view"))

        # Schema View tab
        self.schema_view = SchemaView(palette=self.palette)
        self.schema_view.set_schema_dir(self.schema_dir)
        self.editor_tabs.addTab(self.schema_view, "📐 " + t("schema_view"))

        layout.addWidget(self.editor_tabs, stretch=1)

    def set_validate_button_style(self, style: str) -> None:
        """Set the style for the validate buttons."""
        self.btn_validate.setStyleSheet(style)
        self.btn_validate_all.setStyleSheet(style)

    def update_texts(self) -> None:
        """Update all UI texts (for language changes)."""
        self.title_label.setText(t("json_editor"))
        self.btn_format.setText("{ } " + t("format_json"))
        self.btn_format.setToolTip(t("tooltip_format_json"))
        self.btn_validate.setText("✓ " + t("validate"))
        self.btn_validate.setToolTip(t("tooltip_validate"))
        self.btn_validate_all.setText("✓✓ " + t("validate_all"))
        self.btn_validate_all.setToolTip(t("tooltip_validate_all"))
        self.json_text.setToolTip(t("tooltip_json_editor"))
        self.editor_tabs.setTabText(0, "📝 " + t("code_view"))
        self.editor_tabs.setTabText(1, "🌿 " + t("tree_view"))
        self.editor_tabs.setTabText(2, "📐 " + t("schema_view"))
        self.json_tree_view.update_texts(
            t("expand_all"),
            t("collapse_all"),
            t("search")
        )
