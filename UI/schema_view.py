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
JSON Schema Diagram View Widget

A graphical schema viewer using QGraphicsView/QGraphicsScene to display
JSON Schema structure as connected boxes/nodes showing:
- Elements and their structure (properties, items)
- Data types (string, number, boolean, array, object)
- Constraints (minLength, maxLength, pattern, enum, etc.)
- Required properties
- References ($ref) and definitions
- Cardinality (minItems, maxItems for arrays)
"""

import html
import json
import math
import re
from pathlib import Path

from i18n import t
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# =============================================================================
# Constants
# =============================================================================

# JSON Schema $ref prefix for definitions
DEFINITIONS_PREFIX = "#/definitions/"
DEFINITIONS_PREFIX_LENGTH = len(DEFINITIONS_PREFIX)


# =============================================================================
# Color Scheme
# =============================================================================


class SchemaColors:
    """Color scheme for schema visualization."""

    def __init__(self, palette):
        self.palette = palette
        self.OBJECT_BG = (palette.schema_object_bg_1, palette.schema_object_bg_2)
        self.ARRAY_BG = (palette.schema_array_bg_1, palette.schema_array_bg_2)
        self.STRING_BG = (palette.schema_string_bg_1, palette.schema_string_bg_2)
        self.NUMBER_BG = (palette.schema_number_bg_1, palette.schema_number_bg_2)
        self.BOOLEAN_BG = (palette.schema_boolean_bg_1, palette.schema_boolean_bg_2)
        self.ENUM_BG = (palette.schema_enum_bg_1, palette.schema_enum_bg_2)
        self.REF_BG = (palette.schema_ref_bg_1, palette.schema_ref_bg_2)
        self.ROOT_BG = (palette.schema_root_bg_1, palette.schema_root_bg_2)
        self.COMBINATOR_BG = (palette.schema_enum_bg_1, palette.schema_enum_bg_2)  # Use enum-like color for combinators
        self.REQUIRED_BORDER = palette.schema_required_border
        self.OPTIONAL_BORDER = palette.schema_optional_border
        self.TITLE_COLOR = palette.text_color
        self.TYPE_COLOR = palette.text_color_light
        self.CONSTRAINT_COLOR = palette.text_color_lighter
        self.LINE_COLOR = palette.schema_line_color
        self.ARROW_COLOR = palette.schema_arrow_color

    TYPE_ICONS = {
        "object": "⚙️", "array": "📚", "string": "🅰️", "number": "🔢",
        "integer": "🔢", "boolean": "⚪", "enum": "📋", "ref": "🔗", "any": "❓",
        "allOf": "🤝", "anyOf": "🌀", "oneOf": "🎯", "not": "🚫"
    }


# =============================================================================
# Schema Node (Box) Item
# =============================================================================


class SchemaNodeItem(QGraphicsRectItem):
    """
    A graphical box representing a schema element.

    Displays:
    - Element name (bold, top)
    - Type indicator with icon (italic)
    - Constraints (small text)
    - Required indicator (bold border)
    - Cardinality badge

    Supports click navigation for $ref elements.
    """

    # Node dimensions
    MIN_WIDTH = 160
    MAX_WIDTH = 500
    HEADER_HEIGHT = 28
    PADDING = 8
    CORNER_RADIUS = 8

    def __init__(
            self,
            name: str,
            schema_data: dict,
            colors: SchemaColors,
            is_required: bool = False,
            is_root: bool = False,
            parent: QGraphicsItem | None = None,
            parent_node: "SchemaNodeItem | None" = None,
    ):
        super().__init__(parent)

        self.name = name
        self.schema_data = schema_data
        self.colors = colors
        self.is_required = is_required
        self.is_root = is_root
        self.parent_node_item = parent_node
        self.child_nodes: list[SchemaNodeItem] = []
        self.connection_lines: list[ConnectionLine] = []
        self.type_str = ""
        self.constraints_str = ""

        # Layout attributes for hierarchical positioning
        self.depth: int = 0  # Depth in tree hierarchy (0 for root)
        self.layout_y: float = 0.0  # Calculated Y position for layout

        # Expansion state
        self.is_expanded: bool = False

        # Reference tracking for navigation
        self._ref_target: str | None = None
        self._is_clickable = False

        # Calculate dimensions based on content
        self._calculate_size()

        # Setup appearance
        self._setup_appearance()

        # Make interactive
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        # We handle clicks ourselves now
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

        # Check if this is a clickable reference (must be before tooltip setup)
        self._setup_click_behavior()

        # Setup tooltip with documentation
        self._setup_tooltip()

        # Ensure nodes are above lines
        self.setZValue(10)

    def mousePressEvent(self, event):
        """Record press position for drag detection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
            event.accept()
        else:
            # Let other buttons (like right click) bubble up for context menu
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click for navigation."""
        if event.button() == Qt.MouseButton.RightButton:
            # Double Right click: Focus on parent node
            if self.parent_node_item:
                if self.scene() and hasattr(self.scene(), 'nodeFocusRequested'):
                    self.scene().nodeFocusRequested.emit(self.parent_node_item)
                event.accept()
            else:
                super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle click for focus navigation (toggle expansion if not dragged)."""
        if event.button() == Qt.MouseButton.LeftButton and hasattr(self, '_press_pos'):
            # Check if we moved enough to consider it a drag
            # If movement is small, treat as a click to toggle
            if (event.pos() - self._press_pos).manhattanLength() < 10:
                # Toggle expansion and Focus on this node
                self.set_expanded(not self.is_expanded)

                # The layout update happens in set_expanded
                # We request focus after layout is updated
                if self.scene() and hasattr(self.scene(), 'nodeFocusRequested'):
                    self.scene().nodeFocusRequested.emit(self)

            del self._press_pos
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def set_expanded(self, expanded: bool):
        """Set expansion state and update children visibility."""
        if self.is_expanded != expanded:
            self.is_expanded = expanded
            self.update_subtree_visibility()

            # Trigger layout update if in a scene
            if self.scene() and hasattr(self.scene(), 'update_layout'):
                self.scene().update_layout()

    def update_subtree_visibility(self):
        """Recursively update visibility of children based on expansion state."""
        # Children are visible only if this node is visible AND expanded
        children_visible = self.isVisible() and self.is_expanded

        for child in self.child_nodes:
            child.setVisible(children_visible)

            # Update connection lines
            for line in self.connection_lines:
                if line.end_node == child:
                    line.setVisible(children_visible)

            # Recurse
            child.update_subtree_visibility()

    def reveal_tree(self, expand_self: bool = False):
        """Ensure this node and all its ancestors are expanded and visible."""
        # Walk up the tree and expand all parents
        parent = self.parent_node_item
        while parent:
            parent.set_expanded(True)
            parent = parent.parent_node_item

        if expand_self:
            self.set_expanded(True)

        # Ensure self is visible (should be handled by parent expansion, but safe to check)
        self.setVisible(True)

    def expand_subtree(self, recursive: bool = True):
        """Recursively expand this node and optionally all descendants."""
        self.is_expanded = True
        if recursive:
            for child in self.child_nodes:
                child.expand_subtree(True)

        self.update_subtree_visibility()

    def collapse_subtree(self, recursive: bool = True):
        """Recursively collapse this node and optionally all descendants."""
        # For collapse "from here", we usually want the node itself to stay visible
        # but its children to hide. So we set is_expanded = False.
        self.is_expanded = False
        if recursive:
            for child in self.child_nodes:
                child.collapse_subtree(True)

        self.update_subtree_visibility()

    def _calculate_size(self) -> None:
        """Calculate node size based on content."""
        # Determine type string
        self.type_str = self._get_type_string()
        self.constraints_str = self._get_constraints_string()

        # Calculate width based on name (Bold 10pt)
        name_font = QFont("Segoe UI", 10)
        name_font.setBold(True)
        name_fm = QFontMetrics(name_font)

        # Indicator prefix (the house or dots)
        if self.is_root:
            display_name = f"⌂ {self.name}"
        elif self.is_required:
            display_name = f"● {self.name}"
        else:
            display_name = f"○ {self.name}"

        name_width = name_fm.horizontalAdvance(display_name) + 40

        # Calculate width based on type (Italic 9pt)
        type_font = QFont("Segoe UI", 9)
        type_font.setItalic(True)
        type_fm = QFontMetrics(type_font)

        icon = self._get_type_icon()
        type_display = f"{icon} {self.type_str}"
        type_width = type_fm.horizontalAdvance(type_display) + 60

        # For enums, also consider constraint string width
        constraint_width = 0
        const_font = QFont("Segoe UI", 8)
        const_fm = QFontMetrics(const_font)
        if self.constraints_str:
            constraint_width = const_fm.horizontalAdvance(self.constraints_str) + 40

        # Allow wider nodes for enums
        max_width = 500 if "enum" in self.schema_data else self.MAX_WIDTH
        width = max(self.MIN_WIDTH, min(max_width, max(name_width, type_width, constraint_width)))

        # Height based on content
        height = self.HEADER_HEIGHT + self.PADDING * 2
        if self.type_str:
            height += 18
        if self.constraints_str:
            # More height for enum values
            if "enum" in self.schema_data:
                height += 20
            else:
                height += 16
        if "description" in self.schema_data:
            height += 16

        self.setRect(0, 0, width, height)

    def _get_type_string(self) -> str:
        """Get the type string for display."""
        for combinator in ("allOf", "anyOf", "oneOf", "not"):
            if combinator in self.schema_data:
                return combinator

        if "$ref" in self.schema_data:
            ref = self.schema_data["$ref"]
            if ref.startswith(DEFINITIONS_PREFIX):
                return f"→ {ref[DEFINITIONS_PREFIX_LENGTH:]}"
            return f"→ {ref}"

        schema_type = self.schema_data.get("type", "")
        if isinstance(schema_type, list):
            return " | ".join(schema_type)

        if schema_type == "array":
            items = self.schema_data.get("items", {})
            if "$ref" in items:
                ref = items["$ref"]
                if ref.startswith(DEFINITIONS_PREFIX):
                    return f"[{ref[DEFINITIONS_PREFIX_LENGTH:]}]"
                return f"[{ref}]"
            item_type = items.get("type", "any")
            return f"[{item_type}]"

        return schema_type or "any"

    def _get_type_icon(self) -> str:
        """Get the icon for the schema type."""
        for combinator in ("allOf", "anyOf", "oneOf", "not"):
            if combinator in self.schema_data:
                return self.colors.TYPE_ICONS.get(combinator, "❓")

        if "$ref" in self.schema_data or (
                self.schema_data.get("type") == "array" and "$ref" in self.schema_data.get("items", {})):
            return self.colors.TYPE_ICONS.get("ref", "❓")

        schema_type = self.schema_data.get("type", "any")
        if isinstance(schema_type, list):
            schema_type = schema_type[0]  # Take first type for icon

        if "enum" in self.schema_data:
            return self.colors.TYPE_ICONS.get("enum", "❓")

        return self.colors.TYPE_ICONS.get(schema_type, "❓")

    def _get_constraints_string(self) -> str:
        """Get constraint summary string."""
        constraints = []

        # Format
        if "format" in self.schema_data:
            constraints.append(self.schema_data["format"])

        # String constraints
        if "minLength" in self.schema_data or "maxLength" in self.schema_data:
            min_l = self.schema_data.get("minLength", "")
            max_l = self.schema_data.get("maxLength", "")
            constraints.append(f"len:{min_l}..{max_l}")

        if "pattern" in self.schema_data:
            constraints.append("regex")

        # Number constraints
        if "minimum" in self.schema_data or "maximum" in self.schema_data:
            min_v = self.schema_data.get("minimum", "")
            max_v = self.schema_data.get("maximum", "")
            constraints.append(f"{min_v}..{max_v}")

        # Enum - show actual values
        if "enum" in self.schema_data:
            enum_values = self.schema_data["enum"]
            if len(enum_values) <= 5:
                # Show all values if 5 or fewer
                values_str = " | ".join(str(v) for v in enum_values)
                constraints.append(values_str)
            else:
                # Show first 4 values + count for longer enums
                shown = " | ".join(str(v) for v in enum_values[:4])
                constraints.append(f"{shown} +{len(enum_values) - 4}")

        # Metadata properties
        if "default" in self.schema_data:
            constraints.append(f"def:{self.schema_data['default']}")
        if self.schema_data.get("readOnly"):
            constraints.append("R-O")
        if self.schema_data.get("writeOnly"):
            constraints.append("W-O")
        if self.schema_data.get("deprecated"):
            constraints.append("Deprecated")

        return ", ".join(constraints)

    def _get_background_colors(self) -> tuple[QColor, QColor]:
        """Get gradient colors based on type."""
        for combinator in ("allOf", "anyOf", "oneOf", "not"):
            if combinator in self.schema_data:
                return self.colors.COMBINATOR_BG

        if "$ref" in self.schema_data:
            return self.colors.REF_BG

        schema_type = self.schema_data.get("type", "")

        if schema_type == "object" or "properties" in self.schema_data:
            return self.colors.OBJECT_BG
        elif schema_type == "array":
            return self.colors.ARRAY_BG
        elif schema_type == "string":
            if "enum" in self.schema_data:
                return self.colors.ENUM_BG
            return self.colors.STRING_BG
        elif schema_type in ("number", "integer"):
            return self.colors.NUMBER_BG
        elif schema_type == "boolean":
            return self.colors.BOOLEAN_BG
        else:
            return self.colors.ROOT_BG

    def _setup_appearance(self) -> None:
        """Setup visual appearance."""
        # Gradient background
        color1, color2 = self._get_background_colors()
        gradient = QLinearGradient(0, 0, 0, self.rect().height())
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        self.setBrush(QBrush(gradient))

        # Border
        border_color = (
            self.colors.REQUIRED_BORDER if self.is_required else self.colors.OPTIONAL_BORDER
        )
        pen = QPen(border_color)
        pen.setWidth(2 if self.is_required else 1)
        self.setPen(pen)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Custom paint for rounded corners and all text content."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded rectangle background
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.CORNER_RADIUS, self.CORNER_RADIUS)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(path)

        # Draw header separator line
        header_y = self.HEADER_HEIGHT
        painter.setPen(QPen(QColor("#b0bec5"), 1))
        painter.drawLine(QPointF(0, header_y), QPointF(self.rect().width(), header_y))

        # --- Draw all text content directly ---

        # Title (name)
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(self.colors.TITLE_COLOR)
        if self.is_root:
            display_name = f"⌂ {self.name}"
        elif self.is_required:
            display_name = f"● {self.name}"
        else:
            display_name = f"○ {self.name}"
        painter.drawText(QRectF(self.PADDING, 2, self.rect().width() - self.PADDING * 2, self.HEADER_HEIGHT - 4),
                         display_name)

        # Type
        y_offset = self.HEADER_HEIGHT
        if self.type_str:
            type_font = QFont("Segoe UI", 9)
            type_font.setItalic(True)
            painter.setFont(type_font)
            painter.setPen(self.colors.TYPE_COLOR)
            icon = self._get_type_icon()
            painter.drawText(QRectF(self.PADDING, y_offset, self.rect().width() - self.PADDING * 2, 20),
                             f"{icon} {self.type_str}")
            y_offset += 18

        # Constraints
        if self.constraints_str:
            const_font = QFont("Segoe UI", 8)
            painter.setFont(const_font)
            painter.setPen(self.colors.CONSTRAINT_COLOR)
            painter.drawText(QRectF(self.PADDING, y_offset, self.rect().width() - self.PADDING * 2, 20),
                             self.constraints_str)
            y_offset += 16

        # Description snippet
        if "description" in self.schema_data:
            desc = self.schema_data["description"]
            if len(desc) > 35:
                desc = desc[:32] + "..."
            desc_font = QFont("Segoe UI", 7)
            desc_font.setItalic(True)
            painter.setFont(desc_font)
            painter.setPen(self.colors.palette.text_color_description)
            painter.drawText(QRectF(self.PADDING, y_offset, self.rect().width() - self.PADDING * 2, 20), desc)

    def get_right_anchor(self) -> QPointF:
        """Get connection point on right side."""
        return QPointF(
            self.scenePos().x() + self.rect().width(),
            self.scenePos().y() + self.rect().height() / 2,
        )

    def get_left_anchor(self) -> QPointF:
        """Get connection point on left side."""
        return QPointF(self.scenePos().x(), self.scenePos().y() + self.rect().height() / 2)

    def get_breadcrumb_path(self) -> str:
        """Calculate the full path from root to this node."""
        path_parts = []
        current = self
        while current:
            # Use name, but maybe cleaner without the indicators?
            # Indicator is handled in display logic, here we just want the name
            path_parts.append(current.name)
            current = current.parent_node_item

        # Reverse to get root-to-leaf
        return " > ".join(reversed(path_parts))

    def hoverEnterEvent(self, event):
        """Highlight on hover and show tooltip."""
        super().hoverEnterEvent(event)

        self.setOpacity(0.9)
        pen = self.pen()
        pen.setWidth(pen.width() + 1)
        self.setPen(pen)

        # Change cursor for clickable refs
        if self._is_clickable:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Emit breadcrumb path
        if self.scene() and hasattr(self.scene(), 'nodeHovered'):
            path = self.get_breadcrumb_path()
            self.scene().nodeHovered.emit(path)

        event.accept()

    def hoverLeaveEvent(self, event):
        """Remove highlight on leave."""
        super().hoverLeaveEvent(event)

        self.setOpacity(1.0)
        pen = self.pen()
        pen.setWidth(max(1, pen.width() - 1))
        self.setPen(pen)

        if self._is_clickable:
            self.unsetCursor()

        # Reset breadcrumb path
        if self.scene() and hasattr(self.scene(), 'nodeHovered'):
            self.scene().nodeHovered.emit("")

        event.accept()

    def _setup_click_behavior(self) -> None:
        """Setup click behavior for reference navigation."""
        # Check for direct $ref
        if "$ref" in self.schema_data:
            ref = self.schema_data["$ref"]
            if ref.startswith(DEFINITIONS_PREFIX):
                self._ref_target = ref[DEFINITIONS_PREFIX_LENGTH:]  # Extract definition name
                self._is_clickable = True

        # Check for array items with $ref
        elif self.schema_data.get("type") == "array":
            items = self.schema_data.get("items", {})
            if "$ref" in items:
                ref = items["$ref"]
                if ref.startswith(DEFINITIONS_PREFIX):
                    self._ref_target = ref[DEFINITIONS_PREFIX_LENGTH:]
                    self._is_clickable = True

    def _setup_tooltip(self) -> None:
        """Setup tooltip with element documentation."""
        tooltip_parts = []

        # Element name and type
        tooltip_parts.append(f"<b>{self.name}</b>")
        if self.type_str:
            tooltip_parts.append(f"<i>Typ: {self.type_str}</i>")

        # Required status
        status = "Pflichtfeld" if self.is_required else "Optional"
        tooltip_parts.append(f"Status: {status}")

        # Metadata
        metadata = []
        if "title" in self.schema_data:
            metadata.append(f"Titel: {self.schema_data['title']}")
        if "version" in self.schema_data:
            metadata.append(f"Version: {self.schema_data['version']}")
        if "$schema" in self.schema_data:
            metadata.append(f"Schema: {self.schema_data['$schema']}")
        if "$id" in self.schema_data:
            metadata.append(f"ID: {self.schema_data['$id']}")

        if metadata:
            tooltip_parts.append("<hr><b>Metadaten:</b><br>" + "<br>".join(metadata))

        # Description (full text)
        if "description" in self.schema_data:
            desc = html.escape(self.schema_data["description"])
            # Wrap long descriptions
            if len(desc) > 80:
                # Insert line breaks for readability
                words = desc.split()
                lines = []
                current_line = []
                current_len = 0
                for word in words:
                    if current_len + len(word) + 1 > 80:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        current_len = len(word)
                    else:
                        current_line.append(word)
                        current_len += len(word) + 1
                if current_line:
                    lines.append(" ".join(current_line))
                desc = "<br>".join(lines)
            tooltip_parts.append(f"<hr><b>Beschreibung:</b><br>{desc}")

        # Constraints
        constraints = []
        if "minLength" in self.schema_data:
            constraints.append(f"Min. Länge: {self.schema_data['minLength']}")
        if "maxLength" in self.schema_data:
            constraints.append(f"Max. Länge: {self.schema_data['maxLength']}")
        if "minimum" in self.schema_data:
            constraints.append(f"Minimum: {self.schema_data['minimum']}")
        if "maximum" in self.schema_data:
            constraints.append(f"Maximum: {self.schema_data['maximum']}")
        if "pattern" in self.schema_data:
            pattern = html.escape(str(self.schema_data['pattern']))
            constraints.append(f"Pattern: <code>{pattern}</code>")
        if "format" in self.schema_data:
            constraints.append(f"Format: {self.schema_data['format']}")
        if "minItems" in self.schema_data:
            constraints.append(f"Min. Elemente: {self.schema_data['minItems']}")
        if "maxItems" in self.schema_data:
            constraints.append(f"Max. Elemente: {self.schema_data['maxItems']}")

        if constraints:
            tooltip_parts.append("<hr><b>Einschränkungen:</b><br>" + "<br>".join(constraints))

        # Enum values (full list)
        if "enum" in self.schema_data:
            enum_values = self.schema_data["enum"]
            values_html = "<br>".join(f"• {html.escape(str(v))}" for v in enum_values)
            tooltip_parts.append(f"<hr><b>Erlaubte Werte ({len(enum_values)}):</b><br>{values_html}")

        # Reference hint
        if self._is_clickable and self._ref_target:
            tooltip_parts.append(f"<hr><i>🔗 Klicken um zu '{self._ref_target}' zu navigieren</i>")

        # Set tooltip
        tooltip_html = "<br>".join(tooltip_parts)
        self.setToolTip(tooltip_html)

    def get_ref_target(self) -> str | None:
        """Get the reference target name if this node is a reference."""
        return self._ref_target

    def set_highlighted(self, highlighted: bool):
        """Set the visual state of the node to highlighted or dimmed."""
        opacity = 1.0 if highlighted else 0.2
        self.setOpacity(opacity)
        for line in self.connection_lines:
            line.set_highlighted(highlighted)

    def set_error_highlight(self, is_error: bool):
        """Set error highlighting on this node."""
        if is_error:
            # Highlight with red border for errors
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(3)
            self.setPen(pen)
            self.setOpacity(1.0)
        else:
            # Restore normal border
            border_color = (
                self.colors.REQUIRED_BORDER if self.is_required else self.colors.OPTIONAL_BORDER
            )
            pen = QPen(border_color)
            pen.setWidth(2 if self.is_required else 1)
            self.setPen(pen)
            self.setOpacity(1.0)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Handle item changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Update connected lines when node moves
            for line in self.connection_lines:
                line.update_path()
                # Also update cardinality label position
                if line.cardinality_text:
                    line._add_cardinality_label()

        return super().itemChange(change, value)


# =============================================================================
# Connection Line
# =============================================================================


class ConnectionLine(QGraphicsPathItem):
    """
    A curved connection line between schema nodes.

    Draws a bezier curve with an optional arrow head.
    """

    def __init__(
            self,
            start_node: SchemaNodeItem,
            end_node: SchemaNodeItem,
            colors: SchemaColors,
            cardinality: str = "",
            label: str = "",
            parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent)

        self.start_node = start_node
        self.end_node = end_node
        self.colors = colors
        self.cardinality = cardinality
        self.label = label
        self.cardinality_text: QGraphicsTextItem | None = None

        self._setup_appearance()
        self.update_path()

        # Ensure lines are below nodes
        self.setZValue(1)

    def _setup_appearance(self) -> None:
        """Setup line appearance."""
        pen = QPen(self.colors.LINE_COLOR)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def update_path(self) -> None:
        """Update the path with orthogonal lines between nodes."""
        start = self.start_node.get_right_anchor()
        end = self.end_node.get_left_anchor()

        path = QPainterPath()
        path.moveTo(start)

        # Orthogonal connection (horizontal -> vertical -> horizontal)
        mid_x = start.x() + (end.x() - start.x()) / 2
        path.lineTo(mid_x, start.y())
        path.lineTo(mid_x, end.y())
        path.lineTo(end)

        self.setPath(path)

    def _add_cardinality_label(self) -> None:
        """Add cardinality/text label at uniform distance from end."""
        text = ""
        if self.cardinality:
            text = f"[{self.cardinality}]"

        if self.label:
            if text:
                text += f" {self.label}"
            else:
                text = self.label

        if not text:
            return

        # Position label at a uniform distance from the arrow tip
        path = self.path()
        total_length = path.length()
        # Fixed distance from the arrow tip (35 pixels looks good for clarity)
        offset = 35

        if total_length > offset:
            percentage = path.percentAtLength(total_length - offset)
            label_pos = path.pointAtPercent(percentage)
        else:
            # Fallback for very short lines
            label_pos = path.pointAtPercent(0.5)

        # Create or update cardinality text as child of line
        if not self.cardinality_text:
            self.cardinality_text = QGraphicsTextItem(self)
            font = QFont("Segoe UI", 9)
            if self.cardinality:
                font.setBold(True)
            else:
                font.setItalic(True)  # Italic for simple labels like "uses"
            self.cardinality_text.setFont(font)
            self.cardinality_text.setDefaultTextColor(self.colors.palette.schema_cardinality_text)
            # Ensure label doesn't block hover events for nodes
            self.cardinality_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.cardinality_text.setAcceptHoverEvents(False)

        self.cardinality_text.setPlainText(text)

        # Center the label above the line
        text_width = self.cardinality_text.boundingRect().width()
        text_height = self.cardinality_text.boundingRect().height()
        self.cardinality_text.setPos(
            label_pos.x() - text_width / 2,
            label_pos.y() - text_height / 2 - 8
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Paint the connection with arrow."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw path
        painter.setPen(self.pen())
        painter.drawPath(self.path())

        # Draw arrow at end
        self._draw_arrow(painter)

    def _draw_arrow(self, painter: QPainter) -> None:
        """Draw arrow head at end of path."""
        path = self.path()
        end_point = path.pointAtPercent(1.0)

        # Get direction at end
        t = 0.98
        near_end = path.pointAtPercent(t)

        # Calculate arrow direction
        dx = end_point.x() - near_end.x()
        dy = end_point.y() - near_end.y()

        angle = math.atan2(dy, dx)

        # Arrow dimensions
        arrow_size = 10

        # Arrow points
        p1 = QPointF(
            end_point.x() - arrow_size * math.cos(angle - math.pi / 6),
            end_point.y() - arrow_size * math.sin(angle - math.pi / 6),
        )
        p2 = QPointF(
            end_point.x() - arrow_size * math.cos(angle + math.pi / 6),
            end_point.y() - arrow_size * math.sin(angle + math.pi / 6),
        )

        # Draw filled arrow
        arrow = QPolygonF([end_point, p1, p2])
        painter.setBrush(QBrush(self.colors.ARROW_COLOR))
        painter.setPen(QPen(self.colors.ARROW_COLOR))
        painter.drawPolygon(arrow)

    def set_highlighted(self, highlighted: bool):
        """Set the visual state of the line to highlighted or dimmed."""
        opacity = 1.0 if highlighted else 0.1
        self.setOpacity(opacity)


# =============================================================================
# Schema Graphics Scene
# =============================================================================


class SchemaGraphicsScene(QGraphicsScene):
    """Scene for rendering schema diagram."""

    # Signal emitted when navigation to a definition is requested
    navigationRequested = Signal(str)  # definition name

    # Signal emitted when a node requests focus (click handling)
    nodeFocusRequested = Signal(object)  # SchemaNodeItem

    # Signal emitted when a node is hovered (for breadcrumbs)
    nodeHovered = Signal(str)  # breadcrumb path

    # Layout constants
    H_SPACING = 350  # Horizontal spacing between depth levels (left-to-right hierarchy)
    V_SPACING = 15  # Vertical spacing between leaf nodes
    H_SIBLING_SPACING = 20  # Horizontal spacing between sibling nodes (left-to-right layout)
    START_X = 50
    START_Y = 50

    def __init__(self, parent=None, colors: SchemaColors = None):
        super().__init__(parent)
        self.colors = colors
        self._schema: dict | None = None
        self._definitions: dict = {}
        self._nodes: list[SchemaNodeItem] = []
        self._lines: list[ConnectionLine] = []
        self._definition_nodes: dict[str, SchemaNodeItem] = {}  # Track for navigation
        self._ref_connections: list[tuple[SchemaNodeItem, str]] = []  # Track nodes that need connections to definitions
        self._next_leaf_y: float = 0.0  # Track next Y position for leaf nodes in bottom-up layout

        self.setBackgroundBrush(QBrush(self.colors.palette.schema_bg))

    def set_colors(self, colors: SchemaColors):
        """Set the color scheme for the scene."""
        self.colors = colors
        self.setBackgroundBrush(QBrush(self.colors.palette.schema_bg))

    def expand_all(self) -> None:
        """Expand all nodes in the tree."""
        for node in self._nodes:
            node.is_expanded = True

        # Update visibility starting from root
        root = self.get_root_node()
        if root:
            root.update_subtree_visibility()
            self.update_layout()

    def collapse_all(self) -> None:
        """Collapse all nodes except the root."""
        for node in self._nodes:
            if node.is_root:
                node.is_expanded = True
            else:
                node.is_expanded = False

        # Update visibility starting from root
        root = self.get_root_node()
        if root:
            root.update_subtree_visibility()
            self.update_layout()

    def load_schema(self, schema: dict) -> None:
        """
        Load and render a JSON schema with hierarchical left-to-right layout.
        """
        self.clear()
        self._nodes.clear()
        self._lines.clear()
        self._definition_nodes.clear()
        self._ref_connections.clear()

        self._schema = schema
        self._definitions = schema.get("definitions", {})

        if not schema:
            return

        # Create root node
        title = schema.get("title", "Schema")
        # Ensure root node has full schema data for properties display
        root_node = SchemaNodeItem(title, schema, self.colors, is_required=True, is_root=True)
        self.addItem(root_node)
        self._nodes.append(root_node)

        # PASS 1: Build tree structure and assign depths
        root_node.depth = 0
        self._build_tree(schema, root_node, depth=0)

        # Set initial expansion state: Root expanded, others collapsed (default)
        root_node.is_expanded = True
        root_node.update_subtree_visibility()

        # Perform initial layout
        self.update_layout()

        # Layout definitions if present (definitions are mostly self-contained)
        if self._definitions:
            self._layout_definitions(start_depth=0)

    def update_layout(self) -> None:
        """
        Recalculate layout for the visible tree.
        """
        root_node = self.get_root_node()
        if not root_node:
            return

        # Reset layout counters
        self._next_leaf_y = self.START_Y

        # Calculate Y positions based on visible nodes
        self._calculate_y_positions(root_node)

        # Apply final positions
        self._apply_positions(root_node)

        # Update connections
        self.update_lines()

        # Update scene rect
        self.setSceneRect(self.itemsBoundingRect().adjusted(-50, -50, 50, 50))

    def update_lines(self) -> None:
        """Update all connection lines to match current node positions."""
        for line in self._lines:
            if line.isVisible():
                line.update_path()
                line._add_cardinality_label()

    def _build_tree(self, schema: dict, parent_node: SchemaNodeItem, depth: int,
                    visited_refs: set[str] | None = None) -> None:
        """
        PASS 1: Build tree structure by creating nodes and establishing parent-child relationships.
        Assigns depth to each node. Does NOT position nodes yet.
        """
        if visited_refs is None:
            visited_refs = set()

        # Handle $ref inline expansion
        if "$ref" in schema:
            ref = schema["$ref"]
            if ref.startswith(DEFINITIONS_PREFIX):
                ref_name = ref[DEFINITIONS_PREFIX_LENGTH:]

                # Cycle detection
                if ref_name in visited_refs:
                    parent_node.type_str += " (Recursive)"
                    return

                # Resolve definition
                if ref_name in self._definitions:
                    def_schema = self._definitions[ref_name]

                    if not self._is_complex_type(def_schema):
                        # Simple type: Create a child node to show it explicitly
                        node = SchemaNodeItem(ref_name, def_schema, self.colors, is_required=True,
                                              parent_node=parent_node)
                        node.depth = depth + 1
                        self.addItem(node)
                        self._nodes.append(node)
                        parent_node.child_nodes.append(node)

                        # Create connection line with label "uses"
                        line = ConnectionLine(parent_node, node, self.colors, cardinality="", label="uses")
                        self.addItem(line)
                        line.setVisible(False)  # Default hidden
                        self._lines.append(line)
                        parent_node.connection_lines.append(line)
                        return

                    # Complex type: Recursively build children from definition schema (inline)
                    new_visited = visited_refs | {ref_name}
                    self._build_tree(def_schema, parent_node, depth, new_visited)
            return

        # Handle Array items
        if schema.get("type") == "array" and "items" in schema:
            items = schema["items"]
            self._build_tree(items, parent_node, depth, visited_refs)
            return

        # Handle Combinators (allOf, anyOf, oneOf)
        for combinator in ("allOf", "anyOf", "oneOf"):
            if combinator in schema:
                items = schema[combinator]
                for i, sub_schema in enumerate(items):
                    # Create a virtual node for the combinator branch
                    name = f"{combinator}[{i}]"
                    node = SchemaNodeItem(name, sub_schema, self.colors, is_required=False, parent_node=parent_node)
                    node.depth = depth + 1
                    self.addItem(node)
                    self._nodes.append(node)
                    parent_node.child_nodes.append(node)

                    line = ConnectionLine(parent_node, node, self.colors, label=combinator)
                    self.addItem(line)
                    line.setVisible(False)
                    self._lines.append(line)
                    parent_node.connection_lines.append(line)

                    self._build_tree(sub_schema, node, depth + 1, visited_refs)

        # Handle "not" combinator
        if "not" in schema:
            sub_schema = schema["not"]
            node = SchemaNodeItem("not", sub_schema, self.colors, is_required=False, parent_node=parent_node)
            node.depth = depth + 1
            self.addItem(node)
            self._nodes.append(node)
            parent_node.child_nodes.append(node)

            line = ConnectionLine(parent_node, node, self.colors, label="not")
            self.addItem(line)
            line.setVisible(False)
            self._lines.append(line)
            parent_node.connection_lines.append(line)

            self._build_tree(sub_schema, node, depth + 1, visited_refs)

        # Handle Properties (Object)
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        if not properties:
            return

        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required

            # Create node
            node = SchemaNodeItem(prop_name, prop_schema, self.colors, is_required, parent_node=parent_node)
            node.depth = depth + 1
            self.addItem(node)
            self._nodes.append(node)
            parent_node.child_nodes.append(node)

            # Create connection line
            cardinality = self._get_cardinality(prop_schema, is_required)
            line = ConnectionLine(parent_node, node, self.colors, cardinality)
            self.addItem(line)
            # Lines are hidden by default if parent is collapsed
            line.setVisible(False)
            self._lines.append(line)
            parent_node.connection_lines.append(line)

            # Recursively build children
            self._build_tree(prop_schema, node, depth + 1, visited_refs)

    def _calculate_y_positions(self, node: SchemaNodeItem) -> None:
        """
        PASS 2: Calculate Y positions using bottom-up approach.
        Only considers expanded nodes. Collapsed nodes act as leaves.
        """
        # If node is collapsed or has no children, it's a leaf in the current layout
        if not node.is_expanded or not node.child_nodes:
            # Leaf node: assign next sequential Y position
            node.layout_y = self._next_leaf_y
            self._next_leaf_y += node.rect().height() + self.V_SPACING
        else:
            # Parent node: first calculate positions for all children (recursively)
            # We only traverse children if we are expanded
            for child in node.child_nodes:
                self._calculate_y_positions(child)

            # Then center this node over its children
            child_y_positions = [child.layout_y for child in node.child_nodes]
            if child_y_positions:
                min_y = min(child_y_positions)
                max_y = max(child_y_positions)
                node.layout_y = (min_y + max_y) / 2
            else:
                # Fallback if children somehow didn't get positions
                node.layout_y = self._next_leaf_y
                self._next_leaf_y += node.rect().height() + self.V_SPACING

    def _apply_positions(self, node: SchemaNodeItem) -> None:
        """
        PASS 3: Apply final positions to nodes based on depth (X) and calculated Y.
        X position depends only on depth: X = depth * H_SPACING + START_X
        Y position was calculated in pass 2
        Args:
            node: Current node to position
        """
        x = node.depth * self.H_SPACING + self.START_X
        node.setPos(x, node.layout_y)

        # Recursively apply positions to children
        for child in node.child_nodes:
            self._apply_positions(child)

    def _get_max_depth(self) -> int:
        """Get the maximum depth of nodes in the main tree."""
        if not self._nodes:
            return 0
        return max(node.depth for node in self._nodes)

    def _is_complex_type(self, def_schema: dict) -> bool:
        """Determine if a definition is a complex type (object/array/combinator).

        Complex types are objects, arrays, and any schema using combinators.
        They will be displayed with connection lines to their properties.

        Args:
            def_schema: The schema definition to check

        Returns:
            True if the schema represents a complex type, False otherwise
        """
        schema_type = def_schema.get("type", "")
        has_properties = "properties" in def_schema
        has_combinators = any(c in def_schema for c in ("allOf", "anyOf", "oneOf", "not"))

        # Complex types: objects, arrays, and anything with combinators
        return schema_type in ("object", "array") or has_properties or has_combinators

    def _layout_definitions(self, start_depth: int) -> None:
        """
        Layout definition nodes using the same hierarchical approach as main tree.
        Complex types (objects/arrays) get depth-based layout with connections.
        Simple types are arranged in a grid below complex types.
        Args:
            start_depth: Starting depth for definitions section
        """
        # Separate definitions into complex and simple types
        # This is now handled inline by _build_tree
        pass

    def _create_ref_connections(self) -> None:
        """Create connection lines from nodes to their referenced definitions."""
        # Inline expansion is used now, so no need for explicit connections to definition nodes.
        # This method is kept as a placeholder or for potential future mixed-mode support.
        pass

    def _get_cardinality(self, schema: dict, is_required: bool) -> str:
        """Get cardinality string for a property."""
        if schema.get("type") == "array":
            # For arrays: use minItems if defined, otherwise:
            # - required arrays have at least 1 element
            # - optional arrays have at least 0 elements
            if "minItems" in schema:
                min_items = schema["minItems"]
            else:
                min_items = 1 if is_required else 0
            max_items = schema.get("maxItems", "*")
            return f"{min_items}..{max_items}"
        else:
            return "1" if is_required else "0..1"

    def navigate_to_definition(self, def_name: str) -> None:
        """Navigate to and highlight a definition node."""
        if def_name in self._definition_nodes:
            node = self._definition_nodes[def_name]
            # Select the node
            self.clearSelection()
            node.setSelected(True)
            # Emit signal so view can scroll to it
            self.navigationRequested.emit(def_name)

    def get_definition_node(self, def_name: str) -> SchemaNodeItem | None:
        """Get a definition node by name."""
        return self._definition_nodes.get(def_name)

    def get_root_node(self) -> SchemaNodeItem | None:
        """Get the root node (first node)."""
        return self._nodes[0] if self._nodes else None

    def find_node_by_path(self, json_path: str) -> SchemaNodeItem | None:
        """
        Find a schema node by JSON path or breadcrumb path.

        Args:
            json_path: Path like 'depotInfoList[0].field' or 'Schema > depotInfoList > field'

        Returns:
            The matching SchemaNodeItem or None if not found
        """
        if not json_path or not self._nodes:
            return None

        # Handle breadcrumb format if present
        if " > " in json_path:
            path_parts = json_path.split(" > ")
        else:
            # Parse the JSON path - remove array indices and split by dot
            # Note: we use a regex that handles dots not inside brackets
            clean_path = re.sub(r'\[\d+\]', '', json_path)
            path_parts = clean_path.split('.')

        if not path_parts:
            return None

        # Start from root and traverse
        root_node = self.get_root_node()
        if not root_node:
            return None

        current_node = root_node

        # If the first part matches root title, skip it
        if path_parts[0] == current_node.name:
            path_parts = path_parts[1:]

        if not path_parts:
            return current_node

        last_valid_node = current_node
        for part in path_parts:
            if not part:  # Skip empty parts
                continue

            # 1. Search for matching child node in current scope (hierarchical)
            found_node = self._find_child_recursive(current_node, part)

            # 2. If not found, check if current node has a reference that might contain it
            if not found_node:
                ref_target = current_node.get_ref_target()
                if ref_target:
                    def_node = self.get_definition_node(ref_target)
                    if def_node:
                        found_node = self._find_child_recursive(def_node, part)

            # 3. Last resort: Global search for this specific part name (only if we'd otherwise fail)
            if not found_node:
                for node in self._nodes:
                    if node.name == part:
                        found_node = node
                        break

            if found_node:
                current_node = found_node
                last_valid_node = current_node
            else:
                # If we didn't find the exact part, return the last node we successfully reached.
                # This provides context for rule violations that use custom identifiers.
                return last_valid_node

        return current_node

    def _find_child_recursive(self, parent: SchemaNodeItem, target_name: str, visited=None) -> SchemaNodeItem | None:
        """Robust helper to find a child node by name anywhere in the subtree."""
        if not parent:
            return None

        if visited is None:
            visited = set()
        if parent in visited:
            return None
        visited.add(parent)

        # First check immediate children (highest priority)
        for child in parent.child_nodes:
            if child.name == target_name:
                return child

        # Then check deeper (including through combinators)
        for child in parent.child_nodes:
            # Check if this child is a container or has children
            if child.child_nodes:
                result = self._find_child_recursive(child, target_name, visited)
                if result:
                    return result

        return None

    def highlight_path(self, json_path: str) -> SchemaNodeItem | None:
        """
        Highlight the schema element at the given JSON path.

        Args:
            json_path: Path like 'depotInfoList[0].chargingStationInfoList[0].field'

        Returns:
            The highlighted SchemaNodeItem if found, None otherwise
        """
        # Clear previous highlighting
        self.clear_highlighting()

        # Find the node
        node = self.find_node_by_path(json_path)

        if not node:
            return None

        # Ensure node is visible (expand parents AND the node itself to show children)
        node.reveal_tree(expand_self=True)

        # Highlight the error node with red border (without dimming others)
        # Note: We don't dim other nodes because keeping them fully visible
        # provides better context while the red border is sufficient to draw
        # attention to the error location.
        node.set_error_highlight(True)

        return node

    def clear_highlighting(self) -> None:
        """Clear all highlighting - restore all nodes to full opacity."""
        for node in self._nodes:
            node.setOpacity(1.0)
            node.set_error_highlight(False)
            for line in node.connection_lines:
                line.setOpacity(1.0)


# =============================================================================
# Schema Graphics View
# =============================================================================


class SchemaGraphicsView(QGraphicsView):
    """
    Interactive view for schema diagram.

    Features:
    - Pan (drag)
    - Zoom (scroll wheel)
    - Fit to view
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_view()

        self._is_panning = False
        self._pan_start = QPointF()

    def _setup_view(self) -> None:
        """Setup view properties."""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Enable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Enable mouse tracking for tooltips and hover effects
        self.setMouseTracking(True)
        if self.viewport():
            self.viewport().setMouseTracking(True)

        # We implement manual panning to ensure it works even when clicking on items
        self._is_panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        # Zoom factor
        factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse button press for navigation and panning."""
        if not event:
            return

        # Middle-click or Left-click for panning start
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            # Call super to let items/scene handle their press logic (e.g. recording click pos)
            super().mousePressEvent(event)
            return

        # Mouse back/forward buttons
        if event.button() == Qt.MouseButton.BackButton:
            parent = self.parent()
            if parent and hasattr(parent, '_navigate_back'):
                parent._navigate_back()  # type: ignore[union-attr]
            event.accept()
            return

        if event.button() == Qt.MouseButton.ForwardButton:
            parent = self.parent()
            if parent and hasattr(parent, '_navigate_forward'):
                parent._navigate_forward()  # type: ignore[union-attr]
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for panning."""
        if self._is_panning:
            # Calculate how much the mouse has moved since the last move event
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()

            # Manually scroll the view by updating scrollbar values
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse button release."""
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            if self._is_panning:
                self._is_panning = False
                self.unsetCursor()
                event.accept()

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Show context menu for Expand/Collapse and Navigation."""
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        menu.setMinimumWidth(200)

        # Navigation
        back_action = QAction("◀ Zurück", self)

        # Find the SchemaView parent
        schema_view = self.parent()
        while schema_view:
            if schema_view.__class__.__name__ == "SchemaView":
                break
            schema_view = schema_view.parent()

        has_history = False
        if schema_view and hasattr(schema_view, '_nav_history'):
            has_history = len(schema_view._nav_history) > 0  # type: ignore[union-attr]

        back_action.setEnabled(has_history)
        back_action.triggered.connect(self._back_triggered)
        menu.addAction(back_action)

        menu.addSeparator()

        # Check if we clicked on a node
        item = self.itemAt(event.pos())
        node = None
        if isinstance(item, SchemaNodeItem):
            node = item
        elif item and item.parentItem() and isinstance(item.parentItem(), SchemaNodeItem):
            node = item.parentItem()

        if node:
            menu.addSection(f"Element: {node.name}")

            expand_here = QAction(t("expand_here"), self)
            expand_here.triggered.connect(lambda: self._expand_subtree_triggered(node))
            menu.addAction(expand_here)

            collapse_here = QAction(t("collapse_here"), self)
            collapse_here.triggered.connect(lambda: self._collapse_subtree_triggered(node))
            menu.addAction(collapse_here)

            menu.addSeparator()

        menu.addSection("Global")
        expand_all_action = QAction(t("expand_all"), self)
        expand_all_action.triggered.connect(self._expand_all_triggered)
        menu.addAction(expand_all_action)

        collapse_all_action = QAction(t("collapse_all"), self)
        collapse_all_action.triggered.connect(self._collapse_all_triggered)
        menu.addAction(collapse_all_action)

        menu.exec(event.globalPos())

    def _back_triggered(self) -> None:
        """Trigger back navigation in the parent widget."""
        schema_view = self.parent()
        while schema_view:
            if schema_view.__class__.__name__ == "SchemaView":
                break
            schema_view = schema_view.parent()

        if schema_view and hasattr(schema_view, '_navigate_back'):
            schema_view._navigate_back()  # type: ignore[union-attr]

    def _expand_subtree_triggered(self, node: SchemaNodeItem) -> None:
        """Expand node and its subtree, then zoom."""
        node.expand_subtree(recursive=True)
        scene = self.scene()
        if scene and hasattr(scene, 'update_layout'):
            scene.update_layout()
        self._zoom_to_node_subtree(node)

    def _collapse_subtree_triggered(self, node: SchemaNodeItem) -> None:
        """Collapse node and its subtree without changing zoom."""
        node.collapse_subtree(recursive=True)
        scene = self.scene()
        if scene and hasattr(scene, 'update_layout'):
            scene.update_layout()

    def _zoom_to_node_subtree(self, node: SchemaNodeItem) -> None:
        """Zoom to show the node and all its visible descendants."""

        def get_visible_descendants(n):
            nodes = [n]
            if n.is_expanded:
                for child in n.child_nodes:
                    nodes.extend(get_visible_descendants(child))
            return nodes

        visible_nodes = get_visible_descendants(node)
        if not visible_nodes:
            return

        combined_rect = QRectF()
        for n in visible_nodes:
            # sceneBoundingRect accounts for item pos and size
            rect = n.sceneBoundingRect()
            if combined_rect.isEmpty():
                combined_rect = rect
            else:
                combined_rect = combined_rect.united(rect)

        # Add padding
        combined_rect.adjust(-50, -50, 50, 50)
        self.fitInView(combined_rect, Qt.AspectRatioMode.KeepAspectRatio)

        # Update UI zoom display if needed
        parent = self.parent()
        if parent and hasattr(parent, '_update_zoom_display'):
            parent._update_zoom_display()

    def _expand_all_triggered(self) -> None:
        """Trigger expand all in the scene and fit view."""
        scene = self.scene()
        if scene and hasattr(scene, 'expand_all'):
            scene.expand_all()
            self.fit_to_contents()
            # Update UI zoom display
            parent = self.parent()
            if parent and hasattr(parent, '_update_zoom_display'):
                parent._update_zoom_display()

    def _collapse_all_triggered(self) -> None:
        """Trigger collapse all in the scene without changing zoom."""
        scene = self.scene()
        if scene and hasattr(scene, 'collapse_all'):
            scene.collapse_all()

    def fit_to_contents(self) -> None:
        """Fit view to show all contents."""
        scene = self.scene()
        if scene:
            self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self.resetTransform()


# =============================================================================
# Main Schema View Widget
# =============================================================================


class SchemaView(QWidget):
    """
    Main Schema View widget with toolbar and diagram view.

    Provides graphical visualization of JSON Schema structure
    using QGraphicsView for interactive diagram display.
    """

    schemaLoaded = Signal(str)

    def __init__(self, parent: QWidget | None = None, palette=None):
        super().__init__(parent)
        self.palette = palette or {}
        self.colors = SchemaColors(self.palette)
        self._schema: dict | None = None
        self._schema_path: Path | None = None
        self._schema_dir: Path | None = None

        # Navigation history
        self._nav_history: list[str] = []  # Stack of visited definitions
        self._nav_forward: list[str] = []  # Forward stack for redo
        self._current_view: str = "root"  # Current view identifier

        self._setup_ui()

    def set_theme(self, palette):
        """Update the theme of the schema view."""
        self.palette = palette
        self.colors = SchemaColors(self.palette)
        self.scene.set_colors(self.colors)
        self._update_breadcrumb_style(self.breadcrumb_label.text() != "Path: /")
        if self._schema:
            self.load_schema(self._schema, self.schema_name_label.text())

    def _update_breadcrumb_style(self, hovered: bool):
        """Update breadcrumb style based on current theme and hover state."""
        bg = self.palette.breadcrumb_hover_bg if hovered else self.palette.breadcrumb_bg
        text = self.palette.breadcrumb_text
        border = self.palette.breadcrumb_border
        self.breadcrumb_label.setStyleSheet(
            f"QLabel {{ background-color: {bg.name()}; padding: 3px 8px; "
            f"border-bottom: 1px solid {border.name()}; color: {text.name()}; "
            f"font-family: 'Segoe UI'; font-size: 9pt; }}"
        )

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)

        # Navigation buttons
        self.back_btn = QPushButton("◀ Zurück")
        self.back_btn.setToolTip("Zurück zur vorherigen Ansicht (Alt+Left, Rechtsklick, Maus-Zurück)")
        self.back_btn.setEnabled(False)
        self.back_btn.clicked.connect(self._navigate_back)
        self.back_btn.setShortcut("Alt+Left")
        toolbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton("Vor ▶")
        self.forward_btn.setToolTip("Vorwärts zur nächsten Ansicht (Alt+Right, Maus-Vor)")
        self.forward_btn.setEnabled(False)
        self.forward_btn.clicked.connect(self._navigate_forward)
        self.forward_btn.setShortcut("Alt+Right")
        toolbar.addWidget(self.forward_btn)

        self.home_btn = QPushButton("🏠 Start")
        self.home_btn.setToolTip("Zurück zur Wurzel (Home)")
        self.home_btn.clicked.connect(self._navigate_home)
        self.home_btn.setShortcut("Home")
        toolbar.addWidget(self.home_btn)

        toolbar.addSpacing(15)

        toolbar.addWidget(QLabel("Schema:"))

        self.schema_name_label = QLabel(t("schema_no_schema"))
        self.schema_name_label.setMinimumWidth(250)
        self.schema_name_label.setStyleSheet(
            "QLabel { font-weight: bold; padding: 4px 8px; "
            "background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 3px; }"
        )
        toolbar.addWidget(self.schema_name_label)

        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.clicked.connect(self._reload_schema)
        toolbar.addWidget(self.reload_btn)

        toolbar.addSpacing(20)

        self.fit_btn = QPushButton("📐 Fit")
        self.fit_btn.setToolTip(t("fit_view"))
        self.fit_btn.clicked.connect(self._fit_to_view)
        toolbar.addWidget(self.fit_btn)

        self.reset_btn = QPushButton("🔍 100%")
        self.reset_btn.setToolTip("Reset zoom to 100%")
        self.reset_btn.clicked.connect(self._reset_zoom)
        toolbar.addWidget(self.reset_btn)

        toolbar.addSpacing(10)

        toolbar.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(25)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(150)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        toolbar.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(45)
        toolbar.addWidget(self.zoom_label)

        toolbar.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search schema (Enter)...")
        self.search_bar.setMaximumWidth(200)
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.returnPressed.connect(self._on_search_triggered)
        # Also trigger on clear button click
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        toolbar.addWidget(self.search_bar)

        layout.addLayout(toolbar)

        # Breadcrumb label
        self.breadcrumb_label = QLabel("Path: /")
        self._update_breadcrumb_style(False)
        layout.addWidget(self.breadcrumb_label)

        # Graphics view
        self.scene = SchemaGraphicsScene(colors=self.colors)
        self.scene.navigationRequested.connect(self._on_navigation_requested)
        self.scene.nodeFocusRequested.connect(self._on_node_focus_requested)
        self.scene.nodeHovered.connect(self._on_node_hovered)
        self.view = SchemaGraphicsView(self)
        self.view.setScene(self.scene)
        layout.addWidget(self.view)

        # Legend
        legend = self._create_legend()
        layout.addWidget(legend)

    def _on_node_hovered(self, path: str) -> None:
        """Handle node hover to update breadcrumb."""
        current_text = self.breadcrumb_label.text()
        new_text = f"Path: {path}" if path else "Path: /"

        if current_text != new_text:
            self.breadcrumb_label.setText(new_text)
            self._update_breadcrumb_style(bool(path))

    def _on_node_focus_requested(self, node: SchemaNodeItem) -> None:
        """Handle request to focus on a specific node and its children."""
        # Push current view to history before navigating
        path = node.get_breadcrumb_path()
        if self._current_view != path:
            self._nav_history.append(self._current_view)
            self._nav_forward.clear()
            self._current_view = path
            self._update_nav_buttons()

        self._show_definition(node, ensure_expanded=False)

    def _create_legend(self) -> QWidget:
        """Create a legend explaining the visual elements."""
        legend = QWidget()
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(10, 5, 10, 5)

        items = [
            ("● Required", self.colors.REQUIRED_BORDER),
            ("○ Optional", self.colors.OPTIONAL_BORDER),
            ("Object", self.colors.OBJECT_BG[0]),
            ("Array", self.colors.ARRAY_BG[0]),
            ("String", self.colors.STRING_BG[0]),
            ("Number", self.colors.NUMBER_BG[0]),
            ("Enum", self.colors.ENUM_BG[0]),
            ("Reference", self.colors.REF_BG[0]),
        ]

        for text, color in items:
            label = QLabel(f"  {text}  ")
            label.setStyleSheet(
                f"background-color: {color.name()}; "
                f"border-radius: 3px; padding: 2px 5px; "
                f"font-size: 10px;"
            )
            legend_layout.addWidget(label)

        legend_layout.addStretch()

        return legend

    def set_schema_dir(self, schema_dir: Path) -> None:
        """Set schema directory."""
        self._schema_dir = schema_dir

    def load_schema_file(self, path: Path) -> bool:
        """Load schema from file."""
        try:
            with open(path, encoding="utf-8") as f:
                schema = json.load(f)

            self._schema = schema
            self._schema_path = path

            # Reset navigation history
            self._nav_history.clear()
            self._nav_forward.clear()
            self._current_view = "root"
            self._update_nav_buttons()

            self.scene.load_schema(schema)
            self._focus_on_root_with_children()

            # Update schema name label with version/filename
            if self._schema_dir and path.is_relative_to(self._schema_dir):
                rel_path = path.relative_to(self._schema_dir)
                self.schema_name_label.setText(str(rel_path))
            else:
                self.schema_name_label.setText(path.name)

            title = schema.get("title", path.name)
            self.schemaLoaded.emit(title)

            return True

        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading schema: {e}")
            return False

    def load_schema(self, schema: dict, display_name: str = "") -> None:
        """Load schema from dict."""
        self._schema = schema
        self._schema_path = None

        # Reset navigation history
        self._nav_history.clear()
        self._nav_forward.clear()
        self._current_view = "root"
        self._update_nav_buttons()

        self.scene.load_schema(schema)
        self._focus_on_root_with_children()

        # Update schema name label
        title = schema.get("title", "Schema")
        if display_name:
            self.schema_name_label.setText(display_name)
        else:
            self.schema_name_label.setText(title)

        self.schemaLoaded.emit(title)

    def _focus_on_root_with_children(self) -> None:
        """
        Focus view on root element with its first-level children visible.

        This provides the initial navigation entry point showing:
        - The root element (Schema)
        - All direct child properties on the first level
        """
        root_node = self.scene.get_root_node()
        if not root_node:
            self.view.fit_to_contents()
            return

        # Calculate bounding rect for root and first-level children
        nodes_to_show = [root_node] + root_node.child_nodes

        if not nodes_to_show:
            self.view.fit_to_contents()
            return

        # Build combined bounding rect
        combined_rect = QRectF()

        for node in nodes_to_show:
            node_rect = node.sceneBoundingRect()
            if combined_rect.isEmpty():
                combined_rect = node_rect
            else:
                combined_rect = combined_rect.united(node_rect)

        # Add padding
        combined_rect.adjust(-30, -30, 30, 30)

        # Fit view to show root + first level
        self.view.fitInView(combined_rect, Qt.AspectRatioMode.KeepAspectRatio)

        # Update zoom slider
        transform = self.view.transform()
        scale = transform.m11() * 100
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(min(scale, 400)))
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"{int(scale)}%")

    def _on_navigation_requested(self, def_name: str) -> None:
        """Handle navigation to a definition."""
        node = self.scene.get_definition_node(def_name)
        if node:
            # Push current view to history before navigating
            self._nav_history.append(self._current_view)
            self._nav_forward.clear()  # Clear forward stack on new navigation
            self._current_view = def_name
            self._update_nav_buttons()

            # Navigate to the definition
            self._show_definition(node)

    def _show_definition(self, node: SchemaNodeItem, ensure_expanded: bool = True) -> None:
        """Show a definition node with its children."""
        if ensure_expanded:
            # Ensure node is expanded
            node.set_expanded(True)

        # Center the view on the definition node with its children
        # Only include children if they are visible (expanded)
        nodes_to_show = [node]
        if node.is_expanded:
            nodes_to_show.extend(node.child_nodes)

        combined_rect = QRectF()

        for n in nodes_to_show:
            node_rect = n.sceneBoundingRect()
            if combined_rect.isEmpty():
                combined_rect = node_rect
            else:
                combined_rect = combined_rect.united(node_rect)

        # Add padding
        combined_rect.adjust(-30, -30, 30, 30)

        # Scroll to show the definition
        self.view.fitInView(combined_rect, Qt.AspectRatioMode.KeepAspectRatio)

        # Update zoom slider
        self._update_zoom_display()

    def _navigate_back(self) -> None:
        """Navigate back to the previous view."""
        if not self._nav_history:
            return

        # Push current view to forward stack
        self._nav_forward.append(self._current_view)

        # Pop from history
        target = self._nav_history.pop()
        self._current_view = target
        self._update_nav_buttons()

        # Navigate to target
        self._navigate_to_view(target)

    def _navigate_forward(self) -> None:
        """Navigate forward to the next view."""
        if not self._nav_forward:
            return

        # Push current view to history
        self._nav_history.append(self._current_view)

        # Pop from forward stack
        target = self._nav_forward.pop()
        self._current_view = target
        self._update_nav_buttons()

        # Navigate to target
        self._navigate_to_view(target)

    def _navigate_home(self) -> None:
        """Navigate back to the root view."""
        if self._current_view == "root":
            return

        # Push current view to history
        self._nav_history.append(self._current_view)
        self._nav_forward.clear()
        self._current_view = "root"
        self._update_nav_buttons()

        # Show root
        self._focus_on_root_with_children()

    def _navigate_to_view(self, view_id: str) -> None:
        """Navigate to a specific view by ID."""
        if view_id == "root":
            self._focus_on_root_with_children()
        else:
            # Try to find node by path (new behavior)
            node = self.scene.find_node_by_path(view_id)
            if not node:
                # Fallback to definition node (old behavior)
                node = self.scene.get_definition_node(view_id)

            if node:
                self._show_definition(node)

    def _update_nav_buttons(self) -> None:
        """Update navigation button states."""
        self.back_btn.setEnabled(len(self._nav_history) > 0)
        self.forward_btn.setEnabled(len(self._nav_forward) > 0)

    def _update_zoom_display(self) -> None:
        """Update the zoom slider and label."""
        transform = self.view.transform()
        scale = transform.m11() * 100
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(min(scale, 400)))
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"{int(scale)}%")

    def _reload_schema(self) -> None:
        """Reload current schema."""
        if self._schema_path:
            self.load_schema_file(self._schema_path)
        elif self._schema:
            self.scene.load_schema(self._schema)
            self.view.fit_to_contents()

    def _fit_to_view(self) -> None:
        """Fit diagram to view."""
        self.view.fit_to_contents()
        # Update slider
        transform = self.view.transform()
        scale = transform.m11() * 100
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(scale))
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"{int(scale)}%")

    def _reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self.view.reset_zoom()
        self.zoom_slider.setValue(100)
        self.zoom_label.setText("100%")

    def _on_zoom_changed(self, value: int) -> None:
        """Handle zoom slider change."""
        self.view.resetTransform()
        scale = value / 100.0
        self.view.scale(scale, scale)
        self.zoom_label.setText(f"{value}%")

    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes - only used for resetting on clear."""
        if not text:
            self._on_search_triggered()

    def _on_search_triggered(self) -> None:
        """Filter and reveal nodes based on search text (triggered by Enter)."""
        text = self.search_bar.text()
        search_term = text.lower().strip()

        if not search_term:
            # If search is empty, restore everything to normal state
            for node in self.scene._nodes:
                node.setOpacity(1.0)
                node.set_error_highlight(False)
            return

        # Find matches and their context
        matched_nodes = []
        context_nodes = set()

        for node in self.scene._nodes:
            # Strict case-insensitive matching on name and type
            node_name = str(node.name).lower()
            type_name = str(node.type_str).lower()
            is_match = search_term in node_name or search_term in type_name

            if is_match:
                matched_nodes.append(node)
                # Ensure the path to this node is visible
                curr = node
                while curr:
                    curr.is_expanded = True
                    context_nodes.add(curr)
                    # Add siblings of the match for structural context
                    for child in curr.child_nodes:
                        context_nodes.add(child)
                    curr = curr.parent_node_item

                # Specifically add children of the match
                for child in node.child_nodes:
                    context_nodes.add(child)

        # Apply visibility and highlighting
        if matched_nodes:
            # Update all visibilities based on new expansion states
            root = self.scene.get_root_node()
            if root:
                root.update_subtree_visibility()

            # Recurse layout calculation
            self.scene.update_layout()

            # Set highlighting: matches are bright, context is visible, others dimmed
            for node in self.scene._nodes:
                if node in matched_nodes:
                    node.setOpacity(1.0)
                    # Use a distinct highlight for search matches (Blue border)
                    pen = QPen(QColor("#1976d2"))
                    pen.setWidth(4)
                    node.setPen(pen)
                elif node in context_nodes:
                    node.setOpacity(0.8)
                    node.set_error_highlight(False)  # Restore normal border
                else:
                    node.setOpacity(0.1)
                    node.set_error_highlight(False)

            # Position the view on the first match found
            self._scroll_to_node(matched_nodes[0])
        else:
            # No matches found: heavily dim everything to indicate "no results"
            for node in self.scene._nodes:
                node.setOpacity(0.05)
                node.set_error_highlight(False)

    def highlight_error_path(self, json_path: str) -> bool:
        """
        Highlight the schema element at the given JSON path.
        This is the public API called when an error is selected.

        Args:
            json_path: Path like 'depotInfoList[0].chargingStationInfoList[0].field'

        Returns:
            True if a node was found and highlighted, False otherwise
        """
        if not json_path:
            return False

        # Highlight the path and get the node (if found)
        node = self.scene.highlight_path(json_path)

        if node:
            # Scroll to show the highlighted node
            self._scroll_to_node(node)
            return True

        return False

    def clear_error_highlighting(self) -> None:
        """Clear error highlighting from the schema view."""
        self.scene.clear_highlighting()

    def _scroll_to_node(self, node: SchemaNodeItem) -> None:
        """Scroll the view to show a specific node and its context (parent/children)."""
        if not node:
            return

        # Build list of nodes to include in context
        context_nodes = [node]
        if node.parent_node_item:
            context_nodes.append(node.parent_node_item)

        # Include children (only if expanded or if we want to see where they would be)
        # For better context, we include all direct children.
        context_nodes.extend(node.child_nodes)

        combined_rect = QRectF()
        for n in context_nodes:
            # We only include visible nodes in the bounding rect calculation
            if n.isVisible():
                rect = n.sceneBoundingRect()
                if combined_rect.isEmpty():
                    combined_rect = rect
                else:
                    combined_rect = combined_rect.united(rect)

        if combined_rect.isEmpty():
            combined_rect = node.sceneBoundingRect()

        # Add significant padding for a better overview
        combined_rect.adjust(-100, -100, 100, 100)

        # Fit view to show the context
        self.view.fitInView(combined_rect, Qt.AspectRatioMode.KeepAspectRatio)

        # Update UI zoom display
        self._update_zoom_display()
