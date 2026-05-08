# VDV463 Validator UI - Example Usage

## Starting the Application

### Windows

```cmd
cd UI
run_ui.bat
```

or

```cmd
cd UI
python main_ui.py
```

### Linux/macOS

```bash
cd UI
./run_ui.sh
```

or

```bash
cd UI
python3 main_ui.py
```

## Example Workflow

### 1. First Time Usage

```
1. Start the application
2. You will see three panels:
   - Left: Empty file list
   - Middle: Empty JSON editor
   - Right: "No file selected"
3. Bottom: Configuration panel with "auto" schema version
```

### 2. Load Test Files

If you have test JSON files in the project:

```
1. Click "📂 Open" in the toolbar (or "Dateien hinzufügen" in German)
2. Or drag & drop JSON files directly into the window
3. Or press Ctrl+O
4. Navigate to your test files directory
5. Select one or more JSON files (Ctrl+Click for multiple)
6. Click "Open"
7. Files appear in the left panel with status icons
```

Example test files you might have:

- `tests/fixtures/valid_charging_information.json`
- `tests/fixtures/valid_charging_requests.json`
- `tests/fixtures/invalid_*.json`

### 3. View and Edit JSON

```
1. Click on a file in the left panel
2. JSON content appears in the middle editor with tabs (Editor, Tree View, Schema View)
3. You can edit the content in the Editor tab
4. Modified files show an asterisk (*) in the list
5. Use the green "Validate" button for quick validation
6. Use "{ } Format" button to format the JSON
```

### 4. Validate Single File

```
1. Select a file from the list
2. Click the green "Validate" button in editor panel
3. Or click "✓ Validate" in the toolbar
4. Or press Ctrl+Shift+V
5. Wait for validation to complete
6. File list icon updates (✅ ⚠️ ❌)
7. Results appear in the right panel
```

Expected output:

```
✓ Validation passed | Errors: 0, Warnings: 1, Infos: 1 | Duration: 23.45 ms

├─ WARNING (1)
│  └─ currentSoC: Low battery: currentSoC (15%) is below 20%
└─ INFO (1)
   └─ $: Auto-detected schema version: 1.1
```

### 5. Navigate to Errors

```
1. In the results panel, find an error/warning
2. Use the search box to filter results if needed
3. Double-click on the error line
4. Or click "→ Go to Error" button (or press F8)
5. The editor jumps to the relevant location
6. The line is highlighted
```

### 6. Validate Multiple Files

```
1. Load several JSON files
2. Click "✓✓ Validate All" button in toolbar
3. Or press F5
4. A progress window appears showing each file
5. File list updates with status icons
6. After completion, a summary is shown
```

Example summary:

```
Batch validation complete

Total Files: 5
Total Errors: 2
Total Warnings: 3
Total Infos: 5
```

### 7. Export Results

```
1. After validating a file
2. Go to File → Export Results...
3. Choose a location and filename
4. Click Save
```

The exported JSON contains:

```json
{
  "input_file": "example.json",
  "timestamp": "2025-12-04T08:15:30.123456",
  "message_type": "ProvideChargingInformationRequest",
  "schema_version": "1.1",
  "valid": true,
  "duration_ms": 23.45,
  "summary": {
    "errors": 0,
    "warnings": 1,
    "infos": 1
  },
  "issues": [...]
}
```

### 8. Change Schema Version

```
1. In the bottom configuration panel
2. Click on the schema version dropdown
3. Select "1.0", "1.1", "2.0", or "auto"
4. The next validation uses the selected version
```

### 9. Load Custom Rules

```
1. Click "Load Rules..." button
2. Select a YAML rule configuration file
3. The filename appears in the configuration panel
4. Next validation uses these rules
```

Example rule file location:

- `config/validation_rules.yaml` (if you have one)

### 10. Change Language

```
1. Go to Language menu (or "Sprache")
2. Click "Deutsch" or "English"
3. The entire UI switches language immediately
```

## Common Scenarios

### Scenario A: Check if JSON is Valid VDV463

```
Steps:
1. Load your JSON file
2. Keep schema version on "auto"
3. Click "Validate"
4. Check the status line:
   - ✓ Green = Valid
   - ✗ Red = Invalid
5. Review any errors in the results panel
```

### Scenario B: Fix Validation Errors

```
Steps:
1. Load and validate your JSON file
2. Double-click on an error in results
3. Editor jumps to the problematic field
4. Edit the JSON to fix the issue
5. Click "Validate" again
6. Repeat until all errors are resolved
7. Save with File → Save JSON
```

### Scenario C: Validate Multiple Related Files

```
Steps:
1. Load all related JSON files (e.g., all depot configs)
2. Click "Validate All"
3. Review the batch summary
4. Click through each file individually to see details
5. Fix files with errors
6. Run "Validate All" again to confirm
```

### Scenario D: Compare Before/After

```
Steps:
1. Load original JSON file
2. Validate and note the results
3. Make changes in the editor
4. Validate again
5. Compare the before/after error counts
6. If improved, save with "Save As..." to keep both versions
```

### Scenario E: Generate Validation Report

```
Steps:
1. Load and validate your JSON file(s)
2. For each important file:
   - Select it in the list
   - File → Export Results...
   - Save as "filename_validation_report.json"
3. These reports can be:
   - Attached to documentation
   - Used for audit trails
   - Processed by other tools
```

## Using New UI Features

### Toolbar Quick Actions

The toolbar provides one-click access to common operations:

```
📂 Open (Ctrl+O) - Load JSON files
💾 Save (Ctrl+S) - Save current file
✓ Validate (Ctrl+Shift+V) - Validate current file
✓✓ Validate All (F5) - Batch validate all files
{ } Format (Ctrl+Shift+F) - Format/prettify JSON
→ Go to Error (F8) - Jump to next error
```

All buttons have tooltips showing keyboard shortcuts.

### Search and Filter Results

The results panel includes a search box:

```
1. After validation, results appear grouped by severity
2. Type in the search box to filter:
   - Search by JSON path (e.g., "currentSoC")
   - Search by severity (e.g., "ERROR", "WARNING")
   - Search by message text (e.g., "required field")
3. Click the X button to clear the filter
4. Filtered results update in real-time as you type
```

### Visual Status Indicators

File list shows validation status:

```
✅ Green checkmark = Valid (no errors)
⚠️ Warning sign = Has warnings (passed with warnings)
❌ Red X = Has errors (validation failed)

These icons update automatically after:
- Single file validation
- Batch validation
- Re-validation of modified files
```

## Tips and Tricks

### Tip 1: Keyboard Navigation

- Use arrow keys to navigate in the file list
- Use Ctrl+Home/End to jump to start/end of JSON
- Use F8 to jump to next error
- Use Ctrl+Shift+V to validate quickly
- Hover over toolbar buttons to see all keyboard shortcuts

### Tip 2: Batch Processing Workflow

```
Morning routine:
1. Start UI
2. Load all overnight JSON exports
3. Validate All
4. Review failures
5. Export reports
6. Fix issues
7. Validate All again
```

### Tip 3: Quick Error Check

```
Want to know if files are valid?
1. Load files
2. Validate All
3. Look at batch summary
   - "Passed: 10, Failed: 0" = All good!
   - Any failures = Need attention
```

### Tip 4: Working with Modified Files

```
The asterisk (*) after filename means:
- File has unsaved changes
- Closing will prompt to save
- Good for "try changes, then decide to save"

Status icons show validation state:
- ✅ = Valid (no errors)
- ⚠️ = Has warnings
- ❌ = Has errors
```

### Tip 5: Schema Version Selection

```
- "auto": Best for most cases, detects version from file
- "1.0": Force validation against VDV463 v1.0 schema
- "1.1": Force validation against VDV463 v1.1 schema
- "2.0": Force validation against VDV463 v2.0 schema

Use specific version when:
- You know exactly what version you need
- Auto-detection is incorrect
- Testing compatibility
```

## Troubleshooting Examples

### Problem: "Cannot detect message type"

**Cause:** JSON doesn't have expected VDV463 structure

**Solution:**

```
1. Check if JSON has one of:
   - "depotInfoList" (for ProvideChargingInformationRequest)
   - "chargingRequestList" (for ProvideChargingRequestsRequest)
   - "chargingStatusList" (for ProvideChargingStatusRequest in v2.0)
2. If not, this might not be a VDV463 message
3. Check VDV463 documentation for correct structure
```

### Problem: Many "value exceeds maximum" errors

**Cause:** Custom rules might be too strict, or data is actually invalid

**Solution:**

```
1. Review the validation rules
2. If rules are too strict:
   - Create a custom YAML rule config
   - Adjust the max values
   - Load with "Load Rules..." button
3. If data is invalid:
   - Fix the values in the JSON
   - Save and validate again
```

### Problem: File won't save

**Cause:** JSON syntax is invalid

**Solution:**

```
1. Check error message for JSON syntax issue
2. Common problems:
   - Missing comma
   - Extra comma
   - Unmatched brackets
   - Invalid escape sequences
3. Fix the syntax
4. Try saving again
```

## Advanced Usage

### Creating Custom Rule Configurations

Create a YAML file (e.g., `custom_rules.yaml`):

```yaml
range_rules:
  maxPower:
    min: 0
    max: 500
  currentSoC:
    min: 0
    max: 100

warning_thresholds:
  low_soc_warning: 15
  high_power_warning: 400

cross_field_rules:
  - id: "CUSTOM-001"
    name: "Custom validation rule"
    severity: "WARNING"
    applies_to: ["ProvideChargingRequestsRequest"]
    condition:
      fields: ["chargingRequestData.minTargetSoc", "chargingRequestData.maxTargetSoc"]
      rule: "chargingRequestData.minTargetSoc <= chargingRequestData.maxTargetSoc"
    message: "Min SoC exceeds Max SoC"
```

Then load it in the UI with "Load Rules..." button.

### Batch Processing with External Script

If you want to process many files without the UI:

```python
# batch_validate.py
from pathlib import Path
import sys
sys.path.insert(0, 'src')

from vdv463_validator import VDV463Validator

validator = VDV463Validator(Path('schemas'))
files = Path('data').glob('*.json')

for f in files:
    result = validator.validate_file(f)
    print(f"{f.name}: {'PASS' if result.valid else 'FAIL'} "
          f"({result.error_count} errors)")
```

Then review problematic files in the UI.

### Integration with CI/CD

While the UI is for interactive use, you can combine it with CLI:

```bash
# Validate in CI
python src/vdv463_validator.py data/*.json --quiet --junit-xml report.xml

# If failures, developers can:
# 1. Pull the failed JSON files
# 2. Open in UI
# 3. Fix interactively
# 4. Commit and push
```

## Summary

The VDV463 Validator UI provides:

- ✅ Easy visualization of validation results
- ✅ Interactive error fixing
- ✅ Batch processing capabilities
- ✅ Export functionality for documentation
- ✅ Multi-language support

It complements the command-line validator by adding a graphical interface for development and debugging workflows.

---

For more information:

- See **README.md** for full feature documentation
- See **QUICKSTART.md** for quick reference
- See **IMPLEMENTATION.md** for technical details
