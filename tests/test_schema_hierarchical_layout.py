"""
Tests for hierarchical left-to-right schema layout.

This test verifies that the schema view displays nodes in a deterministic
hierarchical left-to-right layout with:
- Depth-based X positioning
- Parent nodes centered over their children
- No edge crossings in the main tree
- XMLSpy-like visual clarity

Note: These tests require PySide6 and should be run with QT_QPA_PLATFORM=offscreen
in headless environments.
"""

import sys
from pathlib import Path

import pytest

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "UI"))

# Skip all tests in this module if PySide6 is not available
pytest.importorskip("PySide6.QtWidgets")

# Import after skip check
from PySide6.QtWidgets import QApplication  # noqa: E402
from schema_view import (  # noqa: E402
    SchemaColors,
    SchemaGraphicsScene,
)
from theme import get_palette  # noqa: E402

pytestmark = pytest.mark.qt  # Mark all tests in this module as qt tests


class TestSchemaHierarchicalLayout:
    """Test cases for hierarchical left-to-right schema layout."""

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create Qt application for tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def scene(self, qapp):
        """Create a schema scene with default colors."""
        palette = get_palette(dark_mode=False)
        colors = SchemaColors(palette)
        return SchemaGraphicsScene(colors=colors)

    @pytest.fixture
    def sample_schema(self):
        """Load a mock schema for testing layout logic."""
        return {
            "type": "object",
            "title": "TestRoot",
            "properties": {
                "chargingRequestList": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chargingPointId": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                        },
                        "required": ["chargingPointId"],
                    },
                },
                "status": {"type": "string"},
            },
        }

    def test_layout_constants(self, scene):
        """Test that layout constants are set correctly for hierarchical layout."""
        assert scene.H_SPACING == 350, (
            "H_SPACING should be 350 for horizontal spacing between depth levels"
        )
        assert scene.V_SPACING == 15, "V_SPACING should be 15 for vertical spacing between leaves"
        assert scene.H_SIBLING_SPACING == 20, (
            "H_SIBLING_SPACING should be 20 (used for simple type definitions grid)"
        )

    def test_root_position_and_depth(self, scene, sample_schema):
        """Test that root node is at depth 0 and positioned at START_X, START_Y."""
        scene.load_schema(sample_schema)
        root = scene.get_root_node()

        assert root is not None, "Root node should exist"
        assert root.depth == 0, "Root should have depth 0"
        assert root.x() == scene.START_X, f"Root should be at START_X ({scene.START_X})"
        # Y position may vary based on centering, so we just check it's set
        assert root.y() >= 0, "Root Y position should be non-negative"

    def test_depth_assignment(self, scene, sample_schema):
        """Test that all nodes have correct depth assignment."""
        scene.load_schema(sample_schema)
        root = scene.get_root_node()

        # Root should have depth 0
        assert root.depth == 0

        # All children should have depth 1 more than parent
        def check_depths(node):
            for child in node.child_nodes:
                assert child.depth == node.depth + 1, (
                    f"Child '{child.name}' should have depth {node.depth + 1}, got {child.depth}"
                )
                check_depths(child)

        check_depths(root)

    def _expand_all(self, scene):
        """Helper to expand all nodes for layout testing."""
        for node in scene._nodes:
            node.is_expanded = True
        scene.update_layout()

    def test_x_position_based_on_depth(self, scene, sample_schema):
        """Test that X position depends only on depth."""
        scene.load_schema(sample_schema)
        self._expand_all(scene)

        # Group nodes by depth
        nodes_by_depth = {}
        for node in scene._nodes:
            depth = node.depth
            if depth not in nodes_by_depth:
                nodes_by_depth[depth] = []
            nodes_by_depth[depth].append(node)

        # All nodes at same depth should have same X coordinate
        for depth, nodes in nodes_by_depth.items():
            expected_x = depth * scene.H_SPACING + scene.START_X
            for node in nodes:
                assert abs(node.x() - expected_x) < 1.0, (
                    f"Node '{node.name}' at depth {depth} should have X={expected_x}, got {node.x()}"
                )

    def test_parent_centered_over_children(self, scene, sample_schema):
        """Test that parent nodes are vertically centered over their children."""
        scene.load_schema(sample_schema)
        self._expand_all(scene)

        for node in scene._nodes:
            if len(node.child_nodes) >= 2:  # Only test parents with multiple children
                child_y_positions = [child.y() for child in node.child_nodes]
                min_child_y = min(child_y_positions)
                max_child_y = max(child_y_positions)
                expected_parent_y = (min_child_y + max_child_y) / 2

                # Allow some tolerance for centering
                tolerance = 5.0
                assert abs(node.y() - expected_parent_y) < tolerance, (
                    f"Parent '{node.name}' should be centered over children: "
                    f"expected Y≈{expected_parent_y}, got {node.y()}"
                )

    def test_left_to_right_hierarchy(self, scene, sample_schema):
        """Test that deeper nodes are positioned to the right."""
        scene.load_schema(sample_schema)
        self._expand_all(scene)

        # Check parent-child relationships
        for node in scene._nodes:
            for child in node.child_nodes:
                assert child.x() > node.x(), (
                    f"Child '{child.name}' should be to the right of parent '{node.name}'"
                )

    def test_no_node_overlaps(self, scene, sample_schema):
        """Test that no nodes overlap in the layout."""
        scene.load_schema(sample_schema)
        self._expand_all(scene)

        # Check all pairs of nodes for overlaps
        nodes = scene._nodes
        for i, node1 in enumerate(nodes):
            rect1 = node1.sceneBoundingRect()
            for node2 in nodes[i + 1 :]:
                rect2 = node2.sceneBoundingRect()
                # Nodes should not intersect
                assert not rect1.intersects(rect2), (
                    f"Node '{node1.name}' overlaps with '{node2.name}'"
                )

    def test_connection_lines_created(self, scene, sample_schema):
        """Test that connection lines are created between nodes."""
        scene.load_schema(sample_schema)

        # There should be at least some connection lines
        assert len(scene._lines) > 0, "Connection lines should be created"

        # Build a set of definition node objects for efficient lookup
        definition_node_set = set(scene._definition_nodes.values())

        # Each line should connect a parent to a child OR a reference to its definition
        for line in scene._lines:
            assert line.start_node is not None, "Line should have start node"
            assert line.end_node is not None, "Line should have end node"

            # End node should be in start node's children OR in the definition nodes (for references)
            is_child = line.end_node in line.start_node.child_nodes
            is_ref = line.end_node in definition_node_set
            assert is_child or is_ref, (
                f"Connection line from '{line.start_node.name}' to '{line.end_node.name}' "
                "should connect parent to child or reference to definition"
            )

    def test_deterministic_layout(self, scene, sample_schema):
        """Test that the layout is deterministic (same schema produces same layout)."""
        scene.load_schema(sample_schema)

        # Capture layout state (sorted by name to ensure order)
        # Store tuple of (name, x, y, depth)
        first_layout = sorted(
            [(node.name, node.x(), node.y(), node.depth) for node in scene._nodes],
            key=lambda x: (x[0], x[1], x[2]),
        )

        # Reload the same schema
        scene.load_schema(sample_schema)

        # Capture second layout
        second_layout = sorted(
            [(node.name, node.x(), node.y(), node.depth) for node in scene._nodes],
            key=lambda x: (x[0], x[1], x[2]),
        )

        # Verify layouts are identical
        assert len(first_layout) == len(second_layout), "Node count changed between loads"

        for i, (name1, x1, y1, d1) in enumerate(first_layout):
            name2, x2, y2, d2 = second_layout[i]

            assert name1 == name2
            assert abs(x1 - x2) < 0.1, f"Node '{name1}' X position changed: {x1} -> {x2}"
            assert abs(y1 - y2) < 0.1, f"Node '{name1}' Y position changed: {y1} -> {y2}"
            assert d1 == d2, f"Node '{name1}' depth changed: {d1} -> {d2}"

    def test_siblings_same_depth(self, scene, sample_schema):
        """Test that sibling nodes have the same depth."""
        scene.load_schema(sample_schema)

        for node in scene._nodes:
            if node.child_nodes:
                # All siblings should have same depth
                depths = [child.depth for child in node.child_nodes]
                assert len(set(depths)) == 1, (
                    f"Siblings of '{node.name}' should all have same depth"
                )

    def test_inline_expansion(self, scene, sample_schema):
        """Test that references are expanded inline in the main tree."""
        scene.load_schema(sample_schema)

        # In the sample schema, 'chargingRequestList' is an array of 'ChargingRequestData' ($ref).
        # With inline expansion, 'ChargingRequestData' properties (like 'chargingPointId')
        # should appear as descendants of 'chargingRequestList' in the main tree.

        # Find 'chargingRequestList' node
        list_node = next((n for n in scene._nodes if n.name == "chargingRequestList"), None)
        assert list_node is not None, "Should find 'chargingRequestList' node"

        # Find 'chargingPointId' nodes
        # One should be a descendant of list_node
        found_descendant = False

        # Traverse children of list_node
        # Note: Since 'chargingRequestList' -> items -> properties,
        # the properties should be direct children of the list node in the simplified tree builder
        for child in list_node.child_nodes:
            if child.name == "chargingPointId":
                found_descendant = True
                break

        assert found_descendant, (
            "Inline expansion failed: 'chargingPointId' should be a child of 'chargingRequestList'"
        )
