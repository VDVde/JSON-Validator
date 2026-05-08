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
Theme management for the VDV463 Validator UI.

Provides functions to detect dark mode and returns appropriate
stylesheets and color palettes for the application.
"""

import darkdetect
from PySide6.QtGui import QColor


def is_dark_mode() -> bool:
    """Check if the OS is in dark mode."""
    return darkdetect.isDark()


class Palette:
    """A color palette for the application."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, QColor(value))


# Palettes for light and dark themes
light_palette = Palette(
    window_bg="#f8f9fa",
    text_color="#212529",
    editor_bg="#ffffff",
    editor_text="#212529",
    line_number_bg="#f1f3f5",
    line_number_text="#adb5bd",
    current_line_bg="#e7f5ff",  # Light blue for current line
    error_highlight="#fff5f5",  # Light red/pink for errors (better readability)
    schema_bg="#ffffff",
    schema_node_bg="#ffffff",  # Default for general nodes
    schema_node_border="#dee2e6",  # Grey border
    schema_line="#adb5bd",
    schema_arrow="#868e96",
    # JSON Highlighter colors
    key="#0056b3",
    string="#2b8a3e",
    number="#1864ab",
    keyword="#c92a2a",
    bracket="#343a40",
    # JSON Tree View colors
    tree_object="#1971c2",
    tree_array="#862e9c",
    tree_string="#2b8a3e",
    tree_number="#1864ab",
    tree_boolean="#c92a2a",
    tree_null="#868e96",
    # Schema Node colors
    schema_object_bg_1="#e7f5ff", schema_object_bg_2="#d0ebff",
    schema_array_bg_1="#f8f9fa", schema_array_bg_2="#e9ecef",
    schema_string_bg_1="#f4fce3", schema_string_bg_2="#ebfbee",
    schema_number_bg_1="#fff9db", schema_number_bg_2="#fff3bf",
    schema_boolean_bg_1="#fff0f6", schema_boolean_bg_2="#ffdeeb",
    schema_enum_bg_1="#f3f0ff", schema_enum_bg_2="#e5dbff",
    schema_ref_bg_1="#fff9db", schema_ref_bg_2="#fff3bf",
    schema_root_bg_1="#f1f3f5", schema_root_bg_2="#e9ecef",
    schema_required_border="#228be6", schema_optional_border="#adb5bd",
    schema_line_color="#ced4da", schema_arrow_color="#868e96",
    text_color_light="#495057", text_color_lighter="#868e96",
    text_color_description="#868e96",
    breadcrumb_bg="#ffffff",
    breadcrumb_hover_bg="#e7f5ff",
    breadcrumb_text="#343a40",
    breadcrumb_border="#dee2e6",
    schema_cardinality_text="#1c7ed6",
    # Modern Accents
    accent_primary="#228be6",
    accent_hover="#1c7ed6",
    border_color="#dee2e6",
)

dark_palette = Palette(
    window_bg="#1e1e1e",
    text_color="#d4d4d4",
    editor_bg="#1e1e1e",
    editor_text="#d4d4d4",
    line_number_bg="#1e1e1e",
    line_number_text="#858585",
    current_line_bg="#2a2d2e",
    error_highlight="#4b1818",
    schema_bg="#181818",
    schema_node_bg="#252526",
    schema_node_border="#454545",
    schema_line="#555555",
    schema_arrow="#888888",
    # JSON Highlighter colors - VS Code inspired
    key="#9cdcfe",
    string="#ce9178",
    number="#b5cea8",
    keyword="#c586c0",
    bracket="#ffd700",
    # JSON Tree View colors
    tree_object="#4fc1ff",
    tree_array="#dcdcaa",
    tree_string="#ce9178",
    tree_number="#b5cea8",
    tree_boolean="#569cd6",
    tree_null="#808080",
    # Schema Node colors - Modern Dark
    schema_object_bg_1="#303031", schema_object_bg_2="#3c3c3c",
    schema_array_bg_1="#25352a", schema_array_bg_2="#2d4535",
    schema_string_bg_1="#353525", schema_string_bg_2="#45452d",
    schema_number_bg_1="#253035", schema_number_bg_2="#2d3c45",
    schema_boolean_bg_1="#352525", schema_boolean_bg_2="#452d2d",
    schema_enum_bg_1="#2d2535", schema_enum_bg_2="#3a2d45",
    schema_ref_bg_1="#353025", schema_ref_bg_2="#453c2d",
    schema_root_bg_1="#2d2d2d", schema_root_bg_2="#333333",
    schema_required_border="#007acc", schema_optional_border="#454545",
    schema_line_color="#555555", schema_arrow_color="#888888",
    text_color_light="#cccccc", text_color_lighter="#aaaaaa",
    text_color_description="#888888",
    breadcrumb_bg="#252526",
    breadcrumb_hover_bg="#2a2d2e",
    breadcrumb_text="#cccccc",
    breadcrumb_border="#454545",
    schema_cardinality_text="#ffffff",
    # Modern Accents
    accent_primary="#007acc",
    accent_hover="#1c97ea",
    border_color="#3c3c3c",
)


def get_palette(dark_mode: bool) -> Palette:
    """Return the color palette for the current theme."""
    return dark_palette if dark_mode else light_palette


def get_validate_button_style(dark_mode: bool) -> str:
    """Return the stylesheet for the prominent validate button."""
    if dark_mode:
        return """
            QPushButton {
                background-color: #2d6a4f;
                color: #e8f5e9;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                border: 1px solid #40916c;
            }
            QPushButton:hover {
                background-color: #40916c;
            }
            QPushButton:pressed {
                background-color: #1b4332;
            }
        """
    else:
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                border: 1px solid #388e3c;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #2e7d32;
            }
        """


def get_stylesheet(dark_mode: bool) -> str:
    """Return a comprehensive modern QSS stylesheet for the current theme."""
    p = get_palette(dark_mode)

    # Common variables
    bg = p.window_bg.name()
    text = p.text_color.name()
    border = p.border_color.name()
    accent = p.accent_primary.name()

    # Base stylesheet
    style = f"""
        QWidget {{
            background-color: {bg};
            color: {text};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }}

        QMainWindow, QDialog {{
            background-color: {bg};
        }}

        /* Toolbars */
        QToolBar {{
            background-color: {bg};
            border-bottom: 1px solid {border};
            spacing: 10px;
            padding: 5px;
        }}

        QToolButton {{
            background-color: transparent;
            border-radius: 4px;
            padding: 4px;
        }}

        QToolButton:hover {{
            background-color: {p.current_line_bg.name()};
        }}

        /* Tab Bar */
        QTabWidget::pane {{
            border: 1px solid {border};
            top: -1px;
            background-color: {bg};
        }}

        QTabBar::tab {{
            background-color: {p.line_number_bg.name()};
            border: 1px solid {border};
            border-bottom: none;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {p.editor_bg.name()};
            border-bottom: 2px solid {accent};
            font-weight: bold;
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {p.current_line_bg.name()};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {p.line_number_bg.name()};
            border: 1px solid {border};
            padding: 6px 12px;
            border-radius: 4px;
        }}

        QPushButton:hover {{
            background-color: {p.current_line_bg.name()};
            border-color: {accent};
        }}

        QPushButton:pressed {{
            background-color: {border};
        }}

        /* Inputs */
        QLineEdit, QComboBox, QSpinBox {{
            background-color: {p.editor_bg.name()};
            border: 1px solid {border};
            padding: 5px;
            border-radius: 4px;
        }}

        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {accent};
        }}

        /* Lists and Trees */
        QListWidget, QTreeWidget {{
            background-color: {p.editor_bg.name()};
            border: 1px solid {border};
            border-radius: 4px;
            outline: none;
        }}

        QListWidget::item, QTreeWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {p.error_highlight.name() if dark_mode else "#f1f3f5"};
        }}

        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {accent};
            color: white;
        }}

        QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {{
            background-color: {p.current_line_bg.name()};
        }}

        QHeaderView::section {{
            background-color: {p.line_number_bg.name()};
            padding: 6px;
            border: none;
            border-right: 1px solid {border};
            border-bottom: 1px solid {border};
            font-weight: bold;
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {border};
        }}

        QSplitter::handle:horizontal {{
            width: 4px;
        }}

        QSplitter::handle:vertical {{
            height: 4px;
        }}

        /* ScrollBars */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {border};
            min-height: 20px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {accent};
        }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:horizontal {{
            background: {border};
            min-width: 20px;
            border-radius: 5px;
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}

        /* StatusBar */
        QStatusBar {{
            background-color: {bg};
            border-top: 1px solid {border};
            color: {p.text_color_light.name()};
        }}

        QLabel#StatusLabel {{
            font-weight: bold;
        }}
    """

    return style
