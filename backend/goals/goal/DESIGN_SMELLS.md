# Design Smell Analysis — Pause/Resume Goal Feature

**Story**: As a user, I want to pause my goal temporarily and resume later without losing progress.

---

## 1. Smells Present in Our Code

### 1.1 Hub-like Modularization

**Where**: `goals/goal/service.py`

**Why**: The `goal_service` module has dependencies on **6 external modules** — `Goal`, `Task`, `generate_resume_tasks` (from replan), `gather_research` (from integrations), `build_progress_summary` and `format_summary_for_llm` (from progress). The `resume_goal` function orchestrates LLM task generation, web research, progress summarization, task deletion, and task insertion — all in one function.

**Mitigation**: We kept this acceptable by reusing existing infrastructure (`generate_resume_tasks`, `build_progress_summary`) rather than duplicating logic. The alternative would be a dedicated `ResumeOrchestrator` class, but that would introduce **Unnecessary Abstraction** for a single call site.

---

### 1.2 Multifaceted Abstraction

**Where**: `goals/goal/service.py`

**Why**: The `goal_service` module handles **three distinct responsibilities**: (1) CRUD operations (`get_user_goals`, `get_goal_tasks`, `create_goal_with_tasks`), (2) pause logic (`pause_goal`), and (3) resume logic with LLM orchestration (`resume_goal`). These are conceptually different facets of goal management.

**Mitigation**: We chose to keep them together because they all operate on the same `Goal` model and share `_get_user_goal`. Splitting into `pause_service.py` and `resume_service.py` would fragment closely related code and create **Insufficient Modularization** (too-small modules with high coupling).

---

### 1.3 Missing Abstraction (Minor)

**Where**: `statusColor()` and `statusBg()` functions in both `Dashboard.jsx` and `GoalTask.jsx`

**Why**: Goal status-to-color mapping is duplicated across two frontend files. Adding the `"paused"` status required editing both files identically. This is a clump of encoded strings that could be a shared constant or utility.

**Mitigation**: The duplication is limited to two simple switch statements. Extracting a shared `statusStyles.js` module is a valid improvement but was not done to avoid scope creep beyond the acceptance criteria.

---

## 2. Smells NOT Present in Our Code (and Why)

### 2.1 Deficient Encapsulation — NOT PRESENT

Our `_get_user_goal` helper is prefixed with `_` (private by convention). Internal fields like `PAUSABLE_STATUSES` are module-level constants, not exposed on a class. The `GoalResumeRequest` schema uses Pydantic validators to enforce invariants (e.g., `new_end_date` required when mode is `"new_end_date"`, must be after original deadline) — the validation logic is encapsulated within the schema, not scattered across callers.

### 2.2 Broken Hierarchy — NOT PRESENT

We do not use class inheritance in the pause/resume feature. `GoalResumeRequest` is a standalone Pydantic schema, not a subclass of another request model. There are no supertype/subtype relationships that could violate substitutability.

### 2.3 Cyclically-dependent Modularization — NOT PRESENT

The dependency flow is strictly one-directional:
- `router` → `service` → `model`
- `goal.service` → `replan.service` (for `generate_resume_tasks`)
- `goal.service` → `progress.summarizer` (for `build_progress_summary`)

No module imports from a module that imports it back. We verified this by checking import chains — `replan.goal.service` does **not** import from `goals.goal.service`.

### 2.4 Unnecessary Abstraction — NOT PRESENT

We avoided creating abstractions that would only be used once:
- No `PauseManager` class — `pause_goal` is a simple function
- No `ResumeStrategy` pattern — the two modes (`keep_original` vs `new_end_date`) are handled by a single `if/else`, not a strategy hierarchy
- No `TaskRegenerator` wrapper — we reuse `generate_resume_tasks` directly

### 2.5 Insufficient Modularization — NOT PRESENT

Each module has a clear, bounded scope:
- `goal_models.py`: Goal ORM model (7 columns)
- `schemas.py`: Request/response Pydantic models
- `service.py`: Business logic functions
- `router.py`: HTTP endpoint definitions
- `test_pause_resume_goal.py`: 23 focused test cases

The `resume_goal` function is ~50 lines — complex but not excessively long for an orchestration function.

### 2.6 Incomplete Abstraction — NOT PRESENT

Complementary operations are fully implemented:
- `pause_goal` has a matching `resume_goal`
- `GoalResumeRequest` validates both modes completely
- The frontend provides both Pause and Resume buttons with appropriate state transitions
- Replan service handles paused goals consistently (check returns `false`, replan rejects with 400)

### 2.7 Imperative Abstraction — NOT PRESENT

We did not turn any operation into a single-method class. All new code uses plain functions (`pause_goal`, `resume_goal`, `_get_user_goal`, `generate_resume_tasks`), which is idiomatic Python.

### 2.8 Unutilized Abstraction — NOT PRESENT

Every new abstraction is used:
- `PAUSABLE_STATUSES` is used by `pause_goal`
- `GoalResumeRequest` is used by the resume route
- `generate_resume_tasks` is called by `resume_goal`
- `_get_user_goal` is shared by both `pause_goal` and `resume_goal`
- `ResumeModal` React component is rendered conditionally in `GoalTask.jsx`

### 2.9 Duplicate Abstraction — NOT PRESENT

We avoided creating duplicate abstractions:
- `generate_resume_tasks` has a **distinct prompt** from `_generate_replan_tasks` — one says "user fell behind schedule", the other says "user paused and is resuming". They share `_call_llm_for_tasks` internally.
- `_get_user_goal` in goal_service is distinct from `_get_goal_or_404` in replan_service — they serve different modules with different import contexts. Merging them would create a cross-module dependency.

### 2.10 Broken Hierarchy — NOT PRESENT

No inheritance hierarchies exist in the pause/resume code. `GoalResponse` and `GoalWithTasksResponse` share fields via Pydantic composition (the latter extends the former's field set), maintaining proper IS-A semantics.

---

## Summary

| Smell | Status | Location |
|-------|--------|----------|
| Missing Abstraction | Minor — status color duplication | Dashboard.jsx, GoalTask.jsx |
| Deficient Encapsulation | Not present | — |
| Hub-like Modularization | Present (acceptable) | goal_service.py resume_goal |
| Broken Hierarchy | Not present | — |
| Cyclically-dependent Modularization | Not present | — |
| Multifaceted Abstraction | Present (acceptable) | goal_service.py |
| Unnecessary Abstraction | Not present | — |
| Insufficient Modularization | Not present | — |
| Incomplete Abstraction | Not present | — |
| Imperative Abstraction | Not present | — |
| Unutilized Abstraction | Not present | — |
| Duplicate Abstraction | Not present | — |
