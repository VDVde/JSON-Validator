#!/usr/bin/env python3
"""
VDV463 Validation Rules Engine

Handles value range checks and cross-field validation rules
defined in YAML configuration files.
"""

from __future__ import annotations

import operator
import re
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from vdv463_validator import ValidationResult


class ValidationRuleError(Exception):
    """Exception raised for validation rule configuration errors."""

    pass


class ValueRangeValidator:
    """
    Validates VDV463 messages against configurable rules.

    Supports:
    - Simple range checks (min/max)
    - Cross-field validation rules
    - Conditional rules
    - Temporal consistency checks
    - Aggregate/semantic rules
    """

    # Operators for rule evaluation
    OPERATORS: dict[str, Callable] = {
        "<=": operator.le,
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, config_path: Path | None = None):
        """
        Initialize validator with optional configuration file.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config: dict = {}
        self.range_rules: dict = {}
        self.cross_field_rules: list = []
        self.conditional_rules: list = []
        self.semantic_rules: list = []
        self.warning_thresholds: dict = {}
        self.known_vehicle_types: dict = {}

        if config_path:
            self._load_config(config_path)
        else:
            self._load_defaults()

    def _load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValidationRuleError(f"Invalid YAML configuration: {e}") from e
        except FileNotFoundError as e:
            raise ValidationRuleError(f"Configuration file not found: {config_path}") from e

        self.range_rules = self.config.get("range_rules", {})
        self.cross_field_rules = self.config.get("cross_field_rules", [])
        self.conditional_rules = self.config.get("conditional_rules", [])
        self.semantic_rules = self.config.get("semantic_rules", [])
        self.warning_thresholds = self.config.get("warning_thresholds", {})

        # Build vehicle type lookup
        for vtype in self.config.get("known_vehicle_types", []):
            self.known_vehicle_types[vtype["id"]] = vtype

    def _load_defaults(self) -> None:
        """Load default validation rules."""
        self.range_rules = {
            "maxPower": {"min": 0, "max": 1000},
            "minPower": {"min": 0, "max": 500},
            "currentSoC": {"min": 0, "max": 100},
            "targetSoC": {"min": 0, "max": 100},
            "batteryCapacity": {"min": 0, "max": 1000},
            "requestedEnergy": {"min": 0, "max": 1000},
            "priority": {"min": 1, "max": 10},
        }
        self.cross_field_rules = [
            {
                "id": "SOC-002B",
                "name": "minTargetSoc must not exceed maxTargetSoc",
                "description": "Minimum target SoC cannot exceed maximum target SoC",
                "severity": "ERROR",
                "applies_to": ["ProvideChargingRequestsRequest"],
                "condition": {
                    "fields": [
                        "chargingRequestData.minTargetSoc",
                        "chargingRequestData.maxTargetSoc",
                    ],
                    "rule": "chargingRequestData.minTargetSoc <= chargingRequestData.maxTargetSoc",
                },
                "message": "minTargetSoc ({chargingRequestData.minTargetSoc}%) exceeds maxTargetSoc ({chargingRequestData.maxTargetSoc}%)",
            }
        ]
        self.warning_thresholds = {
            "low_soc_warning": 20,
            "high_power_warning": 350,
        }

    def validate(
        self,
        data: dict,
        message_type: str,
        result: ValidationResult,
        skip_range_rules: bool = False,
    ) -> None:
        """
        Validate data against all configured rules.

        Args:
            data: The message data to validate
            message_type: Type of VDV463 message
            result: ValidationResult to collect errors/warnings
            skip_range_rules: If True, skip range/cross-field rules (useful when schema errors exist)
        """
        if not skip_range_rules:
            # 1. Simple range validation
            self._validate_ranges(data, "", result)

            # 2. Cross-field validation
            self._validate_cross_field_rules(data, message_type, result)

            # 3. Conditional rules
            self._validate_conditional_rules(data, message_type, result)

            # 4. Warning thresholds
            self._check_warning_thresholds(data, "", result)

        # 5. Semantic rules - always run as they check logical consistency
        self._validate_semantic_rules(data, message_type, result)

    def _validate_ranges(self, data: Any, path: str, result: ValidationResult) -> None:
        """Recursively validate value ranges."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key

                # Check if this field has range rules
                if key in self.range_rules:
                    self._check_range(key, value, new_path, result)

                # Recurse into nested structures
                self._validate_ranges(value, new_path, result)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                self._validate_ranges(item, new_path, result)

    def _check_range(self, field: str, value: Any, path: str, result: ValidationResult) -> None:
        """Check a single value against range rules."""
        if not isinstance(value, (int, float)):
            return

        rules = self.range_rules[field]
        min_val = rules.get("min")
        max_val = rules.get("max")

        if min_val is not None and value < min_val:
            result.add_range_error(
                path=path,
                message=rules.get("message", f"{field} value {value} is below minimum {min_val}"),
                value=value,
                constraint={"min": min_val, "max": max_val},
            )

        if max_val is not None and value > max_val:
            result.add_range_error(
                path=path,
                message=rules.get("message", f"{field} value {value} exceeds maximum {max_val}"),
                value=value,
                constraint={"min": min_val, "max": max_val},
            )

    def _validate_cross_field_rules(
        self, data: dict, message_type: str, result: ValidationResult
    ) -> None:
        """Validate cross-field rules."""
        for rule in self.cross_field_rules:
            # Check if rule applies to this message type
            if message_type not in rule.get("applies_to", []):
                continue

            # Handle different data structures
            if message_type == "ProvideChargingInformationRequest":
                # Iterate through depot -> chargingStation -> chargingPoint hierarchy
                for i, depot in enumerate(data.get("depotInfoList", [])):
                    for j, station in enumerate(depot.get("chargingStationInfoList", [])):
                        for k, cp in enumerate(station.get("chargingPointInfoList", [])):
                            path_prefix = f"depotInfoList[{i}].chargingStationInfoList[{j}].chargingPointInfoList[{k}]"
                            self._evaluate_cross_field_rule(rule, cp, result, path_prefix)

            elif message_type == "ProvideChargingRequestsRequest":
                items = data.get("chargingRequestList", [])
                for i, item in enumerate(items):
                    path_prefix = f"chargingRequestList[{i}]"
                    self._evaluate_cross_field_rule(rule, item, result, path_prefix)

    def _evaluate_cross_field_rule(
        self, rule: dict, data: dict, result: ValidationResult, path_prefix: str = ""
    ) -> None:
        """Evaluate a single cross-field rule."""
        rule_id = rule.get("id", "UNKNOWN")
        condition = rule.get("condition", {})
        fields = condition.get("fields", [])

        # Extract field values
        values = {}
        for field in fields:
            value = self._get_nested_value(data, field)
            if value is None:
                return  # Skip if required field is missing
            values[field] = value

        # Evaluate the rule
        rule_expr = condition.get("rule", "")

        try:
            passed = self._evaluate_expression(rule_expr, values)
        except Exception:
            return  # Skip if evaluation fails

        if not passed:
            severity = rule.get("severity", "ERROR")
            message = rule.get("message", f"Rule {rule_id} failed")

            # Format message with actual values
            try:
                message = message.format(**values)
            except KeyError:
                pass

            path = f"{path_prefix}.{rule_id}" if path_prefix else rule_id

            if severity == "ERROR":
                result.add_range_error(
                    path=path,
                    message=f"[{rule_id}] {message}",
                    value=values,
                    constraint={"rule": rule_expr},
                )
            else:
                result.add_warning(path=path, message=f"[{rule_id}] {message}", value=values)

    def _validate_conditional_rules(
        self, data: dict, message_type: str, result: ValidationResult
    ) -> None:
        """Validate conditional rules."""
        for rule in self.conditional_rules:
            if message_type not in rule.get("applies_to", []):
                continue

            if message_type == "ProvideChargingRequestsRequest":
                items = data.get("chargingRequestList", [])
                for i, item in enumerate(items):
                    self._evaluate_conditional_rule(rule, item, result, f"chargingRequestList[{i}]")

    def _evaluate_conditional_rule(
        self, rule: dict, data: dict, result: ValidationResult, path_prefix: str = ""
    ) -> None:
        """Evaluate a single conditional rule."""
        rule_id = rule.get("id", "UNKNOWN")
        when = rule.get("when", {})

        # Check if condition is met
        when_field = when.get("field")
        when_value = self._get_nested_value(data, when_field)

        condition_met = False
        if "equals" in when:
            condition_met = when_value == when["equals"]
        elif "greater_than" in when:
            condition_met = when_value is not None and when_value > when["greater_than"]
        elif "less_than" in when:
            condition_met = when_value is not None and when_value < when["less_than"]

        if not condition_met:
            return

        # Condition is met, check "then" requirements
        then = rule.get("then", {})

        # Check required fields
        for required_field in then.get("required_fields", []):
            value = self._get_nested_value(data, required_field)
            if value is None:
                severity = rule.get("severity", "WARNING")
                message = rule.get("message", f"Required field {required_field} is missing")
                path = f"{path_prefix}.{rule_id}" if path_prefix else rule_id

                if severity == "ERROR":
                    result.add_range_error(
                        path=path,
                        message=f"[{rule_id}] {message}",
                        value=None,
                        constraint={"required_field": required_field},
                    )
                else:
                    result.add_warning(path=path, message=f"[{rule_id}] {message}")

    def _check_warning_thresholds(self, data: Any, path: str, result: ValidationResult) -> None:
        """Check warning thresholds."""
        if not isinstance(data, dict):
            return

        # Low SoC warning
        current_soc = self._get_nested_value(data, "currentSoC")
        if current_soc is not None:
            threshold = self.warning_thresholds.get("low_soc_warning", 20)
            if current_soc < threshold:
                result.add_warning(
                    path=f"{path}.currentSoC" if path else "currentSoC",
                    message=f"Low battery: currentSoC ({current_soc}%) is below {threshold}%",
                    value=current_soc,
                )

        # High power warning
        requested_power = self._get_nested_value(data, "requestedPower")
        if requested_power is not None:
            threshold = self.warning_thresholds.get("high_power_warning", 350)
            if requested_power > threshold:
                result.add_warning(
                    path=f"{path}.requestedPower" if path else "requestedPower",
                    message=f"High power request: {requested_power} kW exceeds typical {threshold} kW",
                    value=requested_power,
                )

        # Recurse for nested structures
        if "chargingRequestList" in data:
            for i, item in enumerate(data["chargingRequestList"]):
                self._check_warning_thresholds(item, f"chargingRequestList[{i}]", result)

        if "depotInfoList" in data:
            for i, depot in enumerate(data["depotInfoList"]):
                for j, station in enumerate(depot.get("chargingStationInfoList", [])):
                    for k, cp in enumerate(station.get("chargingPointInfoList", [])):
                        self._check_warning_thresholds(
                            cp,
                            f"depotInfoList[{i}].chargingStationInfoList[{j}].chargingPointInfoList[{k}]",
                            result,
                        )

    def _validate_semantic_rules(
        self, data: dict, message_type: str, result: ValidationResult
    ) -> None:
        """Validate semantic rules."""
        for rule in self.semantic_rules:
            # Check if rule applies to this message type
            if message_type not in rule.get("applies_to", []):
                continue

            # Handle different data structures
            if message_type == "ProvideChargingInformationRequest":
                # Iterate through depot -> chargingStation -> chargingPoint hierarchy
                for i, depot in enumerate(data.get("depotInfoList", [])):
                    for j, station in enumerate(depot.get("chargingStationInfoList", [])):
                        for k, cp in enumerate(station.get("chargingPointInfoList", [])):
                            path_prefix = f"depotInfoList[{i}].chargingStationInfoList[{j}].chargingPointInfoList[{k}]"
                            self._evaluate_semantic_rule(rule, cp, result, path_prefix)

            elif message_type == "ProvideChargingRequestsRequest":
                items = data.get("chargingRequestList", [])
                for i, item in enumerate(items):
                    path_prefix = f"chargingRequestList[{i}]"
                    self._evaluate_semantic_rule(rule, item, result, path_prefix)

    def _evaluate_semantic_rule(
        self, rule: dict, data: dict, result: ValidationResult, path_prefix: str = ""
    ) -> None:
        """Evaluate a single semantic rule against a chargingPointInfo object."""
        rule_id = rule.get("id", "UNKNOWN")
        condition = rule.get("condition", {})
        fields = condition.get("fields", [])

        # Extract field values - use simple field names (relative to chargingPointInfo)
        values = {}
        all_fields_present = True

        for field in fields:
            # Remove the "chargingPointInfo." prefix if present since we're already at that level
            local_field = field
            if local_field.startswith("chargingPointInfo."):
                local_field = local_field[len("chargingPointInfo.") :]

            value = self._get_nested_value(data, local_field)
            if value is None:
                all_fields_present = False
                break
            # Store with both the original field name and local field name
            values[field] = value
            values[local_field] = value

        if not all_fields_present:
            return  # Skip if required fields are missing

        # Evaluate the rule
        rule_expr = condition.get("rule", "")

        try:
            passed = self._evaluate_semantic_expression(rule_expr, values)
        except Exception:
            return  # Skip if evaluation fails

        if not passed:
            severity = rule.get("severity", "WARNING")
            message = rule.get("message", f"Rule {rule_id} failed")

            # Format message with actual values using regex replacement
            # because Python's format() can't handle dots in keys
            for key, val in values.items():
                placeholder = "{" + key + "}"
                message = message.replace(placeholder, str(val))

            path = f"{path_prefix}.{rule_id}" if path_prefix else rule_id

            if severity == "ERROR":
                result.add_range_error(
                    path=path,
                    message=f"[{rule_id}] {message}",
                    value=values,
                    constraint={"rule": rule_expr},
                )
            elif severity == "WARNING":
                result.add_warning(path=path, message=f"[{rule_id}] {message}", value=values)
            else:  # INFO
                result.add_info(path=path, message=f"[{rule_id}] {message}", value=values)

    def _evaluate_semantic_expression(self, expr: str, values: dict) -> bool:
        """
        Evaluate a semantic rule expression.

        Handles expressions like:
        - "field != 'Value' or otherField not in ['A', 'B']"
        - "field == 'Value'"
        """
        # Replace field references with actual values
        eval_expr = expr

        # Sort by length (descending) to replace longer field names first
        sorted_fields = sorted(values.keys(), key=len, reverse=True)

        for field in sorted_fields:
            value = values[field]
            if isinstance(value, str):
                # Quote string values
                eval_expr = eval_expr.replace(field, f"'{value}'")
            elif isinstance(value, bool):
                eval_expr = eval_expr.replace(field, str(value))
            elif value is not None:
                eval_expr = eval_expr.replace(field, str(value))

        try:
            # Safe evaluation using limited globals
            result = eval(eval_expr, {"__builtins__": {}}, {})  # nosec
            return bool(result)
        except Exception:
            return True  # Default to passing if we can't evaluate

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get a value from nested dict using dot notation."""
        if not path:
            return None

        parts = path.replace("[", ".").replace("]", "").split(".")
        current: Any = data

        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                return None

        return current

    def _evaluate_expression(self, expr: str, values: dict) -> bool:
        """
        Evaluate a simple comparison expression.

        Supports: field1 <= field2, field > value, etc.
        """
        # Simple comparison pattern: "field1 op field2" or "field1 op value"
        pattern = r"(\w+(?:\.\w+)*)\s*(<=|>=|<|>|==|!=)\s*(\w+(?:\.\w+)*|\d+(?:\.\d+)?)"
        match = re.match(pattern, expr.strip())

        if not match:
            # Try multiline/complex expressions - simplified evaluation
            return True

        left_field, op, right_field = match.groups()

        # Get left value
        left_val = values.get(left_field)
        if left_val is None:
            return True  # Skip if field not found

        # Get right value (either from values dict or as literal)
        if right_field in values:
            right_val = values[right_field]
        else:
            try:
                right_val = float(right_field)
            except ValueError:
                return True

        if right_val is None:
            return True

        # Apply operator
        op_func = self.OPERATORS.get(op)
        if op_func:
            return bool(op_func(left_val, right_val))

        return True


# =============================================================================
# Utility Functions
# =============================================================================


def now() -> datetime:
    """Return current datetime (for rule evaluation)."""
    return datetime.now()


def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '2h', '30m', '1d'."""
    match = re.match(r"(\d+)([hdms])", duration_str.lower())
    if not match:
        return timedelta()

    value, unit = int(match.group(1)), match.group(2)

    if unit == "d":
        return timedelta(days=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "s":
        return timedelta(seconds=value)

    return timedelta()


# =============================================================================
# Main (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
        try:
            validator = ValueRangeValidator(config_path)
            print(f"✓ Configuration loaded successfully: {config_path}")
            print(f"  - Range rules: {len(validator.range_rules)}")
            print(f"  - Cross-field rules: {len(validator.cross_field_rules)}")
            print(f"  - Conditional rules: {len(validator.conditional_rules)}")
            print(f"  - Semantic rules: {len(validator.semantic_rules)}")
        except ValidationRuleError as e:
            print(f"✗ Configuration error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python validation_rules.py <config.yaml>")
        print("       Validates the configuration file syntax")
