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

"""File management functionality for the VDV463 Validator UI."""

from pathlib import Path

from models.json_file import JSONFile
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QWidget


class FileManager:
    """Manages file operations and recent files list."""

    MAX_RECENT_FILES = 10

    def __init__(self, parent: QWidget | None = None):
        self.parent = parent
        self.settings = QSettings("VDV463", "Validator")
        self.loaded_files: list[JSONFile] = []
        self.current_file: JSONFile | None = None
        self.recent_files: list[str] = self._load_recent_files()

    def _load_recent_files(self) -> list[str]:
        """Load recent files from settings."""
        recent = self.settings.value("recent_files", [])
        if isinstance(recent, str):
            return [recent] if recent else []
        return list(recent) if recent else []

    def _save_recent_files(self) -> None:
        """Save recent files to settings."""
        self.settings.setValue("recent_files", self.recent_files)

    def add_to_recent_files(self, filepath: str) -> None:
        """Add a file to recent files list."""
        # Remove if already exists
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)

        # Add to beginning
        self.recent_files.insert(0, filepath)

        # Keep only MAX_RECENT_FILES
        self.recent_files = self.recent_files[:self.MAX_RECENT_FILES]

        self._save_recent_files()

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.recent_files.clear()
        self._save_recent_files()

    def load_file(self, filepath: Path, file_listbox: QListWidget) -> JSONFile:
        """
        Load a single file.

        Args:
            filepath: Path to the file to load
            file_listbox: QListWidget to update with the new file

        Returns:
            The loaded JSONFile

        Raises:
            OSError: If file cannot be loaded
        """
        # Check if already loaded
        for f in self.loaded_files:
            if f.filepath == filepath:
                # Select existing file
                idx = self.loaded_files.index(f)
                file_listbox.setCurrentRow(idx)
                return f

        json_file = JSONFile(filepath)
        self.loaded_files.append(json_file)
        item = QListWidgetItem(json_file.get_display_name())
        file_listbox.addItem(item)

        # Add to recent files
        self.add_to_recent_files(str(filepath))

        # Select the new file
        file_listbox.setCurrentRow(len(self.loaded_files) - 1)

        return json_file

    def close_file(self, index: int, file_listbox: QListWidget) -> bool:
        """
        Close a file at the given index.

        Args:
            index: Index of file to close
            file_listbox: QListWidget to update

        Returns:
            True if file was closed, False if operation was cancelled
        """
        if index < 0 or index >= len(self.loaded_files):
            return False

        json_file = self.loaded_files[index]

        if json_file.modified and self.parent:
            from i18n import t
            response = QMessageBox.question(
                self.parent,
                t("warning"),
                t("unsaved_changes_single", json_file.filepath.name)
            )
            if response == QMessageBox.StandardButton.Yes:
                self.save_file(json_file)
            elif response != QMessageBox.StandardButton.No:
                return False

        self.loaded_files.pop(index)
        file_listbox.takeItem(index)

        if self.current_file == json_file:
            self.current_file = None

        return True

    def close_all_files(self, file_listbox: QListWidget) -> bool:
        """
        Close all files.

        Args:
            file_listbox: QListWidget to update

        Returns:
            True if all files were closed, False if operation was cancelled
        """
        if not self.parent:
            return False

        from i18n import t
        modified_files = [f for f in self.loaded_files if f.modified]
        if modified_files:
            response = QMessageBox.question(
                self.parent,
                t("warning"),
                t("unsaved_changes_multiple", len(modified_files))
            )
            if response == QMessageBox.StandardButton.Yes:
                for json_file in modified_files:
                    try:
                        self.save_file(json_file)
                    except Exception as e:
                        QMessageBox.critical(self.parent, t("error"), t("error_saving_file", str(e)))
            elif response != QMessageBox.StandardButton.No:
                return False

        self.loaded_files.clear()
        file_listbox.clear()
        self.current_file = None

        return True

    def save_file(self, json_file: JSONFile, filepath: Path | None = None) -> None:
        """
        Save a file.

        Args:
            json_file: The JSONFile to save
            filepath: Optional new filepath (for Save As)

        Raises:
            Exception: If save fails
        """
        json_file.save(filepath)

    def open_files_dialog(self, file_listbox: QListWidget) -> list[JSONFile]:
        """
        Show open files dialog and load selected files.

        Args:
            file_listbox: QListWidget to update with loaded files

        Returns:
            List of loaded JSONFile objects
        """
        from i18n import t
        filepaths, _ = QFileDialog.getOpenFileNames(
            self.parent,
            t("open_files"),
            "",
            "JSON files (*.json);;All files (*.*)"
        )

        loaded = []
        for filepath in filepaths:
            try:
                json_file = self.load_file(Path(filepath), file_listbox)
                loaded.append(json_file)
            except Exception as e:
                if self.parent:
                    QMessageBox.critical(self.parent, t("error"), t("error_loading_file", str(e)))

        return loaded

    def update_file_list_item(self, json_file: JSONFile, file_listbox: QListWidget) -> None:
        """Update file list item with validation status icon."""
        try:
            idx = self.loaded_files.index(json_file)
            item = file_listbox.item(idx)
            if item and json_file.validation_result:
                result = json_file.validation_result
                if result.error_count > 0:
                    icon = "❌"
                elif result.warning_count > 0:
                    icon = "⚠️"
                else:
                    icon = "✅"
                display_name = json_file.get_display_name()
                item.setText(f"{icon} {display_name}")
        except (ValueError, AttributeError):
            pass
