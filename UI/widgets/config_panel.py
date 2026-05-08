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

"""Configuration panel widget for the VDV463 Validator UI."""

from i18n import t
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
)

from vdv463_validator import SchemaVersion


class ConfigPanel(QFrame):
    """Configuration panel widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        # Create UI components
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI components."""
        layout = QGridLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        self.setLayout(layout)

        row = 0

        # Schema version selection
        schema_label = QLabel("📋 " + t("schema_version") + ":")
        schema_label.setStyleSheet("font-weight: bold; color: #1c7ed6;")
        layout.addWidget(schema_label, row, 0)

        self.schema_version_combo = QComboBox()
        self.schema_version_combo.addItems(SchemaVersion.SUPPORTED_VERSIONS + ["auto"])
        self.schema_version_combo.setCurrentText("auto")
        self.schema_version_combo.setToolTip(t("tooltip_schema_version"))
        self.schema_version_combo.setMinimumHeight(30)
        layout.addWidget(self.schema_version_combo, row, 1)

        # Current schema version display
        current_schema_label = QLabel(t("current_schema_version") + ":")
        layout.addWidget(current_schema_label, row, 2)

        self.current_schema_version_label = QLabel("auto")
        self.current_schema_version_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.current_schema_version_label, row, 3)

        # Validation mode checkbox
        self.schema_only_checkbox = QCheckBox(t("schema_only"))
        self.schema_only_checkbox.setToolTip(t("tooltip_schema_only"))
        self.schema_only_checkbox.setChecked(False)
        layout.addWidget(self.schema_only_checkbox, row, 4)

        row += 1

        # Rule configuration
        config_label = QLabel("⚙️ " + t("rule_config") + ":")
        config_label.setStyleSheet("font-weight: bold; color: #1c7ed6;")
        layout.addWidget(config_label, row, 0)

        self.config_label = QLabel(t("no_rules"))
        self.config_label.setStyleSheet("font-style: italic; color: #888;")
        layout.addWidget(self.config_label, row, 1, 1, 2)

        self.btn_load_rules = QPushButton("📁 " + t("load_rules"))
        self.btn_load_rules.setToolTip(t("tooltip_load_rules"))
        self.btn_load_rules.setMinimumHeight(30)
        layout.addWidget(self.btn_load_rules, row, 3)

        layout.setColumnStretch(4, 1)

    def update_texts(self) -> None:
        """Update all UI texts (for language changes)."""
        self.btn_load_rules.setText("📁 " + t("load_rules"))
        self.btn_load_rules.setToolTip(t("tooltip_load_rules"))
        self.schema_version_combo.setToolTip(t("tooltip_schema_version"))
        self.schema_only_checkbox.setText(t("schema_only"))
        self.schema_only_checkbox.setToolTip(t("tooltip_schema_only"))

    def update_version_display(self, schema_version: str | None, ruleset_name: str | None = None) -> None:
        """Update the displayed version information."""
        if schema_version:
            self.current_schema_version_label.setText(schema_version)
        else:
            self.current_schema_version_label.setText("auto")

        # Update the rule configuration label
        if ruleset_name:
            self.config_label.setText(ruleset_name)
        else:
            self.config_label.setText(t("no_rules"))

    def is_schema_only_mode(self) -> bool:
        """Check if schema-only validation mode is enabled."""
        return self.schema_only_checkbox.isChecked()
