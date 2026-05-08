"""
Unit tests for VDV463 Advanced Value Check Rules.

Tests for:
- SoC range validation (0-100%)
- Cross-field validation rules
- Semantic rules (SEM-001, SEM-002, SEM-003)
- Warning thresholds
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validation_rules import ValueRangeValidator

# =============================================================================
# Mock Result Class
# =============================================================================


class MockValidationResult:
    """Mock ValidationResult for testing."""

    def __init__(self):
        self.schema_errors = []
        self.range_errors = []
        self.warnings = []
        self.infos = []
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0

    def add_schema_error(self, path, message, value=None):
        self.schema_errors.append({"path": path, "message": message, "value": value})
        self.error_count += 1

    def add_range_error(self, path, message, value, constraint):
        self.range_errors.append(
            {"path": path, "message": message, "value": value, "constraint": constraint}
        )
        self.error_count += 1

    def add_warning(self, path, message, value=None):
        self.warnings.append({"path": path, "message": message, "value": value})
        self.warning_count += 1

    def add_info(self, path, message, value=None):
        self.infos.append({"path": path, "message": message, "value": value})
        self.info_count += 1


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def advanced_rules_validator():
    """Create validator with advanced rules."""
    rules_path = Path(__file__).parent.parent / "rules" / "advanced_value_check_rules.yaml"
    return ValueRangeValidator(rules_path)


@pytest.fixture
def default_validator():
    """Create validator with default rules."""
    return ValueRangeValidator()


# =============================================================================
# SoC Range Validation Tests
# =============================================================================


class TestSoCRangeValidation:
    """Tests for State of Charge range validation (0-100%)."""

    def test_soc_valid_range(self, advanced_rules_validator):
        """Test valid SoC values within 0-100%."""
        result = MockValidationResult()
        data = {"stateOfCharge": 50}

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0

    def test_soc_at_boundaries(self, advanced_rules_validator):
        """Test SoC at boundary values 0% and 100%."""
        result = MockValidationResult()

        # Test 0%
        data = {"stateOfCharge": 0}
        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0

        # Test 100%
        data = {"stateOfCharge": 100}
        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0

    def test_soc_below_zero(self, advanced_rules_validator):
        """Test SoC below 0% triggers error."""
        result = MockValidationResult()
        data = {"stateOfCharge": -5}

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 1
        assert "stateOfCharge" in result.range_errors[0]["path"]

    def test_soc_above_100(self, advanced_rules_validator):
        """Test SoC above 100% triggers error."""
        result = MockValidationResult()
        data = {"stateOfCharge": 105}

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 1
        assert "stateOfCharge" in result.range_errors[0]["path"]

    def test_multiple_soc_fields(self, advanced_rules_validator):
        """Test multiple SoC fields are all validated."""
        result = MockValidationResult()
        data = {
            "stateOfCharge": 50,
            "stateOfHealth": 95,
            "minTargetSoc": 80,
            "maxTargetSoc": 100,
            "requestedMinSoc": 70,
            "predictedFinalSoc": 90,
        }

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0

    def test_invalid_soc_in_nested_structure(self, advanced_rules_validator):
        """Test SoC validation in nested JSON structure."""
        result = MockValidationResult()
        data = {
            "depotInfoList": [
                {
                    "chargingStationInfoList": [
                        {
                            "chargingPointInfoList": [
                                {
                                    "vehicleInfo": {
                                        "tractionBatteryInfo": {
                                            "stateOfCharge": 150  # Invalid
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 1


# =============================================================================
# Power and Energy Range Tests
# =============================================================================


class TestPowerRangeValidation:
    """Tests for power and energy value ranges."""

    def test_valid_charging_power(self, advanced_rules_validator):
        """Test valid charging power values."""
        result = MockValidationResult()
        data = {"chargingPower": 150}  # 150 kW - typical DC fast charger

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0

    def test_charging_power_exceeds_max(self, advanced_rules_validator):
        """Test charging power exceeds maximum (500 kW)."""
        result = MockValidationResult()
        data = {"chargingPower": 600}  # Exceeds 500 kW max

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 1

    def test_negative_power_invalid(self, advanced_rules_validator):
        """Test negative power values are invalid."""
        result = MockValidationResult()
        data = {"chargingPower": -50}

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 1

    def test_valid_voltage_and_current(self, advanced_rules_validator):
        """Test valid voltage and current values."""
        result = MockValidationResult()
        data = {
            "chargingVoltage": 750,  # Typical DC bus voltage
            "chargingCurrent": 200,  # 200 A
        }

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0


# =============================================================================
# Temperature Range Tests
# =============================================================================


class TestTemperatureRangeValidation:
    """Tests for temperature value ranges."""

    def test_valid_battery_temperature(self, advanced_rules_validator):
        """Test valid battery temperature."""
        result = MockValidationResult()
        data = {"temperature": 25}  # 25°C - room temperature

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0

    def test_connector_temperature_critical(self, advanced_rules_validator):
        """Test critical connector temperature above 90°C."""
        result = MockValidationResult()
        data = {"connectorTemperature": 95}  # Above 90°C max

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 1

    def test_extreme_cold_temperature(self, advanced_rules_validator):
        """Test extreme cold temperature values."""
        result = MockValidationResult()
        data = {"outsideTemperature": -45}  # Very cold but within range

        advanced_rules_validator._validate_ranges(data, "", result)
        assert result.error_count == 0


# =============================================================================
# Cross-Field Validation Tests
# =============================================================================


class TestCrossFieldRulesAdvanced:
    """Tests for advanced cross-field validation rules."""

    def test_min_target_soc_exceeds_max(self, advanced_rules_validator):
        """Test ADV-SOC-001: minTargetSoc must not exceed maxTargetSoc."""
        result = MockValidationResult()
        data = {
            "chargingRequestList": [
                {
                    "chargingRequestData": {
                        "minTargetSoc": 90,
                        "maxTargetSoc": 80,  # Invalid: min > max
                    }
                }
            ]
        }

        advanced_rules_validator._validate_cross_field_rules(
            data, "ProvideChargingRequestsRequest", result
        )
        assert result.error_count >= 1

    def test_valid_target_soc_range(self, advanced_rules_validator):
        """Test valid minTargetSoc <= maxTargetSoc."""
        result = MockValidationResult()
        data = {
            "chargingRequestList": [
                {
                    "chargingRequestData": {
                        "minTargetSoc": 70,
                        "maxTargetSoc": 90,  # Valid: min <= max
                    }
                }
            ]
        }

        advanced_rules_validator._validate_cross_field_rules(
            data, "ProvideChargingRequestsRequest", result
        )
        # No ADV-SOC-001 error expected for valid data
        soc_errors = [e for e in result.range_errors if "ADV-SOC-001" in e.get("message", "")]
        assert len(soc_errors) == 0


# =============================================================================
# Semantic Rules Tests (SEM-001, SEM-002, SEM-003)
# =============================================================================


class TestSemanticRules:
    """Tests for semantic validation rules."""

    def test_sem001_charging_point_status_inconsistency(self, advanced_rules_validator):
        """Test SEM-001: ChargingPointStatus should not be Available during Charging."""
        result = MockValidationResult()

        # Invalid: Status is "Available" but processStatus is "Charging"
        data = {
            "depotInfoList": [
                {
                    "depotId": "D1",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS1",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP1",
                                    "chargingPointStatus": "Available",
                                    "chargingProcessInfo": {"processStatus": "Charging"},
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        advanced_rules_validator._validate_semantic_rules(
            data, "ProvideChargingInformationRequest", result
        )

        # Should have SEM-001 warning
        assert result.warning_count >= 1
        sem001_warnings = [w for w in result.warnings if "SEM-001" in w.get("message", "")]
        assert len(sem001_warnings) == 1

    def test_sem001_valid_occupied_during_charging(self, advanced_rules_validator):
        """Test SEM-001: Occupied status during Charging is valid."""
        result = MockValidationResult()

        # Valid: Status is "Occupied" during "Charging"
        data = {
            "depotInfoList": [
                {
                    "depotId": "D1",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS1",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP1",
                                    "chargingPointStatus": "Occupied",
                                    "chargingProcessInfo": {"processStatus": "Charging"},
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        advanced_rules_validator._validate_semantic_rules(
            data, "ProvideChargingInformationRequest", result
        )

        # Should NOT have SEM-001 warning
        sem001_warnings = [w for w in result.warnings if "SEM-001" in w.get("message", "")]
        assert len(sem001_warnings) == 0

    def test_sem001_available_when_finished(self, advanced_rules_validator):
        """Test SEM-001: Available status when Finished is valid."""
        result = MockValidationResult()

        # Valid: Status is "Available" when processStatus is "Finished"
        data = {
            "depotInfoList": [
                {
                    "depotId": "D1",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS1",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP1",
                                    "chargingPointStatus": "Available",
                                    "chargingProcessInfo": {"processStatus": "Finished"},
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        advanced_rules_validator._validate_semantic_rules(
            data, "ProvideChargingInformationRequest", result
        )

        # Should NOT have SEM-001 warning (Available is ok when not Charging/Preparing)
        sem001_warnings = [w for w in result.warnings if "SEM-001" in w.get("message", "")]
        assert len(sem001_warnings) == 0

    def test_sem001_preparing_status_inconsistency(self, advanced_rules_validator):
        """Test SEM-001: Available during Preparing is also invalid."""
        result = MockValidationResult()

        data = {
            "depotInfoList": [
                {
                    "depotId": "D1",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS1",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP1",
                                    "chargingPointStatus": "Available",
                                    "chargingProcessInfo": {"processStatus": "Preparing"},
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        advanced_rules_validator._validate_semantic_rules(
            data, "ProvideChargingInformationRequest", result
        )

        # Should have SEM-001 warning
        sem001_warnings = [w for w in result.warnings if "SEM-001" in w.get("message", "")]
        assert len(sem001_warnings) == 1

    def test_semantic_rules_multiple_charging_points(self, advanced_rules_validator):
        """Test semantic rules across multiple charging points."""
        result = MockValidationResult()

        data = {
            "depotInfoList": [
                {
                    "depotId": "D1",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS1",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP1",
                                    "chargingPointStatus": "Available",  # Invalid
                                    "chargingProcessInfo": {"processStatus": "Charging"},
                                },
                                {
                                    "chargingPointId": "CP2",
                                    "chargingPointStatus": "Occupied",  # Valid
                                    "chargingProcessInfo": {"processStatus": "Charging"},
                                },
                                {
                                    "chargingPointId": "CP3",
                                    "chargingPointStatus": "Available",  # Valid (no charging)
                                    "chargingProcessInfo": {"processStatus": "Idle"},
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        advanced_rules_validator._validate_semantic_rules(
            data, "ProvideChargingInformationRequest", result
        )

        # Should have exactly 1 SEM-001 warning (for CP1)
        sem001_warnings = [w for w in result.warnings if "SEM-001" in w.get("message", "")]
        assert len(sem001_warnings) == 1


# =============================================================================
# Integration Tests with Full Validator
# =============================================================================


class TestIntegrationAdvancedRules:
    """Integration tests using full validation pipeline."""

    def test_full_validation_valid_data(self, advanced_rules_validator):
        """Test full validation with completely valid data."""
        result = MockValidationResult()

        data = {
            "depotInfoList": [
                {
                    "depotId": "DEPOT-001",
                    "name": "Test Depot",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS-001",
                            "chargingStationStatus": "Available",
                            "totalPower": 450,
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP-001",
                                    "chargingPointStatus": "Occupied",
                                    "presentPower": 150,
                                    "connectorTemperature": 35,
                                    "chargingProcessInfo": {
                                        "processStatus": "Charging",
                                        "deliveredEnergy": 45,
                                    },
                                    "vehicleInfo": {
                                        "vehicleId": "BUS-001",
                                        "tractionBatteryInfo": {
                                            "stateOfCharge": 65,
                                            "stateOfHealth": 95,
                                            "temperature": 28,
                                        },
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        # Run full validation
        advanced_rules_validator.validate(data, "ProvideChargingInformationRequest", result)

        # Should have no errors
        assert result.error_count == 0

    def test_full_validation_multiple_issues(self, advanced_rules_validator):
        """Test full validation detecting multiple issues."""
        result = MockValidationResult()

        data = {
            "depotInfoList": [
                {
                    "depotId": "DEPOT-001",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS-001",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP-001",
                                    "chargingPointStatus": "Available",  # SEM-001 violation
                                    "connectorTemperature": 95,  # Range violation
                                    "chargingProcessInfo": {"processStatus": "Charging"},
                                    "vehicleInfo": {
                                        "tractionBatteryInfo": {
                                            "stateOfCharge": 150,  # Range violation
                                            "stateOfHealth": -10,  # Range violation
                                        }
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        advanced_rules_validator.validate(data, "ProvideChargingInformationRequest", result)

        # Should have multiple issues
        total_issues = result.error_count + result.warning_count
        assert total_issues >= 3  # At least SoC, connector temp, and SEM-001


# =============================================================================
# Warning Threshold Tests
# =============================================================================


class TestWarningThresholds:
    """Tests for warning threshold checks."""

    def test_low_soc_warning_triggered(self, advanced_rules_validator):
        """Test low SoC warning threshold."""
        result = MockValidationResult()
        data = {"currentSoC": 10}  # Below low_soc_warning threshold

        advanced_rules_validator._check_warning_thresholds(data, "", result)
        assert result.warning_count >= 1

    def test_high_power_warning_triggered(self, advanced_rules_validator):
        """Test high power warning threshold."""
        result = MockValidationResult()
        data = {"requestedPower": 400}  # Above high_power_warning threshold

        advanced_rules_validator._check_warning_thresholds(data, "", result)
        assert result.warning_count >= 1

    def test_no_warning_within_thresholds(self, advanced_rules_validator):
        """Test no warning when values within thresholds."""
        result = MockValidationResult()
        data = {
            "currentSoC": 50,  # Well above low_soc_warning
            "requestedPower": 100,  # Below high_power_warning
        }

        advanced_rules_validator._check_warning_thresholds(data, "", result)
        assert result.warning_count == 0


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_data(self, advanced_rules_validator):
        """Test validation with empty data."""
        result = MockValidationResult()
        data = {}

        advanced_rules_validator.validate(data, "ProvideChargingInformationRequest", result)
        assert result.error_count == 0  # No errors for empty data

    def test_missing_optional_fields(self, advanced_rules_validator):
        """Test validation when optional fields are missing."""
        result = MockValidationResult()
        data = {
            "depotInfoList": [
                {
                    "depotId": "D1",
                    "chargingStationInfoList": [],  # Empty station list
                }
            ]
        }

        advanced_rules_validator.validate(data, "ProvideChargingInformationRequest", result)
        # Should not crash with missing nested structures

    def test_null_values(self, advanced_rules_validator):
        """Test handling of null values."""
        result = MockValidationResult()
        data = {"stateOfCharge": None, "temperature": None}

        advanced_rules_validator._validate_ranges(data, "", result)
        # Should not crash with null values

    def test_string_values_for_numeric_fields(self, advanced_rules_validator):
        """Test handling of string values in numeric fields."""
        result = MockValidationResult()
        data = {
            "stateOfCharge": "fifty"  # String instead of number
        }

        advanced_rules_validator._validate_ranges(data, "", result)
        # Should not crash, should skip non-numeric values

    def test_very_deep_nesting(self, advanced_rules_validator):
        """Test validation with very deep nesting."""
        result = MockValidationResult()

        # Create deeply nested structure
        inner = {"stateOfCharge": 50}
        for _ in range(10):
            inner = {"nested": inner}

        data = {"depotInfoList": [inner]}

        advanced_rules_validator._validate_ranges(data, "", result)
        # Should handle deep nesting without stack overflow


# =============================================================================
# Tests: Semantic Rules Always Run (Even with Schema Errors)
# =============================================================================


class TestSemanticRulesAlwaysRun:
    """Tests to verify semantic rules run even when schema validation fails."""

    def test_semantic_rules_run_with_skip_range_rules_true(self, advanced_rules_validator):
        """Test that semantic rules run even when skip_range_rules=True."""
        result = MockValidationResult()

        # Data with semantic rule violation (SEM-001: Available status but Charging process)
        data = {
            "depotInfoList": [
                {
                    "depotId": "DEPOT_001",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS_001",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP_001",
                                    "chargingPointStatus": "Available",  # Correct field name
                                    "chargingProcessInfo": {
                                        "processStatus": "Charging"  # Correct nested field
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        # This simulates the case where schema validation had errors
        # so range rules are skipped, but semantic rules should still run
        advanced_rules_validator.validate(
            data, "ProvideChargingInformationRequest", result, skip_range_rules=True
        )

        # Semantic rule SEM-001 should still detect the violation
        assert result.warning_count > 0 or result.error_count > 0, (
            f"Expected SEM-001 warning. Errors: {result.range_errors}, Warnings: {result.warnings}"
        )
        all_messages = [e["message"] for e in result.range_errors + result.warnings]
        assert any("SEM-001" in msg for msg in all_messages), f"Expected SEM-001 in: {all_messages}"

    def test_range_rules_skipped_but_semantic_runs(self, advanced_rules_validator):
        """Test that range rules are skipped but semantic rules still run."""
        # Data with BOTH range violation AND semantic violation
        data = {
            "depotInfoList": [
                {
                    "depotId": "DEPOT_001",
                    "chargingStationInfoList": [
                        {
                            "chargingStationId": "CS_001",
                            "chargingPointInfoList": [
                                {
                                    "chargingPointId": "CP_001",
                                    "chargingPointStatus": "Available",  # Semantic violation
                                    "chargingProcessInfo": {
                                        "processStatus": "Charging"  # SEM-001 violation
                                    },
                                    "stateOfCharge": 150,  # Range violation (>100%)
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        # First, validate without skipping - should find both errors
        result_full = MockValidationResult()
        advanced_rules_validator.validate(
            data, "ProvideChargingInformationRequest", result_full, skip_range_rules=False
        )
        full_messages = [e["message"] for e in result_full.range_errors + result_full.warnings]

        # Should have range error for stateOfCharge > 100
        has_range_error = any(
            "150" in msg or "100" in msg or "stateOfCharge" in msg.lower() for msg in full_messages
        )
        # Should have semantic error for SEM-001
        has_semantic_error = any("SEM-001" in msg for msg in full_messages)

        assert has_range_error, f"Expected range error in: {full_messages}"
        assert has_semantic_error, f"Expected SEM-001 in: {full_messages}"

        # Now, validate with skip_range_rules=True
        result_skip = MockValidationResult()
        advanced_rules_validator.validate(
            data, "ProvideChargingInformationRequest", result_skip, skip_range_rules=True
        )
        skip_messages = [e["message"] for e in result_skip.range_errors + result_skip.warnings]

        # Should STILL have semantic error even though range was skipped
        has_semantic_in_skip = any("SEM-001" in msg for msg in skip_messages)
        assert has_semantic_in_skip, (
            f"Expected SEM-001 even with skip_range_rules=True: {skip_messages}"
        )

    def test_all_semantic_rules_checked(self, advanced_rules_validator):
        """Test that all semantic rules are checked when skip_range_rules=True."""
        # SEM-001: Available status with Charging process
        data_sem001 = {
            "depotInfoList": [
                {
                    "chargingStationInfoList": [
                        {
                            "chargingPointInfoList": [
                                {
                                    "chargingPointStatus": "Available",
                                    "chargingProcessInfo": {"processStatus": "Charging"},
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        result_sem001 = MockValidationResult()
        advanced_rules_validator.validate(
            data_sem001, "ProvideChargingInformationRequest", result_sem001, skip_range_rules=True
        )
        sem001_messages = [
            e["message"] for e in result_sem001.range_errors + result_sem001.warnings
        ]
        assert any("SEM-001" in msg for msg in sem001_messages), (
            f"SEM-001 not found: {sem001_messages}"
        )

    def test_integration_schema_error_does_not_block_semantic(self):
        """Integration test: schema errors don't prevent semantic rule checks."""
        import json
        import tempfile
        from pathlib import Path as PathLib

        from vdv463_validator import VDV463Validator

        # Create a temporary schema directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_schema_dir = PathLib(temp_dir) / "schemas"
            v11_dir = temp_schema_dir / "v1.1"
            v11_dir.mkdir(parents=True)

            # Create a minimal schema that requires depotId
            mock_schema = {
                "type": "object",
                "required": ["depotInfoList"],
                "properties": {
                    "depotInfoList": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["depotId"],
                            "properties": {
                                "depotId": {"type": "string"},
                                "chargingStationInfoList": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["chargingStationId"],
                                        "properties": {
                                            "chargingStationId": {"type": "string"},
                                            "chargingPointInfoList": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "required": ["chargingPointId"],
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    }
                },
            }

            schema_file = v11_dir / "ProvideChargingInformationRequest.json"
            with open(schema_file, "w") as f:
                json.dump(mock_schema, f)

            rules_path = (
                PathLib(__file__).parent.parent / "rules" / "advanced_value_check_rules.yaml"
            )
            validator = VDV463Validator(schema_dir=temp_schema_dir, config_path=rules_path)

            # JSON with schema error (missing required field depotId) AND semantic violation
            data = {
                "depotInfoList": [
                    {
                        # Missing required depotId - causes schema error
                        "chargingStationInfoList": [
                            {
                                "chargingStationId": "CS1",
                                "chargingPointInfoList": [
                                    {
                                        "chargingPointId": "CP1",
                                        "chargingPointStatus": "Available",  # Semantic violation!
                                        "chargingProcessInfo": {"processStatus": "Charging"},
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }

            # Write to temp file and validate
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(data, f)
                temp_data_path = PathLib(f.name)

            try:
                result = validator.validate_file(temp_data_path)

                # Should have schema errors (missing required field depotId)
                assert result.error_count > 0, "Expected schema errors for missing fields"

                # Check if semantic rule was also detected
                all_messages = []
                for issue in result.to_dict().get("issues", []):
                    all_messages.append(issue.get("message", ""))

                # Semantic rules should have run and found SEM-001
                has_sem001 = any("SEM-001" in msg for msg in all_messages)
                assert has_sem001, (
                    f"SEM-001 should be detected even with schema errors. Messages: {all_messages}"
                )
            finally:
                if temp_data_path.exists():
                    temp_data_path.unlink()
