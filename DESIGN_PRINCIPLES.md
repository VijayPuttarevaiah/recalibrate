# Design Principles Analysis

This document explains how SOLID principles, cohesion, coupling, and clean code practices are followed in the Adaptive Goal Planner application, with concrete examples and metric values.

---

## 1. SOLID Principles

### Single Responsibility Principle (SRP)

Each module has exactly one reason to change.

**Example -- Replan module decomposition:**

```
replan/
├── detect/service.py    # Only detects missed tasks (6 lines)
├── check/service.py     # Only checks if replan is needed (15 lines)
├── goal/service.py      # Only executes replanning
└── routes/router.py     # Only defines HTTP endpoints
```

`detect_missed_tasks()` does one thing -- finds pending tasks past their due date:

```python
# replan/detect/service.py
def detect_missed_tasks(db: Session, goal_id: int) -> list[Task]:
    today = date.today()
    return (
        db.query(Task)
        .filter(Task.goal_id == goal_id, Task.status == "pending", Task.due_date < today)
        .order_by(Task.due_date)
        .all()
    )
```

If detection logic changes (e.g., add grace period), only this file changes. Check logic, replan logic, and routes are unaffected.

### Open/Closed Principle (OCP)

New goal categories can be added to `domain/goal_category.py` without modifying any service code:

```python
# domain/goal_category.py
class GoalCategory(str, Enum):
    CAREER_AND_LEARNING = "career_and_learning"
    FITNESS = "fitness"
    IMMIGRATION = "immigration"
    # To add a new category, add one line here -- no service changes needed
```

New goal statuses can be added to `domain/goal_status.py`:

```python
# domain/goal_status.py
GOAL_STATUSES = {"pending", "in_progress", "completed", "paused"}
TASK_STATUSES = {"pending", "completed", "missed", "skipped"}
```

### Liskov Substitution Principle (LSP)

The `GoalResponse` and `GoalWithTasksResponse` schemas maintain proper IS-A relationship:

```python
class GoalResponse(BaseModel):
    id: int
    title: str
    status: str
    paused_at: datetime | None = None
    task_count: int = 0

class GoalWithTasksResponse(BaseModel):
    # Same fields as GoalResponse + tasks list
    tasks: list[TaskResponse] = Field(default_factory=list)
```

Any code expecting `GoalResponse` fields will work with `GoalWithTasksResponse`.

### Interface Segregation Principle (ISP)

Routes depend only on the specific service functions they need:

```python
# goals/goal/router.py -- imports only what it uses
from goals.goal.service import create_goal_with_tasks, get_user_goals, get_goal_tasks, pause_goal, resume_goal
```

The `get_db` dependency is a minimal interface -- just yields a session:

```python
def get_db():
    session = DBSession().SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

### Dependency Inversion Principle (DIP)

High-level modules depend on abstractions, not concrete implementations:

```python
# Router depends on abstract get_db, not concrete DBSession
@router.get("/goals/")
def get_goals_api(
    current_user: dict = Depends(get_current_user),  # abstract auth
    db: Session = Depends(get_db),                     # abstract DB
):
    return get_user_goals(db, current_user["user_id"])
```

In tests, these dependencies are overridden with test doubles:

```python
# tests/fixtures/db_fixtures.py
app.dependency_overrides[get_db] = override_get_db          # in-memory SQLite
app.dependency_overrides[get_current_user] = lambda: {"user_id": 1}  # mock user
```

---

## 2. Cohesion

### High Cohesion (Good)

**`core/` module** -- All three files serve the same purpose (app foundation):

| File | Purpose | Related? |
|------|---------|----------|
| `base.py` | SQLAlchemy Base class | Yes -- DB foundation |
| `db_session.py` | Database connection management | Yes -- DB foundation |
| `logging_config.py` | Application-wide logging setup | Yes -- App foundation |

**LCC (Lack of Component Cohesion) = 0.0** -- all modules are related.

Previously `core/` also contained `password.py` (auth utility) and `llm_client.py` (external API client), giving **LCC = 1.0** (Feature Concentration smell). These were moved to `auth/utils/` and `clients/` respectively.

### Module Cohesion Examples

| Module | Files | Cohesion | Rationale |
|--------|-------|----------|-----------|
| `core/` | 3 | High | All DB/logging foundation |
| `clients/` | 1 | High | Only external API clients |
| `domain/` | 2 | High | Only domain constants |
| `replan/detect/` | 1 | High | Only missed task detection |
| `auth/utils/` | 3 | High | Only auth helpers (password, email, JWT) |

---

## 3. Coupling

### Low Coupling Architecture

Dependencies flow in one direction: **Router -> Service -> Model**

```
Router (HTTP layer)
  │
  ▼
Service (Business logic)
  │
  ▼
Model (Data layer)
```

No module imports from a module that imports it back. Verified import chains:

```
goals/goal/service.py → replan/goal/service.py (for generate_resume_tasks)
replan/goal/service.py → goals/progress/summarizer.py (for build_progress_summary)
replan/goal/service.py → goals/ai/llm_service.py (for shared JSON parsing)
```

All one-directional. No circular dependencies.

### Shared Constants (Single Source of Truth)

Instead of hardcoding statuses in multiple files:

```python
# domain/goal_status.py -- imported by both goal service and task router
GOAL_STATUSES = {"pending", "in_progress", "completed", "paused"}
PAUSABLE_GOAL_STATUSES = {"pending", "in_progress"}
TASK_STATUSES = {"pending", "completed", "missed", "skipped"}
```

---

## 4. Clean Code Practices

### Named Constants (No Magic Numbers)

```python
# goals/goal/service.py
CHUNK_DAYS = 29  # Each chunk spans ~30 days to keep prompts within token limits

# replan/goal/service.py
MAX_MISSED_TITLES_FOR_PROMPT = 10
EXPLANATION_TEMPERATURE = 0.3
TASK_GENERATION_TEMPERATURE = 0.2
```

### Comments Explain "Why", Not "What"

```python
# Single research pass avoids redundant API calls across chunks
research_context = gather_research(goal_data.goal, goal_data.category, goal_data.notes)

# Chunking keeps each prompt within token limits for longer goals
while current_start <= goal_data.end_date:
```

### Meaningful Variable Names

```python
# Before (single-letter)
for t in tasks:
    task = Task(goal_id=goal.id, title=t["title"])

# After (descriptive)
for task_data in tasks:
    db.add(Task(goal_id=goal.id, title=task_data["title"]))
```

### Structured Logging (No Print Statements)

```python
# Using LogManager instead of print()
logger = LogManager.get_logger()
logger.info(f"Researching: {goal_data.goal} [{goal_data.category}]")
logger.info(f"Generated {len(tasks)} tasks for {current_start} -> {current_end}")
```

---

## 5. Testing Practices

### Test Pyramid

```
        /\
       /  \    Integration tests (23) -- TestClient + in-memory SQLite
      /    \
     /------\
    /        \  Unit tests (329) -- MagicMock, isolated, fast
   /          \
  /____________\
```

### FIRST Properties

| Property | How We Achieve It |
|----------|-------------------|
| **Fast** | Unit tests use MagicMock (no DB/network). Full suite runs in 5 seconds |
| **Independent** | Each test creates its own data. No shared mutable state |
| **Repeatable** | Fixed dates in tests (e.g., `date(2026, 6, 30)`), no `date.today()` |
| **Self-validating** | Every test has explicit `assert` statements |
| **Timely** | Tests written before code (RED-GREEN-REFACTOR commits) |

### Arrange-Act-Assert Pattern

Every test follows AAA:

```python
def test_pause_active_goal(self, auth_client, db_session):
    # Arrange
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="in_progress")

    # Act
    resp = auth_client.patch(f"/goals/{goal.id}/pause")

    # Assert
    assert resp.status_code == HTTP_200_OK
    assert resp.json()["status"] == "paused"
```

### Test Doubles Used

| Double Type | Usage | Example |
|-------------|-------|---------|
| **Mock** | Simulate DB and external services | `db = MagicMock()` |
| **Patch** | Replace service functions | `@patch("goals.goal.service.generate_resume_tasks")` |
| **Fake** | In-memory database for integration tests | `engine = create_engine("sqlite:///:memory:")` |
| **Fixture** | Reusable test setup | `auth_client` fixture provides authenticated TestClient |

---

## 6. Architectural Smell Resolution

### Feature Concentration (Resolved)

**Before:** `core/` had 5 unrelated modules (LCC = 1.0):
- base.py, db_session.py, logging_config.py, password.py, llm_client.py

**After:** Split into cohesive packages:
- `core/` -- base.py, db_session.py, logging_config.py (LCC near 0)
- `clients/` -- llm_client.py
- `auth/utils/` -- password.py

### DRY Violations (Resolved)

**Before:** JSON parsing functions duplicated in `goals/ai/llm_service.py` and `replan/goal/service.py`

**After:** Replan service imports shared functions:
```python
from goals.ai.llm_service import _strip_code_fences, extract_json, _validate_task_list
```

**Before:** Status colors and API fetch duplicated in Dashboard.jsx and GoalTask.jsx

**After:** Extracted to shared `utils/designTokens.js`:
```javascript
import { apiFetch, statusColor, statusBg, formatDate } from "../utils/designTokens";
```
