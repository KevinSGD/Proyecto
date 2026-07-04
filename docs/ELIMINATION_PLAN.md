# Elimination Plan — Hardcoded, Temporary & Demo Data

**System**: University Schedule Optimization Platform v2.0  
**Date**: 2026-06-29  
**Author**: Refactoring Engineer  

---

## Purpose

This document catalogs every hardcoded value, temporary hack, fake data generator, and demo shortcut in the current codebase. Each item has a location, a description of what it does, what replaces it, and the migration phase where it gets eliminated.

Hardcoded items fall into five categories:

| Category | Symbol | Count |
|----------|--------|-------|
| Data literals (subjects, names, labels) | `DATA` | 12 |
| Configuration constants | `CONFIG` | 8 |
| Security/auth shortcuts | `AUTH` | 5 |
| Random data generation | `RANDOM` | 6 |
| Infrastructure assumptions | `INFRA` | 7 |
| **Total** | | **38** |

---

## Category 1: DATA — Hardcoded Data Literals

### DATA-01: 48 Hardcoded Subjects

**File**: `src/scheduler/application/data_builder.py:20-71`  
**What**: Python list literal with 48 subject dictionaries including `nombre`, `creditos`, `categoria`.  
**Example**: `{"nombre": "Cátedra Manuela Beltrán", "creditos": 1, "categoria": "institucional"}`  
**Impact**: The entire solver runs on fake university-specific data.  
**Replacement**: Subjects loaded from `subject` + `plan_subject` tables via `SubjectRepository`. Area coordinators upload offerings through the UI or Excel import.  
**Phase**: Phase 1 (Domain/Persistence)

### DATA-02: "Virtuales" Subject Set

**File**: `src/scheduler/application/data_builder.py:78-87`  
**What**: Hardcoded set of 10 subject names that are "virtual" (don't need physical rooms).  
**Example**: `"Electiva Libre I"`, `"Práctica Profesional"`  
**Impact**: Virtual/presential mode is determined by string matching against a frozen list.  
**Replacement**: `offering_line.modality` field (`presential`, `virtual`, `hybrid`) in the database. Each offering line explicitly declares its modality.  
**Phase**: Phase 1

### DATA-03: "Humanidades Comun" Subject Set

**File**: `src/scheduler/application/data_builder.py:89-101`  
**What**: Hardcoded set of 14 subject names that are shared "humanities" across programs.  
**Example**: `"Formación Ciudadana"`, `"Cátedra de la Paz"`  
**Impact**: Cross-program sharing logic hardcoded by name matching.  
**Replacement**: `subject.is_shared` boolean + `subject_sharing` junction table. Programs declare sharing at the study plan level.  
**Phase**: Phase 1

### DATA-04: "AREAS_DISCIPLINARES" Set

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:61-67`  
**What**: Hardcoded set of 8 "disciplinary area" category names used to decide group counts.  
**Impact**: Whether a subject gets 1 or 2+ groups depends on matching its category against this frozen set.  
**Replacement**: `offering_line.num_groups` is explicitly set by the area coordinator in the offering. No string matching needed.  
**Phase**: Phase 2 (Solver Integration)

### DATA-05: "Infraestructura" String Match

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:107-109`  
**What**: `if mat.categoria == "infraestructura"` determines that the first professor and first PC lab are locked to all infrastructure courses.  
**Impact**: Business rule embedded as string comparison in solver code.  
**Replacement**: Constraint configuration. If an institution wants to pin certain instructors to certain subject groups, they express it through `instructor_assignment` with `is_fixed=true`. Room requirements come from `subject.required_equipment`.  
**Phase**: Phase 2

### DATA-06: Hardcoded Day Names

**File**: `src/scheduler/infrastructure/optimization/extractor.py:~line 15`  
**What**: `["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]`  
**Impact**: Day labels are fixed to Spanish and always 6 days.  
**Replacement**: `DayOfWeek` enum with configurable `ScheduleType` patterns. Days come from `schedule_type.active_days`. Localization handled by frontend i18n.  
**Phase**: Phase 2

### DATA-07: University Name in LoginPage

**File**: `frontend/src/pages/LoginPage.vue:57, 172`  
**What**: `"Universidad Manuel Beltrán"` and `"© 2025 Universidad Manuel Beltrán"` hardcoded in template.  
**Impact**: Login page is unusable for any other institution.  
**Replacement**: Institution name fetched from `/api/institutions/current` on app load. Footer copyright generated from institution metadata.  
**Phase**: Phase 4 (Frontend)

### DATA-08: "GestorAulas" App Name

**File**: `frontend/src/pages/LoginPage.vue:53`  
**What**: Hardcoded app name in login header.  
**Impact**: Cosmetic but prevents white-labeling.  
**Replacement**: App name from institution configuration or environment variable.  
**Phase**: Phase 4

### DATA-09: Export Filename "cronograma_UMB_"

**File**: `frontend/src/pages/CalendarioPage.vue:353`  
**What**: Excel export filename contains university abbreviation `UMB`.  
**Impact**: Downloaded files have wrong name for other institutions.  
**Replacement**: Filename constructed from `institution.abbreviation` + period + timestamp.  
**Phase**: Phase 4

### DATA-10: Hardcoded Production URL

**File**: `frontend/src/services/api.js:2`  
**What**: `"tesisomuerte-production-6d83.up.railway.app"` as API base URL.  
**Impact**: Frontend is bound to a specific Railway deployment.  
**Replacement**: `VITE_API_BASE_URL` environment variable, injected at build time. Defaults to relative `/api` in production (reverse proxy).  
**Phase**: Phase 0 (Foundation)

### DATA-11: Fake Professor Names

**File**: `src/scheduler/application/data_builder.py:119-123`  
**What**: `f"Prof_{i:02d}"` generates 20 fake professor names.  
**Impact**: Solver runs on fictional data.  
**Replacement**: Instructors loaded from `instructor` table.  
**Phase**: Phase 1

### DATA-12: Fake Classroom Names

**File**: `src/scheduler/application/data_builder.py:125-128`  
**What**: `f"Salon_{i:02d}"` and `f"Lab_PC_{i:02d}"` generates fake classrooms.  
**Impact**: Solver runs on fictional rooms.  
**Replacement**: Classrooms loaded from `classroom` table with actual room names, capacities, and equipment.  
**Phase**: Phase 1

---

## Category 2: CONFIG — Hardcoded Configuration Constants

### CONFIG-01: DEFAULT_CONFIG Dict

**File**: `src/scheduler/config/settings.py:all`  
**What**: `seed=123, num_profes=20, num_dias=6, bloques_por_dia=11, max_clases_profe_dia=6, max_clases_profe_semana=26, num_salones_comunes=8, num_salones_pc=12, k_candidatos=6, max_time_seconds=6000`  
**Impact**: All solver parameters are frozen. No per-run customization.  
**Replacement**: `SolverConfig` dataclass populated from `solver_configuration` table (per-institution). Exposed as JSON in `/api/solver/config` endpoint.  
**Phase**: Phase 2

### CONFIG-02: Credit-to-Session Mapping

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:183-211`  
**What**: Rigid `if/elif` chain: 4cr→2×2h, 3cr→1×3h or 2+1, 2cr→1×2h, 1cr→1×1h.  
**Impact**: Cannot handle 5-credit or 6-credit courses. Cannot customize session splits.  
**Replacement**: `session_pattern` table with `credit_hours`, `pattern_name`, `blocks` JSON. Each institution configures its own patterns. Resolver reads from DB.  
**Phase**: Phase 2

### CONFIG-03: SOLVER_TIMEOUT_S = 30

**File**: `frontend/src/store/state.js`  
**What**: Frontend hardcodes a 30-second timeout for solver polling.  
**Impact**: Large instances that need 2+ minutes are incorrectly reported as failed.  
**Replacement**: Server-Sent Events or WebSocket for solver progress. No fixed timeout — the connection stays open until the solver completes.  
**Phase**: Phase 2

### CONFIG-04: CORS allow_origins=["*"]

**File**: `src/scheduler/interfaces/api/main.py:~line 30`  
**What**: Allows any origin to call the API.  
**Impact**: Security vulnerability — any website can make authenticated requests.  
**Replacement**: `CORS_ORIGINS` environment variable, defaulting to `["http://localhost:5173"]` in dev. Production value set to actual frontend domain.  
**Phase**: Phase 0

### CONFIG-05: Hardcoded Week Start / End Hours

**File**: `src/scheduler/config/settings.py` (bloques_por_dia=11)  
**What**: Assumes 11 time blocks per day (e.g., 7am-6pm with 1h blocks).  
**Impact**: Cannot model evening programs (6pm-10pm) or early morning (6am start).  
**Replacement**: `schedule_type` table defines `start_time`, `end_time`, `slot_duration_minutes` per schedule type. Blocks computed dynamically.  
**Phase**: Phase 1

### CONFIG-06: Always 6 Days

**File**: `src/scheduler/config/settings.py` (num_dias=6)  
**What**: Mon-Sat always. Cannot model Mon-Fri or Mon-Sun.  
**Impact**: Night programs that run Mon-Fri only still allocate Saturday slots.  
**Replacement**: `schedule_type.active_days` array. Each schedule type declares which days are active.  
**Phase**: Phase 1

### CONFIG-07: Fixed Number of Classrooms

**File**: `src/scheduler/config/settings.py` (num_salones_comunes=8, num_salones_pc=12)  
**What**: Hardcoded to 8 regular + 12 PC labs. Always.  
**Impact**: Real institutions have different classroom counts.  
**Replacement**: Classrooms come from the `classroom` table. Count is whatever the institution has registered.  
**Phase**: Phase 1

### CONFIG-08: Seed = 123

**File**: `src/scheduler/config/settings.py` (seed=123)  
**What**: Fixed random seed used by `random.sample`/`random.randint` in model_builder.  
**Impact**: In the new system, there is no randomness in the solver (all data comes from DB), so a seed is unnecessary. If needed for CP-SAT's internal search, it becomes a solver configuration parameter.  
**Replacement**: `SolverConfig.random_seed` optional field. Defaults to None (no fixed seed). Useful for reproducibility in testing.  
**Phase**: Phase 2

---

## Category 3: AUTH — Security and Authentication Shortcuts

### AUTH-01: admin/admin Login

**File**: `frontend/src/pages/LoginPage.vue:20`  
**What**: `if (usuario === 'admin' && contrasena === 'admin')` — hardcoded credentials.  
**Impact**: No real authentication. Anyone who reads the source code has full access.  
**Replacement**: JWT-based authentication against `user` table with bcrypt-hashed passwords. Login calls `POST /api/auth/login`, receives access + refresh tokens.  
**Phase**: Phase 3 (Auth/RBAC)

### AUTH-02: setTimeout(500) as Auth Delay

**File**: `frontend/src/pages/LoginPage.vue:19`  
**What**: `setTimeout(() => { ... }, 500)` simulates network latency.  
**Impact**: Cosmetic only — creates false impression of server-side validation.  
**Replacement**: Real HTTP request to auth endpoint. Loading state driven by actual request lifecycle.  
**Phase**: Phase 3

### AUTH-03: No JWT / No Auth Middleware

**File**: `src/scheduler/interfaces/api/main.py`  
**What**: All API endpoints are public. No authentication check anywhere.  
**Impact**: Anyone with the URL can create, modify, or delete any data.  
**Replacement**: `AuthMiddleware` in `interfaces/api/middleware/auth.py`. Every route except `/health` and `/auth/login` requires a valid JWT. Route decorators specify required roles.  
**Phase**: Phase 3

### AUTH-04: No Role-Based Access Control

**File**: Entire codebase  
**What**: No concept of roles or permissions.  
**Impact**: Cannot implement the business workflow (area coordinator uploads, director validates).  
**Replacement**: `Role` enum (`super_admin`, `director`, `area_coordinator`, `viewer`). `user` table has `role` column. FastAPI dependency checks `current_user.role` against required permission.  
**Phase**: Phase 3

### AUTH-05: No Tenant Isolation

**File**: Entire codebase  
**What**: No `institution_id` on any table. Single-tenant only.  
**Impact**: Cannot serve multiple universities from one deployment.  
**Replacement**: `institution_id` UUID on every tenant-scoped table. PostgreSQL Row-Level Security policies filter by `current_setting('app.current_institution_id')`. Middleware sets the session variable from the JWT claim.  
**Phase**: Phase 3

---

## Category 4: RANDOM — Random Data Generation

### RANDOM-01: Random Group Counts

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:71-80`  
**What**: `random.choice([1, 2])` for most subjects, hardcoded `3` for disciplinary areas.  
**Impact**: Group counts are random instead of reflecting actual enrollment demand.  
**Replacement**: `offering_line.num_groups` set by area coordinator based on projected enrollment.  
**Phase**: Phase 2

### RANDOM-02: Random Candidate Professors

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:96`  
**What**: `random.sample(range(num_profes), k_candidatos)` picks 6 random professors per subject.  
**Impact**: Professor-subject assignments are random instead of reflecting qualifications.  
**Replacement**: `instructor_assignment` table links instructors to subject groups. Only assigned instructors appear as candidates in the solver input.  
**Phase**: Phase 2

### RANDOM-03: Random Preferences

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:124`  
**What**: `random.randint(0, 10)` generates fake preference scores.  
**Impact**: Objective function optimizes meaningless preferences.  
**Replacement**: `instructor_assignment.preference_score` (0-10) set by instructor or coordinator. Stored in database.  
**Phase**: Phase 2

### RANDOM-04: Random Student Counts

**File**: `src/scheduler/infrastructure/optimization/model_builder.py:126`  
**What**: `random.randint(20, 25)` generates fake enrollment per group.  
**Impact**: Room capacity constraints use fake data.  
**Replacement**: `offering_line.expected_enrollment` set by area coordinator. Used to match rooms by capacity.  
**Phase**: Phase 2

### RANDOM-05: Fake build_data() Path

**File**: `src/scheduler/application/data_builder.py:build_data()`  
**What**: Entire method generates a complete fake dataset from hardcoded subjects + random professors + random classrooms.  
**Impact**: This path should never exist in production.  
**Replacement**: Delete entirely. Replace with `SolverInputBuilder` service that queries the database via repositories and constructs `SolverInput` DTO.  
**Phase**: Phase 2

### RANDOM-06: norm() Duplication

**File**: `src/scheduler/application/data_builder.py` and `src/scheduler/infrastructure/optimization/model_builder.py`  
**What**: `norm()` function for accent-stripping duplicated in two files. Used for string-matching subject names.  
**Impact**: Fragile string normalization instead of proper ID-based lookups.  
**Replacement**: Delete both. All entity references use UUID primary keys, not string matching.  
**Phase**: Phase 1

---

## Category 5: INFRA — Infrastructure Assumptions

### INFRA-01: create_all Instead of Migrations

**File**: `src/scheduler/infrastructure/database.py`  
**What**: `Base.metadata.create_all(engine)` creates tables on startup.  
**Impact**: Cannot evolve schema without data loss. No migration history.  
**Replacement**: Alembic migrations. `alembic upgrade head` applies schema changes incrementally. Never use `create_all` in production.  
**Phase**: Phase 0

### INFRA-02: NullPool in Database

**File**: `src/scheduler/infrastructure/database.py`  
**What**: `poolclass=NullPool` — no connection pooling.  
**Impact**: Every query opens and closes a TCP connection. Performance degrades under load.  
**Replacement**: Default SQLAlchemy pool (QueuePool) with configurable `pool_size` and `max_overflow`.  
**Phase**: Phase 0

### INFRA-03: threading.Thread for Solver

**File**: `src/scheduler/interfaces/api/main.py:~line 180`  
**What**: Solver runs in `threading.Thread`, managed by a dict of running jobs.  
**Impact**: No persistence across restarts. No worker scaling. GIL contention. Memory not released.  
**Replacement**: Celery task with Redis broker. `solver_task.delay(solver_input_id)` dispatches to worker. Status tracked in `schedule_run` table.  
**Phase**: Phase 2

### INFRA-04: In-Memory Job Registry

**File**: `src/scheduler/interfaces/api/main.py` (global dict)  
**What**: `running_jobs: dict` stores active solver jobs in process memory.  
**Impact**: Jobs lost on restart. Cannot query job status from another process.  
**Replacement**: `schedule_run` table with `status` enum (`queued`, `running`, `completed`, `failed`). Celery updates status via callbacks.  
**Phase**: Phase 2

### INFRA-05: localStorage as Database

**File**: `frontend/src/store/state.js`  
**What**: All materias, profesores, calendario, aulas stored in browser localStorage with manual migration code (v1→v2→v3→v5).  
**Impact**: Data exists only on one browser. No sharing, no backup, no multi-user.  
**Replacement**: All data persisted in PostgreSQL via API. Pinia stores are an in-memory cache of API data. Refresh = refetch.  
**Phase**: Phase 4

### INFRA-06: No Error Handling in API

**File**: `src/scheduler/interfaces/api/main.py`  
**What**: No global exception handler. Unhandled exceptions return 500 with stack trace.  
**Impact**: Exposes internal details to clients. No structured error responses.  
**Replacement**: `error_handler.py` middleware catches exceptions, maps domain exceptions to HTTP status codes, returns `{"error": "code", "message": "..."}` JSON.  
**Phase**: Phase 0

### INFRA-07: pymysql in Dependencies

**File**: `requirements.txt` and `pyproject.toml`  
**What**: `pymysql` is listed as a dependency but never imported anywhere.  
**Impact**: Unused dependency increases attack surface and install time.  
**Replacement**: Remove from all dependency files.  
**Phase**: Phase 0

---

## Elimination Timeline

| Phase | Items Eliminated | Count |
|-------|-----------------|-------|
| Phase 0 (Foundation) | CONFIG-04, DATA-10, INFRA-01, INFRA-02, INFRA-06, INFRA-07 | 6 |
| Phase 1 (Domain/Persistence) | DATA-01 through DATA-03, DATA-11, DATA-12, CONFIG-05 through CONFIG-07, RANDOM-06 | 9 |
| Phase 2 (Solver Integration) | DATA-04 through DATA-06, CONFIG-01, CONFIG-02, CONFIG-03, CONFIG-08, RANDOM-01 through RANDOM-05, INFRA-03, INFRA-04 | 14 |
| Phase 3 (Auth/RBAC) | AUTH-01 through AUTH-05 | 5 |
| Phase 4 (Frontend) | DATA-07 through DATA-09, INFRA-05 | 4 |
| **Total** | | **38** |

After Phase 4, zero hardcoded values remain. Every piece of data comes from the database or environment variables.

---

*End of document.*
