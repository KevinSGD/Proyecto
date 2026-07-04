# Migration Roadmap — Phase 2 to Phase 3 Transition Plan

**System**: University Schedule Optimization Platform v2.0  
**Date**: 2026-06-29  
**Author**: Technical Lead  
**Purpose**: Consolidated planning document. Covers modular solver architecture, documentation standards, migration strategy, and phase-by-phase implementation plan. This document is the single reference needed to begin Phase 3 implementation.

---

## Table of Contents

1. [Guiding Principles](#1-guiding-principles)
2. [Migration Strategy](#2-migration-strategy)
3. [Modular Solver Architecture](#3-modular-solver-architecture)
4. [Documentation Standards](#4-documentation-standards)
5. [Phase-by-Phase Implementation Plan](#5-phase-by-phase-implementation-plan)
6. [Risk Register](#6-risk-register)
7. [Definition of Done](#7-definition-of-done)
8. [Deliverable Checklist](#8-deliverable-checklist)

---

## 1. Guiding Principles

These rules govern every implementation decision during the migration:

1. **The prototype stays operational.** At no point does the existing system break. New code lives in the new structure alongside old code until the old code is explicitly deprecated.

2. **Database is truth.** Every piece of data that currently lives in Python literals, JavaScript localStorage, or configuration dicts moves to PostgreSQL. No exceptions.

3. **Solver is a pure function.** The solver receives a DTO, returns a DTO. It never opens a database connection, never reads a config file, never generates random data. If it needs data, the caller provides it.

4. **Layers never cross upward.** Domain does not import from Application. Application does not import from Infrastructure. Infrastructure does not import from Interfaces. Violations are caught by `import-linter` in CI.

5. **One entity of change.** Each pull request addresses one concern. "Add Instructor entity + repository + migration" is one PR. "Add Instructor entity + classroom entity + solver constraint" is three PRs.

6. **Tests before trust.** No module is considered complete without test coverage. Domain logic gets unit tests. Repositories get integration tests against real PostgreSQL. API routes get HTTP-level tests.

---

## 2. Migration Strategy

### 2.1 Branch Strategy

```
main (production - current prototype)
  └── feat/v2-foundation          ← Phase 0
       └── feat/v2-domain         ← Phase 1
            └── feat/v2-solver    ← Phase 2
                 └── feat/v2-auth ← Phase 3
                      └── feat/v2-frontend ← Phase 4
                           └── feat/v2-hardening ← Phase 5-6
```

Each phase branches from the previous phase's branch. Merges go upward only when the phase is complete and tested. `main` continues serving the prototype until Phase 6 merges.

### 2.2 Coexistence Plan

During migration, the repository contains both old and new code:

```
proyecto/horarios_universidad/
├── backend/                    # NEW — Clean Architecture
│   ├── src/scheduler/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   └── tests/
├── src/scheduler/              # OLD — Prototype (read-only after Phase 0)
│   ├── application/
│   ├── config/
│   ├── infrastructure/
│   └── interfaces/
└── frontend/                   # Incrementally migrated in place
```

The old `src/scheduler/` directory is preserved unchanged as a reference throughout the migration. It is never modified — only read. It gets deleted in the final Phase 6 cleanup.

### 2.3 Database Migration

**Step 1**: The new backend uses a separate database (`scheduler_v2`) during development. The old database (`scheduler` / whatever the prototype uses) is untouched.

**Step 2**: Alembic manages all schema changes in the new database. The initial migration creates the full 35-table schema from DOMAIN_MODEL.md.

**Step 3**: A one-time data migration script (`scripts/migrate_data.py`) reads from the old database (3 tables) and the frontend localStorage export, then writes to the new schema. This script is run once when switching over.

**Step 4**: After Phase 6 validation, the old database is archived and decommissioned.

### 2.4 Frontend Migration

The frontend migrates in place (same `frontend/` directory) because:
- The Vue SPA framework stays the same (Vue 3)
- Tailwind CSS stays the same
- Components are incrementally converted

Migration steps:
1. Add TypeScript, Vue Router, Pinia, Axios to dependencies
2. Convert `main.js` → `main.ts`, set up router and Pinia
3. Convert store/state.js → Pinia stores (one by one)
4. Convert pages to use API calls instead of localStorage
5. Add new pages for new features (Offerings, Settings)
6. Delete dead code (views/, old router)

At each step, the app remains functional. New features (auth, multi-role UI) are added behind Vue Router guards that only activate when connected to the new backend.

---

## 3. Modular Solver Architecture

The solver is decomposed into 8 modules, each with a single responsibility. They execute in a linear pipeline.

### 3.1 Module Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SOLVER PIPELINE                              │
│                                                                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  LOADER  │─>│ VALIDATOR │─>│ ENTITIES │─>│ VARIABLE FACTORY  │  │
│  └──────────┘  └───────────┘  └──────────┘  └─────────┬─────────┘  │
│                                                        │            │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌─────────▼─────────┐  │
│  │PUBLISHER │<─│STATISTICS │<─│OPTIMIZER │<─│   CONSTRAINTS     │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────────┘  │
│                                                                     │
│                     + OBJECTIVE (feeds into OPTIMIZER)               │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Module Specifications

#### Module 1: Loader (`solver/loader.py`)

**Input**: `SolverInput` DTO (from application layer)  
**Output**: Internal `SolverData` with indexed arrays  
**Responsibility**: Converts DTOs into numpy-friendly indexed structures. Builds lookup maps (instructor_id → index, room_id → index, slot → (day, hour) tuple). No CP-SAT dependency.

```python
class SolverData:
    groups: list[GroupData]
    instructors: list[InstructorData]
    rooms: list[RoomData]
    time_slots: list[TimeSlotData]
    # Index maps
    instructor_index: dict[str, int]
    room_index: dict[str, int]
    slot_index: dict[tuple[int, int], int]  # (day, hour) → flat index
    # Candidate maps
    group_candidates: dict[int, list[int]]  # group_idx → [instructor_idx, ...]
    group_rooms: dict[int, list[int]]       # group_idx → [room_idx, ...]
```

#### Module 2: Validator (`solver/validator.py`)

**Input**: `SolverData`  
**Output**: `SolverData` (unchanged) or raises `SolverValidationError`  
**Responsibility**: Checks preconditions before building the model. Fails fast with clear messages.

Validations:
- Every group has at least one candidate instructor
- Every group has at least one compatible room
- Session patterns are consistent with available time slots
- No instructor has zero availability
- Room count ≥ 1

#### Module 3: Entities (`solver/entities.py`)

**Input**: `SolverData`  
**Output**: Named dataclasses used internally by constraints and objective  
**Responsibility**: Defines the internal solver types (not DTOs, not ORM models). These are the types that constraint modules receive.

```python
@dataclass(frozen=True)
class GroupVar:
    group_idx: int
    instructor_vars: dict[int, BoolVar]     # instructor_idx → y[g,p]
    session_vars: list[SessionBlockVar]
    
@dataclass(frozen=True)
class SessionBlockVar:
    block_idx: int
    start_vars: dict[tuple[int, int, int], BoolVar]  # (day, hour, room) → start[b,d,h,s]
    cover_vars: dict[tuple[int, int, int], BoolVar]   # (day, hour, room) → x[b,d,h,s]
```

#### Module 4: Variable Factory (`solver/variable_factory.py`)

**Input**: `SolverData` + CP-SAT `CpModel`  
**Output**: `SolverVariables` — all boolean decision variables  
**Responsibility**: Creates the CP-SAT boolean variables. This is the only module that calls `model.NewBoolVar()`. Variables are organized into the `GroupVar` / `SessionBlockVar` structures.

#### Module 5: Constraints (`solver/constraints/`)

**Input**: `CpModel`, `SolverVariables`, `SolverData`  
**Output**: Side effect — constraints added to model  
**Responsibility**: Each constraint is a separate file implementing `AbstractConstraint`:

```python
class AbstractConstraint(ABC):
    name: str
    description: str
    enabled: bool = True
    
    @abstractmethod
    def apply(self, model: CpModel, variables: SolverVariables, data: SolverData) -> None:
        ...
```

**Constraint catalog** (initial set, preserving current solver's mathematical structure):

| Constraint | File | What it enforces |
|-----------|------|-----------------|
| InstructorNoOverlap | `no_overlap_instructor.py` | One instructor teaches at most one group per time slot |
| RoomNoOverlap | `no_overlap_room.py` | One room hosts at most one group per time slot |
| DailyLimit | `daily_limit.py` | Instructor teaches ≤ N sessions per day |
| WeeklyLimit | `weekly_limit.py` | Instructor teaches ≤ M sessions per week |
| SessionCover | `session_cover.py` | start → cover linkage (if block starts at d,h then slots d,h through d,h+len-1 are covered) |
| OneStart | `one_start.py` | Each session block starts exactly once |
| InstructorAssignment | `instructor_assignment.py` | Each group assigned exactly one instructor |
| InstructorAvailability | `instructor_availability.py` | Sessions only in instructor's available slots |
| RoomCapacity | `room_capacity.py` | Group enrollment ≤ room capacity |
| RoomEquipment | `room_equipment.py` | Room has required equipment for subject |
| ConsecutiveSlots | `consecutive_slots.py` | Session blocks occupy consecutive time slots |
| SameRoom | `same_room.py` | All blocks of one group use the same room |

**Constraint Registry** (`constraints/registry.py`):

```python
class ConstraintRegistry:
    def __init__(self):
        self._constraints: list[AbstractConstraint] = []
    
    def register(self, constraint: AbstractConstraint) -> None: ...
    def enable(self, name: str) -> None: ...
    def disable(self, name: str) -> None: ...
    def apply_all(self, model, variables, data) -> dict[str, bool]: ...
```

Adding a new constraint:
1. Create `solver/constraints/my_new_constraint.py`
2. Implement `AbstractConstraint`
3. Register in `constraints/__init__.py`
4. Done — no other files change

#### Module 6: Objective (`solver/objectives/`)

**Input**: `CpModel`, `SolverVariables`, `SolverData`  
**Output**: Side effect — objective terms added to model  
**Responsibility**: Each objective component is a separate file implementing `AbstractObjective`:

```python
class AbstractObjective(ABC):
    name: str
    weight: float = 1.0
    
    @abstractmethod
    def terms(self, variables: SolverVariables, data: SolverData) -> list[tuple[BoolVar, int]]:
        ...
```

Objective components:
- `WorkloadBalance` — minimizes max-min workload spread across instructors
- `PreferenceSatisfaction` — maximizes sum of instructor preference scores
- `Compactness` — penalizes gaps between an instructor's sessions on the same day

The `ObjectiveBuilder` collects all terms with weights and calls `model.Maximize(sum)`.

#### Module 7: Optimizer (`solver/optimizer.py`)

**Input**: `CpModel` (with variables, constraints, objective already added)  
**Output**: `CpSolver` with solution status  
**Responsibility**: Configures solver parameters (time limit, num workers, seed) and calls `solver.Solve(model)`. Implements solution callbacks for progress reporting.

```python
class OptimizerConfig:
    max_time_seconds: int = 300
    num_workers: int = 4
    random_seed: int | None = None
    log_search_progress: bool = False

class OptimizerResult:
    status: SolverStatus  # optimal, feasible, infeasible, timeout
    wall_time: float
    objective_value: float | None
    solver: CpSolver  # needed by Extractor to read variable values
```

#### Module 8: Extractor & Publisher

**Extractor** (`solver/extractor.py`):  
**Input**: `CpSolver`, `SolverVariables`, `SolverData`  
**Output**: `SolverOutput` DTO  
**Responsibility**: Reads the solution values from the CP-SAT solver and constructs the output DTO. Maps indices back to entity IDs using `SolverData` index maps.

**Publisher** (not in solver — lives in `application/use_cases/publish_schedule.py`):  
**Input**: `SolverOutput` DTO  
**Output**: Persisted `ScheduleRun` + `Assignment` + `SessionBlock` records  
**Responsibility**: Writes the solver output to the database. This is explicitly NOT part of the solver module — it's an application layer concern.

### 3.3 Statistics

The solver pipeline produces statistics at each stage:

```python
@dataclass
class SolverStatistics:
    # Input stats
    groups_total: int
    instructors_total: int
    rooms_total: int
    time_slots_total: int
    
    # Model stats
    num_variables: int
    num_constraints: int
    constraints_by_type: dict[str, int]
    
    # Solution stats
    status: SolverStatus
    groups_scheduled: int
    objective_value: float
    elapsed_seconds: float
    
    # Quality metrics
    workload_spread: float          # max - min instructor load
    avg_preference_score: float
    room_utilization_pct: float
    instructor_utilization_pct: float
```

---

## 4. Documentation Standards

### 4.1 Code Documentation

**Rule**: Default to writing no comments. Only add one when the WHY is non-obvious.

**Allowed comments** (one line max):
```python
# RLS policy filters by institution_id set in session context
# CP-SAT requires all coefficients as integers; scale floats by 1000
# Alembic can't detect column type changes; must drop+recreate
```

**Forbidden comments**:
```python
# This function creates a new instructor          (WHAT, not WHY)
# Added in PR #42 to fix the offering bug          (belongs in git, not code)
# TODO: refactor this later                        (do it now or create an issue)
# Used by the CreateOffering use case              (caller info rots)
```

### 4.2 Module Docstrings

Each Python module (`__init__.py` of a package, or standalone `.py` file with a single class) may have a one-line module docstring if the filename alone is ambiguous:

```python
"""CP-SAT adapter implementing the SolverPort interface."""
```

No multi-paragraph docstrings. No parameter documentation (type hints handle that). No return value documentation.

### 4.3 Type Hints

All public functions must have complete type hints. Use Python 3.10+ syntax:

```python
def find_by_id(self, id: UUID) -> Instructor | None: ...
def list_active(self, institution_id: UUID) -> list[Instructor]: ...
```

### 4.4 API Documentation

FastAPI auto-generates OpenAPI/Swagger docs from Pydantic models and route decorators. No separate API documentation files. The Pydantic models ARE the documentation:

```python
class CreateOfferingRequest(BaseModel):
    period_id: UUID
    area_id: UUID
    lines: list[OfferingLineRequest]

class OfferingLineRequest(BaseModel):
    subject_id: UUID
    num_groups: int = Field(ge=1, le=20)
    expected_enrollment: int = Field(ge=1, le=500)
    modality: Modality
```

### 4.5 Migration Documentation

Each Alembic migration file includes a one-line description in the `revision` message:

```python
"""create instructor and instructor_availability tables"""
revision = "20260701_001"
```

### 4.6 Architecture Decision Records (ADRs)

For decisions that are not obvious from the code, create a short ADR in `docs/adr/`:

```markdown
# ADR-001: Use Celery Instead of Python Threads for Solver Execution

**Status**: Accepted  
**Context**: The solver can run for 5+ minutes. Python threads hold the GIL and cannot be monitored or retried.  
**Decision**: Use Celery with Redis broker.  
**Consequences**: Requires Redis infrastructure. Solver progress reported via WebSocket, not polling.
```

Only create ADRs for decisions that a new team member would question. "Why PostgreSQL?" doesn't need an ADR. "Why Celery instead of asyncio background tasks?" does.

### 4.7 Commit Messages

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`  
Scope: module name (`domain`, `solver`, `api`, `frontend`, `infra`)

Examples:
```
feat(domain): add Instructor entity and repository interface
feat(solver): implement InstructorNoOverlap constraint
fix(api): return 404 instead of 500 for missing offering
test(solver): add unit tests for session cover constraint
refactor(infra): extract database session factory
```

### 4.8 PR Description

Every PR includes:
- **What**: One sentence describing the change
- **Why**: One sentence describing the motivation
- **How to test**: Steps to verify (or "run `pytest tests/unit/domain/`")

No screenshots unless it's a UI change. No lengthy paragraphs.

---

## 5. Phase-by-Phase Implementation Plan

### Phase 0: Foundation (Week 1-2)

**Goal**: Set up the new directory structure, tooling, and development environment without touching existing code.

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 0.1 | Create `backend/` directory structure per REPOSITORY_STRUCTURE.md | Directory tree |
| 0.2 | Set up `pyproject.toml` with all dependencies (new + migrated) | Working `pip install -e ".[dev]"` |
| 0.3 | Configure Alembic with empty initial migration | `alembic upgrade head` works |
| 0.4 | Set up Pydantic Settings (`config/settings.py`) reading from `.env` | All config from env vars |
| 0.5 | Create FastAPI app factory (`interfaces/api/app.py`) with health endpoint | `GET /health` returns 200 |
| 0.6 | Set up `docker-compose.yml` with PostgreSQL and Redis | `docker compose up` works |
| 0.7 | Configure ruff, mypy, pytest, import-linter | All pass on empty project |
| 0.8 | Set up GitHub Actions CI for backend | Green pipeline |
| 0.9 | Fix CORS to use env var (CONFIG-04) | CORS_ORIGINS from `.env` |
| 0.10 | Remove pymysql from dependencies (INFRA-07) | Clean dependency list |
| 0.11 | Add global error handler (INFRA-06) | Structured error responses |
| 0.12 | Replace NullPool with QueuePool (INFRA-02) | Connection pooling |
| 0.13 | Replace `VITE_API_BASE_URL` hardcoded URL (DATA-10) | Env-driven URL |

**Eliminates**: CONFIG-04, DATA-10, INFRA-01, INFRA-02, INFRA-06, INFRA-07 (6 items)

**Acceptance criteria**: `docker compose up` starts PostgreSQL + Redis + backend. `GET /api/health` returns `{"status": "ok"}`. CI pipeline runs ruff + mypy + pytest (all green). Old prototype still works on `main` branch.

---

### Phase 1: Domain & Persistence (Week 3-5)

**Goal**: Implement the full domain model and database schema. All 35 tables from DOMAIN_MODEL.md.

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 1.1 | Create domain entities as Python dataclasses (Institution, Program, Subject, etc.) | `domain/entities/*.py` |
| 1.2 | Create value objects (CreditHours, Semester, SessionPattern, TimeRange) | `domain/value_objects/*.py` |
| 1.3 | Define repository interfaces (abstract base classes) | `domain/repositories/*.py` |
| 1.4 | Create SQLAlchemy ORM models for all 35 tables | `infrastructure/persistence/orm_models.py` |
| 1.5 | Write Alembic migration for full schema | `alembic/versions/001_initial_schema.py` |
| 1.6 | Implement concrete SQLAlchemy repositories | `infrastructure/persistence/repositories/*.py` |
| 1.7 | Implement domain services (OfferingValidator, ConflictDetector, SessionPatternResolver) | `domain/services/*.py` |
| 1.8 | Create seed data script for development | `scripts/seed_dev_data.py` |
| 1.9 | Write unit tests for domain entities and services | `tests/unit/domain/` |
| 1.10 | Write integration tests for repositories against PostgreSQL | `tests/integration/` |
| 1.11 | Create CRUD use cases (CreateOffering, etc.) | `application/use_cases/*.py` |
| 1.12 | Create CRUD API routes | `interfaces/api/routes/*.py` |

**Eliminates**: DATA-01, DATA-02, DATA-03, DATA-11, DATA-12, CONFIG-05, CONFIG-06, CONFIG-07, RANDOM-06 (9 items)

**Acceptance criteria**: All 35 tables exist in PostgreSQL. CRUD operations work for all entities via API. Seed script populates a realistic dev dataset. Repository integration tests pass. Domain unit tests pass.

---

### Phase 2: Solver Integration (Week 6-8)

**Goal**: Port the CP-SAT solver to the modular architecture. Connect it to the database-driven data pipeline. Replace threading with Celery.

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 2.1 | Create `SolverInput` and `SolverOutput` DTOs | `application/dtos/solver_dtos.py` |
| 2.2 | Implement Loader module | `infrastructure/solver/loader.py` |
| 2.3 | Implement Validator module | `infrastructure/solver/validator.py` |
| 2.4 | Implement Variable Factory | `infrastructure/solver/variable_factory.py` |
| 2.5 | Implement Index Builder | `infrastructure/solver/index_builder.py` |
| 2.6 | Port constraints from model_builder.py to individual constraint modules | `infrastructure/solver/constraints/*.py` |
| 2.7 | Port objective function to objective modules | `infrastructure/solver/objectives/*.py` |
| 2.8 | Implement Optimizer module | `infrastructure/solver/optimizer.py` |
| 2.9 | Implement Extractor module | `infrastructure/solver/extractor.py` |
| 2.10 | Implement CP-SAT Adapter (orchestrates the pipeline) | `infrastructure/solver/cpsat_adapter.py` |
| 2.11 | Implement Constraint Registry with enable/disable | `infrastructure/solver/constraints/registry.py` |
| 2.12 | Set up Celery with Redis broker | `infrastructure/tasks/celery_app.py` |
| 2.13 | Implement solver Celery task | `infrastructure/tasks/solver_task.py` |
| 2.14 | Implement SolverOrchestrator use case | `application/services/solver_orchestrator.py` |
| 2.15 | Create solver API routes (POST /solver/run, GET /solver/{id}) | `interfaces/api/routes/solver.py` |
| 2.16 | Write unit tests for each constraint in isolation | `tests/unit/solver/test_constraints/` |
| 2.17 | Write integration test: full solver pipeline with test data | `tests/integration/test_solver_pipeline.py` |
| 2.18 | Verify: solver produces same quality results as prototype with equivalent input | Manual comparison |
| 2.19 | Implement session pattern configuration (from DB) | `session_pattern` table + resolver |

**Eliminates**: DATA-04, DATA-05, DATA-06, CONFIG-01, CONFIG-02, CONFIG-03, CONFIG-08, RANDOM-01 through RANDOM-05, INFRA-03, INFRA-04 (14 items)

**Acceptance criteria**: Solver runs via Celery worker. Each constraint has an isolated unit test. Full pipeline integration test passes. Solver produces feasible schedules from database data. Progress is reportable (Celery state).

---

### Phase 3: Authentication & RBAC (Week 9-10)

**Goal**: Implement JWT authentication, role-based access control, and multi-tenancy.

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 3.1 | Implement JWT provider (issue, validate, refresh) | `infrastructure/auth/jwt_provider.py` |
| 3.2 | Implement password hasher (bcrypt) | `infrastructure/auth/password_hasher.py` |
| 3.3 | Create User entity and repository | Domain + persistence |
| 3.4 | Implement auth middleware (JWT verification) | `interfaces/api/middleware/auth.py` |
| 3.5 | Implement tenant middleware (institution context) | `interfaces/api/middleware/tenant.py` |
| 3.6 | Create auth routes (login, refresh, me) | `interfaces/api/routes/auth.py` |
| 3.7 | Add role checks to all existing routes | Decorator/dependency per route |
| 3.8 | Set up PostgreSQL RLS policies | Alembic migration |
| 3.9 | Create admin CLI for user management | `interfaces/cli/main.py` |
| 3.10 | Write auth API tests | `tests/api/test_auth.py` |
| 3.11 | Write RBAC integration tests (each role can/cannot access specific endpoints) | `tests/api/test_rbac.py` |

**Eliminates**: AUTH-01 through AUTH-05 (5 items)

**Acceptance criteria**: Login returns JWT. All routes require valid JWT. Role-based restrictions enforced. Multi-tenant queries return only tenant's data. Admin CLI can create users.

---

### Phase 4: Frontend Migration (Week 11-14)

**Goal**: Convert the frontend to use the API, Pinia stores, Vue Router, and TypeScript. Remove all hardcoded data.

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 4.1 | Add TypeScript, Vue Router, Pinia to project | Updated `package.json`, `tsconfig.json` |
| 4.2 | Create API service with Axios interceptors (JWT, base URL) | `services/api.ts` |
| 4.3 | Create auth Pinia store + login page connected to real API | Working login |
| 4.4 | Create router with auth guards | Protected routes |
| 4.5 | Migrate materias/subjects to API-backed Pinia store | `stores/subjects.ts` |
| 4.6 | Migrate profesores/instructors to API-backed Pinia store | `stores/instructors.ts` |
| 4.7 | Build Offerings page (new feature) | `pages/OfferingsPage.vue` |
| 4.8 | Build Solver page with WebSocket progress | `pages/SolverPage.vue` |
| 4.9 | Migrate CalendarioPage to read from API | API-backed calendar |
| 4.10 | Remove all hardcoded university names and branding | Dynamic from API |
| 4.11 | Implement Excel import for offerings | File upload → API |
| 4.12 | Implement Excel/PDF export from API | Download endpoints |
| 4.13 | Delete dead code (views/, old router, old state.js) | Clean frontend |
| 4.14 | Set up Vitest and write component tests | `tests/` in frontend |
| 4.15 | Delete `store/state.js` and all localStorage usage | Pinia only |

**Eliminates**: DATA-07, DATA-08, DATA-09, INFRA-05 (4 items)

**Acceptance criteria**: Login works with real credentials. All data loads from API. No localStorage persistence. Calendar displays solver results from database. Excel export works. All hardcoded strings replaced with dynamic values.

---

### Phase 5: Import/Export & Notifications (Week 15-16)

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 5.1 | Implement Excel importer for academic offerings | Backend endpoint + parser |
| 5.2 | Implement Excel exporter for published schedules (preserve current formatting) | Backend endpoint |
| 5.3 | Implement PDF exporter for published schedules | Backend endpoint |
| 5.4 | Implement email notification service | Infrastructure adapter |
| 5.5 | Wire notifications to use cases (offering submitted, schedule published) | Event hooks |

---

### Phase 6: Testing, Hardening & Deployment (Week 17-18)

**Tasks**:

| # | Task | Output |
|---|------|--------|
| 6.1 | End-to-end tests for complete workflow (upload → solve → modify → publish) | `tests/e2e/` |
| 6.2 | Load test with realistic data (500 subjects, 200 instructors, 50 rooms) | Performance report |
| 6.3 | Security review (SQL injection, JWT validation, permission bypasses) | Findings + fixes |
| 6.4 | Production Docker Compose configuration | `docker/docker-compose.prod.yml` |
| 6.5 | Production deployment documentation | `docs/DEPLOYMENT.md` |
| 6.6 | Run data migration from prototype to new system | Migration script executed |
| 6.7 | Delete old `src/scheduler/` prototype code | Clean repository |
| 6.8 | Deploy and monitor | Production system live |

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Solver produces worse results than prototype | Medium | High | Phase 2 Task 2.18: explicit quality comparison. Preserve all mathematical constraints exactly. |
| Alembic migration breaks existing DB | Low | High | Separate database (scheduler_v2). Old DB untouched. |
| Celery adds ops complexity | Medium | Medium | docker-compose includes Redis + worker. Single command to start. |
| TypeScript conversion slows frontend work | Medium | Low | Convert files incrementally. `any` escape hatch for complex cases. Fix later. |
| OR-Tools version incompatibility | Low | Medium | Pin exact version in pyproject.toml. Test on CI. |
| Multi-tenancy RLS performance | Low | Medium | Add `institution_id` indexes. Benchmark queries with 5+ tenants. |

---

## 7. Definition of Done

A phase is "done" when:

1. All tasks in the phase are implemented
2. All tests pass (unit + integration + API)
3. CI pipeline is green (lint + type check + tests)
4. No regressions in previously completed phases
5. Code reviewed by at least one other person
6. All hardcoded items scheduled for this phase are eliminated (per ELIMINATION_PLAN.md)

---

## 8. Deliverable Checklist — Phase 2 Output

This section confirms what was delivered during Phase 2 (documentation/planning):

| # | Deliverable | File | Status |
|---|-------------|------|--------|
| 1 | Complete project audit with prioritized findings | `docs/AUDIT_REPORT.md` | Done (679 lines, 47 findings) |
| 2 | Clean architecture redesign | `docs/ARCHITECTURE.md` | Done (2,226 lines) |
| 3 | Complete domain model with ~35 entities | `docs/DOMAIN_MODEL.md` | Done (1,975 lines) |
| 4 | Generic solver redesign with modular constraints | `docs/SOLVER_DESIGN.md` | Done (2,567 lines) |
| 5 | Repository structure proposal | `docs/REPOSITORY_STRUCTURE.md` | Done |
| 6 | Hardcoded/temporary data elimination plan | `docs/ELIMINATION_PLAN.md` | Done (38 items cataloged) |
| 7 | Modular solver architecture (8 modules) | `docs/MIGRATION_ROADMAP.md` §3 | Done |
| 8 | Documentation standards | `docs/MIGRATION_ROADMAP.md` §4 | Done |
| 9 | Migration strategy (don't break existing) | `docs/MIGRATION_ROADMAP.md` §2 | Done |
| 10 | Final planning document for Phase 3 | `docs/MIGRATION_ROADMAP.md` §5-8 | Done |

**All 10 deliverables are complete. Phase 2 is finished. The project is ready to begin Phase 3 (implementation).**

---

## Timeline Summary

```
Week  1-2:   [Phase 0] Foundation         — structure, tooling, Docker, CI
Week  3-5:   [Phase 1] Domain/Persistence — 35 tables, entities, CRUD
Week  6-8:   [Phase 2] Solver Integration — modular CP-SAT, Celery, constraints
Week  9-10:  [Phase 3] Auth/RBAC          — JWT, roles, multi-tenancy
Week 11-14:  [Phase 4] Frontend           — Pinia, router, TypeScript, API
Week 15-16:  [Phase 5] Import/Export      — Excel, PDF, email notifications
Week 17-18:  [Phase 6] Hardening          — testing, security, deployment
```

Estimated total: **18 weeks** for a team of 2-3 developers.

The prototype remains operational on `main` throughout. Users switch to the new system only after Phase 6 is validated.

---

*End of document.*
