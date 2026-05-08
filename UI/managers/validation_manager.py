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

"""Validation management functionality for the VDV463 Validator UI."""

import logging
import re
import traceback

from i18n import t
from models.json_file import JSONFile
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from vdv463_validator import ValidationResult, VDV463Validator


class ValidationWorker(QThread):
    result_ready = Signal(object)

    def __init__(self, validator, json_file, schema_only):
        super().__init__()
        self.validator = validator
        self.json_file = json_file
        self.schema_only = schema_only

    def run(self):
        if not self.validator or not self.json_file.content:
            self.result_ready.emit(None)
            return

        try:
            result = self.validator.validate_content(
                self.json_file.content,
                filename=str(self.json_file.filepath),
                schema_only=self.schema_only
            )
            self.json_file.validation_result = result
            self.result_ready.emit(result)
        except Exception as e:
            logger.error("Validation failed with exception: %s", e)
            logger.error("Traceback: %s", traceback.format_exc())
            self.result_ready.emit(None)


# Constants for results tree columns
RESULTS_TREE_COLUMN_COUNT = 5  # Line, Severity, Source, Path, Message

# Set up logger
logger = logging.getLogger(__name__)


class ValidationManager:
    """Manages validation operations and result display."""

    def __init__(self, validator: VDV463Validator | None = None):
        self.validator = validator
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.setInterval(500)  # 500ms debounce

    def set_validator(self, validator: VDV463Validator) -> None:
        """Set the validator instance."""
        self.validator = validator

    def validate_file(self, json_file: JSONFile, schema_only: bool = False) -> ValidationResult | None:
        """
        Validate a JSON file.

        Args:
            json_file: The file to validate
            schema_only: If True, skip rule validation (schema only)

        Returns:
            ValidationResult if validation succeeds, None on error
        """
        if not self.validator or not json_file.content:
            return None

        try:
            result = self.validator.validate_content(
                json_file.content,
                filename=str(json_file.filepath),
                schema_only=schema_only
            )
            json_file.validation_result = result
            return result
        except Exception as e:
            logger.error("Validation failed with exception: %s", e)
            logger.error("Traceback: %s", traceback.format_exc())
            return None

    def display_validation_results(
            self,
            result: ValidationResult,
            results_tree: QTreeWidget,
            status_label_setter: callable,
            validation_status_setter: callable,
            json_file_content: str | None = None
    ) -> None:
        """
        Display validation results in tree widget and update status.

        Args:
            result: ValidationResult to display
            results_tree: QTreeWidget to populate with results
            status_label_setter: Callable to set main status label text/style
            validation_status_setter: Callable to set validation status label text/tooltip
            json_file_content: Optional content for line number calculation
        """
        results_tree.setUpdatesEnabled(False)
        try:
            results_tree.clear()

            # Build status text
            file_count_str = t("status_file_count", 1)

            if result.parse_error:
                status_icon = "🔥"
                status_text = t("status_invalid_json", result.parse_error)
                tooltip_summary = t("tooltip_parse_error", file_count_str, result.parse_error)
                status_label_setter(t("validation_failed"), "color: red;")
            elif result.error_count > 0:
                status_icon = "❌"
                status_text = t("status_errors", result.error_count)
                if result.warning_count > 0:
                    status_text += f", {t('status_warnings', result.warning_count)}"
                if result.info_count > 0:
                    status_text += f", {t('status_infos', result.info_count)}"
                tooltip_summary = t("tooltip_invalid_full", file_count_str, result.error_count, result.warning_count,
                                    result.info_count)
                status_label_setter(t("validation_failed"), "color: red;")
            elif result.warning_count > 0:
                status_icon = "⚠"
                status_text = t("status_warnings", result.warning_count)
                if result.info_count > 0:
                    status_text += f", {t('status_infos', result.info_count)}"
                tooltip_summary = t("tooltip_warnings_full", file_count_str, result.warning_count, result.info_count)
                status_label_setter(t("validation_passed"), "color: green;")
            elif result.info_count > 0:
                status_icon = "ℹ"
                status_text = t("status_infos", result.info_count)
                tooltip_summary = t("tooltip_infos_full", file_count_str, result.info_count)
                status_label_setter(t("validation_passed"), "color: green;")
            else:
                status_icon = "✅"
                status_text = t("status_valid")
                tooltip_summary = t("tooltip_valid_full", file_count_str)
                status_label_setter(t("validation_passed"), "color: green;")

            validation_status_setter(f"{status_icon} {status_text}", tooltip_summary)

            # Add detailed status info
            status_text_full = f"{t('validation_passed') if result.valid else t('validation_failed')} | "
            status_text_full += f"{t('errors')}: {result.error_count}, {t('warnings')}: {result.warning_count}, {t('infos')}: {result.info_count}"
            status_text_full += f" | {t('duration')}: {result.duration_ms:.2f} ms"

            status_label_setter(status_text_full, "color: green;" if result.valid else "color: red;")

            if not result.issues:
                item = QTreeWidgetItem()
                item.setText(0, t("no_issues"))
                results_tree.addTopLevelItem(item)
                return

            # Map display names to the actual issue lists from ValidationResult
            severity_groups = [
                ("ERROR", result.errors),
                ("WARNING", result.warnings),
                ("INFO", result.infos)
            ]

            for severity_name, issues in severity_groups:
                if issues:
                    parent = QTreeWidgetItem([f"{t(severity_name)} ({len(issues)})"])
                    results_tree.addTopLevelItem(parent)

                    for issue in issues:
                        # Column 0: Line number
                        line_text = ""
                        if issue.line_number:
                            line_text = str(issue.line_number)
                        elif json_file_content:
                            line_num = self.find_path_line_number(issue.path, json_file_content)
                            line_text = str(line_num) if line_num else ""

                        # Column 1: Severity (Localized)
                        severity_text = t(severity_name)

                        # Column 2: Source (Schema vs Rule)
                        source_text = ""
                        source_icon = ""
                        if issue.rule_id == "SCHEMA":
                            source_text = t("schema_violation")
                            source_icon = "📋 "
                        elif issue.rule_id:
                            source_text = t("rule_violation")
                            source_icon = "⚙️ "
                        else:
                            source_text = t("schema_violation")
                            source_icon = "📋 "
                        source_display = source_icon + source_text

                        # Create child item with all columns at once
                        child_data = [
                            line_text,
                            severity_text,
                            source_display,
                            issue.path,
                            issue.message
                        ]
                        child = QTreeWidgetItem(parent, child_data)

                        # Store path in UserRole data for reliable retrieval
                        child.setData(0, Qt.UserRole, issue.path)

                        # Detailed tooltip
                        tooltip_parts = []
                        if line_text:
                            tooltip_parts.append(f"{t('line')}: {line_text}")
                        tooltip_parts.append(f"{t('severity')}: {severity_text}")
                        tooltip_parts.append(f"{t('source')}: {source_text}")
                        tooltip_parts.append(f"{t('path')}: {issue.path}")
                        tooltip_parts.append(f"{t('message')}: {issue.message}")
                        if issue.rule_id and issue.rule_id != "SCHEMA":
                            tooltip_parts.append(f"Rule ID: {issue.rule_id}")
                        tooltip = "\n".join(tooltip_parts)
                        for col in range(RESULTS_TREE_COLUMN_COUNT):
                            child.setToolTip(col, tooltip)

                    if severity_name == "ERROR":
                        parent.setExpanded(True)
        finally:
            results_tree.setUpdatesEnabled(True)

    @staticmethod
    def find_path_line_number(path: str, text: str) -> int:
        """Find the line number for a JSON path like 'depotInfoList[0].field'."""
        lines = text.split('\n')

        # Parse path into components
        components = re.split(r'\.(?![^\[]*\])', path)

        if not components:
            return 0

        # Get the last meaningful key (without array index)
        last_component = components[-1]
        # Remove array index if present
        last_key = re.sub(r'\[\d+\]$', '', last_component)

        if not last_key:
            return 0

        # Search for the key in the JSON
        search_pattern = f'"{last_key}"'

        # Count occurrences to find the right one based on array indices
        target_occurrence = 1

        # Extract array indices from path
        indices = re.findall(r'\[(\d+)\]', path)
        if indices:
            target_occurrence = 1
            for idx in indices:
                target_occurrence += int(idx)

        occurrence = 0
        found_lines: list[int] = []
        for line_num, line in enumerate(lines, 1):
            if search_pattern in line:
                occurrence += 1
                found_lines.append(line_num)
                if occurrence >= target_occurrence:
                    return line_num

        # If we only found the key once but path points to array index,
        # try to jump to corresponding array element start
        if indices and found_lines:
            try:
                target_index = int(indices[0])
            except ValueError:
                target_index = 0

            key_line = found_lines[0]
            element_counter = -1
            for line_num, line in enumerate(lines[key_line:], key_line):
                if '{' in line:
                    element_counter += 1
                    if element_counter == target_index:
                        return line_num

        # Fallback: return first occurrence if any
        if found_lines:
            return found_lines[0]

        return 0

    @staticmethod
    def highlight_error_line(item: QTreeWidgetItem, editor, json_content: str) -> None:
        """
        Highlight the line containing the error in the JSON editor.

        Args:
            item: QTreeWidgetItem containing error info
            editor: JSON editor widget with highlighting methods
            json_content: JSON file content for line number calculation
        """
        if not item or item.childCount() > 0:
            return

        # Try to get line number from column 0, or calculate from path in column 3
        line_text = item.text(0)
        path = item.text(3)  # Path is now in column 3

        line_number = None
        if line_text and line_text.isdigit():
            line_number = int(line_text)

        if not line_number and path:
            line_number = ValidationManager.find_path_line_number(path, json_content)

        if not line_number:
            return

        # Clear previous highlighting
        editor.clear_error_highlights()

        # Use the editor's built-in error highlighting with theme color
        editor.set_error_highlight(line_number)

        # Move cursor to position and ensure visible
        editor.goto_line(line_number)
