# VDV463 Validator UI

A modern, PySide6-based graphical user interface for validating VDV463 JSON messages. This tool provides a user-friendly environment for editing, validating, and visualizing VDV463 data against official schemas and custom rules.

## Features

*   **Multi-File Validation:** Load and validate multiple JSON files simultaneously.
*   **Live Validation:** Real-time feedback as you edit.
*   **Schema Visualization:** Interactive diagram view of the VDV463 schema structure.
*   **JSON Editor:** Syntax highlighting, code folding, and formatting/minifying tools.
*   **Tree View:** Navigate complex JSON structures easily.
*   **Internationalization:** Fully localized in English and German.
*   **Custom Rules:** Support for loading custom validation rules (YAML).
*   **Dark Mode:** Automatic theme detection based on system settings.

## Requirements

*   Python 3.10 or higher
*   PySide6

## Installation

1.  Navigate to the `ui` directory:
    ```bash
    cd ui
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Windows
Double-click `run_ui.bat` or run from command line:
```powershell
.\run_ui.bat
```

### Linux / macOS
Make the script executable and run it:
```bash
chmod +x run_ui.sh
./run_ui.sh
```

### Manual Start
You can also start the application directly via Python:
```bash
python main_ui.py
```

## License

Licensed under the Apache License, Version 2.0. See the [LICENSE](../LICENSE) file for details.
