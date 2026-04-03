# Adaptive Goal Planner

A full-stack goal planning application that helps users create, track, pause, and resume personal goals with intelligent task generation and adaptive replanning.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [How to Run](#how-to-run)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Use Case Scenarios](#use-case-scenarios)
- [Testing](#testing)
- [TDD Commit History](#tdd-commit-history)
- [CI/CD Pipeline](#cicd-pipeline)
- [Project Structure](#project-structure)
- [Design Principles and Metrics](#design-principles-and-metrics)

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

### Backend Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework for REST API |
| uvicorn | ASGI server |
| sqlalchemy | ORM for database access |
| alembic | Database migrations |
| pydantic | Request/response validation |
| pyjwt / python-jose | JWT authentication |
| bcrypt / passlib | Password hashing |
| pymysql | MySQL database driver |
| httpx | HTTP client for external API calls |
| loguru | Structured logging |
| pytest / pytest-cov | Testing and code coverage |
| python-dotenv | Environment variable loading |
| openai | API client for task generation |
| google-genai | Alternative provider client |

### Frontend Dependencies

| Package | Purpose |
|---------|---------|
| react / react-dom | UI framework |
| react-router-dom | Client-side routing |
| vite | Build tool and dev server |
| axios | HTTP client |
| vitest | Test runner |
| @testing-library/react | Component testing utilities |
| jsdom | Browser environment for tests |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (v2+)
- (For manual setup only) Python >= 3.11 with [uv](https://docs.astral.sh/uv/), Node.js >= 20

---

## How to Run

### Option 1: Docker (Recommended)

This is the easiest way to run the entire application with a single command.

```bash
# 1. Clone the repository
git clone <repository-url>
cd group02

# 2. Create the backend environment file
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys (see Environment Variables section)

# 3. Build and start all services (backend + frontend + database)
docker compose up --build -d

# 4. Verify all containers are running
docker compose ps
```

After startup, the application is available at:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | React application served by Nginx |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **MySQL** | localhost:3306 | Database (user: `user`, password: `password`) |

**Useful Docker commands:**

```bash
# View backend logs
docker compose logs -f api

# View frontend logs
docker compose logs -f frontend

# Stop all services
docker compose down

# Stop and remove all data (reset database)
docker compose down -v

# Rebuild after code changes
docker compose up --build -d
```

### Option 2: Manual Setup (Development)

#### Step 1: Start MySQL

You need a running MySQL 8.0 instance. Using Docker for just the database:

```bash
docker compose up db -d
```

Or create the database manually:

```sql
CREATE DATABASE backend_db;
CREATE USER 'user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON backend_db.* TO 'user'@'%';
```

#### Step 2: Start Backend

```bash
cd backend

# Install uv (Python package manager)
pip install uv

# Install all dependencies
uv sync --frozen

# Create environment file and add API keys
cp .env.example .env

# Start the backend server (auto-reloads on code changes)
uv run uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000

#### Step 3: Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server (auto-reloads on code changes)
npm run dev
```

Frontend runs at http://localhost:5173 (development mode with hot reload).

To build for production:

```bash
npm run build
# Output in frontend/dist/ — can be served with any static file server or Nginx
```

---

## Environment Variables

Create `backend/.env` with the following variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | MySQL connection string | `mysql+pymysql://user:password@localhost:3306/backend_db` |
| `OPENROUTER_API_KEY` | Yes | API key for task generation and chat | `sk-or-v1-...` |
| `SERPER_API_KEY` | Yes | API key for web research during goal creation | `abc123...` |
| `GOOGLE_API_KEY` | No | Google API key (alternative provider) | `AIza...` |
| `LLM_MODEL` | No | Model identifier (default: `openai/gpt-4o-mini`) | `openai/gpt-4o-mini` |
| `SMTP_USER` | No | Email address for sending notifications | `user@gmail.com` |
| `SMTP_PASSWORD` | No | Email app password for notifications | `xxxx xxxx xxxx xxxx` |

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
| GET | `/goals/{id}/replan/check` | Check if goal needs replanning (threshold query param) |
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

### 6. Onboarding and Personalized Roadmap

1. After first login, user is guided through the onboarding flow
2. User selects experience level, preferred hours per week, and focus areas
3. System generates a personalized multi-phase roadmap
4. Roadmap is saved and accessible from the dashboard

### 7. Notifications

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

### Code Coverage

```bash
# Line and branch coverage report
cd backend
uv run pytest --cov=. --cov-branch --cov-report=term-missing
```

| Metric | Value |
|--------|-------|
| **Line Coverage** | 89% |
| **Branch Coverage** | 86% |
| **Backend Tests** | 352 |
| **Frontend Tests** | 65 |
| **Total** | **417** |

### Test Breakdown

| Module | Unit | Integration | Total |
|--------|------|-------------|-------|
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

### Test Types

- **Unit tests** -- Test individual functions with mocked dependencies (`MagicMock`). Fast, isolated, no DB or network.
- **Integration tests** -- Test full API endpoints using `TestClient` with an in-memory SQLite database. Verify router-service-model layers work together.
- **Frontend tests** -- Component rendering and user interaction tests using Vitest and React Testing Library.

---

## TDD Commit History

All new features were developed following the Red-Green-Refactor TDD cycle. Each RED commit introduces a failing test, each GREEN commit adds the minimal code to pass it, and each REFACTOR commit improves code quality without changing behavior.

### Pause/Resume Goal Feature

| Hash | Phase | Description |
|------|-------|-------------|
| `28ff1a9` | RED | Add failing tests for pause/resume goal with smart regeneration |
| `53ba6d7` | GREEN | Implement pause/resume goal with smart task regeneration |
| `db713e8` | GREEN | Add frontend pause/resume UI with ResumeModal and disabled tasks |
| `47cd4a2` | REFACTOR | Add tests for _get_user_goal helper extraction |
| `d75f94f` | GREEN | Handle resume after deadline passed |
| `ba3c888` | RED | Add failing tests for resume improvements |
| `3ca7131` | GREEN | Skip web research on resume and allow flexible end dates |
| `c13921d` | GREEN | Add remaining days warning and flexible date picker |

### Replanning Engine

| Hash | Phase | Description |
|------|-------|-------------|
| `222f61a` | RED | Add failing tests for detect_missed_tasks |
| `9a8947e` | GREEN | Implement detect_missed_tasks |
| `f04e3cc` | REFACTOR | Extract default threshold as named parameter |
| `45be3eb` | RED | Add failing tests for check_goal_needs_replan |
| `66ad12d` | GREEN | Implement check_goal_needs_replan |
| `19d1be4` | RED | Add failing tests for replan_goal |
| `eec5450` | GREEN | Implement replan_goal ownership check and guards |
| `03d9135` | REFACTOR | Abort with 502 and preserve plan when generation fails |

### Task Management

| Hash | Phase | Description |
|------|-------|-------------|
| `66a12ad` | RED | Add failing tests for task status update |
| `42bb179` | GREEN | Implement update_task_status with validation |
| `b06cfd2` | REFACTOR | Extract _get_user_task helper |
| `74fd175` | RED | Add failing tests for task notes and batch update |
| `e8be577` | GREEN | Implement task notes and batch update |
| `66e74b0` | REFACTOR | Batch update uses single commit |

### Progress Summarizer

| Hash | Phase | Description |
|------|-------|-------------|
| `6e005a2` | RED | Add failing tests for build_progress_summary |
| `c007425` | GREEN | Implement build_progress_summary and format_summary_for_llm |
| `f4fd2b5` | REFACTOR | Cap missed tasks at 20 in output |

### Replan Routes

| Hash | Phase | Description |
|------|-------|-------------|
| `9a8a791` | RED | Add failing tests for replan routes |
| `45a6239` | GREEN | Implement check/trigger/history routes |
| `9e75f68` | REFACTOR | Routes are thin, history ordered DESC |

### Code Quality Refactors

| Hash | Phase | Description |
|------|-------|-------------|
| `4d4ab3c` | REFACTOR | Apply DRY and SRP across backend and frontend |
| `2a23411` | REFACTOR | Apply clean code practices across codebase |
| `5a17208` | REFACTOR | Resolve Feature Concentration smell in core module |
| `5303f5a` | REFACTOR | Unify UI consistency across all pages |

---

## CI/CD Pipeline

The GitLab CI pipeline runs automatically on every push:

```
build              test                     run-dpy          submit-dcode      publish       deploy
+----------------+----------------------+----------------+----------------+-------------+----------+
| backend-build  | backend-test         | run-dpy-job    | submit-dcode   | publish     | deploy   |
| frontend-build | backend-test-coverage|                |                |             |          |
|                | frontend-test        |                |                |             |          |
+----------------+----------------------+----------------+----------------+-------------+----------+
  All branches     All branches           All branches     All branches     main/develop  main/develop
  (on change)      (on change)            (backend only)   (backend only)
```

- **Build and test stages** run only when relevant files change (`backend/**/*` or `frontend/**/*`)
- **Publish and deploy** run only on `main` and `develop` branches
- **Code quality** (DPy/DCode) runs on all branches for backend changes

---

## Project Structure

```
group02/
├── backend/
│   ├── auth/                  # Authentication (login, register, verification, password reset)
│   ├── chat/                  # In-app chat with streaming
│   ├── clients/               # External service clients
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

## Design Principles and Metrics

### SOLID Principles

#### Single Responsibility (SRP)

Each module has exactly one reason to change. The replan engine is split into focused modules:

- `replan/detect/service.py` (6 lines) -- only detects missed tasks
- `replan/check/service.py` (15 lines) -- only checks if replan threshold is met
- `replan/goal/service.py` -- only executes replanning
- `replan/routes/router.py` -- only defines HTTP endpoints

If detection logic changes (e.g., add grace period), only `detect/service.py` changes. Check logic, replan logic, and routes are unaffected.

#### Open/Closed (OCP)

New goal categories can be added to `domain/goal_category.py` without modifying any service code:

```python
class GoalCategory(str, Enum):
    CAREER_AND_LEARNING = "career_and_learning"
    FITNESS = "fitness"
    IMMIGRATION = "immigration"
    # Add new categories here -- no service changes needed
```

#### Dependency Inversion (DIP)

Services depend on abstract `get_db` dependency, not concrete database connections. In tests, this is overridden with an in-memory SQLite database:

```python
# Production: real MySQL via dependency injection
db: Session = Depends(get_db)

# Tests: overridden with in-memory SQLite
app.dependency_overrides[get_db] = override_with_sqlite
```

#### Separation of Concerns

Three-layer architecture enforced throughout:

```
Router (HTTP) --> Service (Business Logic) --> Model (Data)
```

Routes never contain `db.query()` calls. Services never return HTTP responses. Models never contain business logic.

### Cohesion and LCOM

**LCOM (Lack of Cohesion of Methods)** measures how related the methods in a module are. Lower is better (0 = perfectly cohesive).

| Module | Files | LCOM | Status |
|--------|-------|------|--------|
| `core/` (base, db_session, logging) | 3 | ~0 | Cohesive -- all app foundation |
| `clients/` (llm_client) | 1 | 0 | Cohesive -- single responsibility |
| `domain/` (goal_category, goal_status) | 2 | 0 | Cohesive -- domain constants |
| `replan/detect/` | 1 | 0 | Cohesive -- single function |
| `auth/utils/` (password, email, auth) | 3 | ~0 | Cohesive -- all auth helpers |

**Resolved smell:** `core/` previously had LCOM = 1.0 (Feature Concentration) because it contained `password.py` and `llm_client.py` alongside DB code. These were moved to `auth/utils/` and `clients/` respectively, reducing LCOM to near 0.

### Coupling

Dependencies flow in one direction only (no circular imports):

```
goals/goal/service.py --> replan/goal/service.py (for generate_resume_tasks)
replan/goal/service.py --> goals/progress/summarizer.py (for progress summary)
replan/goal/service.py --> goals/ai/llm_service.py (for shared JSON parsing)
```

Shared constants avoid cross-module duplication:

```python
# domain/goal_status.py -- single source of truth, imported by service and router
GOAL_STATUSES = {"pending", "in_progress", "completed", "paused"}
TASK_STATUSES = {"pending", "completed", "missed", "skipped"}
```

### DRY (Don't Repeat Yourself)

| What was duplicated | Where | Resolution |
|---------------------|-------|------------|
| JSON parsing (strip fences, extract array, validate) | `goals/ai/llm_service.py` and `replan/goal/service.py` | Replan imports from `goals/ai/llm_service` |
| Status constants | `goal/service.py` and `task/router.py` | Centralized in `domain/goal_status.py` |
| `statusColor()`, `apiFetch()`, `formatDate()` | `Dashboard.jsx` and `GoalTask.jsx` | Extracted to `utils/designTokens.js` |

### Clean Code Practices

| Practice | Example |
|----------|---------|
| Named constants | `CHUNK_DAYS = 29` instead of magic number `timedelta(days=29)` |
| Why-comments | `# Single research pass avoids redundant API calls across chunks` |
| Meaningful names | `task_data` instead of `t`, `goal` instead of `g` |
| Structured logging | `logger.info(...)` instead of `print()` |
| No double negatives | All conditions use positive logic |

### Code Smell Reports

Code smell analysis is performed using **Designite DPy** in the CI/CD pipeline. Reports are generated as pipeline artifacts on every push and can be downloaded from the GitLab pipeline page under the `run-dpy-job` artifacts.

**How to access:**
1. Go to the GitLab project -> Build -> Pipelines
2. Click on the latest pipeline
3. Find the `run-dpy-job` job
4. Click "Download artifacts" -> `smells/` folder contains all CSV reports

**Report files generated:**

| File | Smell Category | Description |
|------|---------------|-------------|
| `ArchitectureSmells.csv` | Architecture | Feature Concentration, Cyclic Dependencies, God Component |
| `DesignSmells.csv` | Design | Long Method, Long Parameter List, Multifaceted Abstraction |
| `ImplementationSmells.csv` | Implementation | Long Statement, Magic Number, Complex Conditional |

Each CSV contains the detected smell instances. Below is a summary of smells detected and their justification:

#### Architecture Smells

| Smell | Location | Status | Justification |
|-------|----------|--------|---------------|
| Feature Concentration in `core/` | `core/` module | Resolved | Moved `password.py` to `auth/utils/` and `llm_client.py` to `clients/`. Now `core/` has LCOM near 0 with only DB and logging. |

#### Design Smells

| Smell | Location | Status | Justification |
|-------|----------|--------|---------------|
| Long Statement in `LLMClient` | `clients/llm_client.py` | False positive | DPy measures runtime string length. Actual max line is 88 chars (under 120 limit). |
| Long Method in `resume_goal` | `goals/goal/service.py` | Acceptable | ~50 lines for an orchestration function that coordinates progress summary, task generation, deletion, and insertion. Further splitting would scatter related logic. |

#### Implementation Smells

| Smell | Location | Status | Justification |
|-------|----------|--------|---------------|
| Magic Number `29` | `goals/goal/service.py`, `replan/goal/service.py` | Resolved | Replaced with named constant `CHUNK_DAYS = 29` with comment explaining the 30-day chunking strategy. |
| Long Statement | Various | False positive | DPy counts expanded f-string length at runtime, not source line length. All source lines are under 120 chars. |

### Key Metrics Summary

| Metric | Value | Target |
|--------|-------|--------|
| Line Coverage | 89% | > 80% |
| Branch Coverage | 86% | > 75% |
| Total Tests | 417 | - |
| Backend Unit Tests | 329 | - |
| Integration Tests | 23 | - |
| Frontend Tests | 65 | - |
| LCOM (core/) | ~0 (resolved from 1.0) | < 0.5 |
| Longest Method | ~50 lines | < 60 |
| Max Function Parameters | 5 | <= 5 |
