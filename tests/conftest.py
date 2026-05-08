"""
Pytest configuration and fixtures for VDV463 Validator tests.
"""

import json
from pathlib import Path

import pytest

# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def schema_dir(project_root) -> Path:
    """Return the schemas directory."""
    return project_root / "schemas"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def rules_dir() -> Path:
    """Return the test rules directory."""
    return Path(__file__).parent / "rules"


# =============================================================================
# Schema Version Fixtures
# =============================================================================


@pytest.fixture(params=["1.0", "1.1", "2.0"])
def schema_version(request) -> str:
    """Parametrized fixture for all schema versions."""
    return request.param


@pytest.fixture
def valid_fixtures_for_version(fixtures_dir, schema_version) -> list[Path]:
    """Return all valid test fixtures for a schema version."""
    version_dir = fixtures_dir / f"v{schema_version}" / "valid"
    if version_dir.exists():
        return list(version_dir.glob("*.json"))
    return []


@pytest.fixture
def invalid_fixtures_for_version(fixtures_dir, schema_version) -> list[Path]:
    """Return all invalid test fixtures for a schema version."""
    version_dir = fixtures_dir / f"v{schema_version}" / "invalid"
    if version_dir.exists():
        return list(version_dir.glob("*.json"))
    return []


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_charging_request() -> dict:
    """Return a minimal valid ProvideChargingRequestsRequest."""
    return {
        "timestamp": "2025-01-15T10:30:00Z",
        "senderId": "DEPOT_001",
        "receiverId": "CMS_001",
        "chargingRequestList": [
            {
                "requestId": "REQ-001",
                "vehicleId": "BUS-001",
                "vehicleType": "eCitaro",
                "batteryCapacity": 292,
                "currentSoC": 30,
                "targetSoC": 90,
                "requestedEnergy": 175,
                "requestedPower": 150,
                "priority": 3,
                "plannedArrival": "2025-01-15T18:00:00Z",
                "plannedDeparture": "2025-01-16T05:00:00Z",
                "chargingPointId": "CP-001",
                "connectorType": "CCS2",
            }
        ],
    }


@pytest.fixture
def sample_charging_info() -> dict:
    """Return a minimal valid ProvideChargingInformationRequest."""
    return {
        "timestamp": "2025-01-15T10:30:00Z",
        "senderId": "CMS_001",
        "receiverId": "DEPOT_001",
        "depotInfoList": [
            {
                "depotId": "DEPOT_001",
                "depotName": "Main Depot",
                "chargingPointList": [
                    {
                        "chargingPointId": "CP-001",
                        "status": "Available",
                        "maxPower": 150,
                        "minPower": 0,
                        "connectorType": "CCS2",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_cross_field_violation() -> dict:
    """Return a charging request with cross-field violations."""
    return {
        "timestamp": "2025-01-15T10:30:00Z",
        "senderId": "DEPOT_001",
        "receiverId": "CMS_001",
        "chargingRequestList": [
            {
                "requestId": "REQ-INVALID",
                "vehicleId": "BUS-001",
                "vehicleType": "eCitaro",
                "batteryCapacity": 292,
                "currentSoC": 80,  # Higher than targetSoC -> violation
                "targetSoC": 70,  # Lower than currentSoC -> violation
                "requestedEnergy": 175,
                "requestedPower": 150,
                "priority": 3,
                "plannedArrival": "2025-01-16T06:00:00Z",  # After departure -> violation
                "plannedDeparture": "2025-01-15T05:00:00Z",  # Before arrival -> violation
                "chargingPointId": "CP-001",
                "connectorType": "CCS2",
            }
        ],
    }


# =============================================================================
# Helper Functions
# =============================================================================


@pytest.fixture
def load_json():
    """Factory fixture to load JSON files."""

    def _load(path: Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    return _load


@pytest.fixture
def save_temp_json(tmp_path):
    """Factory fixture to save JSON to temp directory."""

    def _save(data: dict, filename: str = "test.json") -> Path:
        path = tmp_path / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    return _save
