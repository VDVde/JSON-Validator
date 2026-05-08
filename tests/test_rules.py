"""
Unit tests for VDV463 Validation Rules Engine.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validation_rules import ValidationRuleError, ValueRangeValidator

# =============================================================================
# Validator Initialization Tests
# =============================================================================


class TestValidatorInitialization:
    """Tests for ValueRangeValidator initialization."""

    def test_init_without_config(self):
        """Test initialization without config loads defaults."""
        validator = ValueRangeValidator()
        assert validator.range_rules is not None
        assert len(validator.range_rules) > 0

    def test_init_with_valid_config(self, tmp_path):
        """Test initialization with valid config file."""
        config_path = tmp_path / "rules.yaml"
        config_path.write_text("""
range_rules:
  maxPower:
    min: 0
    max: 500
    message: "Power out of range"
""")
        validator = ValueRangeValidator(config_path)
        assert "maxPower" in validator.range_rules
        assert validator.range_rules["maxPower"]["max"] == 500

    def test_init_with_missing_config(self, tmp_path):
        """Test initialization with missing config raises error."""
        config_path = tmp_path / "nonexistent.yaml"
        with pytest.raises(ValidationRuleError):
            ValueRangeValidator(config_path)

    def test_init_with_invalid_yaml(self, tmp_path):
        """Test initialization with invalid YAML raises error."""
        config_path = tmp_path / "invalid.yaml"
        config_path.write_text("{ invalid: yaml: syntax")
        with pytest.raises(ValidationRuleError):
            ValueRangeValidator(config_path)


# =============================================================================
# Range Validation Tests
# =============================================================================


class TestRangeValidation:
    """Tests for simple range validation."""

    def test_value_within_range(self):
        """Test value within valid range."""
        validator = ValueRangeValidator()
        validator.range_rules = {"maxPower": {"min": 0, "max": 1000}}

        # Mock result object
        result = MockResult()
        data = {"maxPower": 500}

        validator._validate_ranges(data, "", result)
        assert len(result.range_errors) == 0

    def test_value_below_minimum(self):
        """Test value below minimum."""
        validator = ValueRangeValidator()
        validator.range_rules = {
            "maxPower": {"min": 0, "max": 1000, "message": "Power out of range"}
        }

        result = MockResult()
        data = {"maxPower": -10}

        validator._validate_ranges(data, "", result)
        assert len(result.range_errors) == 1

    def test_value_above_maximum(self):
        """Test value above maximum."""
        validator = ValueRangeValidator()
        validator.range_rules = {
            "maxPower": {"min": 0, "max": 1000, "message": "Power out of range"}
        }

        result = MockResult()
        data = {"maxPower": 1500}

        validator._validate_ranges(data, "", result)
        assert len(result.range_errors) == 1

    def test_nested_value_validation(self):
        """Test validation of nested values."""
        validator = ValueRangeValidator()
        validator.range_rules = {"currentSoC": {"min": 0, "max": 100}}

        result = MockResult()
        data = {
            "chargingRequestList": [
                {"currentSoC": 50},
                {"currentSoC": 150},  # Invalid
            ]
        }

        validator._validate_ranges(data, "", result)
        assert len(result.range_errors) == 1

    def test_soc_validation(self):
        """Test SoC range validation."""
        validator = ValueRangeValidator()
        validator.range_rules = {
            "currentSoC": {"min": 0, "max": 100},
            "targetSoC": {"min": 0, "max": 100},
        }

        result = MockResult()
        data = {"currentSoC": 30, "targetSoC": 90}

        validator._validate_ranges(data, "", result)
        assert len(result.range_errors) == 0


# =============================================================================
# Cross-Field Validation Tests
# =============================================================================


class TestCrossFieldValidation:
    """Tests for cross-field validation rules."""

    def test_cross_field_rule_evaluation(self):
        """Test basic cross-field rule evaluation."""
        validator = ValueRangeValidator()
        validator.cross_field_rules = [
            {
                "id": "TEST-001",
                "name": "Test rule",
                "severity": "ERROR",
                "applies_to": ["ProvideChargingRequestsRequest"],
                "condition": {"fields": ["minPower", "maxPower"], "rule": "minPower <= maxPower"},
                "message": "minPower exceeds maxPower",
            }
        ]

        # Valid data
        result = MockResult()
        data = {"chargingRequestList": [{"minPower": 50, "maxPower": 150}]}
        validator._validate_cross_field_rules(data, "ProvideChargingRequestsRequest", result)
        # Should pass - no errors for valid data

    def test_cross_field_rule_violation(self):
        """Test cross-field rule violation detection."""
        validator = ValueRangeValidator()
        validator.cross_field_rules = [
            {
                "id": "TEST-001",
                "severity": "ERROR",
                "applies_to": ["ProvideChargingRequestsRequest"],
                "condition": {"fields": ["minPower", "maxPower"], "rule": "minPower <= maxPower"},
                "message": "minPower ({minPower}) exceeds maxPower ({maxPower})",
            }
        ]

        # Invalid data - minPower > maxPower
        result = MockResult()
        data = {"chargingRequestList": [{"minPower": 200, "maxPower": 100}]}
        validator._validate_cross_field_rules(data, "ProvideChargingRequestsRequest", result)
        assert len(result.range_errors) == 1

    def test_cross_field_warning_severity(self):
        """Test cross-field rule with WARNING severity."""
        validator = ValueRangeValidator()
        validator.cross_field_rules = [
            {
                "id": "TEST-002",
                "severity": "WARNING",
                "applies_to": ["ProvideChargingRequestsRequest"],
                "condition": {
                    "fields": ["currentSoC", "targetSoC"],
                    "rule": "targetSoC > currentSoC",
                },
                "message": "targetSoC should be greater than currentSoC",
            }
        ]

        result = MockResult()
        data = {
            "chargingRequestList": [
                {"currentSoC": 80, "targetSoC": 70}  # Violation
            ]
        }
        validator._validate_cross_field_rules(data, "ProvideChargingRequestsRequest", result)
        assert len(result.warnings) == 1

    def test_rule_applies_to_filtering(self):
        """Test that rules only apply to specified message types."""
        validator = ValueRangeValidator()
        validator.cross_field_rules = [
            {
                "id": "TEST-003",
                "severity": "ERROR",
                "applies_to": ["ProvideChargingInformationRequest"],  # Different type
                "condition": {"fields": ["minPower", "maxPower"], "rule": "minPower <= maxPower"},
                "message": "Test",
            }
        ]

        result = MockResult()
        data = {
            "chargingRequestList": [
                {"minPower": 200, "maxPower": 100}  # Would violate
            ]
        }
        # Rule should not apply to ProvideChargingRequestsRequest
        validator._validate_cross_field_rules(data, "ProvideChargingRequestsRequest", result)
        assert len(result.range_errors) == 0


# =============================================================================
# Conditional Rules Tests
# =============================================================================


class TestConditionalRules:
    """Tests for conditional validation rules."""

    def test_conditional_rule_when_met(self):
        """Test conditional rule when condition is met."""
        validator = ValueRangeValidator()
        validator.conditional_rules = [
            {
                "id": "CND-001",
                "severity": "WARNING",
                "applies_to": ["ProvideChargingRequestsRequest"],
                "when": {"field": "preconditioningRequested", "equals": True},
                "then": {"required_fields": ["batteryTemperature"]},
                "message": "Temperature required for preconditioning",
            }
        ]

        result = MockResult()
        data = {
            "chargingRequestList": [
                {
                    "preconditioningRequested": True,
                    # Missing batteryTemperature
                }
            ]
        }
        validator._validate_conditional_rules(data, "ProvideChargingRequestsRequest", result)
        assert len(result.warnings) == 1

    def test_conditional_rule_when_not_met(self):
        """Test conditional rule when condition is not met."""
        validator = ValueRangeValidator()
        validator.conditional_rules = [
            {
                "id": "CND-001",
                "severity": "WARNING",
                "applies_to": ["ProvideChargingRequestsRequest"],
                "when": {"field": "preconditioningRequested", "equals": True},
                "then": {"required_fields": ["batteryTemperature"]},
                "message": "Temperature required",
            }
        ]

        result = MockResult()
        data = {
            "chargingRequestList": [
                {
                    "preconditioningRequested": False,
                    # Missing batteryTemperature - but shouldn't matter
                }
            ]
        }
        validator._validate_conditional_rules(data, "ProvideChargingRequestsRequest", result)
        assert len(result.warnings) == 0


# =============================================================================
# Warning Threshold Tests
# =============================================================================


class TestWarningThresholds:
    """Tests for warning thresholds."""

    def test_low_soc_warning(self):
        """Test low SoC warning threshold."""
        validator = ValueRangeValidator()
        validator.warning_thresholds = {"low_soc_warning": 20}

        result = MockResult()
        data = {"currentSoC": 15}  # Below threshold

        validator._check_warning_thresholds(data, "", result)
        assert len(result.warnings) == 1
        assert "Low battery" in result.warnings[0]["message"]

    def test_high_power_warning(self):
        """Test high power warning threshold."""
        validator = ValueRangeValidator()
        validator.warning_thresholds = {"high_power_warning": 350}

        result = MockResult()
        data = {"requestedPower": 400}  # Above threshold

        validator._check_warning_thresholds(data, "", result)
        assert len(result.warnings) == 1
        assert "High power" in result.warnings[0]["message"]

    def test_no_warning_within_threshold(self):
        """Test no warning when within thresholds."""
        validator = ValueRangeValidator()
        validator.warning_thresholds = {"low_soc_warning": 20, "high_power_warning": 350}

        result = MockResult()
        data = {"currentSoC": 50, "requestedPower": 150}

        validator._check_warning_thresholds(data, "", result)
        assert len(result.warnings) == 0


# =============================================================================
# Nested Value Access Tests
# =============================================================================


class TestNestedValueAccess:
    """Tests for nested value access."""

    def test_get_simple_value(self):
        """Test getting simple value."""
        validator = ValueRangeValidator()
        data = {"field": "value"}

        result = validator._get_nested_value(data, "field")
        assert result == "value"

    def test_get_nested_value(self):
        """Test getting nested value."""
        validator = ValueRangeValidator()
        data = {"level1": {"level2": {"field": "deep_value"}}}

        result = validator._get_nested_value(data, "level1.level2.field")
        assert result == "deep_value"

    def test_get_array_value(self):
        """Test getting value from array."""
        validator = ValueRangeValidator()
        data = {"items": [{"value": "first"}, {"value": "second"}]}

        result = validator._get_nested_value(data, "items.1.value")
        assert result == "second"

    def test_get_missing_value(self):
        """Test getting missing value returns None."""
        validator = ValueRangeValidator()
        data = {"field": "value"}

        result = validator._get_nested_value(data, "nonexistent")
        assert result is None

    def test_get_empty_path(self):
        """Test getting with empty path returns None."""
        validator = ValueRangeValidator()
        data = {"field": "value"}

        result = validator._get_nested_value(data, "")
        assert result is None


# =============================================================================
# Expression Evaluation Tests
# =============================================================================


class TestExpressionEvaluation:
    """Tests for rule expression evaluation."""

    def test_less_than_equal(self):
        """Test <= operator."""
        validator = ValueRangeValidator()
        values = {"a": 5, "b": 10}

        assert validator._evaluate_expression("a <= b", values) is True
        assert validator._evaluate_expression("b <= a", values) is False

    def test_greater_than(self):
        """Test > operator."""
        validator = ValueRangeValidator()
        values = {"a": 10, "b": 5}

        assert validator._evaluate_expression("a > b", values) is True
        assert validator._evaluate_expression("b > a", values) is False

    def test_equality(self):
        """Test == operator."""
        validator = ValueRangeValidator()
        values = {"a": 5, "b": 5}

        assert validator._evaluate_expression("a == b", values) is True

    def test_compare_with_literal(self):
        """Test comparison with literal value."""
        validator = ValueRangeValidator()
        values = {"power": 150}

        assert validator._evaluate_expression("power <= 200", values) is True
        assert validator._evaluate_expression("power > 200", values) is False


# =============================================================================
# Configuration Loading Tests
# =============================================================================


class TestConfigurationLoading:
    """Tests for configuration file loading."""

    def test_load_complete_config(self, tmp_path):
        """Test loading complete configuration."""
        config_path = tmp_path / "complete.yaml"
        config_path.write_text("""
settings:
  strict_mode: false
  default_severity: WARNING

range_rules:
  maxPower:
    min: 0
    max: 1000
    unit: kW

cross_field_rules:
  - id: TEST-001
    name: Test rule
    severity: ERROR
    applies_to:
      - ProvideChargingRequestsRequest
    condition:
      fields: [minPower, maxPower]
      rule: "minPower <= maxPower"
    message: Invalid power range

warning_thresholds:
  low_soc_warning: 20
  high_power_warning: 350
""")

        validator = ValueRangeValidator(config_path)

        assert "maxPower" in validator.range_rules
        assert len(validator.cross_field_rules) == 1
        assert validator.warning_thresholds["low_soc_warning"] == 20

    def test_load_partial_config(self, tmp_path):
        """Test loading partial configuration."""
        config_path = tmp_path / "partial.yaml"
        config_path.write_text("""
range_rules:
  targetSoC:
    min: 0
    max: 100
""")

        validator = ValueRangeValidator(config_path)

        assert "targetSoC" in validator.range_rules
        assert validator.cross_field_rules == []


# =============================================================================
# Mock Result Class
# =============================================================================


class MockResult:
    """Mock ValidationResult for testing."""

    def __init__(self):
        self.schema_errors = []
        self.range_errors = []
        self.warnings = []
        self.infos = []

    def add_schema_error(self, path, message, value=None):
        self.schema_errors.append({"path": path, "message": message, "value": value})

    def add_range_error(self, path, message, value, constraint):
        self.range_errors.append(
            {"path": path, "message": message, "value": value, "constraint": constraint}
        )

    def add_warning(self, path, message, value=None):
        self.warnings.append({"path": path, "message": message, "value": value})

    def add_info(self, path, message, value=None):
        self.infos.append({"path": path, "message": message, "value": value})
