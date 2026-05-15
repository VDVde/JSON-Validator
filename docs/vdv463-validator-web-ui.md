# VDV463 Validator – Web UI Guide

Diese Anleitung beschreibt die Einrichtung und Nutzung der Browser-basierten
Web-Oberfläche des VDV463 Validators, die als Docker-Container bereitgestellt wird.

## Table of Contents

- [Überblick](#überblick)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [HTTPS & SSL-Zertifikate](#https--ssl-zertifikate)
- [Authentifizierung](#authentifizierung)
- [Umgebungsvariablen (.env)](#umgebungsvariablen-env)
- [Benutzung der Web-Oberfläche](#benutzung-der-web-oberfläche)
- [API-Referenz](#api-referenz)
- [Troubleshooting](#troubleshooting)

---

## Überblick

Die Web UI stellt den VDV463 Validator als sichere HTTPS-Webanwendung bereit.
Sie eignet sich besonders für:

- **Team-Deployments** – mehrere Nutzer greifen gleichzeitig zu
- **Air-gapped / Intranet-Umgebungen** – kein Python-Setup auf Client-Seite nötig
- **CI-Web-Workflows** – Ergebnisse direkt im Browser prüfen und als CSV/JSON exportieren

**Technischer Stack:**

| Komponente | Technologie |
|---|---|
| Frontend | React + Vite (SPA) |
| Backend | FastAPI (Python 3.12) + Uvicorn |
| Reverse Proxy | nginx (TLS 1.2/1.3) |
| Container | Docker Compose |

---

## Voraussetzungen

- **Docker** (Engine ≥ 24 + Docker Compose v2 oder Docker Desktop ≥ 24)
- **OpenSSL** (zum Generieren der Zertifikate)
- Freie Ports **443** (HTTPS) und **80** (HTTP→Redirect)
- Für Produktion: gültige SSL-Zertifikate (Let's Encrypt oder kommerziell)

---

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/VDVde/JSON-Validator.git
cd vdv463-validator

# 2. SSL-Zertifikate generieren (selbstsigniert, nur für lokale Entwicklung)
# Windows:
.\generate-ssl-certs.ps1
# Linux/macOS:
chmod +x generate-ssl-certs.sh && ./generate-ssl-certs.sh

# 3. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env öffnen und JWT_SECRET_KEY setzen (min. 32 Zeichen)

# 4. Anwendung starten
# Der erste Start baut das Frontend automatisch im Container (Dauer: ~2-5 Min)
docker compose up -d

# 5. Browser öffnen
# https://localhost  (Zertifikatswarnung bei selbstsigniertem Cert akzeptieren)
```

---

## HTTPS & SSL-Zertifikate

nginx terminiert TLS auf Port **443** und leitet HTTP (Port 80) automatisch auf
HTTPS um. Die Zertifikate liegen in `nginx/ssl/` (nicht im Git-Repository).

### Selbstsignierte Zertifikate (Entwicklung)

```powershell
# Windows (PowerShell)
.\generate-ssl-certs.ps1

# Linux / macOS
./generate-ssl-certs.sh
```

Erzeugt `nginx/ssl/cert.pem` und `nginx/ssl/key.pem`.

### Let's Encrypt (Produktion)

```bash
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   nginx/ssl/key.pem
docker compose restart nginx
```

### TLS-Konfiguration (nginx)

- Protokolle: **TLS 1.2** und **TLS 1.3**
- Cipher Suite: ECDHE-RSA/ECDSA mit AES-GCM (Forward Secrecy)
- HSTS: aktiviert (`max-age=31536000`)

---

## Authentifizierung

Die Web UI unterstützt zwei Modi:

### Modus 1 – Authentifizierung aktiviert (Standard / Produktion)

Nutzer müssen sich mit E-Mail und Passwort registrieren und anmelden.
Die Sitzungsverwaltung erfolgt über **JWT Bearer Tokens**.

Optionale Ergänzung: **Google OAuth** (via `GOOGLE_CLIENT_ID`).

### Modus 2 – Authentifizierung deaktiviert (Intranet / vertrauenswürdige Netze)

Für air-gapped oder interne Deployments kann die Authentifizierung vollständig
deaktiviert werden:

```env
# .env
DISABLE_AUTH=true
```

> ⚠️ **Warnung:** Niemals mit `DISABLE_AUTH=true` im Internet betreiben.
> Alle API-Endpunkte werden dann ohne Login zugänglich.

---

## Umgebungsvariablen (.env)

Kopiere `.env.example` nach `.env` und fülle die Werte aus:

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `JWT_SECRET_KEY` | **Ja** | Zufälliger Key, min. 32 Zeichen (`openssl rand -hex 32`) |
| `AUTH_SECRET` | Nein | Legacy Basic-Auth im Format `user:password` |
| `DISABLE_AUTH` | Nein | `true` deaktiviert alle Auth-Checks (Standard: `false`) |
| `GOOGLE_CLIENT_ID` | Nein | Google OAuth Client-ID |
| `SMTP_HOST` | Nein | SMTP-Server für E-Mail-Verifikation |
| `SMTP_PORT` | Nein | SMTP-Port (Standard: `587`) |
| `SMTP_USER` | Nein | SMTP-Benutzername |
| `SMTP_PASSWORD` | Nein | SMTP-Passwort |
| `APP_URL` | Nein | Öffentliche URL (für E-Mail-Links, Standard: `https://localhost`) |
| `ALLOWED_ORIGINS` | Nein | CORS-Origins, kommagetrennt (Standard: `https://localhost`) |
| `HTTPS_PORT` | Nein | Externer HTTPS-Port (Standard: `443`) |
| `HTTP_PORT` | Nein | Externer HTTP-Port (Standard: `80`) |

---

## Benutzung der Web-Oberfläche

### 1. Datei laden

- **Drag & Drop**: JSON-Datei in die Dropzone ziehen
- **Datei-Button**: Klick auf „Datei öffnen"

Nach dem Laden wird die Datei automatisch validiert.

### 2. Validierungsergebnisse

Die Ergebnisse erscheinen im rechten Panel, gruppiert nach Schweregrad:

| Symbol | Schweregrad | Bedeutung |
|---|---|---|
| ❌ | ERROR | Schema-Verletzung oder kritischer Logikfehler |
| ⚠️ | WARNING | Plausibilitätsproblem (technisch valide, aber verdächtig) |
| ℹ️ | INFO | Hinweis oder Best-Practice-Empfehlung |

### 3. Ergebnisse filtern

Das Suchfeld über der Ergebnisliste filtert in Echtzeit nach:
- Fehlermeldungstext
- JSON-Pfad
- Schweregrad (ERROR / WARNING / INFO)

### 4. Ergebnisse exportieren

Zwei Export-Buttons stehen zur Verfügung:

| Button | Format | Inhalt |
|---|---|---|
| **CSV** | `.csv` | Excel-kompatibel (mit BOM), Spalten: Schweregrad; Pfad; Meldung; Zeile |
| **JSON** | `.json` | Vollständiger Validierungsbericht |

Der Dateiname basiert auf dem validierten Dateinamen mit Zeitstempel.

### 5. JSON-Editor (Treeview)

Der **Treeview-Tab** zeigt die JSON-Struktur als aufklappbaren Baum:
- **Expand All / Collapse All**: Gesamtstruktur ein-/ausklappen
- Klick auf Fehler in der Ergebnisliste markiert den entsprechenden Knoten im Baum

### 6. Schema-Konfiguration

Im Konfigurations-Panel (Zahnrad-Icon):

- **Schema-Version**: `auto` (Standard), `1.0`, `1.1`, `2.0`
- **Nur Schema prüfen**: Deaktiviert Cross-Field-Regeln (reine JSON-Schema-Validierung)
- **Custom Rules**: YAML-Regeldatei hochladen

---

## API-Referenz

Die vollständige OpenAPI-Dokumentation ist unter **`https://localhost/docs`**
(Swagger UI) bzw. **`https://localhost/redoc`** (ReDoc) erreichbar,
sofern FastAPI im Debug-Modus läuft.

| Endpunkt | Methode | Auth | Beschreibung |
|---|---|---|---|
| `/api/health` | GET | Nein | Health-Check (gibt `{"status":"ok"}` zurück) |
| `/api/server-config` | GET | Nein | Server-Konfiguration (`auth_disabled`, etc.) |
| `/api/schemas` | GET | Ja | Liste verfügbarer Schema-Versionen |
| `/api/schemas/{version}/{type}` | GET | Ja | Schema-Inhalt abrufen |
| `/api/validate` | POST | Ja | JSON-Datei validieren (multipart/form-data) |
| `/api/config` | POST | Ja | Custom-Rules-YAML hochladen und validieren |
| `/api/auth/register` | POST | Nein | Neuen Nutzer registrieren |
| `/api/auth/login` | POST | Nein | Anmelden (gibt JWT zurück) |

---

## Troubleshooting

**Container startet nicht (`unhealthy`):**
```bash
docker logs vdv463-validator-app --tail=30
```
Häufige Ursache: `JWT_SECRET_KEY` nicht gesetzt in `.env`.

**Zertifikatswarnung im Browser:**  
Bei selbstsignierten Zertifikaten einmalig „Risiko akzeptieren" / „Advanced → Proceed".

**Login-Fehler 422:**  
Die Eingabe entspricht nicht dem erwarteten Format. Prüfe E-Mail-Format und Passwortlänge.

**CORS-Fehler bei API-Zugriff:**  
Stelle sicher, dass `ALLOWED_ORIGINS` in `.env` die korrekte Domain enthält.

**Rate Limiting (429):**  
Nach 5 fehlgeschlagenen Anmeldungen wird die IP für 60 Sekunden gesperrt.

**Logs einsehen:**
```bash
docker compose logs -f app     # Backend-Logs
docker compose logs -f nginx   # nginx Access-/Error-Logs
```
