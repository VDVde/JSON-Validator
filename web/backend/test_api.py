import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Setup path for imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "web" / "backend"))
sys.path.append(str(BASE_DIR / "src"))

from main import app  # noqa: E402

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_auth_failure_no_creds():
    response = client.get("/api/schemas")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"

def test_auth_success():
    # Default creds are admin:secret
    response = client.get("/api/schemas", auth=("admin", "secret"))
    assert response.status_code == 200
    assert "schemas" in response.json()
    assert isinstance(response.json()["schemas"], list)

def test_validate_json_missing_auth():
    files = {'file': ('test.json', '{"test": 1}', 'application/json')}
    response = client.post("/api/validate", files=files)
    assert response.status_code == 401

def test_validate_invalid_json():
    # Valid auth, invalid json content
    files = {'file': ('test.json', '{invalid}', 'application/json')}
    response = client.post("/api/validate", files=files, auth=("admin", "secret"))
    assert response.status_code == 200 # It returns 200 with error info in body usually, or VDV validator handles it
    data = response.json()
    assert "summary" in data
    assert data["summary"]["errors"] > 0
