# VDV463 Validator UI — Implementation Guide

English-only implementation notes for the current PySide6-based UI. This document describes structure, integration, and
key behaviors of the GUI.

## Overview

- **Tech stack:** Python 3.10+, PySide6, shared validator core (`src/vdv463_validator.py`).
- **Use cases:** Multi-file validation, JSON editing, schema visualization, bilingual UI, CI-friendly status reporting.
- **Outputs:** On-screen status and per-file results; exportable JSON reports via the File menu.

## Files and Modules (UI/)

- `main_ui.py` — Application entry point; window layout, menu/tabs/status bar, validation flow, shortcuts.
- `json_editor.py` — Editor widget with highlighting, format/minify helpers, cursor reporting.
- `json_tree_view.py` — Tree representation of the active JSON document.
- `schema_view.py` — Graphical schema view (zoom/pan, $ref navigation, history).
- `i18n.py` — Translation registry and helper `t()` for DE/EN strings.
- `splash_screen.py` — Optional splash while loading.
- `theme.py` — Styling constants.
- `run_ui.bat` / `run_ui.sh` — Launchers.

## Core Classes

- `VDV463ValidatorUI` (in `main_ui.py`): main window, menus, toolbar, tabs, status bar, validation orchestration.
- `JSONEditor` (in `json_editor.py`): text editor with line numbers, highlighting, format/minify.
- `JsonTreeView` (in `json_tree_view.py`): bound tree view of the active JSON document.
- `SchemaView` (in `schema_view.py`): diagram view of the active schema with navigation.
- `I18n` (in `i18n.py`): translation lookup via `t(key, *args)`.
- Theme utilities (in `theme.py`): centralized styling for buttons and UI elements.

## UI Layout (summary)

- **Top:** Toolbar with emoji-labeled quick actions (Open, Save, Validate, Validate All, Format, Go to Error).
- **Left:** File list with add/remove, modified markers (`*`), and validation status icons (✅ ⚠️ ❌).
- **Center Tabs:** JSON Editor (with prominent Validate button), Tree View, Schema View.
- **Right:** Results panel with search/filter box, grouped by severity (ERROR/WARNING/INFO), double-click navigation.
- **Bottom:** Configuration panel (schema version, rules) and status bar with icon+text, tooltip summary, cursor
  position, file size.

## Validation Flow

1) Load one or more JSON files (drag & drop, toolbar button, or file dialog).
2) Optionally pick schema version (auto/1.0/1.1/2.0) and load custom rules (YAML).
3) Validate current (`Ctrl+Shift+V`, toolbar button, or green Validate button) or all (`F5`, toolbar).
4) Core validator runs; issues appear grouped by severity in results panel.
5) File list updates with validation status icons (✅ ⚠️ ❌).
6) Status bar updates with readable text and icon; tooltip shows detailed counts.
7) Use search box to filter results by path, severity, or message text.
6) Double-click an issue to jump in the editor; `F8` cycles via “Go to Error”.

## Status Bar Behavior

- Icon + clear text (no abbreviations) and tooltip summary with counts/file context.
- Cursor position (`Line: n, Column: m`) updates on caret move.
- File size updates on file change or edits.

## Shortcuts (selected)

- File: `Ctrl+O` open, `Ctrl+S` save, `Ctrl+Shift+S` save as, `Ctrl+W` close file.
- Edit: `Ctrl+Shift+F` format JSON, `Ctrl+Shift+M` minify JSON.
- Validation: `Ctrl+Shift+V` validate current, `F5` validate all, `F8` go to next error.
- Schema view: `Alt+Left` / `Alt+Right` back/forward; mouse wheel to zoom; drag to pan.
- Toolbar: Quick access to all common operations with emoji labels and tooltips.

## Internationalization

- Keys live in `i18n.py`; `t(key, *args)` formats strings.
- Language switching is runtime; menus, labels, tooltips, status strings update immediately.

## Data and State

- Each loaded file tracks content, modified flag, and last `ValidationResult` (issues with paths/messages).
- Results persist per file until revalidated or closed.

## Recent Files

- Persisted via Qt settings; duplicates are deduped; menu rebuilds on change.

## Schema View

- Renders the active schema with zoom/pan and navigation history; click `$ref` to follow references.

## Error Navigation

- Result items carry JSON paths; double-click highlights the matching line in the editor and moves the caret.

## Export

- Export validation results as JSON from the File menu; run batch validation first to gather all files.

## Dependencies

- Runtime: PySide6 plus validator deps (`requirements.txt`).
- Dev: `requirements-dev.txt`; PyInstaller for Windows builds.

## Architecture Notes

- UI ↔ validator decoupled: core logic in `src/`; UI calls via a thin layer in `main_ui.py`.
- Components are modular (editor/tree/schema) for easier replacement or extension.
- Status wording uses shared i18n keys for consistency.

## Future Improvements (nice-to-have)

- Background validation for large batches.
- Additional schema-view navigation (home/root, search).
- Optional diff/undo history in the editor.
