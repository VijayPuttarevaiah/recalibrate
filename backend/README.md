# 🚀 Backend API

This is a FastAPI backend. This project uses [uv](https://github.com/astral-sh/uv) for lightning-fast dependency management.

---

## ✨ Features

- **⚡ FastAPI**: Built for speed and ease of use.
- **📦 uv Native**: Uses the modern Python package manager for reliable builds.
- **🗄️ Database Ready**: SQLAlchemy integration with Alembic for seamless schema migrations.
- **🔐 Secure Auth**: Built-in login and registration endpoints.
- **🧪 Testing**: Pre-configured with Pytest for standard verification.

---

## 🛠️ Tech Stack

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-FB7185?style=for-the-badge&logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-2C2C2C?style=for-the-badge&logo=python&logoColor=white)

---

## 📋 Prerequisites

Before you begin, ensure you have **uv** installed:

```powershell
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🚀 Quick Start

### 1. Initialize the Environment
Clone the repository and sync the dependencies. `uv` will automatically create a virtual environment for you.

```bash
uv sync
```


### 2. Configure the Database

To initialize alembic
```bash
uv run alembic init alembic
```
Edit `alembic.ini` to set your database URL:

```ini
sqlalchemy.url = sqlite:///./backend.db  # Example for SQLite
```

### 3. Run Migrations
Initialize your database schema using Alembic:

```bash
uv run alembic upgrade head
```

### 4. Start the Application
Launch the development server with auto-reload enabled:

```bash
uv run uvicorn main:app --reload
```

The API will be available at:
- **API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🛠️ Development Commands

| Task | Command |
| :--- | :--- |
| **Sync/Install** | `uv sync` |
| **Add Package** | `uv add <package>` |
| **Run Tests** | `uv run pytest` |
| **Create Migration** | `uv run alembic revision --autogenerate -m "description"` |
| **Apply Migration** | `uv run alembic upgrade head` |

---

## 📁 Project Structure

```text
backend/
├── alembic/          # Database migration logic
├── models/           # SQLAlchemy database models
├── routers/          # FastAPI route handlers
├── tests/            # Pytest test suite
├── main.py           # Application entry point
├── pyproject.toml    # Dependency & project configuration
└── uv.lock           # Deterministic dependency lock file
```

---

## 🤝 Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---
