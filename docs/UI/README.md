# VDV463 JSON Validator - Local UI

A local Python-based graphical user interface for validating VDV463 JSON messages using PySide6.

## Features

- **Multiple File Support**: Load and validate multiple JSON files simultaneously with drag & drop
- **Toolbar with Quick Actions**: Easy access to common operations (Open, Save, Validate, Format)
- **JSON Editor**: View and edit JSON content with syntax highlighting and modification tracking
- **Real-time Validation**: Validate single files or batch process all loaded files
- **Visual Status Indicators**: File list shows validation status with icons (✅ valid, ⚠️ warnings, ❌ errors)
- **Search & Filter**: Filter validation results by severity, path, or message text
- **Error Navigation**: Click on validation errors to jump to the corresponding location in JSON
- **Enhanced Tooltips**: All interactive elements have helpful tooltips with keyboard shortcuts
- **Rule Configuration**: Load custom validation rule sets from YAML files
- **Schema Version Support**: Auto-detect or manually select VDV463 schema versions (1.0, 1.1, 2.0)
- **Multilingual**: Full German and English support, switchable at runtime
- **Export Results**: Save validation results as JSON reports
- **Modern UI Framework**: Built with PySide6 for a native, responsive experience

## Requirements

- Python 3.10+
- PySide6 (GUI framework)
- VDV463 validator dependencies (jsonschema, pyyaml)
- darkdetect (for dark mode support)

## Installation

1. Ensure you have installed the vdv463-validator package with all dependencies:
   ```bash
   pip install -e .
   ```

   This will automatically install:
    - PySide6 and PySide6-sip (UI framework)
    - jsonschema and pyyaml (validation)
    - darkdetect (dark mode detection)

## Usage

### Starting the Application

```bash
python UI/main_ui.py
```

Or on Windows:

```bash
python UI\main_ui.py
```

### Workflow

1. **Load Files**
    - Click "📂 Open" in toolbar or use File → Open JSON Files (Ctrl+O)
    - Drag & drop JSON files directly into the window
    - Select one or multiple JSON files
    - Files appear in the left panel

2. **Select a File**
    - Click on a file in the left panel
    - The JSON content appears in the middle editor
    - You can edit the content (file will be marked with *)
    - Validation status is shown with icons (✅ ⚠️ ❌)

3. **Configure Validation**
    - Select schema version (auto-detect or specific version) in bottom panel
    - Optionally load a custom rule configuration (YAML)

4. **Validate**
    - Click "✓ Validate" button (green) in editor panel or toolbar
    - Use Ctrl+Shift+V to validate current file
    - Click "✓✓ Validate All" in toolbar or press F5 for batch validation
    - Results appear in the right panel with status icons

5. **Review Results**
    - Errors, warnings, and infos are grouped by severity
    - Use search box to filter results by path, severity, or message
    - Double-click an error to navigate to its location in the JSON
    - Use "→ Go to Error" button (F8) to jump to next error

6. **Edit and Format**
    - Use "{ } Format" button (Ctrl+Shift+F) to format JSON
    - Use Ctrl+Shift+M to minify JSON
    - Formatted content is automatically validated

7. **Save Changes**
    - Click "💾 Save" in toolbar or use Ctrl+S to save modifications
    - Use Ctrl+Shift+S for Save As to save to a new file
    - Use File → Export Results to save validation report

8. **Change Language**
    - Use Language menu to switch between German and English
    - All UI elements update immediately

## UI Components

### Toolbar (Top)

- **📂 Open**: Load JSON files (Ctrl+O)
- **💾 Save**: Save current file (Ctrl+S)
- **✓ Validate**: Validate current file (Ctrl+Shift+V)
- **✓✓ Validate All**: Batch validate all files (F5)
- **{ } Format**: Format JSON (Ctrl+Shift+F)
- **→ Go to Error**: Jump to next error (F8)
- All buttons have helpful tooltips with keyboard shortcuts

### Left Panel - File List

- Lists all loaded JSON files
- Shows modification status (*)
- Displays validation status icons:
    - ✅ Valid (no errors)
    - ⚠️ Warnings (validation passed with warnings)
    - ❌ Errors (validation failed)
- Add/Remove files
- Support for drag & drop

### Middle Panel - JSON Editor

- Tabbed interface with:
    - JSON Editor tab with syntax highlighting
    - Tree View tab for structured view
    - Schema View tab for schema visualization
- View and edit JSON content
- Line numbers and cursor position display
- Track modifications
- Prominent green "Validate" button for quick access
- Format and minify controls

### Right Panel - Validation Results

- Status summary with clear text and icons
- Search/filter box to find specific issues
- Error count by severity (expandable groups)
- Detailed issue list with JSON paths
- Navigate to error locations with double-click
- Color-coded severity indicators

### Bottom Panel - Configuration & Status

- Schema version selector (auto, 1.0, 1.1, 2.0)
- Rule configuration loader
- Current settings display
- Status bar with:
    - Validation status icon and text
    - Tooltip with detailed counts
    - Cursor position (Line, Column)
    - File size information

## Keyboard Shortcuts

### File Operations

- **Ctrl+O**: Open JSON files
- **Ctrl+S**: Save current file
- **Ctrl+Shift+S**: Save As
- **Ctrl+W**: Close current file
- **Ctrl+Q**: Quit application

### Editing

- **Ctrl+Shift+F**: Format JSON
- **Ctrl+Shift+M**: Minify JSON

### Validation

- **Ctrl+Shift+V**: Validate current file
- **F5**: Validate all files
- **F8**: Go to next error

### Schema View Navigation

- **Alt+Left**: Navigate back in schema history
- **Alt+Right**: Navigate forward in schema history
- **Mouse Wheel**: Zoom in/out in schema view
- **Mouse Drag**: Pan in schema view

## File Structure

```
UI/
├── main_ui.py         # Main UI application and window layout
├── json_editor.py     # JSON editor widget with highlighting
├── json_tree_view.py  # Tree view of JSON structure
├── schema_view.py     # Graphical schema visualization
├── i18n.py            # Internationalization module
├── theme.py           # UI theme and styling
├── splash_screen.py   # Startup splash screen
├── run_ui.bat         # Windows launcher script
└── run_ui.sh          # Linux/macOS launcher script
```

## Architecture

### Module Separation

- **main_ui.py**: Main application with window layout, menus, tabs, toolbar, and validation orchestration
    - `JSONFile`: File data model with validation state
    - `VDV463ValidatorUI`: Main UI class
    - File management and drag & drop support
    - Validation logic integration
    - Status bar and visual feedback
- **json_editor.py**: Text editor widget with syntax highlighting, line numbers, and format/minify
- **json_tree_view.py**: Tree representation of JSON documents for structured navigation
- **schema_view.py**: Interactive schema diagram with zoom, pan, and $ref navigation
- **i18n.py**: Handles all translations (German/English) via `t(key)` function
- **theme.py**: Centralized styling constants and button styles for consistent UI
- **splash_screen.py**: Optional startup splash screen

### Design Principles

- **Modern UI Framework**: PySide6 for native look and feel
- **Modular Design**: Clear separation between UI components, logic, and validator
- **User-Friendly**: Toolbar with emoji icons, tooltips, visual status indicators
- **Discoverable**: All actions have tooltips showing keyboard shortcuts
- **Responsive**: Visual feedback for all operations with status bar updates
- **Extensible**: Easy to add new languages, features, or customize themes

## Validation Integration

The UI integrates directly with the existing `vdv463_validator.py` module:

```python
from vdv463_validator import VDV463Validator, ValidationResult

validator = VDV463Validator(
    schema_dir=schema_dir,
    config_path=config_path,
    schema_version=schema_version
)

result = validator.validate_file(filepath)
```

Results are displayed in a tree structure with:

- Severity grouping (ERROR, WARNING, INFO)
- JSON path to the issue
- Detailed error message
- Navigation to error location

## Batch Validation

Batch validation processes multiple files with:

- Progress indicator dialog
- Individual file validation with status updates
- Visual status icons in file list (✅ ⚠️ ❌)
- Aggregated statistics in summary
- Detailed report per file

Results are stored per file and can be reviewed individually. The file list automatically updates with validation status
icons after batch processing completes.

## Customization

### Adding Translations

Edit `i18n.py` and add keys to the `TRANSLATIONS` dictionary:

```python
TRANSLATIONS = {
    "de": {
        "new_key": "Neuer Text",
        ...
    },
    "en": {
        "new_key": "New text",
        ...
    }
}
```

### Changing Colors/Styles

UI styling is centralized in `theme.py`:

```python
# Import styling functions
from theme import get_validate_button_style, COLORS, FONTS

# Apply styles
button.setStyleSheet(get_validate_button_style())
label.setFont(FONTS['monospace'])
```

The theme automatically adapts to system dark mode via `darkdetect`.

### Adding New Schema Versions

The UI automatically supports schema versions defined in `vdv463_validator.py`:

```python
SchemaVersion.SUPPORTED_VERSIONS  # ["1.0", "1.1", "2.0", "auto"]
```

## Troubleshooting

### "No module named 'PySide6'"

- Install PySide6: `pip install PySide6`
- Or install all dependencies: `pip install -e .`

### "Schema directory not found"

- Ensure the `schemas/` directory exists in the parent folder
- The UI expects: `../schemas/` relative to `UI/main_ui.py`

### "Failed to initialize validator"

- Check that `src/vdv463_validator.py` is accessible
- Verify all dependencies are installed: `pip install -e .`

### File encoding issues

- All files are handled with UTF-8 encoding
- Ensure your JSON files are UTF-8 encoded

### UI doesn't start

- Check Python version: `python --version` (requires 3.10+)
- Verify PySide6 installation: `python -c "import PySide6; print('OK')"`
- Check error messages for missing dependencies

## Limitations

- Limited syntax highlighting (basic JSON highlighting)
- No undo/redo in editor (use Ctrl+Z at system level)
- Single-threaded (UI may freeze during very large batch validations)
- Schema view may be slow with extremely large schemas

## Future Enhancements

Possible improvements:

- Enhanced syntax highlighting with more colors
- Advanced search/replace in editor
- Diff viewer for comparing files
- Background threading for large batch validations
- Undo/redo functionality in editor
- Auto-save functionality
- Configurable themes and color schemes
- Plugin system for custom validators

## License

Same as the parent vdv463-validator project (Apache 2.0).

## Support

For issues related to:

- **UI**: Check this README and UI code
- **Validation**: See main project README and validator documentation
- **Schemas**: Refer to VDV463 specification
