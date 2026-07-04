# GestorAulas -- Comprehensive Codebase Audit Report

**Project:** University Class Schedule Optimization System (GestorAulas)  
**Date:** 2026-06-28  
**Auditors:** QA Engineering & Refactoring Engineering  
**Scope:** Full-stack audit covering Python backend (`src/scheduler/`) and Vue 3 frontend (`frontend/src/`)

---

## 1. Executive Summary

GestorAulas is a constraint-satisfaction-based university schedule optimizer built with a Python/FastAPI backend (Google OR-Tools CP-SAT solver) and a Vue 3/Vite frontend. The system was developed as a thesis/prototype for Universidad Manuel Beltran and is currently deployed on Railway.

**Overall assessment: The system is a functional prototype unsuitable for production use.** It contains 48 hardcoded subjects baked into Python source code, uses `admin/admin` as its only authentication mechanism (implemented with `setTimeout`), stores all application state in browser localStorage, runs the solver in unmanaged Python threads, and exposes an unrestricted CORS policy. There are zero automated tests. The database layer is optional and structurally mismatched with the frontend data model. The codebase has significant dead code from an abandoned Vue Router migration.

**Findings summary:**
| Priority | Count | Description |
|----------|-------|-------------|
| P0 (Critical) | 8 | Production blockers -- security, data integrity, architectural |
| P1 (High) | 14 | Severe functionality/maintainability limitations |
| P2 (Medium) | 16 | Technical debt requiring attention |
| P3 (Low) | 9 | Minor improvements |

**Total findings: 47**

---

## 2. Methodology

1. **Manual file-by-file code reading** -- every `.py`, `.vue`, `.js`, and configuration file was read in its entirety.
2. **Pattern scanning** -- grep for `TODO`, `FIXME`, `HACK`, `HARDCOD`, dead imports, unused exports.
3. **Cross-referencing** -- traced data flow from frontend state through API calls to solver and back.
4. **Dependency analysis** -- inspected `requirements.txt`, `pyproject.toml`, `package.json` imports.
5. **Line counting** -- `wc -l` across all source files to measure codebase size.

---

## 3. Findings by Category

### 3.1 P0 -- Critical / Blocker

These issues make the system fundamentally unsuitable for production deployment.

---

#### P0-01: Hardcoded credentials with fake authentication

**File:** `frontend/src/pages/LoginPage.vue`, lines 20-26  
**Description:** Authentication is implemented as a client-side string comparison against hardcoded `admin`/`admin` credentials, wrapped in a `setTimeout(500ms)` to simulate network latency. The `isAuthenticated` state is a Vue `ref(false)` in `App.vue` line 14 -- it resets on page refresh and provides no session persistence, no token, no server-side validation.  
**Impact:** Any user can bypass authentication by setting the Vue reactive state directly, or simply reading the source code. The backend API has zero authentication -- all endpoints are publicly accessible.  
**Recommendation:** Implement a proper authentication system with JWT tokens, server-side session validation, password hashing (bcrypt/argon2), and role-based access control.

---

#### P0-02: CORS allows all origins

**File:** `src/scheduler/interfaces/api/main.py`, lines 53-59  
**Description:** The CORS middleware is configured with `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`. This is the most permissive CORS configuration possible.  
**Impact:** Any website on the internet can make authenticated cross-origin requests to the API. Combined with P0-01 (no auth), any website can trigger solver runs, delete all data, or reset the database.  
**Recommendation:** Restrict `allow_origins` to the actual frontend domain(s). Remove `allow_credentials=True` if cookies are not used. Specify only needed methods and headers.

---

#### P0-03: Unauthenticated destructive API endpoints

**File:** `src/scheduler/interfaces/api/main.py`, lines 394-416  
**Description:** `DELETE /api/clear-data` (line 394) deletes all professors and subjects. `DELETE /api/reset-db` (line 408) runs `TRUNCATE TABLE profesores, materias RESTART IDENTITY CASCADE`. Neither endpoint has any authentication, authorization, or confirmation mechanism.  
**Impact:** Anyone with the API URL can permanently destroy all stored data with a single HTTP request.  
**Recommendation:** Add authentication middleware. Require explicit confirmation tokens for destructive operations. Add audit logging.

---

#### P0-04: localStorage is the primary database

**File:** `frontend/src/lib/storage.js`, lines 1-28; `frontend/src/store/state.js`, lines 82-109  
**Description:** All application state -- subjects, professors, schedule events, solver results -- is persisted exclusively in browser `localStorage` under the key `skedopt.ui.v1`. The PostgreSQL database is optional (the app checks `dbOk` before saving and silently skips if unavailable, as shown in `ParametrosPage.vue` lines 171-200). The database stores only a flat `Materia` and `Profesor` table that cannot represent the full data model the frontend uses.  
**Impact:** Clearing browser data destroys all work. No multi-user collaboration is possible. Data cannot be backed up, audited, or versioned. The `localStorage` quota (~5-10MB) limits data capacity.  
**Recommendation:** Make the database the single source of truth. Implement proper CRUD endpoints. Use localStorage only as an offline cache/optimistic-update layer.

---

#### P0-05: Database model does not match frontend data model

**File:** `src/scheduler/infrastructure/models.py`, lines 31-48 (Profesor model); `frontend/src/store/state.js`, lines 172-180 (addProfesor)  
**Description:** The `Profesor` database table has a single `materia_id` FK (line 37: `materia_id = Column(Integer, ForeignKey("materias.id"), nullable=False)`), but the frontend uses a `materiaIds` array (line 176: `materiaIds: []`) allowing many-to-many professor-subject assignments. When saving to the database, only the first materia is stored (`ParametrosPage.vue` line 191: `materia_id: materiaIdToNombre[(p.materiaIds || [])[0]] || null`). The database also lacks fields present in the frontend: `maxHoras`, `estado` (active/suspended), `demanda`, `autoGrupos`, `capacidadGrupo`.  
**Impact:** Database saves silently lose data. A professor assigned to 5 subjects will have only 1 recorded in the database. Restoring from the database loses all suspended status, hour limits, and multi-subject assignments.  
**Recommendation:** Create a proper many-to-many junction table (`profesor_materias`). Add missing columns. Implement database migrations with Alembic.

---

#### P0-06: Solver runs in unmanaged daemon threads

**File:** `src/scheduler/interfaces/api/main.py`, lines 236-238  
**Description:** The solver is launched via `threading.Thread(target=_run_job, args=(job_id, payload), daemon=True)`. There is no thread pool, no concurrency limit, no memory limit, and no mechanism to cancel a running solver. The thread is marked `daemon=True`, meaning it will be killed if the process exits.  
**Impact:** Multiple simultaneous solver requests will spawn multiple threads, each consuming significant CPU (OR-Tools uses up to 2 workers per `solver_runner.py` line 12). This can crash the server. The 5-minute stale-job timeout (`_JOB_STALE_SECONDS = 300`, line 241) does not actually kill the thread -- it only marks the database record as errored. The thread continues running. The solver's `max_time_seconds` can be set to 6000 seconds (100 minutes) by default (`settings.py` line 11), but the frontend overrides this to 30 seconds (`state.js` line 13: `SOLVER_TIMEOUT_S = 30`).  
**Recommendation:** Use Celery or a similar task queue with proper worker management. Implement concurrency limits, memory limits, and graceful cancellation.

---

#### P0-07: No automated tests

**Description:** There are zero test files in the entire codebase. No unit tests, no integration tests, no end-to-end tests.  
**Impact:** Any code change risks introducing regressions with no safety net. The solver's constraint model (400 lines of CP-SAT variable/constraint construction in `model_builder.py`) is particularly risky to modify without tests verifying constraint correctness.  
**Recommendation:** Add pytest-based test suite covering: data builder functions, solver constraint correctness, API endpoint behavior, and frontend component rendering (Vitest).

---

#### P0-08: No database migrations

**File:** `src/scheduler/infrastructure/database.py`, lines 67-75  
**Description:** Database schema is managed via `Base.metadata.create_all(bind=engine)` called at application startup (`main.py` line 62). There is no Alembic or any migration framework. Schema changes require manual intervention or data loss.  
**Impact:** Schema evolution requires dropping and recreating tables, losing all data. No way to track schema history or roll back changes. Multiple developers cannot coordinate schema changes.  
**Recommendation:** Add Alembic. Generate initial migration from current models. Configure auto-generation for future changes.

---

### 3.2 P1 -- High

Issues that severely limit functionality or maintainability.

---

#### P1-01: 48 subjects hardcoded as Python literals

**File:** `src/scheduler/application/data_builder.py`, lines 20-71  
**Description:** The `build_data()` function contains 48 university subjects as a Python list of tuples, each with name, credits, and area. This data represents the entire curriculum of a specific academic program at Universidad Manuel Beltran.  
**Impact:** Adding, removing, or modifying subjects requires editing Python source code, redeploying the application, and restarting the server. The data is only used by the CLI path (`build_data()`), not by the API path (`build_data_from_ui()`), making it effectively dead data for the web application.  
**Recommendation:** Move all subject data to the database. The `build_data()` function can serve as a seed script for initial data population.

---

#### P1-02: "Virtual" and "humanidades" subject classifications hardcoded

**File:** `src/scheduler/application/data_builder.py`, lines 78-101  
**Description:** Two sets of normalized subject names determine which courses are virtual (excluded from physical scheduling) and which are humanities (assigned to common classrooms). These are string-literal sets that must match the hardcoded subject names.  
**Impact:** These classifications cannot be changed without code modification. They are specific to one university's program and would break for any other institution.  
**Recommendation:** Make these classifications configurable -- either as database fields on the subject model or as UI-configurable categories.

---

#### P1-03: Infrastructure professor and classroom always assigned to index 0

**File:** `src/scheduler/infrastructure/optimization/model_builder.py`, lines 107-122  
**Description:** Infrastructure courses are found by string matching (`"infraestructura" in nrm(m)`, line 107). The first professor (`p_infra = 0`, line 109) is always forced to teach infrastructure courses. The first PC lab (`s_infra = salones_pc[0]`, line 112) is always exclusively reserved for infrastructure. Other professors are forcibly removed from infrastructure candidacy (lines 116-117).  
**Impact:** The assignment is arbitrary and based on array index, not on any qualification or preference. Changing professor order changes who teaches infrastructure. The reserved classroom reduces available lab capacity for all other courses.  
**Recommendation:** Make infrastructure assignment configurable through the UI. Allow explicit instructor-course assignments and room reservations.

---

#### P1-04: Random number generation for groups, candidates, and preferences

**File:** `src/scheduler/infrastructure/optimization/model_builder.py`, lines 70-78 (groups), 94-96 (candidates), 124-126 (preferences, students)  
**Description:** When the UI does not provide overrides, the solver randomly determines: how many groups each course has (1, 2, or 3), which professors can teach which courses (`random.sample`), professor preferences (`random.randint(0, 10)`), and student counts per group (`random.randint(20, 25)`). These are seeded by `cfg["seed"]` for reproducibility, but the values are arbitrary.  
**Impact:** The solver produces schedules based on random data rather than real-world assignments. The UI path (`build_data_from_ui`) does override groups and candidates, but preferences and student counts are still random even in the UI path.  
**Recommendation:** Replace all random generation with actual data from the database/UI. Student enrollment counts and professor preferences should be user-configurable.

---

#### P1-05: Credit-to-session mapping is rigid and hardcoded

**File:** `src/scheduler/infrastructure/optimization/model_builder.py`, lines 183-211  
**Description:** The solver maps credit hours to time blocks using a fixed scheme: 1 credit = 1 block, 2 credits = 1 session of 2 blocks, 3 credits = either 1 session of 3 blocks or 1 session of 2 + 1 of 1, 4 credits = 2 sessions of 2 blocks. No other patterns are supported. The valid start positions per session length are also hardcoded (lines 183-187).  
**Impact:** Cannot accommodate courses with 5+ credits, lab courses requiring 3-hour blocks, or any non-standard session structure. The 3-credit dual-pattern adds solver complexity (binary variable `z` per group, lines 180-181).  
**Recommendation:** Make session patterns configurable per course or per credit-hour value.

---

#### P1-06: Only 2 classroom types supported

**File:** `src/scheduler/application/data_builder.py`, lines 123-127; `model_builder.py`, lines 131-148  
**Description:** The system recognizes exactly two classroom types: `"comun"` and `"pc"`. The mapping is rigid: all subjects are classified as `presencial_comun`, `presencial_pc`, or `virtual`. There is no support for specialized labs (chemistry, physics, electronics), auditoriums, or mixed-use spaces.  
**Impact:** The system cannot model universities with more than two types of physical spaces.  
**Recommendation:** Generalize to N classroom types with configurable room-type compatibility per course.

---

#### P1-07: Monolithic API file (418 lines mixing concerns)

**File:** `src/scheduler/interfaces/api/main.py`, 418 lines  
**Description:** This single file contains: FastAPI app creation, CORS configuration, database initialization, request/response Pydantic models (lines 174-197), job management functions (lines 108-169), scheduler execution logic (lines 89-106), all route handlers (health, run, verify, CRUD), and a custom JSON encoder (lines 13-23). Business logic, infrastructure concerns, and interface definitions are fully entangled.  
**Impact:** Difficult to understand, test, or modify any single aspect without reading the entire file. High risk of unintended side effects when changing one route.  
**Recommendation:** Split into separate modules: `routes/health.py`, `routes/scheduler.py`, `routes/data.py`, `services/job_manager.py`, `middleware/auth.py`.

---

#### P1-08: `norm()` / `nrm()` function duplicated

**File:** `src/scheduler/application/data_builder.py`, lines 5-14; `src/scheduler/infrastructure/optimization/model_builder.py`, lines 34-43  
**Description:** Two identical accent-stripping normalization functions exist: `norm()` in `data_builder.py` and `nrm()` in `model_builder.py`. Both manually replace five Spanish accented vowels and strip whitespace.  
**Impact:** Bug fixes or improvements must be applied in two places. The incomplete normalization misses `n` with tilde and other Unicode normalization concerns.  
**Recommendation:** Extract to a shared utility module. Use Python's `unicodedata.normalize('NFKD', ...)` for proper Unicode normalization.

---

#### P1-09: No instructor availability model

**Description:** The solver has no concept of instructor availability. There are no time slots marked as unavailable per professor, no distinction between full-time and part-time instructors (despite the frontend `maxHoras` field), and no way to block specific days or hours for a professor.  
**File:** `model_builder.py` -- entire file; `state.js` line 177 (`maxHoras: 40`)  
**Impact:** The `maxHoras` field in the frontend is collected but never sent to the solver's constraint model. Professors cannot indicate teaching preferences beyond the random `pref` dictionary. The solver may schedule a part-time professor for 6 consecutive days.  
**Recommendation:** Add availability constraints per professor. Honor the `maxHoras` field in the solver model. Allow per-day/per-block availability masks.

---

#### P1-10: No prerequisite handling

**Description:** The system has no concept of course prerequisites or sequencing. There is no way to specify that Course B requires Course A, or that certain courses should not overlap for the same student cohort.  
**Impact:** Generated schedules may create impossible student paths where required courses overlap in the same time slot.  
**Recommendation:** Add a prerequisite/corequisite model. Implement student-path constraints in the solver to avoid conflicts for students following a standard curriculum.

---

#### P1-11: No multi-tenancy or area isolation

**Description:** The system was designed for a single academic program. There is no concept of academic departments, faculties, campuses, or semesters. All subjects, professors, and classrooms exist in a single flat namespace.  
**Impact:** Cannot be used by multiple departments simultaneously. Cannot generate schedules for different semesters or academic periods.  
**Recommendation:** Add a `tenant` or `academic_period` dimension to all data models.

---

#### P1-12: Solver `num_profes` config disconnects from actual professor count

**File:** `src/scheduler/config/settings.py`, line 3 (`num_profes: 20`); `src/scheduler/interfaces/api/main.py`, line 95  
**Description:** The config has a `num_profes` parameter that defaults to 20. When the UI path is used, the solver receives professors from the UI, but the `NUM_PROFES` variable in `model_builder.py` line 10 comes from `cfg["num_profes"]`, not from `len(data["profesores"])`. The professor iteration loops on lines 319, 325, 338, 344, 356 iterate `range(NUM_PROFES)`, which may not match the actual professor count.  
**Impact:** If the UI sends 15 professors but `num_profes` is 20, the solver creates variables for 5 non-existent professors. If the UI sends 25 professors, 5 are silently ignored.  
**Recommendation:** Derive `NUM_PROFES` from `len(data["profesores"])`, never from config.

---

#### P1-13: Frontend category mapping is lossy

**File:** `src/scheduler/application/data_builder.py`, lines 157-165  
**Description:** The `_categoria_a_area_y_tipo()` function maps UI categories to solver areas: `"Software"` maps to `"Desarrollo de Software"` (presencial_pc), `"Humanidades"` maps to `"Humanidades"` (presencial_comun), `"Ciencias Basicas"` maps to `"Ciencias Basicas"` (presencial_comun). All other values default to `"Desarrollo de Software"` (presencial_pc). The original `build_data()` has 7 distinct areas (Desarrollo de Software, Infraestructura TI, Ciencia de Datos, Humanidades, Ciencias Basicas, Investigacion, Idiomas, Electivas), but the frontend only offers 3 categories (`MateriasPage.vue` line 11: `CATEGORIAS = ['Software', 'Humanidades', 'Ciencias Basicas']`).  
**Impact:** Infrastructure, Data Science, Research, Languages, and Elective courses cannot be properly categorized through the UI. Everything falls into one of three buckets, losing the discipline-area granularity the solver uses for workload balancing.  
**Recommendation:** Expose the full area taxonomy in the UI category selector. Allow custom areas.

---

#### P1-14: `AREAS_DISCIPLINARES` hardcoded in solver

**File:** `src/scheduler/infrastructure/optimization/model_builder.py`, lines 61-67  
**Description:** The set `AREAS_DISCIPLINARES = {"desarrollo de software", "ciencia de datos", "infraestructura ti", "disciplinar", "disciplinares"}` determines which courses are eligible for 3-group random selection. This is only used in the non-UI path (when `Gc_override` is None), but it represents domain knowledge embedded in solver code.  
**Impact:** Adding new disciplinary areas requires editing the solver code.  
**Recommendation:** Move to configuration or database. In the UI path this code is not reached, but for the CLI path it should be data-driven.

---

### 3.3 P2 -- Medium

Technical debt that should be addressed for maintainability and reliability.

---

#### P2-01: Day names hardcoded in extractor

**File:** `src/scheduler/infrastructure/optimization/extractor.py`, line 15  
**Description:** `dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]` -- hardcoded Spanish day names used as output labels.  
**Impact:** Cannot support other languages or day configurations. The accent on "Miercoles" and "Sabado" is inconsistent with the frontend which uses "Miercoles" with accent ("Miercoles") and "Sabado" with accent.  
**Recommendation:** Pass day names through configuration. Ensure accent consistency.

---

#### P2-02: Railway production URL hardcoded in frontend

**File:** `frontend/src/services/api.js`, lines 1-3  
**Description:** The production API URL `https://tesisomuerte-production-6d83.up.railway.app/api` is hardcoded as the fallback when `VITE_API_BASE_URL` is not set.  
**Impact:** Deploying to a different environment requires either setting the env var or modifying source code. The URL contains the project name "tesisomuerte" which is informal.  
**Recommendation:** Require `VITE_API_BASE_URL` in production builds. Remove hardcoded fallback. Fail explicitly if not configured.

---

#### P2-03: University name hardcoded in multiple locations

**Files:**
- `LoginPage.vue` line 56: `"Universidad Manuel Beltran"`
- `LoginPage.vue` line 172: `"2025 Universidad Manuel Beltran"`
- `CalendarioPage.vue` line 353: `"cronograma_UMB_"` in export filename
- `App.vue` line 109: `"Sistema de Horarios"` label

**Description:** The institution name and abbreviation are scattered across frontend templates as string literals.  
**Impact:** Deploying for a different institution requires finding and changing every occurrence.  
**Recommendation:** Extract to a single configuration file or environment variable (e.g., `VITE_INSTITUTION_NAME`).

---

#### P2-04: `DashboardPage.vue` room location derived from room number with hardcoded logic

**File:** `frontend/src/pages/DashboardPage.vue`, lines 77-84  
**Description:** `getRoomLocation()` (line 77) extracts a number from the room name and assigns building/floor: `if (nombre.toLowerCase().startsWith('lab')) return "Edificio A - Piso ${num <= 6 ? 1 : 2}"`, else `"Edificio B - Piso ${num <= 4 ? 1 : 2}"`. `getRoomCapacity()` (line 82) returns 30 for labs, 40 for others.  
**Impact:** These physical layout assumptions are specific to one building and will be wrong for any other campus.  
**Recommendation:** Make room metadata (building, floor, capacity) part of the room data model rather than derived from naming conventions.

---

#### P2-05: `NullPool` disables connection pooling

**File:** `src/scheduler/infrastructure/database.py`, line 48  
**Description:** `poolclass=NullPool` is used, meaning every database operation creates a new connection and immediately closes it.  
**Impact:** Higher latency for database operations. Under load, this can exhaust database connection limits. The comment says "Disable connection pooling" without explaining why.  
**Recommendation:** Use default connection pooling (`QueuePool`) with appropriate `pool_size` and `max_overflow` settings. `NullPool` is only appropriate for specific patterns like thread-per-request with SQLite.

---

#### P2-06: `RunJob.created_at` uses `String` instead of `DateTime`

**File:** `src/scheduler/infrastructure/models.py`, lines 57-59  
**Description:** `created_at`, `started_at`, and `finished_at` are all `Column(String)`. Timestamps are stored as ISO format strings.  
**Impact:** Cannot perform date-based queries, ordering, or filtering at the database level. No timezone awareness. Parsing is fragile (e.g., `main.py` line 255: `datetime.fromisoformat(started.replace("Z", "+00:00"))`).  
**Recommendation:** Use `Column(DateTime(timezone=True))` with proper SQLAlchemy UTC handling.

---

#### P2-07: `result_json` stored as `Text` blob

**File:** `src/scheduler/infrastructure/models.py`, line 59  
**Description:** The entire solver result (including the full schedule preview with all assignments) is serialized to JSON and stored in a `Text` column.  
**Impact:** Cannot query individual assignments. The JSON blob can be very large for schedules with hundreds of assignments. No schema validation on the stored JSON.  
**Recommendation:** Normalize the result into proper relational tables (e.g., `schedule`, `assignment` tables).

---

#### P2-08: WeeklyCalendar.vue only shows 5 days (Monday-Friday)

**File:** `frontend/src/components/WeeklyCalendar.vue`, line 9  
**Description:** `const DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']` -- Saturday is missing even though the solver supports 6 days and the main calendar page shows Saturday.  
**Impact:** The WeeklyCalendar component (used in SchedulerView) will not display Saturday classes.  
**Recommendation:** Either include Saturday or derive days from the same source as the rest of the app.

---

#### P2-09: `_JsonEncoder` is optional and fragile

**File:** `src/scheduler/interfaces/api/main.py`, lines 11-23  
**Description:** A custom JSON encoder for numpy types is wrapped in a `try/except ImportError`, falling back to the standard encoder if numpy is not installed.  
**Impact:** If numpy is not installed, serialization of solver results containing numpy types will fail at runtime with a `TypeError`, not at import time.  
**Recommendation:** Add numpy to explicit dependencies or handle numpy type conversion before JSON serialization.

---

#### P2-10: Solver timeout mismatch between backend and frontend

**File:** `src/scheduler/config/settings.py` line 11 (`max_time_seconds: 6000`); `frontend/src/store/state.js` line 13 (`SOLVER_TIMEOUT_S = 30`)  
**Description:** The backend default solver timeout is 6000 seconds (100 minutes). The frontend always sends 30 seconds. The stale-job timeout is 300 seconds (5 minutes).  
**Impact:** The 30-second frontend timeout is very aggressive for large problem instances. The 6000-second backend default is never used but would tie up resources if someone hits the API directly without the frontend override.  
**Recommendation:** Align timeout defaults. Set a reasonable maximum (e.g., 300 seconds) in the backend that cannot be overridden by the client.

---

#### P2-11: `save-data` endpoint silently skips professors without valid materia mapping

**File:** `src/scheduler/interfaces/api/main.py`, lines 360-369  
**Description:** When saving professors, if a `materia_id` cannot be resolved, the professor is silently skipped (`if not materia_id: continue`, line 367).  
**Impact:** Users believe their data is saved, but some professors may be silently dropped. No feedback or error message is returned for skipped records.  
**Recommendation:** Return a warning or error listing which professors could not be saved and why.

---

#### P2-12: Frontend solver progress is simulated, not real

**File:** `frontend/src/pages/ParametrosPage.vue`, lines 65-82  
**Description:** The progress bar uses a quadratic ease-out function based on elapsed time divided by `SOLVER_TIMEOUT_S`, capped at 95%. The "stage" labels (lines 74-82: "Inicializando...", "Construyendo modelo...", "Buscando primera solucion...") are time-based heuristics, not actual solver state.  
**Impact:** Users see a progress bar that may be misleading -- a solver stuck at 5% may show 60% progress if enough time has elapsed.  
**Recommendation:** Stream actual solver status from the backend (e.g., current objective value, number of solutions found).

---

#### P2-13: Classroom capacity hardcoded at 25 in CLI path

**File:** `src/scheduler/application/data_builder.py`, line 127  
**Description:** In `build_data()`, all classrooms get `capacidad_salon[s] = 25` regardless of type.  
**Impact:** The CLI path ignores the UI-configurable capacity values (40 for common, 30 for PC). Only matters for CLI usage, but it means CLI and UI paths produce different results even with the same logical configuration.  
**Recommendation:** Use config values for capacity in both paths.

---

#### P2-14: Exception handling swallows errors silently

**File:** `src/scheduler/interfaces/api/main.py`, lines 125-128  
**Description:** `_update_job_db()` catches all exceptions from the database update, then catches again on rollback, and silently continues. The `init_db()` call (lines 61-64) also catches and prints a warning but continues.  
**Impact:** Database failures during job status updates are silently lost. A job might complete successfully but its result is never recorded.  
**Recommendation:** Log exceptions properly. Consider whether the caller should be notified.

---

#### P2-15: Frontend `profesorId` field name collision

**File:** `frontend/src/store/state.js`, line 139  
**Description:** Each professor object has both an `id` (auto-incremented Vue-local ID) and a `profesorId` (the user-entered code like "DOC-001"). The naming is confusing -- `profesorId` is not the professor's ID, it is their institutional code.  
**Impact:** Code reading and maintenance confusion. The `profesorId` is used as the professor's `codigo` when saving to the database (`ParametrosPage.vue` line 189).  
**Recommendation:** Rename `profesorId` to `codigo` in the frontend data model to match the backend.

---

#### P2-16: No input sanitization on API endpoints

**File:** `src/scheduler/interfaces/api/main.py`, lines 229-238  
**Description:** The `RunRequest` model accepts arbitrary dicts for `materias` and `profesores` (lines 181-182). The `aulas` dict is also unvalidated. Values are cast with `int()` but no bounds checking beyond what Pydantic provides.  
**Impact:** Malformed input could cause unexpected solver behavior, very large problem instances, or memory exhaustion.  
**Recommendation:** Add comprehensive Pydantic validation with min/max bounds on all numeric fields. Limit array sizes.

---

### 3.4 P3 -- Low

Minor improvements for code quality and developer experience.

---

#### P3-01: `pymysql` in dependencies but only PostgreSQL is used

**File:** `requirements.txt` line 4; `pyproject.toml` line 14  
**Description:** `pymysql` (MySQL driver) is listed as a dependency, but the database module (`database.py`) only builds PostgreSQL URLs and uses `psycopg2-binary`.  
**Impact:** Unnecessary dependency increases install size and potential attack surface.  
**Recommendation:** Remove `pymysql` from both `requirements.txt` and `pyproject.toml`.

---

#### P3-02: `requests` library unused

**File:** `requirements.txt` line 10  
**Description:** The `requests` library is listed in `requirements.txt` but no Python file imports or uses it.  
**Impact:** Unnecessary dependency.  
**Recommendation:** Remove from `requirements.txt`.

---

#### P3-03: `StepperBar.vue` component may be unused

**File:** `frontend/src/components/StepperBar.vue`, 88 lines  
**Description:** `StepperBar.vue` uses a `currentStep` prop and has similar but slightly different logic to `ProgressStepper.vue` (which uses `activeStep`). Grep for `StepperBar` shows no imports in any page or component file.  
**Impact:** Dead code in the component library.  
**Recommendation:** Verify usage and remove if unused.

---

#### P3-04: `StatusCard.vue` component only used in dead view

**File:** `frontend/src/components/StatusCard.vue`, 26 lines  
**Description:** Only imported by `DashboardView.vue` (a dead view file -- see Dead Code inventory). Not used by any active page.  
**Impact:** Dead code.  
**Recommendation:** Remove along with `DashboardView.vue`.

---

#### P3-05: Excel column widths hardcoded

**File:** `src/scheduler/infrastructure/exporters/excel_exporter.py`, lines 129-132  
**Description:** Column widths are hardcoded as `{"A": 10, "B": 38, ...}` and row heights as `28` and `95`.  
**Impact:** Minor -- these are reasonable defaults but might not accommodate all data lengths.  
**Recommendation:** Consider auto-width calculation or make configurable.

---

#### P3-06: Copyright year hardcoded as 2025

**File:** `frontend/src/pages/LoginPage.vue`, line 172  
**Description:** `"2025 Universidad Manuel Beltran"` -- the copyright year is a static string.  
**Impact:** Displays outdated year after December 2025.  
**Recommendation:** Use `new Date().getFullYear()` dynamically.

---

#### P3-07: `_safe_stat()` pattern in excel exporter is overly defensive

**File:** `src/scheduler/infrastructure/exporters/excel_exporter.py`, lines 8-12  
**Description:** The `_safe_stat()` function wraps every solver stat call in a try/except returning a default, making it impossible to diagnose which stats are failing.  
**Impact:** Debugging difficulty. Silent data loss in exported statistics.  
**Recommendation:** Log warnings when stats are unavailable. Only catch specific expected exceptions.

---

#### P3-08: `create_engine` imported but unused in models.py

**File:** `src/scheduler/infrastructure/models.py`, line 2  
**Description:** `from sqlalchemy import ... create_engine` is imported but never used (the engine is created in `database.py`).  
**Impact:** Unnecessary import.  
**Recommendation:** Remove `create_engine` from the import statement.

---

#### P3-09: `declarative_base` uses deprecated API

**File:** `src/scheduler/infrastructure/models.py`, line 3  
**Description:** `from sqlalchemy.ext.declarative import declarative_base` -- this import path has been deprecated since SQLAlchemy 1.4 in favor of `from sqlalchemy.orm import declarative_base` (or the newer `DeclarativeBase` pattern in 2.0).  
**Impact:** Will generate deprecation warnings with newer SQLAlchemy versions.  
**Recommendation:** Update to `from sqlalchemy.orm import DeclarativeBase` and use the class-based pattern.

---

## 4. Hardcoded Data Inventory

| # | File | Line(s) | Data | Value |
|---|------|---------|------|-------|
| 1 | `data_builder.py` | 20-71 | 48 university subjects | Names, credits, areas as Python tuples |
| 2 | `data_builder.py` | 78-94 | Virtual course names | 15 normalized subject names in a set |
| 3 | `data_builder.py` | 96-101 | Humanities common courses | 4 normalized subject names in a set |
| 4 | `data_builder.py` | 119 | Professor names | `"Prof_{i+1:02d}"` pattern |
| 5 | `data_builder.py` | 122 | Classroom names | `"Salon_{i+1:02d}"` pattern |
| 6 | `data_builder.py` | 127 | Classroom capacity (CLI) | `25` for all classrooms |
| 7 | `data_builder.py` | 159-165 | Category-to-area mapping | 3 explicit mappings + default |
| 8 | `model_builder.py` | 61-67 | Disciplinary areas | 5 normalized area names |
| 9 | `model_builder.py` | 107-108 | Infrastructure course detection | String match on `"infraestructura"` |
| 10 | `model_builder.py` | 109 | Infrastructure professor | Always professor index 0 |
| 11 | `model_builder.py` | 112 | Infrastructure classroom | Always first PC lab |
| 12 | `model_builder.py` | 183-187 | Valid start positions per session length | Fixed ranges for L=1,2,3 |
| 13 | `model_builder.py` | 371 | Objective weights | `200`, `20`, `1` for balance vs preference |
| 14 | `settings.py` | 1-12 | Default configuration | seed=123, 20 profs, 6 days, 11 blocks, etc. |
| 15 | `extractor.py` | 15 | Day names | `["Lunes", "Martes", ...]` |
| 16 | `LoginPage.vue` | 20 | Auth credentials | `admin` / `admin` |
| 17 | `LoginPage.vue` | 56 | University name | `"Universidad Manuel Beltran"` |
| 18 | `LoginPage.vue` | 172 | Copyright notice | `"2025 Universidad Manuel Beltran"` |
| 19 | `CalendarioPage.vue` | 353 | Export filename prefix | `"cronograma_UMB_"` |
| 20 | `App.vue` | 109 | System subtitle | `"Sistema de Horarios"` |
| 21 | `api.js` | 3 | Production API URL | `"https://tesisomuerte-production-6d83.up.railway.app/api"` |
| 22 | `DashboardPage.vue` | 77-84 | Room location/capacity logic | Building/floor derived from room number |
| 23 | `state.js` | 13 | Solver timeout | `SOLVER_TIMEOUT_S = 30` |
| 24 | `state.js` | 26-29 | Default aulas config | Capacities and counts |
| 25 | `state.js` | 32-33 | Calendar structure | 6 days, 11 hours, Spanish names |
| 26 | `MateriasPage.vue` | 11 | Category options | `['Software', 'Humanidades', 'Ciencias Basicas']` |
| 27 | `WeeklyCalendar.vue` | 9 | Day names (5 only) | `['Lunes', ..., 'Viernes']` |
| 28 | `WeeklyCalendar.vue` | 11-14 | Hour labels (11 blocks) | `['7:00-8:00', ...]` |
| 29 | `ParametrosPage.vue` | 9 | Day-to-index mapping | `DAY_MAP` object |
| 30 | `ParametrosPage.vue` | 107-125 | Infeasibility suggestions | 3 sets of suggestion strings |
| 31 | `main.py` (API) | 282-283 | Verification day/hour names | `DIAS` and `HORAS` arrays |
| 32 | `solver_runner.py` | 12 | Worker count | `min(max(1, cpu_count()), 2)` |
| 33 | `excel_exporter.py` | 129-136 | Column widths and row heights | Fixed pixel values |
| 34 | `App.vue` | 88 | Sidebar color | `#8C1515` (institutional red) |

---

## 5. Dead Code Inventory

| # | File | Lines | Description | Evidence |
|---|------|-------|-------------|----------|
| 1 | `frontend/src/router/index.js` | 1-13 | Vue Router configuration with 2 routes | Never imported in `main.js`. App uses step-based navigation via `state.step`. |
| 2 | `frontend/src/views/DashboardView.vue` | 1-62 | Original dashboard view with StatusCard | Only referenced by the dead router. Not imported by any active component. |
| 3 | `frontend/src/views/SchedulerView.vue` | 1-732 | Full scheduler page with steps, materias, profesores, and results | Only referenced by the dead router. Contains 732 lines of abandoned code. |
| 4 | `frontend/src/components/StatusCard.vue` | 1-26 | Status indicator card component | Only imported by the dead `DashboardView.vue`. |
| 5 | `frontend/src/components/StepperBar.vue` | 1-88 | Alternative stepper bar component | Appears unused -- `ProgressStepper.vue` is used instead. Not imported by any active file. |
| 6 | `data_builder.py` `build_data()` | 17-142 | Original data builder with 48 hardcoded subjects | Only called from `run_pipeline.py` when `data is None`, which only happens via CLI. The API always provides data via `build_data_from_ui()`. |
| 7 | `requirements.txt` line 4 | - | `pymysql` dependency | Only PostgreSQL (`psycopg2-binary`) is used. |
| 8 | `requirements.txt` line 10 | - | `requests` dependency | Not imported anywhere in the codebase. |
| 9 | `models.py` line 2 | - | `create_engine` import | Imported but never used in this file. |

**Total dead lines:** ~920 lines (router 13 + DashboardView 62 + SchedulerView 732 + StatusCard 26 + StepperBar 88)

---

## 6. Temporary / Demo Code Inventory

| # | File | Lines | Description |
|---|------|-------|-------------|
| 1 | `LoginPage.vue` | 19-26 | `setTimeout(500ms)` simulated auth with hardcoded `admin/admin` |
| 2 | `state.js` | 252-281 | `generateDemoSchedule()` function creating fake schedule events with `evt_demo_` prefix |
| 3 | `data_builder.py` | 20-71 | 48 hardcoded subjects as development seed data |
| 4 | `model_builder.py` | 94-96 | Random professor candidate selection (`random.sample`) |
| 5 | `model_builder.py` | 124 | Random preference generation (`random.randint(0, 10)`) |
| 6 | `model_builder.py` | 126 | Random student counts (`random.randint(20, 25)`) |
| 7 | `SchedulerView.vue` | 16-19 | Inline hardcoded sample materias and profesores |
| 8 | `api.js` | 3 | Hardcoded Railway URL (development/thesis deployment) |

---

## 7. Security Issues

| # | Severity | Issue | File | Line(s) |
|---|----------|-------|------|---------|
| 1 | **Critical** | No authentication system | Multiple | - |
| 2 | **Critical** | Hardcoded credentials `admin/admin` | `LoginPage.vue` | 20 |
| 3 | **Critical** | CORS `allow_origins=["*"]` with credentials | `main.py` | 53-59 |
| 4 | **Critical** | Unauthenticated DELETE endpoints (clear-data, reset-db) | `main.py` | 394-416 |
| 5 | **High** | Raw SQL in `reset-db` endpoint | `main.py` | 411 |
| 6 | **High** | No rate limiting on solver endpoint | `main.py` | 229-238 |
| 7 | **High** | No input size limits on solver requests | `main.py` | 174-183 |
| 8 | **Medium** | Exception details exposed to client | `main.py` | 375, 383, 401, 416 |
| 9 | **Medium** | No CSRF protection | `main.py` | - |
| 10 | **Medium** | Solver `max_time_seconds` controllable by client | `main.py` | 95 |
| 11 | **Low** | `.env` file loaded with `dotenv` but no `.env.example` for secrets documentation | `database.py` | 14 |
| 12 | **Low** | Database password potentially in URL parameters (logged in errors) | `database.py` | 38 |

---

## 8. Dependency Analysis

### Backend (`requirements.txt` / `pyproject.toml`)

| Package | Version | Used? | Notes |
|---------|---------|-------|-------|
| `ortools` | 9.15.6755 | Yes | Core solver. Pinned version. |
| `pandas` | unpinned | Yes | DataFrame operations in extractor/exporter |
| `openpyxl` | unpinned | Yes | Excel file formatting |
| `pymysql` | unpinned | **No** | MySQL driver -- only PostgreSQL is used |
| `psycopg2-binary` | unpinned | Yes | PostgreSQL driver |
| `python-dotenv` | unpinned | Yes | `.env` file loading |
| `sqlalchemy` | unpinned | Yes | ORM -- uses deprecated `declarative_base` path |
| `fastapi` | unpinned | Yes | Web framework |
| `uvicorn[standard]` | unpinned | Yes | ASGI server (in requirements.txt only, not pyproject.toml) |
| `requests` | unpinned | **No** | Not imported anywhere |

**Issues:**
- `fastapi` and `uvicorn` are in `requirements.txt` but not in `pyproject.toml` dependencies.
- Most packages are unpinned, risking breaking changes on install.
- `pymysql` and `requests` are unnecessary.

### Frontend (inferred from imports)

| Package | Used? | Notes |
|---------|-------|-------|
| `vue` | Yes | Core framework (v3, Composition API) |
| `vue-router` | **Partially** | Installed and configured but never used in active app |
| `xlsx` (SheetJS) | Yes | Excel export in CalendarioPage |
| `vite` | Yes | Build tool |

---

## 9. Metrics

### Lines of Code

| Category | Files | Total Lines |
|----------|-------|-------------|
| Python backend (source) | 12 | 1,555 |
| Python backend (__init__.py) | 10 | 10 |
| Vue pages | 6 | 4,127 |
| Vue components | 6 | 682 |
| JS modules (store, api, lib, composables) | 5 | 490 |
| Dead Vue files (views, router) | 3 | 807 |
| **Total** | **42** | **7,671** |

### Complexity Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| Largest Python file | `main.py` (API) -- 418 lines | Monolithic, needs splitting |
| Largest Vue file | `CalendarioPage.vue` -- 973 lines | Complex but well-structured |
| Largest dead file | `SchedulerView.vue` -- 732 lines | Should be removed |
| CP-SAT model builder | 400 lines | High complexity, no tests |
| Total CP-SAT variables | Dynamic (combinatorial) | Can be very large for 40+ subjects |
| Number of database tables | 3 | Insufficient for the data model |
| Number of API endpoints | 9 | All in one file |
| Test coverage | 0% | No tests exist |
| Dead code ratio | ~12% (807/7,671) | Significant cleanup opportunity |

---

## 10. Conclusion and Migration Risk Assessment

### Current State

The system is a **working thesis prototype** that successfully demonstrates constraint-based schedule optimization. The CP-SAT solver model, while complex and hardcoded, is mathematically sound and produces valid schedules when properly configured through the UI. The Vue 3 frontend is well-designed from a UX perspective with good accessibility attributes and responsive design.

### Migration Risks

**High Risk:**
1. **Solver model refactoring** -- The 400-line `model_builder.py` is the intellectual core of the system. Any refactoring must preserve the mathematical properties of the constraint model. Without tests, this is extremely risky.
2. **Data model migration** -- Moving from localStorage to database-first requires rethinking the entire data flow. The many-to-many professor-subject relationship needs a junction table.
3. **Authentication addition** -- Retrofitting auth into a system designed without it affects every endpoint and the entire frontend navigation flow.

**Medium Risk:**
4. **Dead code removal** -- The router, views, and unused components can be safely removed, but must verify no runtime dynamic imports exist.
5. **Configuration extraction** -- Moving hardcoded values to configuration is straightforward but tedious, with many string-matching dependencies.

**Low Risk:**
6. **Dependency cleanup** -- Removing `pymysql` and `requests` is safe.
7. **Frontend category expansion** -- Adding more categories to `MateriasPage` is low risk.

### Recommended Migration Order

1. **Add tests first** -- Before any refactoring, write tests that verify current solver behavior (golden-file tests comparing output for known inputs).
2. **Fix security** -- Add authentication, restrict CORS, protect destructive endpoints.
3. **Fix data model** -- Design proper database schema, add Alembic migrations, implement many-to-many relationships.
4. **Remove dead code** -- Clean up router, dead views, unused dependencies.
5. **Extract configuration** -- Move all hardcoded values to configuration.
6. **Refactor API** -- Split monolithic `main.py` into modular routes.
7. **Add task queue** -- Replace threading with Celery or equivalent.
8. **Generalize solver** -- Make constraint model configurable for different institutions.

---

*End of Audit Report*
