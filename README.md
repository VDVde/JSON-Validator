# JSON-Validator a Community Tool for validating JSON schemas e.g. VDV463

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/license/apache-2-0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/VDVde/JSON-Validator/actions/workflows/ci.yml/badge.svg)](https://github.com/VDVde/JSON-Validator/actions)
[![Windows Build](https://github.com/VDVde/JSON-Validator/actions/workflows/build.yml/badge.svg)](https://github.com/VDVde/JSON-Validator/actions/workflows/build.yml)
[![Latest Release](https://img.shields.io/github/v/release/VDVde/JSON-Validator?include_prereleases&label=latest)](https://github.com/VDVde/JSON-Validator/releases/tag/latest)

CLI tool and GUI for validating VDV463 electric bus charging infrastructure messages (ProvideChargingInformationRequest,
ProvideChargingRequestsRequest) against JSON Schema with cross-field validation. Supports multi-version schemas, CI/CD
pipelines with JUnit XML output. 

> ⚠️ **Disclaimer**: This is an unofficial, community-developed tool. In particular, it is not provided, endorsed, approved, recommended or maintained by VDV working groups 
or VDV (Verband Deutscher Verkehrsunternehmen) in any way. The official VDV 463 specification should be obtained directly from VDV. Use this software at your own risk.

![logo](media/logo.png)
---

## Table of Contents

- [Features](#features)
- [Documentation](#documentation)
- [Downloads](#downloads)
- [Web UI (Docker)](#web-ui-docker)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Security](#security)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Multi-version schema support** – VDV463 v1.0, v1.1, v2.0 with auto-detection
- **Three severity levels** – ERROR, WARNING, INFO with configurable fail threshold
- **Cross-field validation** – Plausibility checks beyond JSON Schema (power limits, SoC consistency, temporal
  constraints)
- **CI/CD integration** – JUnit XML reports, standardized exit codes, environment variables
- **Batch processing** – Validate multiple files in a single run
- **Extensible rules** – YAML-based configuration for custom validation rules
- **Graphical User Interface** – PySide6-based GUI for interactive validation with:
    - Multi-file support with JSON editor
    - Interactive Schema View diagram
    - Multilingual support (German/English)
- **Web UI** – Browser-based validator served as a Docker container with:
    - HTTPS (TLS 1.2/1.3 via nginx), JWT authentication, optional auth-bypass for internal networks
    - Real-time search/filter, CSV & JSON export of validation results
    - JSON Treeview, Schema configuration, Custom Rules upload
- **Windows Executable** – Standalone `.exe` available, no Python installation required

---

## Documentation

- **User Interface Guide:** See `docs/vdv463-validator-ui.md` for a step-by-step walkthrough of the PySide6-based GUI (
  loading files, editing, validation flow, schema view, exporting results, troubleshooting).
- **Web UI Guide:** See `docs/vdv463-validator-web-ui.md` for Docker setup, HTTPS configuration, authentication modes,
  environment variables, API reference, and troubleshooting.
- **CI/CD & CLI Guide:** See `docs/vdv463-validator-ci-cd.md` for command-line usage, exit codes, environment variables,
  and ready-to-use snippets for GitLab CI, GitHub Actions, and Jenkins.
- **Additional references:** Existing documents in `docs/` (e.g., rules, schema versions) remain available for deeper
  technical details.

---

## Downloads

### Latest Development Build

The latest successful build from the main branch is always available:

| File                                                                                                                                                    | Description                    |
|---------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| [VDV463Validator-latest.exe](https://github.com/VDVde/JSON-Validator/releases/download/latest/VDV463Validator-latest.exe)                     | Standalone Windows executable  |
| [VDV463-Validator-latest-portable.zip](https://github.com/VDVde/JSON-Validator/releases/download/latest/VDV463-Validator-latest-portable.zip) | Portable ZIP (extract and run) |

### Stable Releases

For stable versions with installers, see
the [Releases page](https://github.com/VDVde/JSON-Validator/releases).

Each release includes:

- **Windows Installer** (`.exe`) – With Start Menu and Desktop shortcuts
- **Standalone Executable** (`.exe`) – Single file, no installation required
- **Portable ZIP** – Extract and run anywhere

---

## Graphical User Interface (UI)

A PySide6-based GUI is available for interactive validation and editing. For a full walkthrough (loading files, editing,
validation flow, schema view, exporting results, troubleshooting), see the **User Interface Guide**
at `docs/vdv463-validator-ui.md`.

**Quick start:**

- Windows: run `UI\run_ui.bat`
- Linux/macOS: run `./UI/run_ui.sh`
- Direct: `python UI/main_ui.py`

The UI supports multi-file validation, JSON editing with syntax highlighting, an interactive schema view, and bilingual
operation (DE/EN).

---

## Web UI (Docker)

Ein Browser-basierter Validator steht als Docker-Container zur Verfügung. Er bietet HTTPS-Support, JWT-Authentifizierung und einen vollständigen Validierungs-Workflow.

**Voraussetzungen:** Docker & OpenSSL

**Schnellstart:**

```bash
# 1. Zertifikate generieren (selbstsigniert)
.\generate-ssl-certs.ps1      # Windows
./generate-ssl-certs.sh       # Linux/macOS

# 2. Umgebung konfigurieren
cp .env.example .env
# JWT_SECRET_KEY in .env setzen (min. 32 Zeichen)

# 3. Start (baut das Frontend automatisch im Container)
docker compose up -d

# 4. https://localhost öffnen
```

For **trusted internal networks** without a login requirement, set `DISABLE_AUTH=true` in `.env`.

> ⚠️ Never use `DISABLE_AUTH=true` on internet-facing deployments.

---

## Installation

### Requirements

- Python 3.10+
- pip

### Install from Source

```bash
git clone https://github.com/VDVde/JSON-Validator.git
cd vdv463-validator
pip install .
```

### Development Setup

```bash
pip install -e .[dev]
pre-commit install
```

### Docker (Web UI)

```bash
pip install .[docker,web]
# or use docker compose directly
docker compose up -d
```

---

## Project Structure

```
vdv463-validator/
│
├── src/                              # Source code
│   ├── __init__.py
│   ├── vdv463_validator.py           # Main validator script
│   └── validation_rules.py           # Validation rules engine
│
├── schemas/                          # JSON Schemas (git-ignored, dynamic)
│   ├── README.md                     # Documentation of official sources
│   ├── v1.0/                         # Cached official v1.0
│   ├── v1.1/                         # Cached official v1.1
│   └── v2.0/                         # Cached official v2.0 (Draft)
│
├── scripts/                          # Maintenance scripts
│   └── update_schemas.py             # Pull latest schemas from VDV GitHub
│
├── rules/                            # Validation rules configuration
│   ├── default.yaml                  # Default validation rules
│   ├── strict.yaml                   # Strict mode rules
│   └── custom/                       # User-defined rules
│       └── .gitkeep
│
├── docs/                             # Documentation
│   ├── vdv463-validator-ui.md        # Desktop UI user guide
│   ├── vdv463-validator-web-ui.md    # Web UI / Docker guide (new)
│   ├── vdv463-validator-ci-cd.md     # CLI & CI/CD guide
│   ├── USAGE.md                      # Detailed usage guide (legacy)
│   ├── RULES.md                      # Validation rules reference
│   ├── SCHEMA_VERSIONS.md            # Schema version differences
│   ├── CI_CD.md                      # CI/CD integration guide (legacy)
│   ├── UI/                           # UI Documentation (legacy)
│   │   ├── README.md                 # UI feature documentation
│   │   ├── QUICKSTART.md             # UI quick start guide
│   │   ├── IMPLEMENTATION.md         # UI technical architecture
│   │   └── example_usage.md          # UI usage examples
│   └── examples/                     # Example configurations
│       ├── gitlab-ci.yml
│       ├── github-actions.yml
│       └── jenkinsfile
│
├── UI/                               # Graphical User Interface (PySide6)
│   ├── __init__.py
│   ├── main_ui.py                    # Main UI application window
│   ├── theme.py                      # UI theming and styling
│   ├── i18n.py                       # Internationalization (DE/EN)
│   ├── json_editor.py                # JSON editor with syntax highlighting
│   ├── json_tree_view.py             # Hierarchical JSON tree display
│   ├── schema_view.py                # Interactive schema diagram
│   ├── splash_screen.py              # Startup splash screen
│   │
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   └── json_file.py              # JSON file data model
│   │
│   ├── utils/                        # Utility functions
│   │   ├── __init__.py
│   │   └── path_utils.py             # Resource path resolution
│   │
│   ├── managers/                     # Business logic managers
│   │   ├── __init__.py
│   │   ├── file_manager.py           # File operations and recent files
│   │   └── validation_manager.py     # Validation execution and results
│   │
│   ├── widgets/                      # UI panel components
│   │   ├── __init__.py
│   │   ├── file_panel.py             # File list panel
│   │   ├── editor_panel.py           # JSON editor with tabs
│   │   ├── results_panel.py          # Validation results panel
│   │   └── config_panel.py           # Configuration panel
│   │
│   ├── run_ui.bat                    # Windows launcher
│   └── run_ui.sh                     # Linux/macOS launcher
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # pytest fixtures
│   ├── test_validator.py             # Validator unit tests
│   ├── test_rules.py                 # Rules engine tests
│   │
│   ├── fixtures/                     # Test data
│   │   ├── v1.0/                     # Test files for schema v1.0
│   │   │   ├── valid/
│   │   │   │   ├── charging_info_minimal.json
│   │   │   │   ├── charging_info_complete.json
│   │   │   │   ├── charging_request_minimal.json
│   │   │   │   └── charging_request_complete.json
│   │   │   └── invalid/
│   │   │       ├── missing_required_field.json
│   │   │       ├── invalid_type.json
│   │   │       └── schema_violation.json
│   │   │
│   │   ├── v1.1/                     # Test files for schema v1.1
│   │   │   ├── valid/
│   │   │   │   ├── charging_info_with_grid_connection.json
│   │   │   │   └── charging_request_with_optional_fields.json
│   │   │   └── invalid/
│   │   │       └── invalid_optional_field.json
│   │   │
│   │   ├── v2.0/                     # Test files for schema v2.0
│   │   │   ├── valid/
│   │   │   │   ├── charging_status.json
│   │   │   │   └── charging_info_v2.json
│   │   │   └── invalid/
│   │   │       └── invalid_status_type.json
│   │   │
│   │   └── cross_field/              # Cross-field validation test cases
│   │       ├── power_violations.json
│   │       ├── soc_inconsistencies.json
│   │       ├── temporal_conflicts.json
│   │       └── valid_cross_field.json
│   │
│   └── rules/                        # Test-specific rule configurations
│       ├── test_rules_strict.yaml
│       └── test_rules_minimal.yaml
│
├── ci/                               # CI/CD configuration templates
│   ├── gitlab/
│   │   └── .gitlab-ci.yml
│   ├── github/
│   │   └── workflows/
│   │       ├── ci.yml
│   │       ├── release.yml
│   │       └── validate-pr.yml
│   └── jenkins/
│       └── Jenkinsfile
│
├── .github/                          # GitHub-specific files
│   ├── workflows/
│   │   ├── ci.yml                    # CI workflow (tests, linting)
│   │   └── build.yml                 # Windows build & release workflow
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .gitignore
├── LICENSE                           # Apache 2.0 License
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── requirements-dev.txt              # Development dependencies
├── requirements-docker.txt           # Docker-specific dependencies
├── pyproject.toml                    # Python project configuration
├── Dockerfile                        # Multi-stage Docker build
├── docker-compose.yml                # Docker Compose (app + nginx)
├── .env.example                      # Environment variable template
├── generate-ssl-certs.ps1            # Self-signed cert generator (Windows)
├── generate-ssl-certs.sh             # Self-signed cert generator (Linux/macOS)
├── nginx/
│   └── nginx.conf                    # nginx reverse proxy config (TLS 1.2/1.3)
└── Makefile                          # Common commands
```

---

## Usage

| Variante | Wann | Einstieg |
|---|---|---|
| **Desktop UI** | Interaktive Validierung, Bearbeitung, Schema-Visualisierung | `python UI/main_ui.py` oder `UI\run_ui.bat` |
| **Web UI** | Team-Deployment, Browser-Zugriff, Docker | `docker compose up -d` → https://localhost |
| **CLI / CI/CD** | Automatisierung, Pipelines, Batch-Verarbeitung | `python src/vdv463_validator.py message.json` |

Detaillierte Anleitungen:
- Desktop UI: `docs/vdv463-validator-ui.md`
- Web UI: `docs/vdv463-validator-web-ui.md`
- CLI / CI/CD: `docs/vdv463-validator-ci-cd.md`

Key schema versions supported: **1.0**, **1.1**, **2.0** with auto-detection.

> [!IMPORTANT]
> **Official Schemas:** This repository does not contain the official VDV463 JSON schemas to avoid 
> licensing issues and ensure you always use the latest official versions. The validator will 
> automatically download them from the [VDVde/VDV463](https://github.com/VDVde/VDV463) repository 
> on first use. See `schemas/README.md` for details.

Custom validation rules can be provided via YAML (see `rules/` and the guides above for examples).

---

## Security

### Dependency Scanning

This project uses **[GuardDog](https://github.com/DataDog/guarddog)** to automatically scan all Python dependencies for:

- 🔍 **Malicious packages** – Known malware signatures
- 🎭 **Typosquatting** – Packages with names similar to popular packages
- ⚠️ **Suspicious patterns** – Obfuscated code, network calls in setup scripts

The security scan runs automatically on every build and **blocks the build if suspicious packages are detected**.

### Running Security Scan Locally

```bash
# Install GuardDog
pip install guarddog

# Scan requirements.txt
guarddog pypi verify requirements.txt

# Scan with detailed output
guarddog pypi verify requirements.txt --output-format=sarif
```

---

## Testing

### Run Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validator.py

# Run tests for specific schema version
pytest tests/ -k "v1_1"
```

### Test Structure

Tests are organized by schema version and validation type:

```
tests/fixtures/
├── v1.0/valid/      # Valid v1.0 messages
├── v1.0/invalid/    # Invalid v1.0 messages (schema violations)
├── v1.1/valid/      # Valid v1.1 messages
├── v1.1/invalid/    # Invalid v1.1 messages
├── v2.0/valid/      # Valid v2.0 messages
├── v2.0/invalid/    # Invalid v2.0 messages
└── cross_field/     # Cross-field validation test cases
```

---

## Configuration Reference

### Validation Config Structure

```yaml
settings:
  strict_mode: false
  default_severity: "WARNING"

range_rules:
  maxPower:
    min: 0
    max: 1000
    unit: "kW"

cross_field_rules:
  - id: "PWR-001"
    name: "minPower must not exceed maxPower"
    severity: "ERROR"
    applies_to: ["ProvideChargingInformationRequest"]
    condition:
      fields: ["minPower", "maxPower"]
      rule: "minPower <= maxPower"
    message: "minPower ({minPower} kW) exceeds maxPower ({maxPower} kW)"

warning_thresholds:
  low_soc_warning: 20
  high_power_warning: 350
```

See [`docs/RULES.md`](docs/RULES.md) for complete reference.

---

## Contributing

Contributions are welcome! Please read the following before submitting:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/VDVde/JSON-Validator.git
cd vdv463-validator
pip install -r requirements-dev.txt
pre-commit install
```

### Build Windows Executable Locally

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller main.spec --noconfirm --clean

# Output in dist/main/VDV463Validator.exe
```

---

## License

This project is licensed under the Apache 2.0 License – see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- VDV (Verband Deutscher Verkehrsunternehmen) for the VDV463 specification
- The open-source community for jsonschema and related tools