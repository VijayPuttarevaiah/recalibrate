# 🚀 Backend API

This is a robust FastAPI backend designed for scalability and ease of development. It handles user registration, email verification, authentication (JWT), and session management (Logout).

---

## ✨ Features

- **⚡ FastAPI**: High-performance web framework for building APIs.
- **📦 uv Native**: Modern Python package management for faster builds and deterministic dependencies.
- **🗄️ Database**: SQLAlchemy ORM with **Alembic** migrations.
- **🔐 Secure Auth**: 
  - JWT-based authentication.
  - Password hashing via `bcrypt`.
  - Token blacklisting on logout.
- **📧 Email Service**: Integrated email verification flow.
- **🧪 Testing**: Comprehensive test suite using `pytest` with in-memory database isolation.

---

## 🛠️ Tech Stack

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-FB7185?style=for-the-badge&logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-2C2C2C?style=for-the-badge&logo=python&logoColor=white)

---

## 📋 Prerequisites

Ensure you have **uv** installed for dependency management:

```powershell
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 🚀 Getting Started

### 1. Setup Environment
Clone the repo and install dependencies:
```bash
uv sync
```

### 2. Configuration
The application uses `config/config.ini`. Update your credentials (SMTP, DB URL, JWT secrets) there:
```ini
[database]
url = sqlite:///./backend.db

[email]
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_user = your-email@gmail.com
smtp_password = your-app-password

[oauth2]
secret_key = your-very-secret-key
```

### 3. Database Migrations
We use Alembic to manage database schema changes.

- **Initialize migrations** (if not already done): `uv run alembic init alembic`
- **Generate a new migration**: 
  ```bash
  uv run alembic revision --autogenerate -m "description of changes"
  ```
- **Apply migrations**: 
  ```bash
  uv run alembic upgrade head
  ```

### 4. Run the Application
Start the server with auto-reload:
```bash
uv run uvicorn main:app --reload
```
- **Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🐳 Docker Deployment

The application uses **MySQL 8.0** as the production database when running in Docker.

### 1. Run with Docker Compose
```bash
docker-compose up --build
```
This will:
- Spin up a **MySQL** container (`db`).
- Build the `api` service and wait for MySQL to be healthy.
- **Automatically apply database migrations** via `start.sh`.
- Expose the API on `http://127.0.0.1:8000`.

### 2. Manual Migration Management (Optional)
If you need to manually manage migrations while the container is running:
- **Apply migrations**: `docker-compose exec api uv run alembic upgrade head`
- **Create new migration**: `docker-compose exec api uv run alembic revision --autogenerate -m "description"`

---

## 🏗️ Architecture & How It Works

### 🧩 Core Components
1. **`main.py`**: The entry point. It initializes the FastAPI app, registers routers, and sets up the database lifespan.
2. **`models/`**: Defines the database schema using SQLAlchemy. 
   - `User`: Handles user data and verification status.
   - `BlacklistedToken`: Stores invalidated tokens after logout.
3. **`routers/`**: Contains API endpoints grouped by functionality.
   - `register.py`: User signup.
   - `login.py`: Authenticates users and issues JWTs.
   - `logout.py`: Invalidates JWTs by blacklisting them.
   - `email_verification.py`: Handles verification codes and email delivery.
4. **`utils/`**: Shared helper functions.
   - `db_session.py`: Singleton for database connections.
   - `password.py`: Security logic for hashing.
   - `email_sender.py`: SMTP logic.

### 🔄 Authentication Flow
1. User **Registers** -> Account created with `is_verified=False`.
2. User **Verify Email** -> Code sent via SMTP; user submits code to activate account.
3. User **Login** -> Validates password and returns a JWT `access_token`.
4. User **Access Protected Routes** -> Frontend sends JWT in `Authorization: Bearer <token>` header.
5. User **Logout** -> Token is sent to `/logout` and added to `blacklisted_tokens` in DB.

---

## 🧪 Testing

Run tests to ensure everything is working correctly:
```bash
uv run pytest
```
*Note: Tests use an in-memory SQLite database (`conftest.py`) to prevent data corruption in your development DB.*

---
