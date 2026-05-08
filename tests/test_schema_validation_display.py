"""
Test that schema validation errors are properly displayed in the UI.

This test specifically addresses the issue where schema validation errors
might not be displayed in the UI after PR #29.
"""

import pytest

from vdv463_validator import Severity, VDV463Validator


class TestSchemaValidationDisplay:
    """Test that schema validation errors are properly generated and displayable."""

    @pytest.fixture
    def validator(self, schema_dir):
        """Create a validator instance."""
        return VDV463Validator(schema_dir=schema_dir, schema_version="auto")

    def test_schema_errors_have_schema_rule_id(self, validator):
        """Test that schema validation errors are tagged with rule_id='SCHEMA'."""
        # File with missing required fields
        content = """
{
  "timestamp": "2025-01-15T10:00:00Z",
  "senderId": "DEPOT_001",
  "receiverId": "CMS_001",
  "chargingRequestList": [
    {
      "requestId": "REQ-001"
    }
  ]
}
"""
        result = validator.validate_content(content, schema_only=False)

        # Get schema errors
        schema_errors = [i for i in result.issues if i.rule_id == "SCHEMA"]

        # Should have schema errors for missing required fields
        assert len(schema_errors) > 0, "Expected schema errors for missing required fields"

        # Verify all schema errors have rule_id="SCHEMA"
        for err in schema_errors:
            assert err.rule_id == "SCHEMA", (
                f"Schema error should have rule_id='SCHEMA', got {err.rule_id}"
            )
            assert err.severity == Severity.ERROR, "Schema errors should be ERROR severity"

    def test_schema_errors_coexist_with_rule_errors(self, validator, rules_dir, project_root):
        """Test that schema and rule errors can both be present and distinguishable."""
        # File with both schema violations (missing fields) and rule violations (out of range values)
        content = """
{
  "timestamp": "2025-01-15T10:00:00Z",
  "senderId": "DEPOT_001",
  "receiverId": "CMS_001",
  "chargingRequestList": [
    {
      "chargingRequestId": "REQ-001",
      "vehicleId": "BUS-123",
      "chargingRequestData": {
        "requestedEnergy": 999999,
        "requestedPower": 999999,
        "currentSoC": 150,
        "targetSoC": 200
      }
    }
  ]
}
"""
        # Create validator with rules
        config_path = project_root / "rules" / "default.yaml"
        validator_with_rules = VDV463Validator(
            schema_dir=validator.schema_manager.schema_dir,
            config_path=config_path,
            schema_version="auto",
        )

        result = validator_with_rules.validate_content(content, schema_only=False)

        # Get schema and rule errors
        schema_errors = [i for i in result.issues if i.rule_id == "SCHEMA"]
        rule_errors = [i for i in result.issues if i.rule_id and i.rule_id != "SCHEMA"]

        # Should have both types of errors
        assert len(schema_errors) > 0, "Expected schema errors for missing required fields"
        assert len(rule_errors) > 0, "Expected rule errors for out-of-range values"

        # Verify they are distinguishable
        for err in schema_errors:
            assert err.rule_id == "SCHEMA"
        for err in rule_errors:
            assert err.rule_id != "SCHEMA"

    def test_schema_only_mode_shows_schema_errors(self, validator):
        """Test that schema_only=True still shows schema errors."""
        content = """
{
  "timestamp": "2025-01-15T10:00:00Z",
  "senderId": "DEPOT_001",
  "receiverId": "CMS_001",
  "chargingRequestList": [
    {
      "requestId": "REQ-001"
    }
  ]
}
"""
        result = validator.validate_content(content, schema_only=True)

        schema_errors = [i for i in result.issues if i.rule_id == "SCHEMA"]

        # Should have schema errors even in schema_only mode
        assert len(schema_errors) > 0, "Expected schema errors in schema_only mode"

    def test_schema_validation_runs_before_rule_validation(
        self, validator, rules_dir, project_root
    ):
        """Test that schema validation runs regardless of schema_only parameter."""
        content = """
{
  "timestamp": "2025-01-15T10:00:00Z",
  "senderId": "DEPOT_001",
  "receiverId": "CMS_001",
  "chargingRequestList": [
    {
      "requestId": "REQ-001"
    }
  ]
}
"""

        # Create validator with rules
        config_path = project_root / "rules" / "default.yaml"
        validator_with_rules = VDV463Validator(
            schema_dir=validator.schema_manager.schema_dir,
            config_path=config_path,
            schema_version="auto",
        )

        # Test with schema_only=True
        result_schema_only = validator_with_rules.validate_content(content, schema_only=True)
        schema_errors_only = [i for i in result_schema_only.issues if i.rule_id == "SCHEMA"]

        # Test with schema_only=False
        result_full = validator_with_rules.validate_content(content, schema_only=False)
        schema_errors_full = [i for i in result_full.issues if i.rule_id == "SCHEMA"]

        # Schema errors should be the same in both modes
        assert len(schema_errors_only) == len(schema_errors_full), (
            "Schema validation should produce same errors regardless of schema_only parameter"
        )

        # Schema error messages should be identical
        schema_messages_only = {e.message for e in schema_errors_only}
        schema_messages_full = {e.message for e in schema_errors_full}
        assert schema_messages_only == schema_messages_full, (
            "Schema error messages should be identical in both modes"
        )

    def test_missing_message_type_shows_schema_error(self, validator):
        """Test that files without a valid message type show a schema error."""
        content = """
{
  "timestamp": "2025-01-15T10:00:00Z"
}
"""
        result = validator.validate_content(content, schema_only=False)

        schema_errors = [i for i in result.issues if i.rule_id == "SCHEMA"]

        # Should have at least one schema error about missing message type
        assert len(schema_errors) > 0, "Expected schema error for missing message type"

        # Check that the error message mentions the missing message type
        error_messages = [e.message for e in schema_errors]
        assert any("message type" in msg.lower() for msg in error_messages), (
            "Expected error message about message type"
        )

    def test_invalid_json_shows_schema_error(self, validator):
        """Test that invalid JSON shows a schema error."""
        # Invalid JSON: missing comma after "json" on line 181
        content = """
{
  "timestamp": "2025-01-15T10:00:00Z",
  "invalid": "json"
  "missingComma": "here"
}
"""
        result = validator.validate_content(content, schema_only=False)

        schema_errors = [i for i in result.issues if i.rule_id == "SCHEMA"]

        # Should have a schema error for invalid JSON
        assert len(schema_errors) > 0, "Expected schema error for invalid JSON"
        assert result.parse_error is not None, "Expected parse_error to be set"
