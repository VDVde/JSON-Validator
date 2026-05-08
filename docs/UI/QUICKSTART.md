# VDV463 Validator UI - Quick Start Guide

## 🚀 Schnellstart / Quick Start

### Windows

Doppelklick auf `run_ui.bat` oder in der Kommandozeile:

```cmd
cd UI
python main_ui.py
```

### Linux / macOS

In Terminal:

```bash
cd UI
./run_ui.sh
```

oder:

```bash
cd UI
python3 main_ui.py
```

## 📋 5-Minute Tutorial

### Schritt 1: Dateien laden / Load Files

1. Klicken Sie auf **"📂 Öffnen"** / **"📂 Open"** in der Symbolleiste
2. Oder verwenden Sie **Drag & Drop** - ziehen Sie JSON-Dateien direkt ins Fenster
3. Oder drücken Sie **Strg+O** / **Ctrl+O**
4. Wählen Sie eine oder mehrere JSON-Dateien aus
5. Die Dateien erscheinen in der linken Liste

### Schritt 2: Datei auswählen / Select File

1. Klicken Sie auf eine Datei in der Liste
2. Der JSON-Inhalt wird im mittleren Editor angezeigt
3. Sie können den Inhalt bearbeiten (Datei wird mit * markiert)
4. Das Validierungsstatus-Symbol zeigt den aktuellen Zustand:
    - ✅ = Gültig / Valid
    - ⚠️ = Warnungen / Warnings
    - ❌ = Fehler / Errors

### Schritt 3: Validierung starten / Start Validation

**Einzelne Datei:**

- Klicken Sie auf den grünen **"Validieren"** / **"Validate"** Button im Editor-Panel
- Oder klicken Sie auf **"✓ Validieren"** / **"✓ Validate"** in der Symbolleiste
- Oder drücken Sie **Strg+Shift+V** / **Ctrl+Shift+V**

**Alle Dateien:**

- Klicken Sie auf **"✓✓ Alle validieren"** / **"✓✓ Validate All"** in der Symbolleiste
- Oder drücken Sie **F5**
- Ein Fortschrittsfenster zeigt den Status
- Die Dateiliste wird mit Status-Symbolen aktualisiert

### Schritt 4: Ergebnisse prüfen / Review Results

1. Ergebnisse erscheinen im rechten Panel
2. Verwenden Sie das **Suchfeld** zum Filtern von Ergebnissen
    - Nach Schweregrad, Pfad oder Nachrichtentext filtern
3. Fehler sind nach Schweregrad gruppiert:
    - 🔴 **FEHLER** / **ERROR**: Muss behoben werden
    - ⚠️ **WARNUNG** / **WARNING**: Sollte geprüft werden
    - ℹ️ **INFO**: Informativ
4. Doppelklick auf einen Fehler springt zur entsprechenden Stelle im JSON
5. Oder verwenden Sie **"→ Zu Fehler"** / **"→ Go to Error"** (F8)

### Schritt 5: Änderungen speichern / Save Changes

- Klicken Sie auf **"💾 Speichern"** / **"💾 Save"** in der Symbolleiste
- Oder drücken Sie **Strg+S** / **Ctrl+S**
- **Datei → Speichern unter...** / **File → Save As...** (Strg+Shift+S / Ctrl+Shift+S)
- **Datei → Ergebnisse exportieren...** / **File → Export Results...**

## 🌍 Sprache ändern / Change Language

**Menü → Sprache → Deutsch / English**

Die komplette Oberfläche wechselt sofort die Sprache.

## ⚙️ Konfiguration / Configuration

### Schema-Version

Wählen Sie die VDV463-Version aus der Dropdown-Liste:

- **auto**: Automatische Erkennung (empfohlen)
- **1.0**: VDV463 Version 1.0
- **1.1**: VDV463 Version 1.1
- **2.0**: VDV463 Version 2.0

### Regelkonfiguration / Rule Configuration

1. Klicken Sie auf **"Regeln laden..."** / **"Load Rules..."**
2. Wählen Sie eine YAML-Regelkonfigurationsdatei
3. Die Regeln werden für die Validierung verwendet

## 📊 Batch-Validierung / Batch Validation

Validieren Sie mehrere Dateien gleichzeitig:

1. Laden Sie mehrere JSON-Dateien
2. Klicken Sie auf **"Alle validieren"** / **"Validate All"**
3. Fortschrittsanzeige zeigt Status für jede Datei
4. Zusammenfassung zeigt:
    - Anzahl der Dateien
    - Gesamt-Fehler, -Warnungen, -Infos
    - Bestanden/Fehlgeschlagen

## 🎯 Tastaturkürzel / Keyboard Shortcuts

### Datei / File

- **Strg+O** / **Ctrl+O**: Dateien öffnen / Open files
- **Strg+S** / **Ctrl+S**: Datei speichern / Save file
- **Strg+Shift+S** / **Ctrl+Shift+S**: Speichern unter / Save As
- **Strg+W** / **Ctrl+W**: Datei schließen / Close file
- **Strg+Q** / **Ctrl+Q**: Beenden / Quit

### Bearbeiten / Edit

- **Strg+Shift+F** / **Ctrl+Shift+F**: JSON formatieren / Format JSON
- **Strg+Shift+M** / **Ctrl+Shift+M**: JSON minimieren / Minify JSON

### Validierung / Validation

- **Strg+Shift+V** / **Ctrl+Shift+V**: Aktuelle Datei validieren / Validate current file
- **F5**: Alle Dateien validieren / Validate all files
- **F8**: Zum nächsten Fehler springen / Go to next error

## 💡 Tipps / Tips

### Fehlernavigation / Error Navigation

1. Wählen Sie einen Fehler in der Ergebnisliste
2. Doppelklick oder **"Zu Fehler springen"** / **"Go to Error"**
3. Die entsprechende Zeile wird markiert

### Datei-Änderungen / File Changes

- Geänderte Dateien haben ein ***** im Namen
- Beim Schließen werden Sie gefragt, ob Sie speichern möchten
- Validierungsergebnisse bleiben pro Datei erhalten

### JSON-Editor

- Monospace-Font für bessere Lesbarkeit
- Horizontal und vertikal scrollbar
- Änderungen werden automatisch erkannt

## 🔧 Problemlösung / Troubleshooting

### UI startet nicht / UI won't start

**Problem:** `No module named 'PySide6'`

**Lösung:**

- Installieren Sie alle Abhängigkeiten: `pip install -e .`
- Oder nur PySide6: `pip install PySide6`
- Überprüfen Sie die Python-Version: `python --version` (mind. 3.10)

### Validierung schlägt fehl / Validation fails

**Problem:** `Schema directory not found`

**Lösung:**

- Stellen Sie sicher, dass der Ordner `schemas/` im Hauptverzeichnis existiert
- Pfad: `vdv463-validator/schemas/`

**Problem:** `Failed to initialize validator`

**Lösung:**

- Installieren Sie Abhängigkeiten: `pip install jsonschema pyyaml`
- Überprüfen Sie, dass `src/vdv463_validator.py` vorhanden ist

### JSON-Datei kann nicht geladen werden / Can't load JSON file

**Problem:** Encoding-Fehler

**Lösung:**

- Stellen Sie sicher, dass die Datei UTF-8 kodiert ist
- Verwenden Sie einen Editor wie VS Code mit UTF-8

## 📚 Weitere Informationen / More Information

Siehe **README.md** für:

- Detaillierte Funktionsbeschreibung
- Architektur-Dokumentation
- Anpassungsmöglichkeiten
- API-Referenz

## 🆘 Support

Bei Fragen oder Problemen:

1. Prüfen Sie README.md und QUICKSTART.md
2. Prüfen Sie die Hauptdokumentation des vdv463-validator
3. Erstellen Sie ein Issue auf GitHub

## ✨ Features auf einen Blick / Features at a Glance

✅ Mehrere Dateien gleichzeitig laden (mit Drag & Drop)
✅ Symbolleiste mit Schnellzugriff-Aktionen
✅ JSON-Editor mit Syntax-Hervorhebung
✅ Visuelle Status-Indikatoren (✅ ⚠️ ❌)
✅ Such- und Filterfunktion für Ergebnisse
✅ Echtzeit-Validierung
✅ Fehlernavigation per Klick oder Tastatur
✅ Hilfreiche Tooltips mit Tastaturkürzeln
✅ Regelkonfiguration per YAML
✅ Schema-Versions-Unterstützung (1.0, 1.1, 2.0, auto)
✅ Zweisprachig (Deutsch/Englisch)
✅ Export von Validierungsergebnissen
✅ Batch-Validierung mit Fortschrittsanzeige
✅ Moderne PySide6-Benutzeroberfläche
✅ Dark Mode Unterstützung

---

**Viel Erfolg mit dem VDV463 Validator!** 🎉

**Happy validating with VDV463 Validator!** 🎉
