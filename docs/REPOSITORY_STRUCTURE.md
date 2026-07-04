# Repository Structure Proposal

**System**: University Schedule Optimization Platform v2.0  
**Date**: 2026-06-29  
**Author**: Software Architect  

---

## 1. Current Structure (Problems)

```
proyecto/horarios_universidad/
├── frontend/                    # Vue 3 SPA — monolithic state, no router, hardcoded URLs
│   └── src/
│       ├── pages/               # 6 pages in flat directory, some unused
│       ├── components/          # 6 generic components, no domain separation
│       ├── views/               # DEAD CODE — DashboardView, SchedulerView never mounted
│       ├── router/index.js      # DEAD CODE — imported nowhere
│       ├── store/state.js       # localStorage-as-database — the real "persistence layer"
│       ├── services/api.js      # Hardcoded production URL
│       └── composables/         # 2 composables
├── src/scheduler/
│   ├── application/
│   │   ├── data_builder.py      # 48 hardcoded subjects, fake professors
│   │   └── services/run_pipeline.py
│   ├── config/settings.py       # Hardcoded defaults: seed=123, 6 days, 11 blocks
│   ├── infrastructure/
│   │   ├── database.py          # create_all, no migrations
│   │   ├── models.py            # 3 tables (Materia, Profesor, RunJob)
│   │   ├── optimization/
│   │   │   ├── model_builder.py # 400-line monolith with random data generation
│   │   │   ├── solver_runner.py
│   │   │   └── extractor.py     # Hardcoded day names
│   │   └── exporters/excel_exporter.py
│   └── interfaces/api/
│       ├── main.py              # 418-line monolith: routes + logic + job management
│       └── schemas.py
├── outputs/                     # Excel files committed to repo
├── requirements.txt             # Includes unused pymysql
└── pyproject.toml
```

**Key problems:**
- No tests directory at all
- Dead code (views/, router/)
- Output artifacts committed to git
- No Docker configuration
- No CI/CD configuration
- No environment separation
- Single monolithic API file
- Frontend has no type checking, no linting, no testing

---

## 2. Proposed Structure

```
proyecto/horarios_universidad/
│
├── backend/
│   ├── pyproject.toml                      # Single source of truth for dependencies
│   ├── alembic.ini                         # Database migration configuration
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/                       # Migration files (timestamped)
│   │
│   ├── src/
│   │   └── scheduler/
│   │       ├── __init__.py
│   │       │
│   │       ├── domain/                     # LAYER 1: Pure business logic
│   │       │   ├── __init__.py
│   │       │   ├── entities/               # Domain entities (dataclasses)
│   │       │   │   ├── __init__.py
│   │       │   │   ├── institution.py      # Institution, AcademicPeriod
│   │       │   │   ├── program.py          # Program, StudyPlan, PlanSubject
│   │       │   │   ├── subject.py          # Subject, SubjectGroup
│   │       │   │   ├── instructor.py       # Instructor, InstructorAvailability
│   │       │   │   ├── classroom.py        # Classroom, ClassroomEquipment
│   │       │   │   ├── schedule.py         # ScheduleType, TimeSlot, DayOfWeek
│   │       │   │   ├── offering.py         # AcademicOffering, OfferingLine
│   │       │   │   ├── schedule_run.py     # ScheduleRun, Assignment, SessionBlock
│   │       │   │   └── user.py             # User, Role
│   │       │   │
│   │       │   ├── value_objects/           # Immutable domain primitives
│   │       │   │   ├── __init__.py
│   │       │   │   ├── credit_hours.py     # CreditHours (1-6, validated)
│   │       │   │   ├── semester.py         # Semester (1-12, validated)
│   │       │   │   ├── session_pattern.py  # SessionPattern (how credits split into blocks)
│   │       │   │   └── time_range.py       # TimeRange (start_hour, end_hour)
│   │       │   │
│   │       │   ├── repositories/           # Abstract interfaces (ports)
│   │       │   │   ├── __init__.py
│   │       │   │   ├── institution_repo.py
│   │       │   │   ├── subject_repo.py
│   │       │   │   ├── instructor_repo.py
│   │       │   │   ├── classroom_repo.py
│   │       │   │   ├── offering_repo.py
│   │       │   │   ├── schedule_run_repo.py
│   │       │   │   └── user_repo.py
│   │       │   │
│   │       │   ├── services/               # Domain services (pure logic spanning entities)
│   │       │   │   ├── __init__.py
│   │       │   │   ├── offering_validator.py    # Validates offering against study plan
│   │       │   │   ├── conflict_detector.py     # Detects schedule conflicts
│   │       │   │   └── session_pattern_resolver.py  # Resolves credits → session blocks
│   │       │   │
│   │       │   └── exceptions.py           # Domain-specific exceptions
│   │       │
│   │       ├── application/                # LAYER 2: Use cases / orchestration
│   │       │   ├── __init__.py
│   │       │   ├── dtos/                   # Data Transfer Objects (input/output)
│   │       │   │   ├── __init__.py
│   │       │   │   ├── offering_dtos.py
│   │       │   │   ├── schedule_dtos.py
│   │       │   │   ├── solver_dtos.py      # SolverInput, SolverOutput
│   │       │   │   └── auth_dtos.py
│   │       │   │
│   │       │   ├── use_cases/              # One file per use case
│   │       │   │   ├── __init__.py
│   │       │   │   ├── create_offering.py
│   │       │   │   ├── validate_offering.py
│   │       │   │   ├── consolidate_offerings.py
│   │       │   │   ├── run_solver.py
│   │       │   │   ├── modify_schedule.py
│   │       │   │   ├── publish_schedule.py
│   │       │   │   ├── import_excel.py
│   │       │   │   └── export_schedule.py
│   │       │   │
│   │       │   └── services/               # Application services (cross-cutting)
│   │       │       ├── __init__.py
│   │       │       ├── solver_orchestrator.py   # Assembles SolverInput, dispatches to Celery
│   │       │       └── notification_service.py
│   │       │
│   │       ├── infrastructure/             # LAYER 3: External adapters
│   │       │   ├── __init__.py
│   │       │   ├── persistence/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── database.py         # Engine, session factory, connection config
│   │       │   │   ├── orm_models.py       # SQLAlchemy ORM models (~35 tables)
│   │       │   │   └── repositories/       # Concrete repository implementations
│   │       │   │       ├── __init__.py
│   │       │   │       ├── sqla_institution_repo.py
│   │       │   │       ├── sqla_subject_repo.py
│   │       │   │       ├── sqla_instructor_repo.py
│   │       │   │       ├── sqla_classroom_repo.py
│   │       │   │       ├── sqla_offering_repo.py
│   │       │   │       ├── sqla_schedule_run_repo.py
│   │       │   │       └── sqla_user_repo.py
│   │       │   │
│   │       │   ├── solver/                 # OR-Tools CP-SAT adapter
│   │       │   │   ├── __init__.py
│   │       │   │   ├── cpsat_adapter.py    # Implements SolverPort interface
│   │       │   │   ├── index_builder.py    # Precomputes lookup indices
│   │       │   │   ├── variable_factory.py # Creates boolean decision variables
│   │       │   │   ├── constraints/        # Constraint plugin registry
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── registry.py     # ConstraintRegistry with enable/disable
│   │       │   │   │   ├── base.py         # AbstractConstraint interface
│   │       │   │   │   ├── no_overlap_instructor.py
│   │       │   │   │   ├── no_overlap_room.py
│   │       │   │   │   ├── daily_limit.py
│   │       │   │   │   ├── weekly_limit.py
│   │       │   │   │   ├── instructor_availability.py
│   │       │   │   │   ├── room_capacity.py
│   │       │   │   │   ├── consecutive_slots.py
│   │       │   │   │   ├── same_room_sessions.py
│   │       │   │   │   └── preferred_time.py
│   │       │   │   │
│   │       │   │   ├── objectives/         # Objective function components
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── base.py         # AbstractObjective interface
│   │       │   │   │   ├── workload_balance.py
│   │       │   │   │   ├── preference_satisfaction.py
│   │       │   │   │   └── compactness.py
│   │       │   │   │
│   │       │   │   └── extractor.py        # Reads CP-SAT solution → SolverOutput
│   │       │   │
│   │       │   ├── importers/
│   │       │   │   ├── __init__.py
│   │       │   │   └── excel_importer.py   # Reads Excel offerings into DTOs
│   │       │   │
│   │       │   ├── exporters/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── excel_exporter.py   # Writes schedule to Excel
│   │       │   │   └── pdf_exporter.py     # Writes schedule to PDF
│   │       │   │
│   │       │   ├── auth/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── jwt_provider.py     # JWT token creation/validation
│   │       │   │   └── password_hasher.py  # bcrypt hashing
│   │       │   │
│   │       │   └── tasks/
│   │       │       ├── __init__.py
│   │       │       ├── celery_app.py       # Celery configuration
│   │       │       └── solver_task.py      # Celery task: run_solver
│   │       │
│   │       ├── interfaces/                 # LAYER 4: Entry points
│   │       │   ├── __init__.py
│   │       │   ├── api/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── app.py              # FastAPI app factory
│   │       │   │   ├── dependencies.py     # Dependency injection (repos, services)
│   │       │   │   ├── middleware/
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── auth.py         # JWT verification middleware
│   │       │   │   │   ├── tenant.py       # Tenant context middleware
│   │       │   │   │   └── error_handler.py
│   │       │   │   │
│   │       │   │   └── routes/             # One file per resource
│   │       │   │       ├── __init__.py
│   │       │   │       ├── auth.py         # POST /auth/login, POST /auth/refresh
│   │       │   │       ├── institutions.py # CRUD /institutions
│   │       │   │       ├── programs.py     # CRUD /programs
│   │       │   │       ├── subjects.py     # CRUD /subjects
│   │       │   │       ├── instructors.py  # CRUD /instructors
│   │       │   │       ├── classrooms.py   # CRUD /classrooms
│   │       │   │       ├── offerings.py    # CRUD /offerings + consolidation
│   │       │   │       ├── solver.py       # POST /solver/run, GET /solver/{id}
│   │       │   │       ├── schedules.py    # GET /schedules, PATCH modify, POST publish
│   │       │   │       ├── exports.py      # GET /exports/excel, GET /exports/pdf
│   │       │   │       └── health.py       # GET /health
│   │       │   │
│   │       │   └── cli/
│   │       │       ├── __init__.py
│   │       │       └── main.py             # Typer CLI for admin tasks
│   │       │
│   │       └── config/
│   │           ├── __init__.py
│   │           └── settings.py             # Pydantic Settings (from env vars)
│   │
│   └── tests/
│       ├── conftest.py                     # Shared fixtures (test DB, factories)
│       ├── factories/                      # Factory Boy factories for all entities
│       │   ├── __init__.py
│       │   └── ...
│       ├── unit/
│       │   ├── domain/                     # Pure domain logic tests
│       │   │   ├── test_session_pattern_resolver.py
│       │   │   ├── test_conflict_detector.py
│       │   │   └── test_offering_validator.py
│       │   └── solver/
│       │       ├── test_constraints/       # One test file per constraint
│       │       │   ├── test_no_overlap_instructor.py
│       │       │   ├── test_no_overlap_room.py
│       │       │   └── ...
│       │       ├── test_variable_factory.py
│       │       └── test_index_builder.py
│       ├── integration/
│       │   ├── test_repositories.py        # SQLAlchemy repos against real PostgreSQL
│       │   ├── test_solver_pipeline.py     # End-to-end solver execution
│       │   └── test_excel_import_export.py
│       └── api/
│           ├── test_auth.py
│           ├── test_offerings.py
│           ├── test_solver.py
│           └── test_schedules.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts                      # TypeScript Vite config
│   ├── tsconfig.json                       # TypeScript configuration
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       │
│       ├── router/
│       │   └── index.ts                    # Vue Router (actually used this time)
│       │
│       ├── stores/                         # Pinia stores (replace localStorage state)
│       │   ├── auth.ts                     # JWT tokens, user info, login/logout
│       │   ├── offerings.ts               # Academic offerings CRUD
│       │   ├── schedule.ts                # Active schedule, assignments
│       │   ├── institutions.ts            # Institution/program data
│       │   └── notifications.ts           # Toast/alert state
│       │
│       ├── services/
│       │   ├── api.ts                      # Axios instance with interceptors
│       │   └── websocket.ts               # WebSocket for solver progress
│       │
│       ├── composables/
│       │   ├── useAuth.ts                  # Auth guards, permission checks
│       │   ├── useScheduleConflicts.ts     # Conflict detection logic
│       │   └── usePagination.ts
│       │
│       ├── components/
│       │   ├── common/                     # Reusable UI primitives
│       │   │   ├── BaseButton.vue
│       │   │   ├── BaseInput.vue
│       │   │   ├── BaseModal.vue
│       │   │   ├── BaseTable.vue
│       │   │   ├── ToastContainer.vue
│       │   │   └── ProgressBar.vue
│       │   │
│       │   ├── schedule/                   # Schedule-specific components
│       │   │   ├── WeeklyCalendar.vue
│       │   │   ├── AssignmentCard.vue
│       │   │   ├── ConflictBadge.vue
│       │   │   └── SolverProgress.vue
│       │   │
│       │   └── layout/
│       │       ├── AppSidebar.vue
│       │       ├── AppHeader.vue
│       │       └── AppLayout.vue
│       │
│       ├── pages/                          # Route-level views
│       │   ├── LoginPage.vue
│       │   ├── DashboardPage.vue
│       │   ├── SubjectsPage.vue
│       │   ├── InstructorsPage.vue
│       │   ├── ClassroomsPage.vue
│       │   ├── OfferingsPage.vue
│       │   ├── SolverPage.vue
│       │   ├── SchedulePage.vue
│       │   ├── CalendarPage.vue
│       │   └── SettingsPage.vue
│       │
│       └── types/                          # TypeScript interfaces
│           ├── api.ts                      # API request/response types
│           ├── models.ts                   # Domain model interfaces
│           └── schedule.ts                 # Schedule-specific types
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml                  # PostgreSQL, Redis, backend, frontend, Celery worker
│
├── docs/                                   # Architecture & design documents
│   ├── AUDIT_REPORT.md
│   ├── ARCHITECTURE.md
│   ├── DOMAIN_MODEL.md
│   ├── SOLVER_DESIGN.md
│   ├── REPOSITORY_STRUCTURE.md
│   ├── ELIMINATION_PLAN.md
│   └── MIGRATION_ROADMAP.md
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml                  # pytest, ruff, mypy
│       └── frontend-ci.yml                # vitest, eslint, tsc
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Design Decisions

### 3.1 Monorepo with `backend/` and `frontend/`

The current structure has `frontend/` as a peer to `src/` at the project root, with `pyproject.toml` at root level. This blurs the boundary. Moving Python code into `backend/` with its own `pyproject.toml` makes each half independently buildable and deployable.

### 3.2 Clean Architecture Layers in `backend/src/scheduler/`

Four directories map directly to Clean Architecture layers:

| Directory | Layer | May import from | Never imports from |
|-----------|-------|-----------------|-------------------|
| `domain/` | Domain | stdlib only | application, infrastructure, interfaces |
| `application/` | Application | domain | infrastructure, interfaces |
| `infrastructure/` | Infrastructure | domain, application | interfaces |
| `interfaces/` | Interfaces | domain, application, infrastructure | — |

This is enforced by convention during code review, and can be enforced by import-linter in CI.

### 3.3 One File Per Use Case

Each use case (`create_offering.py`, `run_solver.py`, etc.) contains a single class with an `execute()` method. This keeps files small (50-150 lines each), makes it trivial to find the business logic for any workflow, and prevents the 418-line monolith problem.

### 3.4 Constraint Plugin Architecture

Constraints are individual files in `infrastructure/solver/constraints/`. Each implements `AbstractConstraint` with a `name`, `apply(model, variables, indices)` method, and optional `enabled` flag. The `ConstraintRegistry` discovers them, allows per-run enable/disable via configuration, and passes them to the solver adapter in order. Adding a new constraint = adding one file + registering it. No existing code changes.

### 3.5 Pinia Stores Replace localStorage State

The `state.js` file (with its localStorage migrations) is replaced by Pinia stores that talk to the API. The API is the single source of truth — the frontend caches state in Pinia, not in localStorage.

### 3.6 TypeScript for Frontend

The current frontend has zero type safety. Converting to TypeScript catches API contract mismatches at build time and provides autocompletion for the 35-entity domain model.

### 3.7 Tests as First-Class Directory

The `tests/` directory mirrors the source structure. Domain tests are pure (no DB, no framework). Integration tests hit a real PostgreSQL instance. API tests use FastAPI's TestClient. Solver constraint tests each create a minimal model and verify one constraint in isolation.

---

## 4. Files to Delete

These files are dead code or artifacts that should not exist in the new structure:

| File | Reason |
|------|--------|
| `frontend/src/views/DashboardView.vue` | Dead code — never mounted |
| `frontend/src/views/SchedulerView.vue` | Dead code — never mounted |
| `frontend/src/router/index.js` | Dead code — imported nowhere |
| `outputs/*.xlsx` | Build artifacts — should be in `.gitignore` |
| `outputs/~$*.xlsx` | Excel temp lock files — should never be committed |
| `requirements.txt` | Superseded by `pyproject.toml` |

### Files to Move and Rename

| Current Path | New Path | Notes |
|-------------|----------|-------|
| `src/scheduler/` | `backend/src/scheduler/` | Under backend root |
| `frontend/` | `frontend/` | Stays at same level |
| `pyproject.toml` | `backend/pyproject.toml` | Backend-scoped |
| `src/scheduler/infrastructure/models.py` | `backend/src/scheduler/infrastructure/persistence/orm_models.py` | Expanded to ~35 tables |
| `src/scheduler/infrastructure/database.py` | `backend/src/scheduler/infrastructure/persistence/database.py` | Same role |
| `src/scheduler/infrastructure/optimization/` | `backend/src/scheduler/infrastructure/solver/` | Renamed for clarity |
| `src/scheduler/interfaces/api/main.py` | Split into `app.py` + `routes/*.py` | No more monolith |
| `src/scheduler/config/settings.py` | `backend/src/scheduler/config/settings.py` | Pydantic Settings |

---

## 5. New Dependencies

### Backend (`pyproject.toml`)

```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "psycopg[binary]>=3.2",      # psycopg3, replaces psycopg2-binary
    "ortools>=9.10",
    "pandas>=2.2",
    "openpyxl>=3.1",
    "pydantic>=2.9",
    "pydantic-settings>=2.5",
    "python-jose[cryptography]>=3.3",  # JWT
    "passlib[bcrypt]>=1.7",
    "celery[redis]>=5.4",
    "python-dotenv>=1.0",
    "python-multipart>=0.0.9",    # File uploads
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",               # TestClient for async FastAPI
    "factory-boy>=3.3",
    "ruff>=0.6",                 # Linter + formatter
    "mypy>=1.11",
    "import-linter>=2.0",        # Enforce layer boundaries
    "pre-commit>=3.8",
]
```

**Removed**: `pymysql` (unused), `requests` (unused).  
**Added**: `alembic`, `celery[redis]`, JWT libraries, testing tools.

### Frontend (`package.json`)

```json
{
  "dependencies": {
    "vue": "^3.5",
    "vue-router": "^4.4",
    "pinia": "^2.2",
    "axios": "^1.7",
    "xlsx": "^0.18"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0",
    "typescript": "^5.6",
    "vue-tsc": "^2.1",
    "vite": "^8.0",
    "tailwindcss": "^3.4",
    "autoprefixer": "^10.5",
    "@tailwindcss/forms": "^0.5",
    "vitest": "^2.1",
    "@vue/test-utils": "^2.4",
    "eslint": "^9.11",
    "@typescript-eslint/parser": "^8.7"
  }
}
```

**Removed**: Nothing critical.  
**Added**: `vue-router`, `pinia`, `axios`, TypeScript, testing tools.

---

## 6. .gitignore Additions

```gitignore
# Python
__pycache__/
*.pyc
*.egg-info/
dist/
.venv/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/

# Frontend
node_modules/
frontend/dist/

# Outputs (never commit generated files)
outputs/
*.xlsx
~$*

# Environment
.env
.env.local
.env.production

# Docker
docker/data/

# IDE
.vscode/
.idea/
```

---

## 7. CI/CD Configuration Sketch

### `.github/workflows/backend-ci.yml`

Triggers on push/PR touching `backend/**`:
1. Set up Python 3.12
2. Install dependencies with `pip install -e ".[dev]"`
3. `ruff check .` — lint
4. `ruff format --check .` — formatting
5. `mypy src/` — type checking
6. Start PostgreSQL service container
7. `pytest tests/` — all tests

### `.github/workflows/frontend-ci.yml`

Triggers on push/PR touching `frontend/**`:
1. Set up Node 20
2. `npm ci`
3. `npx eslint src/` — lint
4. `npx vue-tsc --noEmit` — type check
5. `npx vitest run` — tests
6. `npm run build` — verify build succeeds

---

*End of document.*
