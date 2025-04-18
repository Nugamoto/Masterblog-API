> 🇬🇧 For the English version see [README.md](README.md)

# Masterblog API 📝⚡️

Ein schlankes, aber funktionsreiches **Flask + JWT**‑Backend (mit kleinem Frontend) zum Verwalten von Blog‑Beiträgen.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://www.python.org/) 
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask)](https://flask.palletsprojects.com/) 
[![License](https://img.shields.io/badge/license-MIT-green)](#lizenz) 

---

## ✨ Funktionen

- **JWT‑Authentifizierung** – sicheres Registrieren / Login mit gehashten Passwörtern (`pbkdf2_sha256`)  
- **Vollständiges CRUD** für Beiträge und verschachtelte Kommentare  
- **Komfort‑Features** – Pagination, Feldsuche & Sortierung, Dark‑Mode‑SPA‑Frontend  
- **Sicherheit** – konfigurierbare Rate‑Limits (Standard 100 Req/h, strenger bei Auth‑Routen)  
- **Interaktive Doku** – Swagger UI unter `/api/docs`  
- **Zero‑DB** – JSON‑Dateien für schnelle Demos (leicht gegen echte DB austauschbar)

---

## 🚀 Schnellstart

```bash
# 1. Repository klonen & virtuelle Umgebung einrichten
git clone https://github.com/Nugamoto/Masterblog-API.git
cd Masterblog-API
python -m venv .venv && source .venv/bin/activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Geheimnisse konfigurieren
cp .env.example .env            # lokale Konfig anlegen
echo "JWT_SECRET_KEY=my_super_secret_key" >> .env

# 4. Backend starten  (http://127.0.0.1:5002)
cd backend
python backend_app.py

# 5. Frontend starten (http://127.0.0.1:5001)
cd ../frontend
python frontend_app.py
```

> Beide Server laden bei `debug=True` automatisch neu.

**Optional: Docker**

```bash
docker compose up -d        # `docker-compose.yml` folgt bald
```

---

## 🗄️ Umgebungsvariablen

| Variable | Zweck | Standard |
|----------|-------|----------|
| `JWT_SECRET_KEY` | HMAC‑Schlüssel zum Signieren von Access/Refresh Tokens | – |
| `RATE_LIMIT` | Anfragen pro Stunde (z. B. `100/hour`) | `100/hour` |

Sei sicher, deine Werte in **`.env`** abzulegen (niemals Secrets committen). Eine Vorlage findest du in **`.env.example`**.

---

## 🗺️ Projektstruktur

```
Masterblog-API
├─ backend/          # Flask REST API
│  ├─ backend_app.py
│  ├─ helpers.py
│  └─ static/masterblog.json   # Swagger-Spec
├─ frontend/         # Kleines Flask‑Frontend
│  ├─ templates/
│  └─ static/
└─ .guides/          # Dev‑Notizen & Assets
```

---

## 🔌 API‑Spickzettel

| Verb | Endpoint | Geschützt | Beschreibung |
|------|----------|-----------|--------------|
| `POST` | `/api/v1/register` | – | Benutzer registrieren |
| `POST` | `/api/v1/login` | – | JWT erhalten |
| `GET / POST` | `/api/v1/posts` | `POST` braucht JWT | Beiträge listen (`page`, `limit`, `sort`, `direction`) oder Beitrag erstellen |
| `PUT / DELETE` | `/api/v1/posts/<id>` | ✅ | eigenen Beitrag ändern / löschen |
| `GET` | `/api/v1/posts/search?title=...&tag=...` | – | Mehrfeldsuche |
| `POST` | `/api/v1/posts/<id>/comments` | ✅ | Kommentar hinzufügen |

Beispiel – Beitrag erstellen:

```bash
curl -X POST http://127.0.0.1:5002/api/v1/posts   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -d '{"title":"Hallo","content":"Welt"}'
```

---

## 🛠️ Entwicklung

```bash
ruff check . && ruff format .   # Linting & Formatting
pytest                          # Tests (folgen)
```

Funktioniert sofort mit VS Code (`.vscode/settings.json`).

---

## 🔮 Roadmap

- [ ] JSON‑Store → SQLite via SQLAlchemy ersetzen  
- [ ] GitHub‑Actions‑CI‑Pipeline  
- [ ] Docker Compose mit Nginx‑Reverse‑Proxy  
- [ ] Unit‑ & Integrationstests  
- [ ] i18n für das Frontend  

---

## 🤝 Mitwirken

Pull Requests & Issues sind willkommen! Schau dir `CONTRIBUTING.md` an (oder eröffne eins 😊).

---

## 📝 Lizenz

Dieses Projekt steht unter der **MIT‑Lizenz** – siehe [`LICENSE`](LICENSE) für Details.

---

> Mit ♥ von [@Nugamoto](https://github.com/Nugamoto) erstellt