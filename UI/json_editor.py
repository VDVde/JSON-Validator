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
JSON Editor with line numbers and syntax highlighting.
Custom QPlainTextEdit-based editor for JSON files.
"""

import re

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class JSONHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for JSON content."""

    def __init__(self, parent=None, palette=None):
        super().__init__(parent)
        self.palette = palette
        self._init_formats()
        self._init_rules()

    def set_theme(self, palette) -> None:
        """Set the theme for the highlighter."""
        self.palette = palette
        self._init_formats()
        self.rehighlight()

    def _init_formats(self) -> None:
        """Initialize text formats for different JSON elements."""
        p = self.palette
        # Keys (property names)
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(p.key)
        self.key_format.setFontWeight(QFont.Weight.Bold)

        # String values
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(p.string)

        # Numbers
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(p.number)

        # Booleans and null
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(p.keyword)
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        # Brackets and braces
        self.bracket_format = QTextCharFormat()
        self.bracket_format.setForeground(p.bracket)
        self.bracket_format.setFontWeight(QFont.Weight.Bold)

    def _init_rules(self) -> None:
        """Initialize highlighting rules."""
        self.rules = []

        # JSON keys (property names before colon)
        self.rules.append((re.compile(r'"(?:[^"\\]|\\.)*"\s*(?=:)'), self.key_format))
        # Numbers
        self.rules.append((re.compile(r'\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b'), self.number_format))
        # Booleans and null
        self.rules.append((re.compile(r'\b(?:true|false|null)\b'), self.keyword_format))
        # Brackets and braces
        self.rules.append((re.compile(r'[\[\]{}]'), self.bracket_format))

    def highlightBlock(self, text: str) -> None:
        """Apply syntax highlighting to a block of text."""
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

        # Highlight string values
        string_pattern = re.compile(r'"(?:[^"\\]|\\.)*"')
        for match in string_pattern.finditer(text):
            rest = text[match.end():].lstrip()
            if not rest.startswith(':'):
                self.setFormat(match.start(), match.end() - match.start(), self.string_format)


class LineNumberArea(QWidget):
    """Widget for displaying line numbers."""

    def __init__(self, editor: 'JSONCodeEditor'):
        super().__init__(editor)
        self.editor = editor
        self.palette = editor.palette

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.editor.line_number_area_paint_event(event)

    def set_theme(self, palette):
        self.palette = palette
        self.update()


class JSONCodeEditor(QPlainTextEdit):
    """
    Code editor with line numbers and JSON syntax highlighting.
    """

    def __init__(self, parent=None, palette=None):
        super().__init__(parent)
        self.palette = palette
        self._error_selections = []

        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.line_number_area = LineNumberArea(self)
        self.highlighter = JSONHighlighter(self.document(), self.palette)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.set_theme(self.palette)

        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

    def set_theme(self, palette):
        self.palette = palette
        self.highlighter.set_theme(palette)
        self.line_number_area.set_theme(palette)

        # Set editor background and text color
        bg_color = palette.editor_bg.name()
        text_color = palette.editor_text.name()
        self.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")

        self.highlight_current_line()
        self.update()

    def line_number_area_width(self) -> int:
        digits = len(str(self.blockCount()))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = self.palette.current_line_bg
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        extra_selections.extend(self._error_selections)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        bg_color = self.palette.line_number_bg
        painter.fillRect(event.rect(), QColor(bg_color))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(self.palette.line_number_text)
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def set_error_highlight(self, line: int, color: QColor | None = None) -> None:
        if color is None:
            color = self.palette.error_highlight

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(color)
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        doc = self.document()
        if doc:
            cursor = QTextCursor(doc.findBlockByLineNumber(line - 1))
            selection.cursor = cursor
            self._error_selections.append(selection)
            self.highlight_current_line()

    def clear_error_highlights(self) -> None:
        self._error_selections = []
        self.highlight_current_line()

    def goto_line(self, line: int) -> None:
        doc = self.document()
        if not doc:
            return
        block = doc.findBlockByLineNumber(line - 1)
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()

    def get_current_line(self) -> int:
        return self.textCursor().blockNumber() + 1

    def get_current_column(self) -> int:
        return self.textCursor().columnNumber() + 1
