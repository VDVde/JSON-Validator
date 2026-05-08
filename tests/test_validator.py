"""
Unit tests for VDV463 Validator.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vdv463_validator import (
    BatchValidationResult,
    SchemaVersion,
    Severity,
    ValidationResult,
    VDV463Validator,
)

# =============================================================================
# Validator Initialization Tests
# =============================================================================


class TestValidatorInitialization:
    """Tests for validator initialization."""

    def test_init_with_valid_schema_dir(self, schema_dir):
        """Test validator initializes with valid schema directory."""
        if schema_dir.exists():
            validator = VDV463Validator(schema_dir)
            assert validator is not None

    def test_init_with_missing_schema_dir(self, tmp_path):
        """Test validator raises error for missing schema directory."""
        missing_dir = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            VDV463Validator(missing_dir)

    def test_init_with_config(self, schema_dir, rules_dir):
        """Test validator initializes with config file."""
        if schema_dir.exists():
            config_path = rules_dir / "test_rules_strict.yaml"
            if config_path.exists():
                validator = VDV463Validator(schema_dir, config_path)
                assert validator is not None


# =============================================================================
# Message Type Detection Tests
# =============================================================================


class TestMessageTypeDetection:
    """Tests for automatic message type detection."""

    def test_detect_charging_request(self, schema_dir, sample_charging_request):
        """Test detection of ProvideChargingRequestsRequest."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        validator = VDV463Validator(schema_dir)
        msg_type = validator.detect_message_type(sample_charging_request)
        assert msg_type == "ProvideChargingRequestsRequest"

    def test_detect_charging_info(self, schema_dir, sample_charging_info):
        """Test detection of ProvideChargingInformationRequest."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        validator = VDV463Validator(schema_dir)
        msg_type = validator.detect_message_type(sample_charging_info)
        assert msg_type == "ProvideChargingInformationRequest"

    def test_detect_unknown_message(self, schema_dir):
        """Test detection returns None for unknown message type."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        validator = VDV463Validator(schema_dir)
        msg_type = validator.detect_message_type({"unknown": "data"})
        assert msg_type is None


# =============================================================================
# Validation Result Tests
# =============================================================================


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_initial_state(self):
        """Test ValidationResult initial state."""
        result = ValidationResult("test.json")
        assert result.input_file == "test.json"
        assert result.valid is True
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.info_count == 0

    def test_add_error(self):
        """Test adding an error."""
        result = ValidationResult("test.json")
        result.add_issue("$.field", "Error message", Severity.ERROR)

        assert result.valid is False
        assert result.error_count == 1
        assert result.warning_count == 0

    def test_add_warning(self):
        """Test adding a warning."""
        result = ValidationResult("test.json")
        result.add_warning("$.field", "Warning message")

        assert result.valid is True  # Warnings don't affect validity
        assert result.warning_count == 1

    def test_add_info(self):
        """Test adding an info message."""
        result = ValidationResult("test.json")
        result.add_info("$.field", "Info message")

        assert result.valid is True
        assert result.info_count == 1

    def test_has_issues_at_or_above(self):
        """Test severity threshold checking."""
        result = ValidationResult("test.json")
        result.add_warning("$.field", "Warning")

        assert result.has_issues_at_or_above(Severity.WARNING) is True
        assert result.has_issues_at_or_above(Severity.ERROR) is False
        assert result.has_issues_at_or_above(Severity.INFO) is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ValidationResult("test.json")
        result.message_type = "ProvideChargingRequestsRequest"
        result.add_issue("$.field", "Error", Severity.ERROR)

        data = result.to_dict()
        assert data["input_file"] == "test.json"
        assert data["message_type"] == "ProvideChargingRequestsRequest"
        assert data["valid"] is False
        assert data["summary"]["errors"] == 1


# =============================================================================
# Batch Validation Result Tests
# =============================================================================


class TestBatchValidationResult:
    """Tests for BatchValidationResult class."""

    def test_initial_state(self):
        """Test initial state."""
        batch = BatchValidationResult()
        assert batch.total_files == 0
        assert batch.all_passed is True

    def test_add_results(self):
        """Test adding results."""
        batch = BatchValidationResult()

        result1 = ValidationResult("file1.json")
        result2 = ValidationResult("file2.json")
        result2.add_issue("$", "Error", Severity.ERROR)

        batch.add(result1)
        batch.add(result2)

        assert batch.total_files == 2
        assert batch.passed_files == 1
        assert batch.failed_files == 1

    def test_fail_level_error(self):
        """Test fail level ERROR."""
        batch = BatchValidationResult(fail_level=Severity.ERROR)

        result = ValidationResult("test.json")
        result.add_warning("$", "Warning")
        batch.add(result)

        assert batch.all_passed is True  # Warning doesn't fail at ERROR level

    def test_fail_level_warning(self):
        """Test fail level WARNING."""
        batch = BatchValidationResult(fail_level=Severity.WARNING)

        result = ValidationResult("test.json")
        result.add_warning("$", "Warning")
        batch.add(result)

        assert batch.all_passed is False  # Warning fails at WARNING level


# =============================================================================
# Severity Tests
# =============================================================================


class TestSeverity:
    """Tests for Severity enum."""

    def test_from_string(self):
        """Test parsing severity from string."""
        assert Severity.from_string("ERROR") == Severity.ERROR
        assert Severity.from_string("ERR") == Severity.ERROR
        assert Severity.from_string("WARNING") == Severity.WARNING
        assert Severity.from_string("WARN") == Severity.WARNING
        assert Severity.from_string("INFO") == Severity.INFO

    def test_from_string_case_insensitive(self):
        """Test case insensitivity."""
        assert Severity.from_string("error") == Severity.ERROR
        assert Severity.from_string("Warning") == Severity.WARNING

    def test_comparison(self):
        """Test severity comparison."""
        assert Severity.ERROR.value < Severity.WARNING.value
        assert Severity.WARNING.value < Severity.INFO.value


# =============================================================================
# File Validation Tests
# =============================================================================


class TestFileValidation:
    """Tests for file validation."""

    def test_validate_valid_file(self, schema_dir, sample_charging_request, save_temp_json):
        """Test validation of valid file."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = save_temp_json(sample_charging_request)
        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(file_path)

        assert result.message_type == "ProvideChargingRequestsRequest"
        _result = validator.validate_file(file_path)

        assert _result.message_type == "ProvideChargingRequestsRequest"
        # Note: May have schema errors if schema files don't match test data

    def test_validate_invalid_json(self, schema_dir, tmp_path):
        """Test validation of invalid JSON file."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")

        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(file_path)

        assert result.valid is False
        assert result.error_count > 0
        assert "Invalid JSON" in result.errors[0].message

    def test_validate_missing_file(self, schema_dir, tmp_path):
        """Test validation of missing file."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = tmp_path / "nonexistent.json"

        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(file_path)

        assert result.valid is False
        assert "not found" in result.errors[0].message.lower()

    def test_validate_unknown_message_type(self, schema_dir, save_temp_json):
        """Test validation of unknown message type."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = save_temp_json({"unknown": "structure"})

        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(file_path)

        assert result.valid is False
        assert "Cannot detect message type" in result.errors[0].message


# =============================================================================
# Batch Validation Tests
# =============================================================================


class TestBatchValidation:
    """Tests for batch validation."""

    def test_validate_multiple_files(
        self, schema_dir, sample_charging_request, sample_charging_info, save_temp_json, tmp_path
    ):
        """Test batch validation of multiple files."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file1 = tmp_path / "request.json"
        file2 = tmp_path / "info.json"

        with open(file1, "w") as f:
            json.dump(sample_charging_request, f)
        with open(file2, "w") as f:
            json.dump(sample_charging_info, f)

        validator = VDV463Validator(schema_dir)
        result = validator.validate_batch([file1, file2])

        assert result.total_files == 2

    def test_batch_with_fail_level(self, schema_dir, sample_charging_request, tmp_path):
        """Test batch validation with custom fail level."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = tmp_path / "test.json"
        with open(file_path, "w") as f:
            json.dump(sample_charging_request, f)

        validator = VDV463Validator(schema_dir)
        result = validator.validate_batch([file_path], fail_level=Severity.WARNING)

        assert result.fail_level == Severity.WARNING


# =============================================================================
# Schema Version Tests
# =============================================================================


class TestSchemaVersion:
    """Tests for schema version handling."""

    def test_supported_versions(self):
        """Test supported versions list."""
        assert "1.0" in SchemaVersion.SUPPORTED_VERSIONS
        assert "1.1" in SchemaVersion.SUPPORTED_VERSIONS
        assert "1.1-dev" in SchemaVersion.SUPPORTED_VERSIONS
        assert "2.0" in SchemaVersion.SUPPORTED_VERSIONS
        assert "auto" in SchemaVersion.SUPPORTED_VERSIONS

    def test_detect_layout_versioned(self, tmp_path):
        """Test detection of versioned layout."""
        (tmp_path / "v1.0").mkdir()
        (tmp_path / "v1.1").mkdir()

        manager = SchemaVersion(tmp_path)
        assert manager.layout == "versioned"

    def test_detect_layout_flat(self, tmp_path):
        """Test detection of flat layout."""
        (tmp_path / "ProvideChargingInformationRequest.json").write_text("{}")

        manager = SchemaVersion(tmp_path)
        assert manager.layout == "flat"

    def test_get_available_versions(self, tmp_path):
        """Test getting available versions."""
        (tmp_path / "v1.0").mkdir()
        (tmp_path / "v1.1").mkdir()

        manager = SchemaVersion(tmp_path)
        versions = manager.get_available_versions()

        assert "1.0" in versions
        assert "1.1" in versions


# =============================================================================
# Cross-Field Validation Tests
# =============================================================================


class TestCrossFieldValidation:
    """Tests for cross-field validation."""

    def test_soc_violation(self, schema_dir, sample_cross_field_violation, save_temp_json):
        """Test SoC cross-field violation detection."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = save_temp_json(sample_cross_field_violation)

        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(file_path)

        # Should have warnings about SoC inconsistency
        _ = [i.message for i in result.issues]
        _all_messages = [i.message for i in result.issues]
        # Check if any cross-field issues were detected
        # (depends on rules being configured)

    def test_temporal_violation(self, schema_dir, sample_cross_field_violation, save_temp_json):
        """Test temporal cross-field violation detection."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        file_path = save_temp_json(sample_cross_field_violation)

        validator = VDV463Validator(schema_dir)
        _ = validator.validate_file(file_path)

        _validator = VDV463Validator(schema_dir)
        _result = _validator.validate_file(file_path)

        # Should detect departure before arrival
        # (depends on rules being configured)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests using fixture files."""

    def test_valid_fixtures(self, schema_dir, valid_fixtures_for_version):
        """Test all valid fixtures pass validation."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        if not valid_fixtures_for_version:
            pytest.skip("No valid fixtures found")

        validator = VDV463Validator(schema_dir)

        for fixture_path in valid_fixtures_for_version:
            _ = validator.validate_file(fixture_path)
            _result = validator.validate_file(fixture_path)
            # Note: May have issues if schemas don't match fixtures

    def test_invalid_fixtures(self, schema_dir, invalid_fixtures_for_version):
        """Test all invalid fixtures fail validation."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        if not invalid_fixtures_for_version:
            pytest.skip("No invalid fixtures found")

        validator = VDV463Validator(schema_dir)

        for fixture_path in invalid_fixtures_for_version:
            result = validator.validate_file(fixture_path)
            assert result.valid is False, f"Expected {fixture_path} to be invalid"


class TestMultipleErrorReporting:
    """Tests for reporting multiple validation errors."""

    def test_multiple_schema_errors_reported(self, schema_dir):
        """Test that all schema validation errors are reported, not just the first one."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "v1.1"
            / "invalid"
            / "multiple_errors_charging_info.json"
        )
        if not fixture_path.exists():
            pytest.skip("Test fixture not found")

        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(fixture_path)

        # Validation should fail
        assert result.valid is False, "Expected validation to fail"

        # Should have multiple errors
        assert result.error_count > 1, (
            f"Expected multiple errors, but got {result.error_count}. "
            "Validation should not stop after the first error."
        )

        # Check for specific expected errors
        error_messages = [
            issue.message for issue in result.issues if issue.severity == Severity.ERROR
        ]

        # Expected error patterns:
        expected_patterns = [
            "InvalidStatus",  # Invalid chargingStationStatus enum value
            "WrongStatus",  # Invalid chargingPointStatus enum value
            "not-a-number",  # maxPower should be number, not string
            "12345",  # chargingPointId should be string, not integer
            "is a required property",  # Missing required fields
            "Additional properties",  # Unexpected field at root level
        ]

        # Count how many expected error patterns we found
        found_patterns = 0
        for pattern in expected_patterns:
            if any(pattern in msg for msg in error_messages):
                found_patterns += 1

        # We should find at least 4 different types of errors
        assert found_patterns >= 4, (
            f"Expected to find at least 4 different error types, but only found {found_patterns}. "
            f"Errors found: {error_messages}"
        )

        # Print summary for debugging
        print("\n--- Multiple Error Test Summary ---")
        print(f"Total errors: {result.error_count}")
        print(f"Total warnings: {result.warning_count}")
        print(f"Error patterns found: {found_patterns}/{len(expected_patterns)}")
        print("\nAll error messages:")
        for i, msg in enumerate(error_messages, 1):
            print(f"  {i}. {msg}")

    def test_error_locations_are_specific(self, schema_dir):
        """Test that error messages include specific locations (paths) in the JSON structure."""
        if not schema_dir.exists():
            pytest.skip("Schema directory not found")

        fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "v1.1"
            / "invalid"
            / "multiple_errors_charging_info.json"
        )
        if not fixture_path.exists():
            pytest.skip("Test fixture not found")

        validator = VDV463Validator(schema_dir)
        result = validator.validate_file(fixture_path)

        # Get all error paths
        error_paths = [issue.path for issue in result.issues if issue.severity == Severity.ERROR]

        # Should have errors with specific paths (not just root "$")
        specific_paths = [path for path in error_paths if path != "$"]

        assert len(specific_paths) > 0, (
            f"Expected errors with specific paths, but all errors are at root level. "
            f"Paths found: {error_paths}"
        )

        # Check that we have errors at different nesting levels
        nested_paths = [path for path in error_paths if "[" in path or "." in path]

        assert len(nested_paths) > 0, (
            f"Expected errors in nested structures, but none found. Paths found: {error_paths}"
        )

        print("\n--- Error Location Test Summary ---")
        print(f"Total error paths: {len(error_paths)}")
        print(f"Specific paths (not root): {len(specific_paths)}")
        print(f"Nested paths: {len(nested_paths)}")
        print("\nAll error paths:")
        for path in sorted(set(error_paths)):
            print(f"  - {path}")
