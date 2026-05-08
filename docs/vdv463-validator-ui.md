# VDV463 Validator - User Interface Guide

This guide provides detailed instructions for using the graphical user interface (UI) of the VDV463 Validator. The UI
allows for interactive validation, editing, and analysis of VDV463 JSON messages.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation & Startup](#installation--startup)
- [User Interface Overview](#user-interface-overview)
- [Step-by-Step Usage](#step-by-step-usage)
    - [1. Loading Files](#1-loading-files)
    - [2. Editing JSON](#2-editing-json)
    - [3. Validating Messages](#3-validating-messages)
    - [4. Analyzing Results](#4-analyzing-results)
    - [5. Using the Schema View](#5-using-the-schema-view)
    - [6. Exporting Results](#6-exporting-results)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Introduction

The VDV463 Validator UI is a desktop application designed to help developers and integrators validate VDV463 charging
infrastructure messages. It provides a visual environment to check compliance with the VDV463 standard (versions 1.0,
1.1, and 2.0) and identify cross-field inconsistencies.

## Features

- **Toolbar with Quick Actions**: One-click access to common operations with emoji icons (📂 Open, 💾 Save, ✓ Validate, ✓✓
  Validate All, { } Format, → Go to Error).
- **Multi-file workflow**: Load, edit, and validate multiple JSON files at once (drag & drop or file dialog).
- **Visual Status Indicators**: File list shows validation status with icons (✅ valid, ⚠️ warnings, ❌ errors).
- **Search & Filter Results**: Filter validation results by path, severity, or message text in real-time.
- **JSON editor**: Syntax highlighting, line numbers, and change markers; supports format (`Ctrl+Shift+F`) and
  minify (`Ctrl+Shift+M`).
- **Interactive Schema View**: Diagram of the active schema with zoom/pan and navigation between references.
- **Result navigation**: Double-click issues to jump to the exact line; quick navigation via **Go to Error** (F8).
- **Enhanced Tooltips**: All interactive elements have helpful tooltips showing keyboard shortcuts.
- **Status bar insights**: Live status with clear wording (e.g., "❌ 3 errors, 1 warning"), plus cursor position and file
  size.
- **Rule configuration**: Load YAML rule sets to apply custom validations.
- **Recent files**: Quick access list for previously opened JSON files.
- **Multilingual**: Switch UI between German and English at runtime.
- **Cross-platform**: Windows, Linux, macOS.

---

## Installation & Startup

### Option 1: Windows Executable (Recommended)

1. Download the latest `VDV463Validator.exe` from
   the [Releases page](https://github.com/VDVde/JSON-Validator/releases).
2. Double-click the executable to start the application. No installation is required.

### Option 2: Running from Source

**Prerequisites:**

- Python 3.10 or higher
- `pip` package manager

**Installation:**

1. Clone the repository:
   ```bash
   git clone https://github.com/VDVde/JSON-Validator.git
   cd vdv463-validator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This installs PySide6 and all required dependencies.*

**Startup:**

- **Windows:** Run `UI\run_ui.bat`
- **Linux/macOS:** Run `./UI/run_ui.sh`
- **Python direct:** `python UI/main_ui.py`

---

## User Interface Overview

The application window is divided into five main areas:

1. **Toolbar (Top):** Quick access buttons with emoji icons for common operations (Open, Save, Validate, Validate All,
   Format, Go to Error). All buttons have tooltips showing keyboard shortcuts.
2. **File List (Left Panel):** Displays all loaded JSON files. Icons indicate the validation status (✅ valid, ⚠️
   warnings, ❌ errors). Files with unsaved changes are marked with an asterisk (*).
3. **Main Area (Center):** Contains tabs for:
    * **JSON Editor:** For viewing and editing the raw JSON with syntax highlighting. Includes a prominent green "
      Validate" button for quick validation.
    * **Tree View:** A hierarchical view of the JSON data.
    * **Schema View:** A graphical representation of the VDV463 schema with zoom and navigation.
4. **Results Panel (Right Panel):** Shows validation results grouped by severity (Error, Warning, Info). Includes a
   search box to filter results by path, severity, or message text.
5. **Status Bar (Bottom):** Shows validation status with icon and counts (e.g., "❌ 3 errors, 1 warning"), tooltip
   summary with file context, cursor position (Line, Column), and file size.

---

## Step-by-Step Usage

### 1. Loading Files

You can load JSON files into the validator in several ways:

* **Drag & Drop:** Drag JSON files from your file explorer and drop them into the application window.
* **Toolbar Button:** Click the "📂 Open" button in the top toolbar.
* **Keyboard Shortcut:** Press `Ctrl+O`.
* **Menu:** Go to `File > Open JSON Files...`.

Loaded files will appear in the list on the left with a validation status icon next to each file name.

### 2. Editing JSON

1. Select a file from the **File List**.
2. The content will appear in the **JSON Editor** tab.
3. You can modify the JSON directly in the editor.
4. Use the **{ } Format** button in the toolbar (or press `Ctrl+Shift+F`) to format/prettify the JSON.
5. Modified files are marked with an asterisk (*) in the file list.
6. To save changes, click the **💾 Save** button in the toolbar, press `Ctrl+S`, or go to `File > Save JSON`.

### 3. Validating Messages

**Validate Single File:**

1. Select the file you want to validate.
2. Click the green **Validate** button in the editor panel, or click **✓ Validate** in the toolbar, or
   press `Ctrl+Shift+V`.
3. The file's status icon updates (✅ ⚠️ ❌) based on the validation result.

**Validate All Files:**

1. Click **✓✓ Validate All** in the toolbar or press `F5`.
2. All loaded files run sequentially with a progress dialog showing the status.
3. File list icons update automatically to show each file's validation status.

**Schema Version:**
Auto-detect is on by default (1.0 / 1.1 / 2.0). Override via the schema dropdown in the bottom bar if needed.

### 4. Analyzing Results

After validation, the **Results Panel** on the right displays the findings:

* **Search box:** Filter results by typing in the search field. Search by JSON path, severity (ERROR/WARNING/INFO), or
  message text. Results filter in real-time.
* **Status bar:** Shows an icon plus clear text (e.g., `❌ 2 errors, 1 warning`). Hover to see a summary including file
  count and severities.
* **Result list:** Issues are grouped by severity (ERROR, WARNING, INFO).
* **Navigation:** Double-click an issue to jump to the line in the JSON editor; use **→ Go to Error** button in the
  toolbar (F8) to cycle through errors.

### 5. Using the Schema View

The **Schema View** tab helps you understand the structure of the VDV463 standard.

* **Navigation:**
    * Click references (`→`) to jump to definitions.
    * `Alt+Left` / `Alt+Right` for back/forward, mouse wheel to zoom, click-drag to pan.
* **Symbols:** `⌂` root, `●` required, `○` optional.

### 6. Exporting Results

To save the validation report:

1. Go to `File > Export Results...`.
2. Choose a location to save the JSON report.
3. The report contains detailed information about all validation issues for all processed files.

---

## Configuration

### Custom Validation Rules

You can extend the standard validation with custom rules (e.g., power limits, project-specific checks).

1. Create a YAML rule file (see `rules/default.yaml` for examples).
2. In the UI, click **Load Rules...** in the bottom bar.
3. Select your YAML file.
4. Re-validate to apply the rules.

### Language

Switch the interface language via the **Language** menu (German / English). The change applies immediately.

---

## Troubleshooting

**"Invalid JSON" Error:** The file has syntax errors. The editor highlights the failing line; fix and re-validate.

**"Schema not found":** Ensure the `schemas/` directory is present. When running from source, launch from the repo root.

**Status shows errors even after fixes:** Re-run validation (Validate / Validate All) after saving changes.

**Application crashes on startup:** Verify dependencies (`pip install -r requirements.txt`). Ensure Python 3.10+ is
installed. Check that PySide6 is properly installed with `python -c "import PySide6; print('OK')"`.
