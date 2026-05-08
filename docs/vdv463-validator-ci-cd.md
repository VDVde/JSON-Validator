# VDV463 Validator - CI/CD & CLI Guide

This guide details how to use the VDV463 Validator via the Command Line Interface (CLI) and integrate it into Continuous
Integration / Continuous Deployment (CI/CD) pipelines.

## Table of Contents

- [Command Line Interface (CLI)](#command-line-interface-cli)
    - [Basic Usage](#basic-usage)
    - [Command Arguments](#command-arguments)
    - [Exit Codes](#exit-codes)
- [CI/CD Integration](#cicd-integration)
    - [Environment Variables](#environment-variables)
    - [GitLab CI](#gitlab-ci)
    - [GitHub Actions](#github-actions)
    - [Jenkins](#jenkins)
- [Validation Rules & Configuration](#validation-rules--configuration)
    - [Severity Levels](#severity-levels)
    - [Custom Rules](#custom-rules)

---

## Command Line Interface (CLI)

The validator can be run directly from the terminal, making it suitable for automated scripts and batch processing.

### Basic Usage

**Validate a single file:**

```bash
python src/vdv463_validator.py message.json
```

**Validate multiple files (glob pattern):**

```bash
python src/vdv463_validator.py messages/*.json
```

**Validate with a specific schema version:**

```bash
python src/vdv463_validator.py message.json --schema-version 1.1
```

**Generate a JUnit XML report (for CI tools):**

```bash
python src/vdv463_validator.py messages/*.json --junit-xml report.xml --quiet
```

### Command Arguments

| Option             | Short | Description                                                                       |
|--------------------|-------|-----------------------------------------------------------------------------------|
| `input_files`      |       | One or more JSON files to validate (supports wildcards).                          |
| `--config`         | `-c`  | Path to a custom validation rules YAML file.                                      |
| `--schema-dir`     | `-s`  | Directory containing JSON schemas (default: `./schemas`).                         |
| `--schema-version` | `-V`  | Force schema version: `1.0`, `1.1`, `2.0`, or `auto` (default).                   |
| `--output`         | `-o`  | Path to save the JSON validation report.                                          |
| `--junit-xml`      | `-j`  | Path to save a JUnit XML report (for CI integration).                             |
| `--quiet`          | `-q`  | Suppress standard output (useful for CI logs).                                    |
| `--fail-level`     | `-L`  | Minimum severity level to cause a non-zero exit code: `ERROR`, `WARNING`, `INFO`. |
| `--no-output`      |       | Do not write a JSON report file.                                                  |
| `--list-versions`  |       | List available schema versions and exit.                                          |

### Exit Codes

The validator returns standard exit codes to indicate the result of the operation:

| Code | Meaning                                                                    |
|------|----------------------------------------------------------------------------|
| `0`  | **Success**: All validations passed (no issues at or above fail level).    |
| `1`  | **Validation Failed**: Issues found at or above the configured fail level. |
| `2`  | **Input Error**: File not found or unreadable.                             |
| `3`  | **Schema Error**: Error loading or parsing the schema.                     |
| `4`  | **Configuration Error**: Invalid arguments or configuration.               |

---

## CI/CD Integration

The validator is designed to be easily integrated into CI/CD pipelines to automatically check VDV463 messages on every
commit or pull request.

### Environment Variables

You can configure the validator using environment variables, which is often cleaner in CI configurations.

| Variable                | Description                                  | Default     |
|-------------------------|----------------------------------------------|-------------|
| `VDV463_SCHEMA_DIR`     | Path to schema directory                     | `./schemas` |
| `VDV463_SCHEMA_VERSION` | Schema version (`1.0`, `1.1`, `2.0`, `auto`) | `auto`      |
| `VDV463_CONFIG`         | Path to validation rules YAML                | -           |
| `VDV463_FAIL_LEVEL`     | Fail threshold (`ERROR`, `WARNING`, `INFO`)  | `ERROR`     |
| `VDV463_QUIET`          | Minimal output (`true`/`false`)              | `false`     |
| `VDV463_JUNIT_XML`      | JUnit XML output path                        | -           |

### GitLab CI

Add the following job to your `.gitlab-ci.yml`:

```yaml
validate_vdv463:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install jsonschema pyyaml
  script:
    - python src/vdv463_validator.py messages/*.json 
        --quiet 
        --junit-xml vdv463-report.xml
        --fail-level ERROR
  artifacts:
    reports:
      junit: vdv463-report.xml
    paths:
      - vdv463-report.xml
    when: always
```

### GitHub Actions

Create a workflow file `.github/workflows/validate.yml`:

```yaml
name: VDV463 Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install jsonschema pyyaml
        
      - name: Run Validator
        run: |
          python src/vdv463_validator.py messages/*.json \
            --quiet \
            --junit-xml results.xml \
            --fail-level ERROR
            
      - name: Publish Test Report
        uses: mikepenz/action-junit-report@v3
        if: always()
        with:
          report_paths: results.xml
```

### Jenkins

Add a stage to your `Jenkinsfile`:

```groovy
pipeline {
    agent any
    stages {
        stage('Validate VDV463') {
            steps {
                sh 'pip install jsonschema pyyaml'
                sh 'python src/vdv463_validator.py messages/*.json --junit-xml report.xml --fail-level ERROR'
            }
            post {
                always {
                    junit 'report.xml'
                }
            }
        }
    }
}
```

---

## Validation Rules & Configuration

### Severity Levels

The validator categorizes issues into three levels:

1. **ERROR**: Critical failures. The message is invalid according to the schema or fundamental logic (
   e.g., `minPower > maxPower`).
2. **WARNING**: Plausibility issues. The message is technically valid but suspicious (e.g., extremely high power
   values).
3. **INFO**: Informational notes or best practice recommendations.

By default, the CLI only fails (exit code 1) on **ERROR**. You can change this with `--fail-level`:

```bash
# Fail on Warnings and Errors
python src/vdv463_validator.py ... --fail-level WARNING
```

### Custom Rules

You can define custom validation rules in a YAML file to enforce project-specific constraints (e.g., limiting maximum
power for a specific depot).

**Example `my_rules.yaml`:**

```yaml
cross_field_rules:
  - id: "CUSTOM-001"
    name: "Depot Power Limit"
    severity: "WARNING"
    applies_to: ["ProvideChargingRequestsRequest"]
    condition:
      fields: ["requestedPower"]
      rule: "requestedPower <= 150"
    message: "Requested power {requestedPower} kW exceeds depot limit of 150 kW"
```

**Usage:**

```bash
python src/vdv463_validator.py messages/*.json --config my_rules.yaml
```
