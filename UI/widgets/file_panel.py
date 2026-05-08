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

"""File list panel widget for the VDV463 Validator UI."""

from i18n import t
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


class FilePanel(QFrame):
    """File list panel widget."""

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

        # Title
        self.title_label = QLabel(t("loaded_files"))
        accent = self.palette.accent_primary.name() if self.palette else "#1c7ed6"
        self.title_label.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {accent};")
        layout.addWidget(self.title_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.btn_add_files = QPushButton("➕ " + t("add_files"))
        self.btn_add_files.setToolTip(t("tooltip_add_files"))
        btn_layout.addWidget(self.btn_add_files)

        self.btn_remove_file = QPushButton("🗑️")
        self.btn_remove_file.setToolTip(t("remove_selected"))
        self.btn_remove_file.setFixedWidth(40)
        btn_layout.addWidget(self.btn_remove_file)

        layout.addLayout(btn_layout)

        # File list
        self.file_listbox = QListWidget()
        layout.addWidget(self.file_listbox)

    def update_texts(self) -> None:
        """Update all UI texts (for language changes)."""
        self.title_label.setText(t("loaded_files"))
        self.btn_add_files.setText("➕ " + t("add_files"))
        self.btn_add_files.setToolTip(t("tooltip_add_files"))
        self.btn_remove_file.setToolTip(t("remove_selected"))
        self.file_listbox.setToolTip(t("tooltip_file_list"))
