# CI/CD Integration Guide

This document describes how to integrate the VDV463 Validator into various CI/CD systems.

## Quick Reference

### Environment Variables

| Variable                | Description                                  | Default        |
|-------------------------|----------------------------------------------|----------------|
| `VDV463_SCHEMA_DIR`     | Path to schema directory                     | `./schemas`    |
| `VDV463_SCHEMA_VERSION` | Schema version (`1.0`, `1.1`, `2.0`, `auto`) | `auto`         |
| `VDV463_CONFIG`         | Path to validation rules YAML                | -              |
| `VDV463_FAIL_LEVEL`     | Fail threshold (`ERROR`, `WARNING`, `INFO`)  | `ERROR`        |
| `VDV463_QUIET`          | Minimal output (`true`/`false`)              | `false`        |
| `VDV463_JUNIT_XML`      | JUnit XML output path                        | -              |
| `VDV463_OUTPUT`         | JSON report output path                      | auto-generated |

### Exit Codes

| Code | Meaning                                  |
|------|------------------------------------------|
| `0`  | All validations passed                   |
| `1`  | Validation issues at or above fail level |
| `2`  | Input error (file not found)             |
| `3`  | Schema loading error                     |
| `4`  | Configuration error                      |

---

## GitLab CI

### Basic Setup

```yaml
# .gitlab-ci.yml
stages:
  - validate

validate_vdv463:
  stage: validate
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
      - "*_validation_*.json"
    when: always
    expire_in: 30 days
```

### Multi-Stage Validation

```yaml
# Strict and normal validation in parallel
validate_normal:
  stage: validate
  script:
    - python src/vdv463_validator.py messages/*.json -q -j report.xml -L ERROR
  artifacts:
    reports:
      junit: report.xml

validate_strict:
  stage: validate
  script:
    - python src/vdv463_validator.py messages/*.json -q -j report-strict.xml -L WARNING
  allow_failure: true  # Don't block pipeline
  artifacts:
    reports:
      junit: report-strict.xml
```

---

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/validate.yml
name: VDV463 Validation

on:
  push:
    paths:
      - 'messages/**/*.json'
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install jsonschema pyyaml

      - name: Validate VDV463 messages
        run: |
          python src/vdv463_validator.py messages/*.json \
            --quiet \
            --junit-xml test-results.xml \
            --fail-level ERROR

      - name: Publish Test Results
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: VDV463 Validation
          path: test-results.xml
          reporter: java-junit
```

### Matrix Strategy (Multiple Fail Levels)

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        fail-level: [ERROR, WARNING]
      fail-fast: false
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install jsonschema pyyaml
      - name: Validate (${{ matrix.fail-level }})
        run: |
          python src/vdv463_validator.py messages/*.json \
            -q -j results-${{ matrix.fail-level }}.xml \
            -L ${{ matrix.fail-level }}
        continue-on-error: ${{ matrix.fail-level == 'WARNING' }}
```

---

## Jenkins

### Declarative Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    parameters {
        choice(
            name: 'FAIL_LEVEL',
            choices: ['ERROR', 'WARNING', 'INFO'],
            description: 'Minimum severity that causes build failure'
        )
        choice(
            name: 'SCHEMA_VERSION',
            choices: ['auto', '1.0', '1.1', '2.0'],
            description: 'VDV463 schema version'
        )
    }
    
    environment {
        VDV463_FAIL_LEVEL = "${params.FAIL_LEVEL}"
        VDV463_SCHEMA_VERSION = "${params.SCHEMA_VERSION}"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install jsonschema pyyaml'
            }
        }
        
        stage('Validate') {
            steps {
                sh '''
                    python src/vdv463_validator.py messages/*.json \
                        --quiet \
                        --junit-xml vdv463-results.xml \
                        --fail-level ${VDV463_FAIL_LEVEL} \
                        --schema-version ${VDV463_SCHEMA_VERSION}
                '''
            }
            post {
                always {
                    junit 'vdv463-results.xml'
                    archiveArtifacts artifacts: '*_validation_*.json', allowEmptyArchive: true
                }
            }
        }
    }
    
    post {
        failure {
            emailext(
                subject: "VDV463 Validation Failed: ${currentBuild.fullDisplayName}",
                body: "Check: ${env.BUILD_URL}",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
    }
}
```

---

## Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  paths:
    include:
      - messages/*

pool:
  vmImage: 'ubuntu-latest'

variables:
  VDV463_FAIL_LEVEL: 'ERROR'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install jsonschema pyyaml
    displayName: 'Install dependencies'

  - script: |
      python src/vdv463_validator.py messages/*.json \
        --quiet \
        --junit-xml $(Build.ArtifactStagingDirectory)/test-results.xml \
        --fail-level $(VDV463_FAIL_LEVEL)
    displayName: 'Validate VDV463 messages'

  - task: PublishTestResults@2
    condition: always()
    inputs:
      testResultsFormat: 'JUnit'
      testResultsFiles: '$(Build.ArtifactStagingDirectory)/test-results.xml'
      testRunTitle: 'VDV463 Validation'
```

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY schemas/ ./schemas/
COPY rules/ ./rules/

ENTRYPOINT ["python", "src/vdv463_validator.py"]
CMD ["--help"]
```

### Usage

```bash
# Build
docker build -t vdv463-validator .

# Validate files
docker run -v $(pwd)/messages:/data vdv463-validator \
    /data/*.json --quiet --fail-level ERROR

# With JUnit output
docker run -v $(pwd)/messages:/data -v $(pwd)/reports:/reports \
    vdv463-validator /data/*.json -q -j /reports/results.xml
```

---

## Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: vdv463-validate
        name: Validate VDV463 Messages
        entry: python src/vdv463_validator.py
        language: python
        types: [json]
        files: ^messages/.*\.json$
        args: ['--quiet', '--fail-level', 'ERROR', '--no-output']
        additional_dependencies: ['jsonschema', 'pyyaml']
```

Install:

```bash
pip install pre-commit
pre-commit install
```
