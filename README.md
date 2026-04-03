# Adaptive Goal Planner

A full-stack goal planning application that helps users create, track, pause, and resume personal goals with intelligent task generation and adaptive replanning.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Setup](#manual-setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Use Case Scenarios](#use-case-scenarios)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Project Structure](#project-structure)
- [Design Principles](#design-principles)

---

## Features

- **User Authentication** -- Register, login, email verification, password reset with JWT tokens
- **Goal Creation** -- Create goals with category detection, date range, and notes
- **Task Generation** -- Automatic daily task roadmap generated based on goal parameters
- **Task Management** -- Mark tasks as completed/pending/missed/skipped, add notes
- **Goal Pause/Resume** -- Pause goals temporarily; resume with keep-original-deadline or set-new-deadline options with intelligent task regeneration
- **Adaptive Replanning** -- Detects missed tasks and regenerates an adjusted plan
- **In-App Chat** -- Goal-level and task-level guidance with streaming responses
- **Notifications** -- Email alerts for upcoming deadlines, overdue tasks, and completed milestones
- **Onboarding** -- Personalized roadmap based on user preferences
- **Dashboard** -- Visual progress tracking with status badges, progress bars, and replan indicators

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Python, FastAPI, SQLAlchemy | Python >= 3.11 |
| **Frontend** | React, Vite | Node 20, React 19 |
| **Database** | MySQL | 8.0 |
| **Containerization** | Docker, Docker Compose | Docker 24+ |
| **CI/CD** | GitLab CI | - |
| **Testing** | pytest, pytest-cov, Vitest | - |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- (For manual setup) Python >= 3.11 with [uv](https://docs.astral.sh/uv/), Node.js >= 20

---

## Quick Start (Docker)

```bash
git clone <repository-url>
cd group02

# Create backend environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys (see Environment Variables section)

# Start all services
docker compose up --build -d
```

The application will be available at:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **MySQL**: localhost:3306

To stop:
```bash
docker compose down
```

To reset database:
```bash
docker compose down -v
docker compose up --build -d
```

---

## Manual Setup

### Backend

```bash
cd backend

# Install uv (Python package manager)
pip install uv

# Install dependencies
uv sync --frozen

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:5173 in your browser (development mode).

### Database

If not using Docker, you need a MySQL 8.0 instance:

```sql
CREATE DATABASE backend_db;
CREATE USER 'user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON backend_db.* TO 'user'@'%';
```

---

## Environment Variables

Create `backend/.env` with the following:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | MySQL connection string. Default: `mysql+pymysql://user:password@localhost:3306/backend_db` |
| `OPENROUTER_API_KEY` | Yes | API key for task generation and chat features |
| `SERPER_API_KEY` | Yes | API key for web research during goal creation |
| `GOOGLE_API_KEY` | No | Google API key (alternative provider) |
| `LLM_MODEL` | No | Model identifier. Default: `openai/gpt-4o-mini` |
| `SMTP_USER` | No | Email address for sending notifications |
| `SMTP_PASSWORD` | No | Email password/app password |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create a new account |
| POST | `/login` | Login with email and password |
| POST | `/logout` | Logout and blacklist token |
| POST | `/send-code` | Send email verification code |
| POST | `/verify` | Verify email with code |
| POST | `/forgot-password` | Request password reset |
| POST | `/verify-reset-code` | Verify reset code |
| POST | `/reset-password` | Set new password |

### Goals

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/goals/create` | Create goal with auto-generated tasks |
| GET | `/goals/` | List all user goals with task counts |
| GET | `/goals/{id}/tasks` | Get goal details with full task list |
| PATCH | `/goals/{id}/pause` | Pause an active goal |
| PATCH | `/goals/{id}/resume` | Resume a paused goal (body: `{mode, new_end_date?}`) |
| POST | `/goals/category` | Detect goal category |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/tasks/{id}/status` | Update task status (pending/completed/missed/skipped) |
| PATCH | `/tasks/{id}/notes` | Add or update task notes |
| GET | `/tasks/{id}` | Get task details |
| PATCH | `/tasks/batch-status` | Batch update multiple task statuses |

### Replanning

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/goals/{id}/replan/check` | Check if goal needs replanning |
| POST | `/goals/{id}/replan` | Trigger adaptive replanning |
| GET | `/goals/{id}/replan/history` | Get adjustment history |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/sessions` | Start a new chat session |
| POST | `/chat/sessions/{id}/messages/stream` | Send message with streaming response |
| GET | `/chat/sessions/{id}` | Get chat history |
| POST | `/chat/explain/task/{id}` | Get quick task explanation |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/{user_id}` | Get user notifications |
| PATCH | `/notifications/{id}/read` | Mark notification as read |

---

## Use Case Scenarios

### 1. New User Registration and Goal Creation

1. User registers at `/register` with email, name, and password
2. Verification code sent to email; user enters code at `/verify`
3. User logs in and lands on the Dashboard
4. Clicks "Create Goal", enters: goal description, start date, end date, optional notes
5. System detects category, performs web research, and generates a daily task roadmap
6. Goal appears on Dashboard with progress bar and task count

### 2. Daily Task Management

1. User clicks a goal card on Dashboard to see task list
2. Tasks are listed chronologically with status indicators
3. User marks tasks as completed by clicking the checkbox
4. User adds notes to tasks (progress, blockers, learnings)
5. Progress bar updates in real-time based on completed tasks
6. Filter tasks by status: All, Pending, Completed, Missed

### 3. Falling Behind Schedule (Replanning)

1. System detects 3+ missed tasks (past due date, still pending)
2. Dashboard shows amber warning badge on the goal card
3. GoalTask page shows replan banner: "You're X tasks behind schedule"
4. User clicks "Adjust My Plan"
5. System analyzes completed progress, generates new tasks for remaining time
6. Old pending tasks removed, new adjusted tasks inserted
7. Adjustment history logged with explanation

### 4. Pausing and Resuming a Goal

1. User clicks "Pause" button on the goal task page
2. Goal status changes to "paused", reminders stop, tasks are disabled
3. Dashboard shows the goal with reduced opacity and "Paused" badge
4. When ready, user clicks "Resume" and sees the Resume Modal:
   - **Keep original deadline**: Tasks compressed into remaining time
   - **Set new end date**: Pick any future date (shorten or extend)
5. If deadline has already passed, "Keep original" is disabled with a message
6. If less than 5 days remain, a warning badge shows "Only X days left"
7. System regenerates tasks based on completed progress and remaining time

### 5. In-App Chat Guidance

1. User clicks "Ask AI" button on the goal page for goal-level guidance
2. Or clicks the chat icon on a specific task for task-level help
3. Chat drawer opens with streaming responses
4. User can ask follow-up questions; suggested questions provided
5. Full chat page available at `/goals/{id}/chat` with session history

### 6. Notifications

1. System checks for upcoming deadlines, overdue tasks, and completed milestones
2. Email notifications sent for important events
3. In-app notification bell shows unread count
4. User can mark notifications as read

---

## Testing

### Run All Tests

```bash
# Backend (352 tests)
cd backend
uv run pytest

# Frontend (65 tests)
cd frontend
npm run test -- --run
```

### Test Coverage

```bash
cd backend
uv run pytest --cov=. --cov-branch --cov-report=term-missing
```

Current coverage: **89% line coverage, 86% branch coverage**

### Test Breakdown

| Module | Unit Tests | Integration Tests | Total |
|--------|-----------|-------------------|-------|
| Goals (pause/resume, CRUD) | 27 | 23 | 50 |
| Replanning | 25 | - | 25 |
| Authentication | 20 | - | 20 |
| Chat | 72 | - | 72 |
| Notifications | 35 | - | 35 |
| Progress Summarizer | 11 | - | 11 |
| Onboarding/Roadmap | 22 | - | 22 |
| Models/Schemas/Utils | 17 | - | 17 |
| Workflows | 10 | - | 10 |
| Frontend (React) | 65 | - | 65 |
| **Total** | | | **417** |

### Test Categories

- **Unit tests**: Test individual functions with mocked dependencies (MagicMock)
- **Integration tests**: Test API endpoints with in-memory SQLite database (TestClient)
- **Frontend tests**: Component rendering and interaction tests (Vitest + React Testing Library)

---

## CI/CD Pipeline

The GitLab CI pipeline runs automatically on every push:

```
build          test                    run-dpy         submit-dcode     publish      deploy
+--------------+---------------------+---------------+---------------+------------+---------+
| backend-build| backend-test        | run-dpy-job   | submit-dcode  | publish    | deploy  |
| frontend-build| backend-test-coverage|              |               |            |         |
|              | frontend-test       |               |               |            |         |
+--------------+---------------------+---------------+---------------+------------+---------+
  All branches   All branches         All branches    All branches    main/develop  main/develop
  (on change)    (on change)          (backend only)  (backend only)
```

- **Build and test stages** run only when relevant files change (`backend/**/*` or `frontend/**/*`)
- **Publish and deploy** run only on `main` and `develop` branches

---

## Project Structure

```
group02/
├── backend/
│   ├── auth/                  # Authentication (login, register, verification, password reset)
│   ├── chat/                  # In-app chat with streaming
│   ├── clients/               # External service clients (LLM provider)
│   ├── core/                  # App foundation (DB session, base model, logging)
│   ├── domain/                # Domain constants (goal categories, statuses)
│   ├── goals/
│   │   ├── goal/              # Goal CRUD, pause/resume service and routes
│   │   ├── task/              # Task status and notes management
│   │   ├── models/            # SQLAlchemy models (Goal, Task, GoalAdjustment)
│   │   ├── progress/          # Progress summarizer for replanning context
│   │   ├── integrations/      # Web search service
│   │   ├── ai/                # Task generation service
│   │   └── roadmap/           # Personalized roadmap generation
│   ├── notifications/         # Email and in-app notifications
│   ├── onboarding/            # User preferences and initial setup
│   ├── replan/                # Adaptive replanning engine
│   │   ├── detect/            # Missed task detection
│   │   ├── check/             # Replan threshold check
│   │   ├── goal/              # Replan execution with task regeneration
│   │   └── routes/            # Replan API endpoints
│   ├── tests/                 # Shared test fixtures, model tests, workflow tests
│   ├── main.py                # FastAPI app entry point
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/             # React page components
│   │   ├── components/        # Shared components (Navbar, ChatDrawer, Toast)
│   │   ├── hooks/             # Custom React hooks (useChat, use_auth)
│   │   ├── services/          # API client services
│   │   └── utils/             # Shared utilities (designTokens, validators)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .gitlab-ci.yml
└── README.md
```

---

## Design Principles

For a detailed analysis of design principles, metrics, and examples, see [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md).

### Summary

| Principle | How It's Applied |
|-----------|-----------------|
| **Single Responsibility** | Each module has one purpose: `detect/service.py` only detects missed tasks, `check/service.py` only checks thresholds |
| **Open/Closed** | New goal categories can be added to `domain/goal_category.py` without modifying service logic |
| **Dependency Inversion** | Services depend on abstract DB session (`get_db`), not concrete connections |
| **DRY** | Shared utilities: `domain/goal_status.py` (status constants), `utils/designTokens.js` (frontend), `goals/ai/llm_service.py` (JSON parsing) |
| **Separation of Concerns** | Three-layer architecture: Router (HTTP) -> Service (Business Logic) -> Model (Data) |
| **High Cohesion** | `core/` contains only app foundation (DB, logging, base model). External clients separated to `clients/` |

### Key Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Line Coverage | 89% | > 80% |
| Branch Coverage | 86% | > 75% |
| Total Tests | 417 | - |
| Feature Concentration (core/) | Resolved | LCC < 0.5 |
| Longest Method | ~50 lines | < 60 |
| Max Function Parameters | 8 (resolved via dataclass) | <= 5 |
