#!/usr/bin/env python3
"""
Update VDV463 JSON Schemas from official VDV GitHub repository.

This script downloads the latest schemas from the VDVde/VDV463 repository
and saves them to the local schemas/ directory.
"""

import urllib.request
from pathlib import Path

# Configuration
REPO_URL = "https://raw.githubusercontent.com/VDVde/VDV463"
SCHEMAS = {
    "v1.0": {
        "branch": "1.0.0",
        "files": [
            "ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest.json"
        ]
    },
    "v1.1": {
        "branch": "1.1.0",
        "files": [
            "ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest.json"
        ]
    },
    "v1.1-dev": {
        "branch": "v1.1-dev",
        "files": [
            "ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest.json"
        ]
    },
    "v2.0": {
        "branch": "main",
        "files": [
            "ProvideChargingInformationRequest.json",
            "ProvideChargingRequestsRequest.json",
            "ProvideChargingStatusRequest.json",
            "ErrorResponse.json",
            "BootNotificationRequest.json",
            "HeartbeatRequest.json",
            "StatusNotificationRequest.json"
        ]
    }
}

BASE_DIR = Path(__file__).parent.parent
SCHEMAS_DIR = BASE_DIR / "schemas"

def download_file(url, dest_path):
    print(f"Downloading {url} -> {dest_path}")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print(f"Updating VDV463 schemas in {SCHEMAS_DIR}...")

    for version, config in SCHEMAS.items():
        v_dir = SCHEMAS_DIR / version
        v_dir.mkdir(parents=True, exist_ok=True)

        branch = config["branch"]
        # v1.0.0 uses "v1.0/" folder, others use "schema/"
        folder = "v1.0" if branch == "1.0.0" else "schema"

        for filename in config["files"]:
            url = f"{REPO_URL}/{branch}/{folder}/{filename}"
            dest = v_dir / filename

            if download_file(url, dest):
                print(f"  Successfully updated {version}/{filename}")
            else:
                print(f"  Failed to update {version}/{filename}")

    print("\nUpdate complete.")

if __name__ == "__main__":
    main()
