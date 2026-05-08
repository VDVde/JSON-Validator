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
Internationalization module for VDV463 Validator UI.
Supports German and English.
"""

# Language strings
TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        # Menu and main window
        "app_title": "VDV463 JSON Validator",
        "app_subtitle": "Elektrische Bus-Ladeinfrastruktur",
        "file": "Datei",
        "language": "Sprache",
        "help": "Hilfe",

        # File menu
        "open_files": "JSON-Dateien öffnen...",
        "close_selected": "Ausgewählte schließen",
        "close_all": "Alle schließen",
        "save_json": "JSON speichern",
        "save_as": "Speichern unter...",
        "export_results": "Ergebnisse exportieren...",
        "exit": "Beenden",

        # Buttons
        "add_files": "Dateien hinzufügen",
        "remove_selected": "Ausgewählte entfernen",
        "validate": "Validieren",
        "validate_all": "Alle validieren",
        "clear_results": "Ergebnisse löschen",
        "goto_error": "Zu Fehler springen",

        # Tooltips
        "tooltip_add_files": "JSON-Dateien zum Validieren hinzufügen (Strg+O)",
        "tooltip_remove_selected": "Ausgewählte Dateien aus der Liste entfernen",
        "tooltip_validate": "Aktuelle Datei validieren (Strg+Umschalt+V)",
        "tooltip_validate_all": "Alle geladenen Dateien validieren (F5)",
        "tooltip_clear_results": "Validierungsergebnisse löschen",
        "tooltip_goto_error": "Zum ausgewählten Fehler im Editor springen (F8)",
        "tooltip_format_json": "JSON-Code formatieren und einrücken (Strg+Umschalt+F)",
        "tooltip_load_rules": "Benutzerdefinierte Validierungsregeln aus YAML-Datei laden",
        "tooltip_schema_version": "VDV463 Schema-Version auswählen (auto = automatische Erkennung)",
        "tooltip_file_list": "Liste der geladenen JSON-Dateien. Doppelklick zum Öffnen.",
        "tooltip_json_editor": "JSON-Editor mit Syntaxhervorhebung. Bearbeiten Sie hier Ihre Dateien.",
        "tooltip_results_panel": "Validierungsergebnisse. Doppelklick auf einen Fehler springt zur entsprechenden Zeile.",
        "tooltip_save": "Aktuelle Datei speichern (Strg+S)",
        "tooltip_save_as": "Aktuelle Datei unter neuem Namen speichern (Strg+Umschalt+S)",

        # Labels
        "loaded_files": "Geladene Dateien",
        "json_editor": "JSON Editor",
        "validation_results": "Validierungsergebnisse",
        "schema_version": "Schema-Version",
        "rule_config": "Regelkonfiguration",
        "no_file": "Keine Datei ausgewählt",
        "file_count": "Dateien: {}",

        # Results
        "status": "Status",
        "line": "Zeile",
        "severity": "Schwere",
        "path": "Pfad",
        "message": "Nachricht",
        "value": "Wert",
        "duration": "Dauer",

        # Severity levels
        "ERROR": "FEHLER",
        "WARNING": "WARNUNG",
        "INFO": "INFO",

        # Messages
        "validation_passed": "✓ Validierung erfolgreich",
        "validation_failed": "✗ Validierung fehlgeschlagen",
        "errors": "Fehler",
        "warnings": "Warnungen",
        "infos": "Infos",
        "no_issues": "Keine Probleme gefunden",
        "select_file_first": "Bitte zuerst eine Datei auswählen",
        "no_files_loaded": "Keine Dateien geladen",
        "invalid_json": "Ungültiges JSON",
        "file_saved": "Datei gespeichert: {}",
        "results_exported": "Ergebnisse exportiert: {}",
        "error_loading_file": "Fehler beim Laden der Datei: {}",
        "error_saving_file": "Fehler beim Speichern der Datei: {}",

        # Batch validation
        "batch_validation": "Batch-Validierung",
        "validating_file": "Validiere {} von {}: {}",
        "batch_complete": "Batch-Validierung abgeschlossen",
        "total_files": "Dateien gesamt",
        "passed": "Bestanden",
        "failed": "Fehlgeschlagen",
        "total_errors": "Fehler gesamt",
        "total_warnings": "Warnungen gesamt",
        "total_infos": "Infos gesamt",

        # Rule configuration
        "load_rules": "Regeln laden...",
        "no_rules": "Keine (Standard-Regeln)",
        "rules_loaded": "Regeln geladen: {}",
        "error_loading_rules": "Fehler beim Laden der Regeln: {}",

        # Dialogs
        "confirm": "Bestätigen",
        "cancel": "Abbrechen",
        "ok": "OK",
        "warning": "Warnung",
        "error": "Fehler",
        "information": "Information",
        "unsaved_changes_single": "Die Datei {} hat ungespeicherte Änderungen. Vor dem Schließen speichern?",
        "unsaved_changes_multiple": "{} Dateien haben ungespeicherte Änderungen. Alle vor dem Schließen speichern?",

        # Context menu
        "copy": "Kopieren",
        "copy_selected": "Markierte kopieren",
        "copy_all": "Alle kopieren",
        "export_selected_csv": "Markierte exportieren (CSV)...",
        "export_all_csv": "Alle exportieren (CSV)...",
        "export_results_title": "Ergebnisse exportieren",
        "export_error_title": "Export Fehler",
        "export_error_msg": "Fehler beim Exportieren: {}",
        "copy_path": "Pfad kopieren",
        "copy_value": "Wert kopieren",
        "select_all": "Alles auswählen",
        "find": "Suchen...",

        # New features
        "format_json": "JSON formatieren",
        "minify_json": "JSON komprimieren",
        "recent_files": "Zuletzt geöffnet",
        "no_recent_files": "Keine zuletzt geöffneten Dateien",
        "clear_recent": "Liste leeren",
        "edit": "Bearbeiten",
        "undo": "Rückgängig",
        "redo": "Wiederholen",
        "cut": "Ausschneiden",
        "paste": "Einfügen",
        "line_column": "Zeile: {}, Spalte: {}",
        "file_size": "Größe: {}",
        "drop_files_here": "Dateien hier ablegen",

        # About
        "about": "Über",
        "about_text": "VDV463 JSON Validator\nVersion 3.0.0\n\nEin Werkzeug zur Validierung von VDV463-Nachrichten.",

        # Keyboard shortcuts
        "keyboard_shortcuts": "Tastenkürzel",
        "shortcuts_title": "Tastenkürzel",
        "shortcuts_text": """<h3>Datei</h3>
<table>
<tr><td><b>Strg+O</b></td><td>Dateien öffnen</td></tr>
<tr><td><b>Strg+S</b></td><td>Speichern</td></tr>
<tr><td><b>Strg+Umschalt+S</b></td><td>Speichern unter</td></tr>
<tr><td><b>Strg+W</b></td><td>Datei schließen</td></tr>
</table>

<h3>Bearbeiten</h3>
<table>
<tr><td><b>Strg+Z</b></td><td>Rückgängig</td></tr>
<tr><td><b>Strg+Y</b></td><td>Wiederholen</td></tr>
<tr><td><b>Strg+X</b></td><td>Ausschneiden</td></tr>
<tr><td><b>Strg+C</b></td><td>Kopieren</td></tr>
<tr><td><b>Strg+V</b></td><td>Einfügen</td></tr>
<tr><td><b>Strg+Umschalt+F</b></td><td>JSON formatieren</td></tr>
<tr><td><b>Strg+Umschalt+M</b></td><td>JSON komprimieren</td></tr>
</table>

<h3>Validierung</h3>
<table>
<tr><td><b>Strg+Umschalt+V</b></td><td>Aktuelle Datei validieren</td></tr>
<tr><td><b>F5</b></td><td>Alle Dateien validieren</td></tr>
<tr><td><b>F8</b></td><td>Zum nächsten Fehler</td></tr>
</table>

<h3>Schema-Ansicht</h3>
<table>
<tr><td><b>Alt+Links</b></td><td>Zurück navigieren</td></tr>
<tr><td><b>Alt+Rechts</b></td><td>Vorwärts navigieren</td></tr>
<tr><td><b>Home</b></td><td>Zur Wurzel (Start)</td></tr>
<tr><td><b>Rechtsklick</b></td><td>Zurück navigieren</td></tr>
<tr><td><b>Mausrad</b></td><td>Zoomen</td></tr>
<tr><td><b>Linksklick + Ziehen</b></td><td>Ansicht verschieben</td></tr>
<tr><td><b>Klick auf Referenz</b></td><td>Zur Definition navigieren</td></tr>
</table>

<h3>Symbole</h3>
<table>
<tr><td><b>⌂</b></td><td>Wurzelelement (Root)</td></tr>
<tr><td><b>●</b></td><td>Pflichtfeld (Required)</td></tr>
<tr><td><b>○</b></td><td>Optionales Feld</td></tr>
<tr><td><b>→</b></td><td>Referenz ($ref)</td></tr>
</table>""",

        # JSON Tree View
        "code_view": "Code",
        "tree_view": "Baumansicht",
        "expand_all": "Alle aufklappen",
        "collapse_all": "Alle zuklappen",
        "search": "Suchen",
        "search_results": "Ergebnisse durchsuchen...",
        "filter_results": "Ergebnisse filtern...",

        # Status Bar
        "status_file_count": "{} Datei(en)",
        "status_errors": "{} Fehler",
        "status_warnings": "{} Warnungen",
        "status_infos": "{} Infos",
        "status_valid": "Gültig",
        "status_invalid_json": "Ungültiges JSON: {}",
        "tooltip_parse_error": "{}: Parse-Fehler - {}",
        "tooltip_invalid_full": "{}: {} Fehler, {} Warnungen, {} Infos",
        "tooltip_warnings_full": "{}: {} Warnungen, {} Infos",
        "tooltip_infos_full": "{}: {} Infos",
        "tooltip_valid_full": "{}: Keine Probleme gefunden",

        # Schema View
        "schema_view": "Schema-Ansicht",
        "schema_select": "Schema auswählen",
        "schema_reload": "Neu laden",
        "schema_element": "Element",
        "schema_type": "Typ",
        "schema_constraints": "Einschränkungen",
        "schema_cardinality": "Kardinalität",
        "schema_required": "Pflichtfeld",
        "schema_optional": "Optional",
        "schema_definitions": "Definitionen",
        "schema_no_schema": "Kein Schema geladen",
        "schema_loading": "Schema wird geladen...",
        "expand_here": "Ab hier aufklappen",
        "collapse_here": "Ab hier einklappen",
        "fit_view": "Ansicht einpassen",

        # Version Display
        "current_schema_version": "Aktuelle Schema-Version",
        "current_ruleset": "Aktuelle Regeln",
        "no_custom_rules": "Keine (Standard)",
        "schema_version_label": "Schema",
        "ruleset_label": "Regeln",

        # Validation Mode
        "validation_mode": "Validierungsmodus",
        "schema_only": "Nur Schema",
        "schema_and_rules": "Schema + Regeln",
        "tooltip_schema_only": "Nur gegen JSON Schema validieren (ohne zusätzliche Regeln)",
        "tooltip_schema_and_rules": "Gegen JSON Schema UND zusätzliche Regeln validieren",

        # Error Classification
        "source": "Quelle",
        "schema_violation": "Schema-Verletzung",
        "rule_violation": "Regel-Verletzung",
        "error_source": "Fehlerquelle",
    },

    "en": {
        # Menu and main window
        "app_title": "VDV463 JSON Validator",
        "app_subtitle": "Electric Bus Charging Infrastructure",
        "file": "File",
        "language": "Language",
        "help": "Help",

        # File menu
        "open_files": "Open JSON Files...",
        "close_selected": "Close Selected",
        "close_all": "Close All",
        "save_json": "Save JSON",
        "save_as": "Save As...",
        "export_results": "Export Results...",
        "exit": "Exit",

        # Buttons
        "add_files": "Add Files",
        "remove_selected": "Remove Selected",
        "validate": "Validate",
        "validate_all": "Validate All",
        "clear_results": "Clear Results",
        "goto_error": "Go to Error",

        # Tooltips
        "tooltip_add_files": "Add JSON files to validate (Ctrl+O)",
        "tooltip_remove_selected": "Remove selected files from the list",
        "tooltip_validate": "Validate current file (Ctrl+Shift+V)",
        "tooltip_validate_all": "Validate all loaded files (F5)",
        "tooltip_clear_results": "Clear validation results",
        "tooltip_goto_error": "Jump to selected error in editor (F8)",
        "tooltip_format_json": "Format and indent JSON code (Ctrl+Shift+F)",
        "tooltip_load_rules": "Load custom validation rules from YAML file",
        "tooltip_schema_version": "Select VDV463 schema version (auto = automatic detection)",
        "tooltip_file_list": "List of loaded JSON files. Double-click to open.",
        "tooltip_json_editor": "JSON editor with syntax highlighting. Edit your files here.",
        "tooltip_results_panel": "Validation results. Double-click an error to jump to the corresponding line.",
        "tooltip_save": "Save current file (Ctrl+S)",
        "tooltip_save_as": "Save current file with new name (Ctrl+Shift+S)",

        # Labels
        "loaded_files": "Loaded Files",
        "json_editor": "JSON Editor",
        "validation_results": "Validation Results",
        "schema_version": "Schema Version",
        "rule_config": "Rule Configuration",
        "no_file": "No file selected",
        "file_count": "Files: {}",

        # Results
        "status": "Status",
        "line": "Line",
        "severity": "Severity",
        "path": "Path",
        "message": "Message",
        "value": "Value",
        "duration": "Duration",

        # Severity levels
        "ERROR": "ERROR",
        "WARNING": "WARNING",
        "INFO": "INFO",

        # Messages
        "validation_passed": "✓ Validation passed",
        "validation_failed": "✗ Validation failed",
        "errors": "Errors",
        "warnings": "Warnings",
        "infos": "Infos",
        "no_issues": "No issues found",
        "select_file_first": "Please select a file first",
        "no_files_loaded": "No files loaded",
        "invalid_json": "Invalid JSON",
        "file_saved": "File saved: {}",
        "results_exported": "Results exported: {}",
        "error_loading_file": "Error loading file: {}",
        "error_saving_file": "Error saving file: {}",

        # Batch validation
        "batch_validation": "Batch Validation",
        "validating_file": "Validating {} of {}: {}",
        "batch_complete": "Batch validation complete",
        "total_files": "Total Files",
        "passed": "Passed",
        "failed": "Failed",
        "total_errors": "Total Errors",
        "total_warnings": "Total Warnings",
        "total_infos": "Total Infos",

        # Rule configuration
        "load_rules": "Load Rules...",
        "no_rules": "None (Default Rules)",
        "rules_loaded": "Rules loaded: {}",
        "error_loading_rules": "Error loading rules: {}",

        # Dialogs
        "confirm": "Confirm",
        "cancel": "Cancel",
        "ok": "OK",
        "warning": "Warning",
        "error": "Error",
        "information": "Information",
        "unsaved_changes_single": "File {} has unsaved changes. Save before closing?",
        "unsaved_changes_multiple": "{} file(s) have unsaved changes. Save all before closing?",

        # Context menu
        "copy": "Copy",
        "copy_selected": "Copy Selected",
        "copy_all": "Copy All",
        "export_selected_csv": "Export Selected (CSV)...",
        "export_all_csv": "Export All (CSV)...",
        "export_results_title": "Export Results",
        "export_error_title": "Export Error",
        "export_error_msg": "Error exporting: {}",
        "copy_path": "Copy Path",
        "copy_value": "Copy Value",
        "select_all": "Select All",
        "find": "Find...",

        # New features
        "format_json": "Format JSON",
        "minify_json": "Minify JSON",
        "recent_files": "Recent Files",
        "no_recent_files": "No recent files",
        "clear_recent": "Clear List",
        "edit": "Edit",
        "undo": "Undo",
        "redo": "Redo",
        "cut": "Cut",
        "paste": "Paste",
        "line_column": "Line: {}, Column: {}",
        "file_size": "Size: {}",
        "drop_files_here": "Drop files here",

        # About
        "about": "About",
        "about_text": "VDV463 JSON Validator\nVersion 3.0.0\n\nA tool for validating VDV463 messages.",

        # Keyboard shortcuts
        "keyboard_shortcuts": "Keyboard Shortcuts",
        "shortcuts_title": "Keyboard Shortcuts",
        "shortcuts_text": """<h3>File</h3>
<table>
<tr><td><b>Ctrl+O</b></td><td>Open files</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save</td></tr>
<tr><td><b>Ctrl+Shift+S</b></td><td>Save As</td></tr>
<tr><td><b>Ctrl+W</b></td><td>Close file</td></tr>
</table>

<h3>Edit</h3>
<table>
<tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
<tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
<tr><td><b>Ctrl+X</b></td><td>Cut</td></tr>
<tr><td><b>Ctrl+C</b></td><td>Copy</td></tr>
<tr><td><b>Ctrl+V</b></td><td>Paste</td></tr>
<tr><td><b>Ctrl+Shift+F</b></td><td>Format JSON</td></tr>
<tr><td><b>Ctrl+Shift+M</b></td><td>Minify JSON</td></tr>
</table>

<h3>Validation</h3>
<table>
<tr><td><b>Ctrl+Shift+V</b></td><td>Validate current file</td></tr>
<tr><td><b>F5</b></td><td>Validate all files</td></tr>
<tr><td><b>F8</b></td><td>Go to next error</td></tr>
</table>

<h3>Schema View</h3>
<table>
<tr><td><b>Alt+Left</b></td><td>Navigate back</td></tr>
<tr><td><b>Alt+Right</b></td><td>Navigate forward</td></tr>
<tr><td><b>Home</b></td><td>Go to root</td></tr>
<tr><td><b>Right-click</b></td><td>Navigate back</td></tr>
<tr><td><b>Mouse wheel</b></td><td>Zoom</td></tr>
<tr><td><b>Left-click + Drag</b></td><td>Pan view</td></tr>
<tr><td><b>Click on Reference</b></td><td>Navigate to definition</td></tr>
</table>

<h3>Symbols</h3>
<table>
<tr><td><b>⌂</b></td><td>Root element</td></tr>
<tr><td><b>●</b></td><td>Required field</td></tr>
<tr><td><b>○</b></td><td>Optional field</td></tr>
<tr><td><b>→</b></td><td>Reference ($ref)</td></tr>
</table>""",

        # JSON Tree View
        "code_view": "Code",
        "tree_view": "Tree View",
        "expand_all": "Expand All",
        "collapse_all": "Collapse All",
        "search": "Search",
        "search_results": "Search results...",
        "filter_results": "Filter results...",

        # Status Bar
        "status_file_count": "{} file(s)",
        "status_errors": "{} errors",
        "status_warnings": "{} warnings",
        "status_infos": "{} infos",
        "status_valid": "Valid",
        "status_invalid_json": "Invalid JSON: {}",
        "tooltip_parse_error": "{}: Parse error - {}",
        "tooltip_invalid_full": "{}: {} errors, {} warnings, {} infos",
        "tooltip_warnings_full": "{}: {} warnings, {} infos",
        "tooltip_infos_full": "{}: {} infos",
        "tooltip_valid_full": "{}: No issues found",

        # Schema View
        "schema_view": "Schema View",
        "schema_select": "Select Schema",
        "schema_reload": "Reload",
        "schema_element": "Element",
        "schema_type": "Type",
        "schema_constraints": "Constraints",
        "schema_cardinality": "Cardinality",
        "schema_required": "Required",
        "schema_optional": "Optional",
        "schema_definitions": "Definitions",
        "schema_no_schema": "No schema loaded",
        "schema_loading": "Loading schema...",
        "expand_here": "Expand from here",
        "collapse_here": "Collapse from here",
        "fit_view": "Fit to view",

        # Version Display
        "current_schema_version": "Current Schema Version",
        "current_ruleset": "Current Rules",
        "no_custom_rules": "None (Default)",
        "schema_version_label": "Schema",
        "ruleset_label": "Rules",

        # Validation Mode
        "validation_mode": "Validation Mode",
        "schema_only": "Schema Only",
        "schema_and_rules": "Schema + Rules",
        "tooltip_schema_only": "Validate against JSON Schema only (without additional rules)",
        "tooltip_schema_and_rules": "Validate against JSON Schema AND additional rules",

        # Error Classification
        "source": "Source",
        "schema_violation": "Schema Violation",
        "rule_violation": "Rule Violation",
        "error_source": "Error Source",
    }
}


class I18n:
    """Internationalization handler."""

    def __init__(self, language: str = "en"):
        """
        Initialize with default language.

        Args:
            language: Language code ("de" or "en")
        """
        self.language = language if language in TRANSLATIONS else "en"

    def set_language(self, language: str) -> None:
        """
        Set the current language.

        Args:
            language: Language code ("de" or "en")
        """
        if language in TRANSLATIONS:
            self.language = language

    def get(self, key: str, *args) -> str:
        """
        Get translated string.

        Args:
            key: Translation key
            *args: Format arguments

        Returns:
            Translated string, formatted with args if provided
        """
        translation = TRANSLATIONS[self.language].get(key, key)
        if args:
            try:
                return translation.format(*args)
            except (IndexError, KeyError):
                return translation
        return translation

    def __call__(self, key: str, *args) -> str:
        """Shorthand for get()."""
        return self.get(key, *args)


# Global instance (can be changed at runtime)
_i18n = I18n("en")


def get_i18n() -> I18n:
    """Get global i18n instance."""
    return _i18n


def set_language(language: str) -> None:
    """Set global language."""
    _i18n.set_language(language)


def t(key: str, *args) -> str:
    """
    Translate key (shorthand).

    Args:
        key: Translation key
        *args: Format arguments

    Returns:
        Translated string
    """
    return _i18n.get(key, *args)
