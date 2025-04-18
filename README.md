# Masterblog API 📝⚡️

A minimal yet feature‑rich **Flask + JWT** backend (with a micro‑frontend) for managing blog posts.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://www.python.org/) 
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask)](https://flask.palletsprojects.com/) 
[![License](https://img.shields.io/badge/license-MIT-green)](#license) 

---

## ✨ Features

- **JWT Authentication** – secure register / login flow with hashed passwords (`pbkdf2_sha256`)  
- **Full CRUD** for posts and nested comments  
- **Quality of Life** – pagination, field‑level search & sort, dark‑mode SPA‑like frontend  
- **Security** – configurable rate‑limits (default 100 req/h, stricter on auth routes)  
- **Interactive Docs** – Swagger UI automatically available at `/api/docs`  
- **Zero‑DB** – JSON file storage for quick demos (easily swappable for a real DB)

---

## 🚀 Quick start

```bash
# 1. Clone & create virtual env
git clone https://github.com/Nugamoto/Masterblog-API.git
cd Masterblog-API
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure secrets
cp .env.example .env          # create your local config
echo "JWT_SECRET_KEY=my_super_secret_key" >> .env

# 4. Start backend  (http://127.0.0.1:5002)
cd backend
python backend_app.py

# 5. Start frontend (http://127.0.0.1:5001)
cd ../frontend
python frontend_app.py
```

> Both servers auto‑reload while `debug=True`.

**Optional Docker**

```bash
docker compose up -d        # `docker-compose.yml` coming soon
```

---

## 🗄️ Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `JWT_SECRET_KEY` | HMAC secret for signing access/refresh tokens | – |
| `RATE_LIMIT` | Requests per hour (e.g. `100/hour`) | `100/hour` |

Place your values in **`.env`** (never commit secrets). A template is provided as **`.env.example`**.

---

## 🗺️ Project layout

```
Masterblog-API
├─ backend/          # Flask REST API
│  ├─ backend_app.py
│  ├─ helpers.py
│  └─ static/masterblog.json   # Swagger spec
├─ frontend/         # Tiny Flask‑served HTML/JS client
│  ├─ templates/
│  └─ static/
└─ .guides/          # Dev notes & assets
```

---

## 🔌 API cheat sheet

| Verb | Endpoint | Protected | Description |
|------|----------|-----------|-------------|
| `POST` | `/api/v1/register` | – | create user |
| `POST` | `/api/v1/login` | – | obtain JWT |
| `GET / POST` | `/api/v1/posts` | `POST` needs JWT | list (supports `page`, `limit`, `sort`, `direction`) or create post |
| `PUT / DELETE` | `/api/v1/posts/<id>` | ✅ | update / delete **own** post |
| `GET` | `/api/v1/posts/search?title=...&tag=...` | – | multi‑field search |
| `POST` | `/api/v1/posts/<id>/comments` | ✅ | add comment |

Example – create a post:

```bash
curl -X POST http://127.0.0.1:5002/api/v1/posts   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -d '{"title":"Hello","content":"World"}'
```

---

## 🛠️ Development

```bash
ruff check . && ruff format .   # lint & format
pytest                          # run tests (coming soon)
```

Works out of the box with VS Code (`.vscode/settings.json`).

---

## 🔮 Roadmap

- [ ] Swap JSON store → SQLite via SQLAlchemy  
- [ ] GitHub Actions CI pipeline  
- [ ] Docker Compose with Nginx reverse‑proxy  
- [ ] Unit + integration tests  
- [ ] i18n for frontend UI  

---

## 🤝 Contributing

Pull requests & issues welcome! Please read `CONTRIBUTING.md` (or open one 😊).

---

## 📝 License

This project is released under the **MIT License** – see [`LICENSE`](LICENSE) for details.

---

> Made with ♥ by [@Nugamoto](https://github.com/Nugamoto)
