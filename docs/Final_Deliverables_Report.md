# Adaptive Goal Planner -- Final Deliverables Report

## Team Members

| Name | Role |
|------|------|
| Vijay Puttarevaiah | Full-Stack Developer, DevOps |
| Manavraj Karansinh Thakor | Full-Stack Developer |
| Hinesh Jayeshkumar Patel | Backend Developer, Frontend Auth |
| Aditya Natvarbhai Lad | Backend Developer, Workflows |

---

## Project Summary

| Metric | Value |
|--------|-------|
| Total Story Points | 51 |
| Story Points Completed | 48 |
| User Story Coverage | 94% |
| Total Tests | 417 (352 backend + 65 frontend) |
| Line Coverage | 87% |
| Branch Coverage | 85% |
| Merged MRs | 33 |
| Total Commits | 255 |

---

## Sprint Overview

| Sprint | Duration | Stories Completed |
|--------|----------|-------------------|
| Sprint 1 | Jan 26 -- Feb 9 | System Setup, Architecture, Auth, Goal Category Detection |
| Sprint 2 | Feb 10 -- Feb 23 | Goal Creation, Notifications |
| Sprint 3 | Feb 26 -- Mar 11 | Plan Adjustment, Progress Tracking, Bug Fixes |
| Sprint 4 | Mar 12 -- Mar 25 | Roadmap, Chat, Pause/Resume, Task Notes, Workflows |
| Sprint 5 | Mar 26 -- Apr 3 | Smell Reduction, Deployment, Documentation |

---

## User Stories -- Detailed Breakdown

### Story 1: System Setup and Requirement Gathering

| | Details |
|---|---|
| **Issue** | #1 |
| **Story Points** | 0 |
| **Sprint** | Sprint 1 |
| **Status** | Closed |
| **Assigned To** | Aditya, Hinesh, Manav, Vijay |
| **Description** | Requirement discussions, scope definition, risk identification, and tech stack agreement. No development effort required. |

---

### Story 2: System Architecture

| | Details |
|---|---|
| **Issue** | #2 |
| **Story Points** | 1 |
| **Sprint** | Sprint 1 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Layered architecture design (router/service/model); React project initialization; folder structure organization; routing and layout setup; Docker + CI/CD pipeline configuration |

**Story Point Rationale:** Lightweight overall (1 SP). Effort limited to application scaffolding and architectural planning without complex logic.

---

### Story 3: User Accounts and Secure Access

| | Details |
|---|---|
| **Issue** | #3 |
| **Story Points** | 4 |
| **Sprint** | Sprint 1 |
| **Status** | Closed |
| **Assigned To** | Aditya, Hinesh |
| **Supported Features** | JWT-based authentication; Register/Login/Logout; Password hashing (bcrypt); Password reset with email verification; Token blacklisting on logout; Protected routes; Session persistence |

**Key Files:**
- Backend: `auth/login/`, `auth/register/`, `auth/logout/`, `auth/email_verification/`, `auth/password_reset/`, `auth/utils/auth.py`, `auth/utils/password.py`
- Frontend: `Login.jsx`, `Register.jsx`, `ForgotPassword.jsx`, `ResetPassword.jsx`, `SetNewPassword.jsx`, `VerifyEmail.jsx`, `VerifyResetCode.jsx`, `AuthContext.jsx`, `use_auth.js`

**Story Point Rationale:** Security implementation required multiple screens, state management, protected routing, encryption, token management, and authorization middleware. 4 SP justified due to complexity across both layers.

---

### Story 4: Goal Category Detection and Model Selection

| | Details |
|---|---|
| **Issue** | #5 |
| **Story Points** | 4 |
| **Sprint** | Sprint 1 |
| **Status** | Closed |
| **Assigned To** | Manav, Vijay |
| **Supported Features** | Goal text processing and category detection (Career, Fitness, Immigration); Model routing logic; Database category storage; Category display in UI without exposing system logic |

**Key Files:**
- Backend: `goals/category/service.py`, `goals/category/router.py`, `clients/llm_client.py`, `domain/goal_category.py`
- Frontend: `CreateGoal.jsx`

**Story Point Rationale:** Core business logic involving algorithmic text processing and model selection. Backend-heavy with category abstraction. 4 SP justified.

---

### Story 5: Goal Creation and Timeline Definition

| | Details |
|---|---|
| **Issue** | #4 |
| **Story Points** | 6 |
| **Sprint** | Sprint 2 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Natural language goal input parsing; Timeline/deadline validation; 30-day chunk batching for task generation; Web research integration; Task generation via external service; Dashboard display with progress bars |

**Key Files:**
- Backend: `goals/goal/service.py`, `goals/goal/router.py`, `goals/ai/llm_service.py`, `goals/integrations/web_search_service.py`
- Frontend: `CreateGoal.jsx`, `Dashboard.jsx`

**Story Point Rationale:** Core user-facing feature involving form handling, validation, research integration, chunk-based task generation, and dashboard rendering. 6 SP justified due to high complexity.

---

### Story 6: Progress Tracking and Task Completion

| | Details |
|---|---|
| **Issue** | #11 |
| **Story Points** | 3 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Vijay |
| **Supported Features** | Task status updates (pending/completed/missed/skipped); Task notes with whitespace sanitization; Batch status updates; Progress bar calculation; Filter tasks by status |

**Key Files:**
- Backend: `goals/task/router.py`, `domain/goal_status.py`
- Frontend: `GoalTask.jsx` (TaskCard, FilterPill components)
- Tests: `test_task_status_update.py`, `test_task_notes_batch.py`

**Story Point Rationale:** Multiple task operations with validation, batch processing, and frontend filter/progress UI. 3 SP justified.

---

### Story 7: Adaptive Plan Adjustment

| | Details |
|---|---|
| **Issue** | #12 |
| **Story Points** | 4 |
| **Sprint** | Sprint 3 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Missed task detection; Replan threshold check (configurable); Progress-aware task regeneration; Safety abort when generation fails (502); Adjustment history logging; Trade-off explanation generation |

**Key Files:**
- Backend: `replan/detect/service.py`, `replan/check/service.py`, `replan/goal/service.py`, `replan/routes/router.py`
- Frontend: `GoalTask.jsx` (ReplanBanner, AdjustmentHistory components)
- Tests: `test_detect_missed.py`, `test_check_replan.py`, `test_replan_goal.py`, `test_replan_routes.py`

**Story Point Rationale:** Complex multi-step orchestration: detect, summarize, generate, delete, insert, explain, log. 4 SP justified.

---

### Story 8: Smart Reminders and Notifications

| | Details |
|---|---|
| **Issue** | #13 |
| **Story Points** | 5 |
| **Sprint** | Sprint 2 |
| **Status** | Closed |
| **Assigned To** | Hinesh |
| **Supported Features** | Background scheduler for daily checks; Overdue task detection; Upcoming deadline alerts; Completed task notifications; Email notifications via SMTP; In-app notification bell with unread count; Mark notifications as read |

**Key Files:**
- Backend: `notifications/services/notification_service.py`, `notifications/services/reminder_service.py`, `notifications/routers/notifications.py`
- Frontend: Notification bell component in Navbar
- Tests: `test_notification_service.py`, `test_notification_router.py`, `test_reminder_service.py`

**Story Point Rationale:** Scheduler logic, timezone handling, deduplication, email integration, and frontend notification UI. 5 SP justified.

---

### Story 9: Personalized Step-by-Step Roadmap Generation

| | Details |
|---|---|
| **Issue** | #10 |
| **Story Points** | 4 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Hinesh |
| **Supported Features** | Onboarding preference collection (experience level, hours/week, focus areas); Agent-based roadmap generation (coding, fitness, immigration, career agents); Multi-phase roadmap display; Preferences stored for future access |

**Key Files:**
- Backend: `onboarding/services/preference_service.py`, `onboarding/routers/onboarding_router.py`, `goals/roadmap/service.py`, `goals/roadmap/router.py`
- Frontend: `Onboarding.jsx`, `Roadmap.jsx`
- Tests: `test_preference_service.py`, `test_onboarding_router.py`, `test_roadmap_service.py`, `test_roadmap_api.py`

**Story Point Rationale:** Multiple agent types, preference storage, and multi-phase roadmap generation. 4 SP justified.

---

### Story 10: Goal Analytics and Insights Dashboard

| | Details |
|---|---|
| **Issue** | #14 |
| **Story Points** | 2 |
| **Sprint** | Sprint 3 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Progress summarizer with monthly stats; Completion rate calculation; Missed task tracking; Compact progress context for replanning; Behind-schedule indicators on dashboard |

**Key Files:**
- Backend: `goals/progress/summarizer.py`
- Frontend: `Dashboard.jsx` (StatCard, BehindBadge, GoalCard components)
- Tests: `test_progress_summarizer.py`

**Story Point Rationale:** Statistics calculation and LLM-friendly formatting. 2 SP justified.

---

### Story 11: Multiple Goals Management

| | Details |
|---|---|
| **Issue** | #15 |
| **Story Points** | 2 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Dashboard grid with multiple goal cards; Per-goal task counts; Per-goal replan status checks; Category-based icons and color coding |

**Key Files:**
- Backend: `goals/goal/service.py` (get_user_goals)
- Frontend: `Dashboard.jsx`

**Story Point Rationale:** Goal list with per-goal metadata aggregation. 2 SP justified.

---

### Story 12: Goal Pause and Resume

| | Details |
|---|---|
| **Issue** | #16 |
| **Story Points** | 3 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Vijay |
| **Supported Features** | Pause active goals (status, timestamp); Resume with two modes: keep-original-deadline or set-new-end-date; Task regeneration based on completed progress; Deadline-passed handling (disable keep-original); Remaining days warning (badge when < 5 days); Disabled task interactions when paused; Paused goal styling on dashboard (reduced opacity, grey badge); Replan check skips paused goals |

**Key Files:**
- Backend: `goals/goal/service.py` (pause_goal, resume_goal), `goals/goal/schemas.py` (GoalResumeRequest), `goals/goal/router.py`
- Frontend: `GoalTask.jsx` (ResumeModal, pause/resume buttons, paused banner)
- Tests: `test_pause_resume_goal.py` (27 tests), `test_integration_goal_endpoints.py` (23 tests)

**TDD Commits:**

| Hash | Phase | Description |
|------|-------|-------------|
| `28ff1a9` | RED | Add failing tests for pause/resume |
| `53ba6d7` | GREEN | Implement pause/resume with task regeneration |
| `db713e8` | GREEN | Add frontend UI with ResumeModal |
| `47cd4a2` | REFACTOR | Extract _get_user_goal helper |
| `ba3c888` | RED | Add failing tests for resume improvements |
| `3ca7131` | GREEN | Skip web research, allow flexible dates |
| `c13921d` | GREEN | Add remaining days warning |

**Story Point Rationale:** Full-stack feature: backend service with two resume modes, schema validation, frontend modal with date picker, task disabling, deadline detection, and comprehensive test coverage (50 tests). 3 SP justified.

---

### Story 15: Contextual Learning and Resource Support

| | Details |
|---|---|
| **Issue** | #19 |
| **Story Points** | 3 |
| **Sprint** | Sprint 4 |
| **Status** | Open (In Progress) |
| **Assigned To** | Manav |
| **Description** | Contextual learning resources and support features. Partially implemented. |

---

### Story 16: In-App AI Guidance for Understanding Goals and Tasks

| | Details |
|---|---|
| **Issue** | #60 |
| **Story Points** | 5 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Goal-level and task-level chat sessions; Streaming responses (SSE); Session history and management; Quick task explanations; Suggested follow-up questions; Chat drawer and full-page chat |

**Key Files:**
- Backend: `chat/services/chat_service.py`, `chat/routers/chat_router.py`, `chat/models/chat_models.py`
- Frontend: `ChatPage.jsx`, `ChatDrawer.jsx`, `ChatInput.jsx`, `ChatMessage.jsx`, `SuggestionChips.jsx`, `useChat.js`, `Chatapi.js`
- Tests: `test_chat_service.py` (45 tests), `test_chat_router.py` (15 tests), `test_chat_models.py`, `test_chat_schemas.py`

**Story Point Rationale:** Complex streaming implementation, session management, rate limiting, multiple UI components. 5 SP justified.

---

### Story 16 (Task Notes): Task Completion Notes

| | Details |
|---|---|
| **Issue** | #51 |
| **Story Points** | 2 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Manav |
| **Supported Features** | Add/update task notes; Whitespace sanitization; Notes modal with character limit; Batch task updates |

**Key Files:**
- Backend: `goals/task/router.py`
- Frontend: `GoalTask.jsx` (NotesModal component)

**Story Point Rationale:** CRUD operations with validation and modal UI. 2 SP justified.

---

### Agentic Workflow Implementation

| | Details |
|---|---|
| **Issue** | #32 |
| **Story Points** | 3 |
| **Sprint** | Sprint 4 |
| **Status** | Closed |
| **Assigned To** | Aditya |
| **Supported Features** | Goal creation workflow with state management; Replan workflow with research and task generation; Workflow orchestration using LangGraph |

**Key Files:**
- Backend: `workflows/goal_creation_workflow.py`, `workflows/replan_workflow.py`
- Tests: `test_goal_creation_workflow.py`, `test_replan_workflow.py`

**Story Point Rationale:** Complex state machine design with multiple nodes and transitions. 3 SP justified.

---

## Story Points by Team Member

| Team Member | Stories | Story Points |
|-------------|---------|-------------|
| **Manav** | Architecture, Goal Creation, Plan Adjustment, Analytics Dashboard, Multiple Goals, AI Chat, Task Notes, Category Detection | 1 + 6 + 4 + 2 + 2 + 5 + 2 + 2 = **24 SP** |
| **Vijay** | Category Detection, Progress Tracking, Goal Pause/Resume, CI/CD, Smell Reduction, Deployment | 2 + 3 + 3 = **8 SP** |
| **Hinesh** | User Accounts, Notifications, Roadmap Generation | 2 + 5 + 4 = **11 SP** |
| **Aditya** | User Accounts, Agentic Workflows | 2 + 3 = **5 SP** |
| **All** | System Setup | 0 SP |
| **Total** | | **48 SP** |

---

## Deployment

| Environment | Frontend | Backend API | API Docs |
|-------------|----------|-------------|----------|
| **Development** | http://18.117.130.226:8081 | http://18.117.130.226:8073 | http://18.117.130.226:8073/docs |
| **Production** | http://18.117.130.226:8082 | http://18.117.130.226:8074 | http://18.117.130.226:8074/docs |

**Infrastructure:** AWS EC2 t3.micro (us-east-2), Docker containers, MySQL 8.0

---

## CI/CD Pipeline

| Stage | Jobs | Trigger |
|-------|------|---------|
| build | backend-build, frontend-build | All branches (on change) |
| test | backend-test, backend-test-coverage, frontend-test | All branches (on change) |
| run-dpy | run-dpy-job (code smell analysis) | All branches (backend only) |
| submit-dcode | submit-dcode-job (quality submission) | All branches (backend only) |
| publish | publish (Docker Hub push) | main/develop only |
| deploy | deploy (SSH to EC2) | main/develop only |

---

## Code Quality

### Test Summary

| Category | Count |
|----------|-------|
| Backend Unit Tests | 329 |
| Backend Integration Tests | 23 |
| Frontend Tests | 65 |
| **Total** | **417** |

### Coverage

| Metric | Value |
|--------|-------|
| Line Coverage | 87% |
| Branch Coverage | 85% |

### Code Smell Analysis (DPy)

Reports with justification columns stored in `docs/smells/`:

| Category | Detected | Status |
|----------|----------|--------|
| Architecture smells | 0 | Clean |
| Design smells | 46 | All justified |
| Implementation smells | 280 | Mostly false positives (Long Statement from f-string expansion) |

### Design Principles

| Principle | Application |
|-----------|------------|
| Single Responsibility | Each module has one purpose (e.g., detect/ only detects, check/ only checks) |
| Open/Closed | New categories added to domain/goal_category.py without modifying services |
| Dependency Inversion | Services depend on abstract get_db, overridden in tests with SQLite |
| DRY | Shared constants (domain/goal_status.py), shared utils (designTokens.js) |
| High Cohesion | core/ has LCOM near 0 (only DB + logging). Feature Concentration resolved. |
| Low Coupling | One-directional dependencies: Router -> Service -> Model |

---

## Repository Artifacts

| Artifact | Location |
|----------|----------|
| Root README | `README.md` |
| Final Report | `docs/Final_Deliverables_Report.md` |
| Architecture Smells | `docs/smells/ArchitectureSmells.csv` |
| Design Smells | `docs/smells/backend_design_smells.csv` |
| Implementation Smells | `docs/smells/backend_implementation_smells.csv` |
| Class/Module Metrics | `docs/smells/backend_class_module_metrics.csv` |
| Function Metrics | `docs/smells/backend_function_metrics.csv` |
| CI/CD Pipeline | `.gitlab-ci.yml` |
| Docker Config | `docker-compose.yml` |

---

## Risks and Mitigation

| Risk | Mitigation |
|------|-----------|
| External API rate limiting | Retry mechanism; resume skips web research to reduce API calls |
| Task generation failure | Safety abort: if generation returns empty, abort with 502 without modifying existing plan |
| Stale tasks after long pause | Resume regenerates tasks based on actual completed progress |
| Security vulnerabilities | JWT blacklisting; bcrypt password hashing; authorization middleware |
| EC2 IP changes on restart | Pipeline and CI/CD variables updated; Elastic IP recommended |
| Docker Hub rate limits | Retry failed jobs; shared runner limitation documented |
