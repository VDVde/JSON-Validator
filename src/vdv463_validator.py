#!/usr/bin/env python3
"""
VDV463 Message Validator - JSON Schema Validation Tool

A command-line tool for validating VDV463 ProvideChargingInformationRequest
and ProvideChargingRequestsRequest messages against JSON Schema with
configurable value range checks.

Features:
  - Multi-version schema support (VDV463 v1.0, v1.1, v2.0)
  - Three severity levels: ERROR, WARNING, INFO
  - Configurable fail threshold for CI/CD
  - Batch validation with JUnit XML reports

Usage:
    # Interactive (single file, detailed output)
    python vdv463_validator.py message.json

    # CI/CD with specific schema version
    python vdv463_validator.py messages/*.json --schema-version 1.1 --quiet

    # Fail only on errors (ignore warnings)
    python vdv463_validator.py messages/*.json --fail-level ERROR

    # Fail on errors and warnings (ignore info)
    python vdv463_validator.py messages/*.json --fail-level WARNING
"""

import argparse
import glob
import io
import json
import os
import sys
import urllib.request
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

import jsonschema
from jsonschema import Draft4Validator, Draft7Validator, FormatChecker

from validation_rules import ValueRangeValidator

# =============================================================================
# Custom Format Checker with date-time support
# =============================================================================

# Create a format checker with date-time validation
format_checker = FormatChecker()


@format_checker.checks("date-time", raises=ValueError)
def check_datetime(value: object) -> bool:
    """Validate ISO 8601 date-time format."""
    if not isinstance(value, str):
        return True  # Let schema validation handle non-strings
    import re

    # ISO 8601 date-time pattern
    # Accepts: 2024-12-04T10:30:00Z, 2024-12-04T10:30:00+01:00, 2024-12-04T10:30:00.123Z
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
    if not re.match(pattern, value):
        raise ValueError(f"'{value}' is not a valid date-time format")

    # Also verify it's a valid date using datetime
    try:
        # Remove timezone for parsing
        dt_str = value.replace("Z", "+00:00")
        if "+" in dt_str or (dt_str.count("-") > 2):
            # Has timezone
            from datetime import datetime

            # Try parsing with timezone
            if "+" in dt_str:
                dt_part = dt_str.split("+")[0]
            else:
                # Find the last - that's part of timezone
                parts = dt_str.rsplit("-", 1)
                if ":" in parts[-1]:
                    dt_part = parts[0]
                else:
                    dt_part = dt_str
            datetime.fromisoformat(dt_part.replace("T", " "))
        else:
            from datetime import datetime

            datetime.fromisoformat(value.replace("T", " "))
    except (ValueError, TypeError) as e:
        raise ValueError(f"'{value}' is not a valid date-time: {e}") from e

    return True


@format_checker.checks("date", raises=ValueError)
def check_date(value: object) -> bool:
    """Validate ISO 8601 date format."""
    if not isinstance(value, str):
        return True  # Let schema validation handle non-strings
    from datetime import datetime

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"'{value}' is not a valid date format (expected YYYY-MM-DD)") from e
    return True


@format_checker.checks("time", raises=ValueError)
def check_time(value: object) -> bool:
    """Validate ISO 8601 time format."""
    if not isinstance(value, str):
        return True  # Let schema validation handle non-strings
    import re

    pattern = r"^\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
    if not re.match(pattern, value):
        raise ValueError(f"'{value}' is not a valid time format")
    return True


# =============================================================================
# Constants and Enums
# =============================================================================


class ExitCode(IntEnum):
    """Standardized exit codes for CI/CD integration."""

    SUCCESS = 0
    VALIDATION_FAILED = 1
    INPUT_ERROR = 2
    SCHEMA_ERROR = 3
    CONFIG_ERROR = 4


class Severity(IntEnum):
    """
    Validation severity levels.

    Lower value = more severe. Used for threshold comparison.
    """

    ERROR = 1
    WARNING = 2
    INFO = 3

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Parse severity from string."""
        mapping = {
            "ERROR": cls.ERROR,
            "ERR": cls.ERROR,
            "E": cls.ERROR,
            "WARNING": cls.WARNING,
            "WARN": cls.WARNING,
            "W": cls.WARNING,
            "INFO": cls.INFO,
            "I": cls.INFO,
        }
        return mapping.get(value.upper(), cls.ERROR)

    def __str__(self) -> str:
        return self.name


# =============================================================================
# Schema Version Management
# =============================================================================


class SchemaVersion:
    """
    Manages VDV463 schema versions.

    Supported versions:
      - 1.0: Initial VDV463 specification
      - 1.1: Added optional fields, relaxed constraints
      - 2.0: Major revision with new message types
    """

    SUPPORTED_VERSIONS = ["1.0", "1.1", "1.1-dev", "2.0", "auto"]

    # Schema file mapping per version
    VERSION_SCHEMAS = {
        "1.0": {
            "ProvideChargingInformationRequest": "v1.0/ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest": "v1.0/ProvideChargingRequestsRequest.json",
        },
        "1.1": {
            "ProvideChargingInformationRequest": "v1.1/ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest": "v1.1/ProvideChargingRequestsRequest.json",
        },
        "1.1-dev": {
            "ProvideChargingInformationRequest": "v1.1-dev/ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest": "v1.1-dev/ProvideChargingRequestsRequest.json",
        },
        "2.0": {
            "ProvideChargingInformationRequest": "v2.0/ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest": "v2.0/ProvideChargingRequestsRequest.json",
            "ProvideChargingStatusRequest": "v2.0/ProvideChargingStatusRequest.json",
            "ErrorResponse": "v2.0/ErrorResponse.json",
            "BootNotificationRequest": "v2.0/BootNotificationRequest.json",
            "HeartbeatRequest": "v2.0/HeartbeatRequest.json",
            "StatusNotificationRequest": "v2.0/StatusNotificationRequest.json",
        },
    }

    # JSON Schema draft per VDV463 version
    VERSION_DRAFT = {
        "1.0": Draft4Validator,
        "1.1": Draft4Validator,
        "1.1-dev": Draft4Validator,
        "2.0": Draft7Validator,
    }

    # Official GitHub Repository mapping
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/VDVde/VDV463"
    VERSION_BRANCHES = {
        "1.0": "1.0.0",
        "1.1": "1.1.0",
        "1.1-dev": "v1.1-dev",
        "2.0": "main",
    }

    # Flat schema layout (legacy support)
    FLAT_SCHEMAS = {
        "ProvideChargingInformationRequest": "ProvideChargingInformationRequest.json",
        "ProvideChargingRequestsRequest": "ProvideChargingRequestsRequest.json",
    }

    def __init__(self, schema_dir: Path, version: str = "auto"):
        """
        Initialize schema version manager.

        Args:
            schema_dir: Base directory containing schema files
            version: Schema version ("1.0", "1.1", "2.0", or "auto")
        """
        self.schema_dir = schema_dir
        self.requested_version = version
        self.detected_version: str | None = None
        self.layout: str = "unknown"  # "versioned" or "flat"

        self._detect_layout()

    def _detect_layout(self) -> None:
        """Detect schema directory layout (versioned vs flat)."""
        # Check for versioned layout (v1.0/, v1.1/, v2.0/ subdirectories)
        for version in ["1.0", "1.1", "2.0"]:
            version_dir = self.schema_dir / f"v{version}"
            if version_dir.is_dir():
                self.layout = "versioned"
                return

        # Check for flat layout (schemas directly in directory)
        for schema_file in self.FLAT_SCHEMAS.values():
            if (self.schema_dir / schema_file).exists():
                self.layout = "flat"
                return

    def get_schema_path(self, message_type: str, version: str | None = None) -> Path:
        """
        Get path to schema file for given message type and version.
        Downloads from GitHub if missing locally.

        Args:
            message_type: VDV463 message type
            version: Schema version (uses requested_version if None)

        Returns:
            Path to schema file

        Raises:
            FileNotFoundError: If schema file not found and download fails
        """
        version = version or self.requested_version

        # Determine relative path in the schemas directory
        if self.layout == "versioned" and version != "auto":
            schemas = self.VERSION_SCHEMAS.get(version, {})
            if message_type not in schemas:
                raise FileNotFoundError(
                    f"Message type '{message_type}' not supported in version {version}"
                )
            rel_path = schemas[message_type]
            path = self.schema_dir / rel_path
        else:
            # Flat layout or auto-detect
            if message_type not in self.FLAT_SCHEMAS:
                raise FileNotFoundError(f"Unknown message type: {message_type}")
            rel_path = self.FLAT_SCHEMAS[message_type]
            path = self.schema_dir / rel_path

        # Dynamic loading: If file is missing, try to download from GitHub
        if not path.exists():
            print(f"Schema missing: {path}. Attempting download from VDV GitHub...")
            if self._download_schema(message_type, version, path):
                print(f"Successfully downloaded schema to {path}")
            else:
                raise FileNotFoundError(
                    f"Schema file not found and could not be downloaded: {path}\n"
                    f"Please check your internet connection or ensure the schema exists at the source."
                )

        return path

    def _download_schema(self, message_type: str, version: str, dest_path: Path) -> bool:
        """Download schema from official VDV GitHub repository."""
        if version == "auto":
            version = "1.1"  # Default for download

        branch = self.VERSION_BRANCHES.get(version)
        if not branch:
            return False

        # Construct raw URL
        filename = dest_path.name
        # v1.0.0 uses "v1.0/" folder, others use "schema/"
        folder = "v1.0" if branch == "1.0.0" else "schema"
        url = f"{self.GITHUB_RAW_BASE}/{branch}/{folder}/{filename}"

        try:
            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Fetch schema
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    content = response.read().decode("utf-8")
                    # Validate that it's actually JSON
                    json.loads(content)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return True
        except Exception as e:
            print(f"Error downloading schema from {url}: {e}")
            return False

        return False

    def get_validator_class(self, version: str | None = None):
        """Get appropriate JSON Schema validator class for version."""
        version = version or self.requested_version
        if version == "auto":
            version = "1.1"  # Default to 1.1
        return self.VERSION_DRAFT.get(version, Draft4Validator)

    def get_available_versions(self) -> list[str]:
        """Get list of available schema versions in schema_dir."""
        versions = []

        if self.layout == "versioned":
            for version in ["1.0", "1.1", "1.1-dev", "2.0"]:
                version_dir = self.schema_dir / f"v{version}"
                if version_dir.is_dir():
                    versions.append(version)
        elif self.layout == "flat":
            versions.append("flat")

        return versions

    def detect_message_version(self, data: dict) -> str | None:
        """
        Try to detect schema version from message content.

        Args:
            data: Message data

        Returns:
            Detected version or None
        """
        # Check for version field (if present in message)
        if "schemaVersion" in data:
            version = data["schemaVersion"]
            return str(version) if version is not None else None

        # Check for v2.0-specific fields
        if "chargingStatusList" in data:
            return "2.0"

        # Check for v1.1-specific optional fields
        if "depotInfoList" in data:
            depot = data["depotInfoList"][0] if data["depotInfoList"] else {}
            if "gridConnectionInfo" in depot:  # v1.1+ field
                return "1.1"

        # Default to 1.0
        return "1.0"


# =============================================================================
# Validation Result
# =============================================================================


class ValidationIssue:
    """Single validation issue (error, warning, or info)."""

    def __init__(
        self,
        path: str,
        message: str,
        severity: Severity,
        value: Any = None,
        rule_id: str | None = None,
        constraint: dict | None = None,
        line_number: int | None = None,
    ):
        self.path = path
        self.message = message
        self.severity = severity
        self.value = value
        self.rule_id = rule_id
        self.constraint = constraint or {}
        self.line_number = line_number

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "message": self.message,
            "severity": str(self.severity),
            "value": repr(self.value) if self.value is not None else None,
            "rule_id": self.rule_id,
            "line_number": self.line_number,
        }


class ValidationResult:
    """Container for validation results of a single file."""

    def __init__(self, input_file: str):
        self.input_file = input_file
        self.timestamp = datetime.now().isoformat()
        self.message_type: str | None = None
        self.schema_version: str | None = None
        self.issues: list[ValidationIssue] = []
        self.parse_error: str | None = None
        self.duration_ms: float = 0
        self.content: str | None = None  # Store content for line number calculation

    def add_issue(
        self,
        path: str,
        message: str,
        severity: Severity,
        value: Any = None,
        rule_id: str | None = None,
        constraint: dict | None = None,
        line_number: int | None = None,
    ) -> None:
        """Add a validation issue."""
        self.issues.append(
            ValidationIssue(
                path=path,
                message=message,
                severity=severity,
                value=value,
                rule_id=rule_id,
                constraint=constraint,
                line_number=line_number,
            )
        )

    # Convenience methods for backward compatibility
    def add_schema_error(self, path: str, message: str, value: Any = None) -> None:
        """Add a JSON Schema validation error."""
        self.add_issue(path, message, Severity.ERROR, value, rule_id="SCHEMA")

    def add_range_error(self, path: str, message: str, value: Any, constraint: dict) -> None:
        """Add a value range validation error."""
        self.add_issue(path, message, Severity.ERROR, value, rule_id="RULE", constraint=constraint)

    def add_warning(self, path: str, message: str, value: Any = None) -> None:
        """Add a validation warning."""
        self.add_issue(path, message, Severity.WARNING, value, rule_id="RULE")

    def add_info(self, path: str, message: str, value: Any = None) -> None:
        """Add an informational message."""
        self.add_issue(path, message, Severity.INFO, value)

    def get_issues_by_severity(self, severity: Severity) -> list[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [i for i in self.issues if i.severity == severity]

    @property
    def errors(self) -> list[ValidationIssue]:
        return self.get_issues_by_severity(Severity.ERROR)

    @property
    def warnings(self) -> list[ValidationIssue]:
        return self.get_issues_by_severity(Severity.WARNING)

    @property
    def infos(self) -> list[ValidationIssue]:
        return self.get_issues_by_severity(Severity.INFO)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def info_count(self) -> int:
        return len(self.infos)

    def has_issues_at_or_above(self, threshold: Severity) -> bool:
        """Check if there are any issues at or above the given severity threshold."""
        return any(issue.severity.value <= threshold.value for issue in self.issues)

    @property
    def valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return self.error_count == 0

    def to_dict(self) -> dict:
        """Convert result to dictionary for JSON output."""
        return {
            "input_file": self.input_file,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "schema_version": self.schema_version,
            "valid": self.valid,
            "duration_ms": round(self.duration_ms, 2),
            "summary": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "infos": self.info_count,
            },
            "issues": [issue.to_dict() for issue in self.issues],
        }


# =============================================================================
# Batch Validation Result
# =============================================================================


class BatchValidationResult:
    """Container for validation results of multiple files."""

    def __init__(self, fail_level: Severity = Severity.ERROR):
        self.results: list[ValidationResult] = []
        self.timestamp = datetime.now().isoformat()
        self.total_duration_ms: float = 0
        self.fail_level = fail_level

    def add(self, result: ValidationResult) -> None:
        """Add a single file's validation result."""
        self.results.append(result)

    @property
    def total_files(self) -> int:
        return len(self.results)

    @property
    def total_errors(self) -> int:
        return sum(r.error_count for r in self.results)

    @property
    def total_warnings(self) -> int:
        return sum(r.warning_count for r in self.results)

    @property
    def total_infos(self) -> int:
        return sum(r.info_count for r in self.results)

    def get_failed_files(self, threshold: Severity | None = None) -> list[ValidationResult]:
        """Get files that failed at the given threshold."""
        threshold = threshold or self.fail_level
        return [r for r in self.results if r.has_issues_at_or_above(threshold)]

    @property
    def passed_files(self) -> int:
        return self.total_files - len(self.get_failed_files())

    @property
    def failed_files(self) -> int:
        return len(self.get_failed_files())

    @property
    def all_passed(self) -> bool:
        """Check if all files passed at the configured fail_level."""
        return len(self.get_failed_files()) == 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "validation_report": {
                "timestamp": self.timestamp,
                "total_duration_ms": round(self.total_duration_ms, 2),
                "fail_level": str(self.fail_level),
                "summary": {
                    "total_files": self.total_files,
                    "passed": self.passed_files,
                    "failed": self.failed_files,
                    "total_errors": self.total_errors,
                    "total_warnings": self.total_warnings,
                    "total_infos": self.total_infos,
                },
                "results": [r.to_dict() for r in self.results],
            }
        }


# =============================================================================
# Main Validator
# =============================================================================


class VDV463Validator:
    """Main validator for VDV463 messages."""

    def __init__(
        self, schema_dir: Path, config_path: Path | None = None, schema_version: str = "auto"
    ):
        """
        Initialize validator.

        Args:
            schema_dir: Directory containing JSON schema files
            config_path: Path to validation rules configuration (YAML)
            schema_version: Schema version to use ("1.0", "1.1", "2.0", "auto")

        Raises:
            FileNotFoundError: If schema_dir does not exist
        """
        if not schema_dir.exists():
            raise FileNotFoundError(f"Schema directory not found: {schema_dir}")

        self.schema_manager = SchemaVersion(schema_dir, schema_version)
        self.schemas: dict[str, dict] = {}
        self.validators: dict[str, jsonschema.Draft4Validator] = {}
        self.range_validator = ValueRangeValidator(config_path)
        self.schema_version = schema_version

    def _get_or_load_schema(self, message_type: str, version: str | None = None):
        """Load schema on demand."""
        cache_key = f"{message_type}:{version or self.schema_version}"

        if cache_key not in self.validators:
            schema_path = self.schema_manager.get_schema_path(message_type, version)

            with open(schema_path, encoding="utf-8") as f:
                schema = json.load(f)

            validator_class = self.schema_manager.get_validator_class(version)
            self.schemas[cache_key] = schema
            # Use our custom format_checker with date-time support
            self.validators[cache_key] = validator_class(schema, format_checker=format_checker)

        return self.validators[cache_key]

    def detect_message_type(self, data: dict) -> str | None:
        """Detect message type based on content structure."""
        if "depotInfoList" in data:
            return "ProvideChargingInformationRequest"
        elif "chargingRequestList" in data:
            return "ProvideChargingRequestsRequest"
        elif "chargingStatusList" in data:  # v2.0
            return "ProvideChargingStatusRequest"
        return None

    def _find_line_number_for_path(self, path: str, content: str) -> int | None:
        """
        Find the line number in JSON content for a given JSON path.

        This uses a heuristic approach that works well for most cases but may not
        be 100% accurate for deeply nested arrays with multiple occurrences of the
        same field name in different contexts.

        Args:
            path: JSON path like 'depotInfoList[0].chargingStationInfoList[0].field'
            content: The original JSON content as string

        Returns:
            Line number (1-indexed) or None if not found
        """
        if path == "$" or not path:
            return None

        import re

        lines = content.split("\n")

        # Parse path into components
        components = re.split(r"\.(?![^\[]*\])", path)

        if not components:
            return None

        # Get the last meaningful key (without array index)
        last_component = components[-1]
        # Remove array index if present
        last_key = re.sub(r"\[\d+\]$", "", last_component)

        if not last_key:
            return None

        # Search for the key in the JSON
        search_pattern = f'"{last_key}"'

        # Extract array indices from path for occurrence counting
        indices = re.findall(r"\[(\d+)\]", path)
        # Use a better heuristic: count from the last index (most specific)
        target_occurrence = int(indices[-1]) + 1 if indices else 1

        occurrence_count = 0
        first_occurrence_line = None
        for line_num, line in enumerate(lines, 1):
            if search_pattern in line:
                occurrence_count += 1
                if first_occurrence_line is None:
                    first_occurrence_line = line_num
                if occurrence_count == target_occurrence:
                    return line_num

        # Fallback to first occurrence if target not found
        return first_occurrence_line

    def validate_content(
        self, content: str, filename: str = "live_validation", schema_only: bool = False
    ) -> ValidationResult:
        """Validate a single VDV463 message from a string."""
        import time

        start_time = time.perf_counter()

        result = ValidationResult(filename)
        # Store content for line number calculation
        result.content = content

        # Load input file
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            result.add_schema_error("$", f"Invalid JSON: {e.msg} at line {e.lineno}")
            result.parse_error = str(e)
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            return result

        # Detect message type
        msg_type = self.detect_message_type(data)
        if msg_type is None:
            result.add_schema_error(
                "$",
                "Cannot detect message type. Expected 'depotInfoList', "
                "'chargingRequestList', or 'chargingStatusList'",
            )
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            return result

        result.message_type = msg_type

        # Detect/use schema version
        if self.schema_version == "auto":
            detected_version = self.schema_manager.detect_message_version(data)
            result.schema_version = detected_version
        else:
            result.schema_version = self.schema_version

        # Schema validation
        try:
            validator = self._get_or_load_schema(msg_type, result.schema_version)
        except FileNotFoundError as e:
            result.add_schema_error("$", str(e))
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            return result
        except Exception as e:
            # Catch any other exception during schema loading
            result.add_schema_error("$", f"Error loading schema: {e}")
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            return result

        # Run schema validation
        try:
            for error in validator.iter_errors(data):
                path = self._format_path(error.absolute_path)
                line_number = self._find_line_number_for_path(path, content)
                result.add_issue(
                    path,
                    error.message,
                    Severity.ERROR,
                    error.instance,
                    rule_id="SCHEMA",
                    line_number=line_number,
                )
        except Exception as e:
            # Catch any exception during schema validation
            result.add_schema_error("$", f"Error during schema validation: {e}")

        # Value range validation - only run if schema_only is False
        if not schema_only:
            try:
                self.range_validator.validate(data, msg_type, result, skip_range_rules=False)
            except Exception as e:
                # Catch any exception during rule validation
                result.add_issue(
                    "$", f"Error during rule validation: {e}", Severity.ERROR, rule_id="RULE"
                )

        # Add info about detected version
        if self.schema_version == "auto" and result.schema_version:
            result.add_info(
                "$", f"Auto-detected schema version: {result.schema_version}", result.schema_version
            )

        result.duration_ms = (time.perf_counter() - start_time) * 1000
        return result

    def validate_file(self, input_path: Path) -> ValidationResult:
        """Validate a single VDV463 message file."""
        try:
            content = input_path.read_text(encoding="utf-8")
            return self.validate_content(content, str(input_path))
        except FileNotFoundError:
            result = ValidationResult(str(input_path))
            result.add_schema_error("$", f"Input file not found: {input_path}")
            return result
        except PermissionError:
            result = ValidationResult(str(input_path))
            result.add_schema_error("$", f"Permission denied: {input_path}")
            return result
        except Exception as e:
            result = ValidationResult(str(input_path))
            result.add_schema_error("$", f"An unexpected error occurred: {e}")
            return result

    def validate_batch(
        self, input_paths: list[Path], fail_level: Severity = Severity.ERROR
    ) -> BatchValidationResult:
        """Validate multiple VDV463 message files."""
        import time

        start_time = time.perf_counter()

        batch_result = BatchValidationResult(fail_level=fail_level)

        for input_path in input_paths:
            result = self.validate_file(input_path)
            batch_result.add(result)

        batch_result.total_duration_ms = (time.perf_counter() - start_time) * 1000
        return batch_result

    @staticmethod
    def _format_path(path) -> str:
        """Format JSON path for error reporting."""
        parts = []
        for p in path:
            if isinstance(p, int):
                parts.append(f"[{p}]")
            else:
                parts.append(f".{p}" if parts else p)
        return "".join(parts) if parts else "$"


# =============================================================================
# Output Writers
# =============================================================================


class OutputWriter:
    """Handles output formatting and writing."""

    SEVERITY_ICONS = {
        Severity.ERROR: "✗",
        Severity.WARNING: "⚠",
        Severity.INFO: "ℹ",
    }

    @staticmethod
    def write_json(batch_result: BatchValidationResult, output_path: Path) -> None:
        """Write JSON report."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(batch_result.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def write_junit_xml(batch_result: BatchValidationResult, output_path: Path) -> None:
        """Write JUnit XML report for CI/CD integration."""
        testsuites = Element("testsuites")
        testsuites.set("name", "VDV463 Validation")
        testsuites.set("tests", str(batch_result.total_files))
        testsuites.set("failures", str(batch_result.failed_files))
        testsuites.set("time", str(batch_result.total_duration_ms / 1000))

        testsuite = SubElement(testsuites, "testsuite")
        testsuite.set("name", "VDV463 Message Validation")
        testsuite.set("tests", str(batch_result.total_files))
        testsuite.set("failures", str(batch_result.failed_files))
        testsuite.set("time", str(batch_result.total_duration_ms / 1000))
        testsuite.set("timestamp", batch_result.timestamp)

        for result in batch_result.results:
            testcase = SubElement(testsuite, "testcase")
            testcase.set("name", Path(result.input_file).name)
            testcase.set(
                "classname",
                f"vdv463.{result.schema_version or 'unknown'}.{result.message_type or 'unknown'}",
            )
            testcase.set("time", str(result.duration_ms / 1000))

            # Check if this file failed at the configured threshold
            if result.has_issues_at_or_above(batch_result.fail_level):
                failure = SubElement(testcase, "failure")

                # Count issues at or above threshold
                relevant_issues = [
                    i for i in result.issues if i.severity.value <= batch_result.fail_level.value
                ]

                failure.set(
                    "message",
                    f"{len(relevant_issues)} issue(s) at {batch_result.fail_level} level or above",
                )
                failure.set("type", "ValidationError")

                error_details = []
                for issue in relevant_issues[:50]:
                    icon = OutputWriter.SEVERITY_ICONS.get(issue.severity, "?")
                    error_details.append(
                        f"{icon} [{issue.severity}] [{issue.path}] {issue.message}"
                    )

                if len(relevant_issues) > 50:
                    error_details.append(f"... and {len(relevant_issues) - 50} more issues")

                failure.text = "\n".join(error_details)

            # Add all issues as system-out for reference
            if result.issues:
                system_out = SubElement(testcase, "system-out")
                all_issues = []
                for issue in result.issues[:100]:
                    all_issues.append(f"[{issue.severity}] [{issue.path}] {issue.message}")
                system_out.text = "\n".join(all_issues)

        xml_declaration = b'<?xml version="1.0" encoding="UTF-8"?>\n'
        with open(output_path, "wb") as f:
            f.write(xml_declaration)
            f.write(tostring(testsuites, encoding="utf-8"))

    @staticmethod
    def print_summary_interactive(batch_result: BatchValidationResult) -> None:
        """Print detailed interactive summary for CLI usage."""
        print("\n" + "=" * 70)
        print("VDV463 VALIDATION SUMMARY")
        print("=" * 70)

        if batch_result.total_files == 1:
            result = batch_result.results[0]
            print(f"Input File:      {result.input_file}")
            print(f"Message Type:    {result.message_type or 'Unknown'}")
            print(f"Schema Version:  {result.schema_version or 'Unknown'}")
            print(f"Timestamp:       {result.timestamp}")
            print(f"Duration:        {result.duration_ms:.2f} ms")
            print(f"Fail Level:      {batch_result.fail_level}")
            print("-" * 70)

            if result.has_issues_at_or_above(batch_result.fail_level):
                print(f"✗ FAILED (issues at {batch_result.fail_level} level or above)")
            elif result.error_count == 0 and result.warning_count == 0:
                print("✓ PASSED - No issues found")
            else:
                print("✓ PASSED - Issues below fail threshold")

            print(f"  Errors:   {result.error_count}")
            print(f"  Warnings: {result.warning_count}")
            print(f"  Infos:    {result.info_count}")

            for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
                issues = result.get_issues_by_severity(severity)
                if issues:
                    icon = OutputWriter.SEVERITY_ICONS.get(severity, "?")
                    print(f"\n{severity.name}S:")
                    for issue in issues[:10]:
                        print(f"  {icon} [{issue.path}] {issue.message}")
                    if len(issues) > 10:
                        print(f"  ... and {len(issues) - 10} more")

        else:
            print(f"Files Validated: {batch_result.total_files}")
            print(f"Fail Level:      {batch_result.fail_level}")
            print(f"Total Duration:  {batch_result.total_duration_ms:.2f} ms")
            print("-" * 70)
            print(f"{'Status':<10} {'Err':<5} {'Warn':<5} {'Info':<5} {'Version':<8} {'File'}")
            print("-" * 70)

            for result in batch_result.results:
                failed = result.has_issues_at_or_above(batch_result.fail_level)
                status = "✗ FAIL" if failed else "✓ PASS"
                filename = Path(result.input_file).name
                version = result.schema_version or "?"
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                print(
                    f"{status:<10} {result.error_count:<5} {result.warning_count:<5} "
                    f"{result.info_count:<5} {version:<8} {filename}"
                )

            print("-" * 70)
            print(f"Total: {batch_result.passed_files} passed, {batch_result.failed_files} failed")
            print(
                f"Issues: {batch_result.total_errors} errors, "
                f"{batch_result.total_warnings} warnings, "
                f"{batch_result.total_infos} infos"
            )

        print("=" * 70 + "\n")

    @staticmethod
    def print_summary_ci(batch_result: BatchValidationResult) -> None:
        """Print minimal CI-friendly summary."""
        if batch_result.all_passed:
            print(
                f"[PASS] VDV463 Validation: {batch_result.total_files} file(s) passed "
                f"(fail-level: {batch_result.fail_level})"
            )
        else:
            print(
                f"[FAIL] VDV463 Validation: {batch_result.failed_files}/{batch_result.total_files} "
                f"file(s) failed (fail-level: {batch_result.fail_level})"
            )
            for result in batch_result.get_failed_files():
                print(
                    f"  - {Path(result.input_file).name}: "
                    f"{result.error_count}E/{result.warning_count}W/{result.info_count}I"
                )


# =============================================================================
# Environment Configuration
# =============================================================================


def get_env_config() -> dict:
    """Read configuration from environment variables."""
    return {
        "schema_dir": os.environ.get("VDV463_SCHEMA_DIR"),
        "config": os.environ.get("VDV463_CONFIG"),
        "schema_version": os.environ.get("VDV463_SCHEMA_VERSION", "auto"),
        "fail_level": os.environ.get("VDV463_FAIL_LEVEL", "ERROR"),
        "quiet": os.environ.get("VDV463_QUIET", "").lower() in ("true", "1", "yes"),
        "junit_xml": os.environ.get("VDV463_JUNIT_XML"),
        "output": os.environ.get("VDV463_OUTPUT"),
    }


def merge_config(args: argparse.Namespace, env_config: dict) -> argparse.Namespace:
    """Merge CLI arguments with environment configuration."""
    if args.schema_dir == Path(__file__).parent.parent / "schemas" and env_config["schema_dir"]:
        args.schema_dir = Path(env_config["schema_dir"])

    if args.config is None and env_config["config"]:
        args.config = Path(env_config["config"])

    if args.schema_version == "auto" and env_config["schema_version"] != "auto":
        args.schema_version = env_config["schema_version"]

    if args.fail_level == "ERROR" and env_config["fail_level"]:
        args.fail_level = env_config["fail_level"]

    if not args.quiet and env_config["quiet"]:
        args.quiet = True

    if args.junit_xml is None and env_config["junit_xml"]:
        args.junit_xml = Path(env_config["junit_xml"])

    if args.output is None and env_config["output"]:
        args.output = Path(env_config["output"])

    return args


# =============================================================================
# Filename Generation
# =============================================================================


def generate_output_filename(input_paths: list[Path]) -> Path:
    """Generate output filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if len(input_paths) == 1:
        stem = input_paths[0].stem
        return input_paths[0].parent / f"{stem}_validation_{timestamp}.json"
    else:
        return Path.cwd() / f"vdv463_validation_{timestamp}.json"


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """Main CLI entry point."""
    # Force UTF-8 encoding for stdout and stderr to handle emojis and special characters
    if sys.platform == "win32":
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except (AttributeError, io.UnsupportedOperation):
            pass  # Fallback if stdout/stderr are already wrapped or redirected

    parser = argparse.ArgumentParser(
        description="Validate VDV463 messages against JSON Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive usage:
    %(prog)s message.json
    %(prog)s message.json --schema-version 1.1

  CI/CD pipeline:
    %(prog)s messages/*.json --quiet --junit-xml report.xml
    %(prog)s messages/*.json --fail-level WARNING --junit-xml report.xml

  Fail levels:
    --fail-level ERROR    Only errors cause failure (default)
    --fail-level WARNING  Errors and warnings cause failure
    --fail-level INFO     Any issue causes failure

  Environment variables:
    VDV463_SCHEMA_DIR      Schema directory path
    VDV463_SCHEMA_VERSION  Schema version (1.0, 1.1, 2.0, auto)
    VDV463_CONFIG          Validation rules config path
    VDV463_FAIL_LEVEL      Fail level (ERROR, WARNING, INFO)
    VDV463_QUIET           Set to 'true' for minimal output
    VDV463_JUNIT_XML       JUnit XML output path
    VDV463_OUTPUT          JSON output path

Exit codes:
    0 - All validations passed
    1 - Validation issues at or above fail level
    2 - Input error (file not found)
    3 - Schema loading error
    4 - Configuration error
        """,
    )

    parser.add_argument(
        "input_files", type=Path, nargs="*", help="VDV463 message JSON file(s) to validate"
    )
    parser.add_argument(
        "--config", "-c", type=Path, default=None, help="Validation rules configuration file (YAML)"
    )
    parser.add_argument(
        "--schema-dir",
        "-s",
        type=Path,
        default=Path(__file__).parent.parent / "schemas",
        help="Directory containing JSON schema files (default: ./schemas)",
    )
    parser.add_argument(
        "--schema-version",
        "-V",
        choices=SchemaVersion.SUPPORTED_VERSIONS,
        default="auto",
        help="VDV463 schema version (default: auto-detect)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="JSON report output path (default: auto-generated)",
    )
    parser.add_argument(
        "--junit-xml", "-j", type=Path, default=None, help="JUnit XML output for CI/CD integration"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output (CI-friendly)")
    parser.add_argument(
        "--fail-level",
        "-L",
        choices=["ERROR", "ERR", "WARNING", "WARN", "INFO"],
        default="ERROR",
        help="Minimum severity level that causes failure (default: ERROR)",
    )
    parser.add_argument("--no-output", action="store_true", help="Don't write JSON output file")
    parser.add_argument(
        "--list-versions", action="store_true", help="List available schema versions and exit"
    )

    args = parser.parse_args()

    # Merge config with environment
    args = merge_config(args, get_env_config())

    # Internal glob expansion for input files (needed for some shells/OS)
    expanded_files = []
    for f_path in args.input_files:
        path_str = str(f_path)
        if "*" in path_str or "?" in path_str:
            glob_matches = glob.glob(path_str, recursive=True)
            if glob_matches:
                expanded_files.extend([Path(m) for m in glob_matches])
            # If no matches for a glob pattern, we just skip it
        else:
            expanded_files.append(f_path)
    args.input_files = expanded_files

    # Parse fail level
    fail_level = Severity.from_string(args.fail_level)

    # List versions mode
    if args.list_versions:
        if args.schema_dir.exists():
            manager = SchemaVersion(args.schema_dir)
            versions = manager.get_available_versions()
            print(f"Schema directory: {args.schema_dir}")
            print(f"Layout: {manager.layout}")
            print(f"Available versions: {', '.join(versions) if versions else 'none found'}")
        else:
            print(f"Schema directory not found: {args.schema_dir}")
        return ExitCode.SUCCESS

    # Check if input files were provided
    if not args.input_files:
        if not args.quiet:
            print("No input files provided. Nothing to validate.")

        # Still write empty reports if requested to satisfy CI expectations
        if args.junit_xml:
            empty_batch = BatchValidationResult(fail_level=fail_level)
            OutputWriter.write_junit_xml(empty_batch, args.junit_xml)
            if not args.quiet:
                print(f"Empty JUnit XML written to: {args.junit_xml}")

        return ExitCode.SUCCESS

    # Validate inputs
    missing_files = [f for f in args.input_files if not f.exists()]
    if missing_files:
        for f in missing_files:
            print(f"Error: Input file not found: {f}", file=sys.stderr)
        return ExitCode.INPUT_ERROR

    if not args.schema_dir.exists():
        print(f"Error: Schema directory not found: {args.schema_dir}", file=sys.stderr)
        return ExitCode.SCHEMA_ERROR

    if args.config and not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        return ExitCode.CONFIG_ERROR

    # Initialize validator
    try:
        validator = VDV463Validator(args.schema_dir, args.config, args.schema_version)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return ExitCode.SCHEMA_ERROR
    except Exception as e:
        print(f"Error initializing validator: {e}", file=sys.stderr)
        return ExitCode.CONFIG_ERROR

    # Run validation
    try:
        batch_result = validator.validate_batch(args.input_files, fail_level)
    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        return ExitCode.INPUT_ERROR

    # Write outputs
    if not args.no_output:
        output_path = args.output or generate_output_filename(args.input_files)
        OutputWriter.write_json(batch_result, output_path)
        if not args.quiet:
            print(f"JSON report written to: {output_path}")

    if args.junit_xml:
        OutputWriter.write_junit_xml(batch_result, args.junit_xml)
        if not args.quiet:
            print(f"JUnit XML written to: {args.junit_xml}")

    # Print summary
    if args.quiet:
        OutputWriter.print_summary_ci(batch_result)
    else:
        OutputWriter.print_summary_interactive(batch_result)

    # Determine exit code
    if not batch_result.all_passed:
        return ExitCode.VALIDATION_FAILED

    return ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
