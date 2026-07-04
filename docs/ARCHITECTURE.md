# Architecture Design Document

**System**: University Schedule Optimization Platform
**Version**: 2.0 (Redesign)
**Status**: Approved for implementation
**Date**: 2026-06-28

---

## Table of Contents

1. [Architectural Overview](#1-architectural-overview)
2. [Backend Architecture](#2-backend-architecture)
3. [Solver Architecture](#3-solver-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Communication Between Modules](#5-communication-between-modules)
6. [Authentication and Authorization](#6-authentication-and-authorization)
7. [Repository Structure](#7-repository-structure)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [Technology Decisions](#9-technology-decisions)
10. [Scalability Considerations](#10-scalability-considerations)
11. [Migration Strategy](#11-migration-strategy)

---

## 1. Architectural Overview

### Problem Statement

The current prototype is a monolithic system with 49 hardcoded subjects, randomly
generated professors, and no concept of institutional structure. The entire
"database" is localStorage on the browser. The solver contains university-specific
logic (subject names like "Catedra Manuela Beltran", infrastructure professor
assignments by string matching). There is no authentication, no roles, no audit
trail, and no way for multiple academic areas to collaborate on schedule creation.

This redesign transforms the prototype into a generic, multi-tenant university
schedule generation engine where data drives everything and the solver is a pure
optimization function.

### Architectural Pattern: Clean Architecture

The system follows Clean Architecture (Ports and Adapters) with four concentric
layers. The dependency rule is absolute: inner layers never import from outer
layers.

```
+------------------------------------------------------------------+
|                        INTERFACES LAYER                          |
|  FastAPI routes, CLI commands, WebSocket handlers                |
|  This layer adapts external input to application use cases.      |
+------------------------------------------------------------------+
|                       APPLICATION LAYER                          |
|  Use cases, DTOs, command/query handlers                         |
|  Orchestrates domain objects. No framework imports.              |
+------------------------------------------------------------------+
|                         DOMAIN LAYER                             |
|  Entities, value objects, repository interfaces, domain services |
|  Pure Python. Zero external dependencies.                        |
+------------------------------------------------------------------+
|                      INFRASTRUCTURE LAYER                        |
|  SQLAlchemy repos, OR-Tools adapter, Excel I/O, email, Redis    |
|  Implements interfaces defined in Domain.                        |
+------------------------------------------------------------------+
```

**Layer responsibilities:**

**Domain Layer** (innermost) -- Contains the business rules that exist regardless
of any software system. An `Instructor` entity has availability constraints. A
`Classroom` has capacity and equipment. A `Subject` has credit hours. These rules
do not change if you switch databases, replace the solver, or rewrite the UI. The
domain layer defines repository interfaces (ports) but never implements them.

**Application Layer** -- Contains use cases that orchestrate domain entities. "Area
coordinator uploads an academic offering" is a use case. It receives a DTO, calls
domain services for validation, and invokes repository interfaces to persist. This
layer knows nothing about FastAPI, SQLAlchemy, or OR-Tools. It depends only on the
domain layer.

**Infrastructure Layer** -- Implements the interfaces declared in the domain layer.
The `SQLAlchemySubjectRepository` implements `SubjectRepository`. The
`ORToolsSolverAdapter` implements `ScheduleSolver`. The `ExcelImporter` implements
`OfferingImporter`. This layer contains all framework-specific code.

**Interfaces Layer** (outermost) -- HTTP routes, CLI commands, WebSocket endpoints.
Translates HTTP requests into DTOs, calls use cases, and formats responses. This
layer is thin. A route handler should be 5-15 lines: parse input, call use case,
return response.

### Why Clean Architecture for This Project

The solver is the most valuable piece of this system. It took significant effort to
build the CP-SAT model correctly. Clean Architecture lets us:

1. Swap the database without touching the solver or business rules.
2. Run the solver in tests with in-memory repositories.
3. Replace the FastAPI interface with a CLI, gRPC, or batch processor.
4. Evolve the domain model (add new constraint types) without touching infrastructure.
5. Test use cases in isolation with mock repositories.

The prototype's biggest failure was coupling: `data_builder.py` contains hardcoded
subject lists, `model_builder.py` contains infrastructure-professor heuristics by
string matching, and the API layer creates database sessions directly. Clean
Architecture eliminates all of this coupling.

---

## 2. Backend Architecture

### Python Package Structure

```
backend/
  src/
    schedule_engine/
      domain/
        entities/
          __init__.py
          university.py          # University aggregate root
          area.py                # AcademicArea entity
          program.py             # AcademicProgram entity
          study_plan.py          # StudyPlan entity
          subject.py             # Subject entity
          academic_offering.py   # AcademicOffering + Group value object
          instructor.py          # Instructor entity
          contract.py            # Contract value object
          specialty.py           # Specialty value object
          availability.py        # Availability value object
          classroom.py           # Classroom entity
          equipment.py           # Equipment value object
          constraint.py          # Constraint entity (soft/hard)
          schedule.py            # Schedule aggregate root
          time_slot.py           # TimeSlot value object
          assignment.py          # Assignment value object
          publication.py         # Publication entity
          user.py                # User entity
          role.py                # Role + Permission value objects
          import_record.py       # ImportRecord entity
          validation.py          # ValidationRecord entity

        value_objects/
          __init__.py
          credit_hours.py        # CreditHours (1-6, validated)
          day_of_week.py         # DayOfWeek enum
          time_block.py          # TimeBlock (start_hour, end_hour)
          semester.py            # Semester (year, period)
          constraint_type.py     # ConstraintType enum (hard/soft)
          schedule_status.py     # ScheduleStatus enum
          offering_status.py     # OfferingStatus enum

        repositories/
          __init__.py
          university_repository.py
          area_repository.py
          subject_repository.py
          instructor_repository.py
          classroom_repository.py
          offering_repository.py
          schedule_repository.py
          constraint_repository.py
          user_repository.py

        services/
          __init__.py
          offering_validation_service.py   # Domain rules for offering validation
          conflict_detection_service.py    # Detects scheduling conflicts
          constraint_evaluation_service.py # Evaluates constraint satisfaction
          schedule_scoring_service.py      # Scores schedule quality

        exceptions.py            # Domain-specific exceptions

      application/
        use_cases/
          __init__.py
          offerings/
            __init__.py
            create_offering.py          # Area submits offering
            validate_offering.py        # Director validates
            consolidate_offerings.py    # Merge all offerings for solver
            import_offering_excel.py    # Import from Excel
          schedule/
            __init__.py
            generate_schedule.py        # Trigger solver
            get_schedule_status.py      # Poll solver job
            modify_assignment.py        # Director moves a class
            publish_schedule.py         # Publish final schedule
            export_schedule.py          # Export to Excel/PDF
          subjects/
            __init__.py
            create_subject.py
            update_subject.py
            list_subjects.py
          instructors/
            __init__.py
            create_instructor.py
            update_instructor.py
            assign_specialties.py
            set_availability.py
          classrooms/
            __init__.py
            create_classroom.py
            update_classroom.py
            set_equipment.py
          users/
            __init__.py
            register_user.py
            authenticate_user.py
            assign_role.py
          constraints/
            __init__.py
            create_constraint.py
            update_constraint.py

        dto/
          __init__.py
          offering_dto.py
          schedule_dto.py
          subject_dto.py
          instructor_dto.py
          classroom_dto.py
          solver_input_dto.py    # Structured input for solver
          solver_output_dto.py   # Structured output from solver
          user_dto.py
          auth_dto.py

        interfaces/
          __init__.py
          solver_interface.py       # Abstract: ScheduleSolver
          importer_interface.py     # Abstract: OfferingImporter
          exporter_interface.py     # Abstract: ScheduleExporter
          notification_interface.py # Abstract: NotificationService
          task_queue_interface.py   # Abstract: TaskQueue

      infrastructure/
        persistence/
          __init__.py
          database.py               # Engine, session factory, base
          models/
            __init__.py
            university_model.py
            area_model.py
            program_model.py
            study_plan_model.py
            subject_model.py
            offering_model.py
            group_model.py
            instructor_model.py
            contract_model.py
            specialty_model.py
            availability_model.py
            classroom_model.py
            equipment_model.py
            constraint_model.py
            schedule_model.py
            assignment_model.py
            publication_model.py
            user_model.py
            role_model.py
            import_model.py
            validation_model.py
            run_job_model.py
          repositories/
            __init__.py
            sqlalchemy_university_repo.py
            sqlalchemy_area_repo.py
            sqlalchemy_subject_repo.py
            sqlalchemy_instructor_repo.py
            sqlalchemy_classroom_repo.py
            sqlalchemy_offering_repo.py
            sqlalchemy_schedule_repo.py
            sqlalchemy_constraint_repo.py
            sqlalchemy_user_repo.py

        solver/
          __init__.py
          ortools_adapter.py      # Implements ScheduleSolver interface
          model_builder.py        # Builds CP-SAT model from DTOs
          solution_extractor.py   # Extracts assignments from solved model
          progress_callback.py    # Reports solver progress via callback

        importers/
          __init__.py
          excel_importer.py       # Reads Excel offering files
          csv_importer.py         # Reads CSV offering files

        exporters/
          __init__.py
          excel_exporter.py       # Writes schedule to Excel
          pdf_exporter.py         # Writes schedule to PDF

        auth/
          __init__.py
          jwt_provider.py         # JWT token creation/validation
          password_hasher.py      # bcrypt password hashing

        tasks/
          __init__.py
          celery_app.py           # Celery application configuration
          solver_task.py          # Celery task for solver execution
          export_task.py          # Celery task for large exports

        notifications/
          __init__.py
          email_service.py        # Email notification implementation

      interfaces/
        api/
          __init__.py
          app.py                  # FastAPI application factory
          dependencies.py         # Dependency injection (get_db, get_current_user)
          middleware.py           # CORS, request ID, error handling
          routes/
            __init__.py
            auth_routes.py        # POST /auth/login, /auth/refresh
            university_routes.py  # CRUD /universities
            area_routes.py        # CRUD /areas
            subject_routes.py     # CRUD /subjects
            instructor_routes.py  # CRUD /instructors
            classroom_routes.py   # CRUD /classrooms
            offering_routes.py    # CRUD + validate /offerings
            schedule_routes.py    # Generate, status, modify, publish
            constraint_routes.py  # CRUD /constraints
            import_routes.py      # POST /import/offerings
            export_routes.py      # GET /export/schedule
            user_routes.py        # User management (admin)
            health_routes.py      # GET /health, /health/db

        websocket/
          __init__.py
          solver_progress.py      # WebSocket: solver progress updates

        cli/
          __init__.py
          commands.py             # CLI commands (migrate, seed, solve)
```

### Domain Layer Details

**Entities** are objects with identity. An `Instructor` with `id=5` is the same
instructor even if their name changes. Entities enforce their own invariants.

```python
# domain/entities/instructor.py (conceptual, not runnable)

class Instructor:
    def __init__(
        self,
        id: InstructorId,
        institutional_id: str,
        full_name: str,
        contract: Contract,
        specialties: list[Specialty],
        availability: list[Availability],
    ):
        self._id = id
        self._institutional_id = institutional_id
        self._full_name = full_name
        self._contract = contract
        self._specialties = list(specialties)
        self._availability = list(availability)

    @property
    def max_weekly_hours(self) -> int:
        return self._contract.max_weekly_hours

    def can_teach(self, subject: Subject) -> bool:
        """Check if instructor has a matching specialty."""
        return any(
            s.subject_area == subject.area
            for s in self._specialties
        )

    def is_available_at(self, day: DayOfWeek, block: TimeBlock) -> bool:
        """Check if instructor is available at a specific time."""
        return any(
            a.day == day and a.covers(block)
            for a in self._availability
        )

    def add_specialty(self, specialty: Specialty) -> None:
        if specialty not in self._specialties:
            self._specialties.append(specialty)
```

**Value Objects** are immutable and compared by value, not identity:

```python
# domain/value_objects/credit_hours.py

class CreditHours:
    def __init__(self, value: int):
        if not 1 <= value <= 6:
            raise ValueError(f"Credit hours must be 1-6, got {value}")
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    @property
    def weekly_blocks(self) -> int:
        """Number of time blocks per week this subject requires."""
        return self._value

    def session_patterns(self) -> list[tuple[int, ...]]:
        """Valid session-length patterns for this credit count.

        Returns list of tuples where each tuple represents one valid
        pattern. E.g., 4 credits -> [(2, 2)] meaning two 2-block sessions.
        3 credits -> [(3,), (2, 1)] meaning one 3-block or one 2+1 split.
        """
        patterns = {
            1: [(1,)],
            2: [(2,)],
            3: [(3,), (2, 1)],
            4: [(2, 2)],
            5: [(3, 2)],
            6: [(3, 3), (2, 2, 2)],
        }
        return patterns[self._value]
```

**Repository Interfaces** define the contract that infrastructure must fulfill:

```python
# domain/repositories/instructor_repository.py

from abc import ABC, abstractmethod

class InstructorRepository(ABC):
    @abstractmethod
    def find_by_id(self, instructor_id: InstructorId) -> Instructor | None:
        ...

    @abstractmethod
    def find_by_area(self, area_id: AreaId) -> list[Instructor]:
        ...

    @abstractmethod
    def find_available_for_subject(
        self, subject_id: SubjectId
    ) -> list[Instructor]:
        ...

    @abstractmethod
    def save(self, instructor: Instructor) -> Instructor:
        ...

    @abstractmethod
    def delete(self, instructor_id: InstructorId) -> None:
        ...
```

### Application Layer Details

Use cases are the entry points for all operations. Each use case is a single
class with an `execute` method. It receives a DTO, orchestrates domain objects,
and returns a result DTO.

```python
# application/use_cases/schedule/generate_schedule.py (conceptual)

class GenerateScheduleUseCase:
    def __init__(
        self,
        offering_repo: OfferingRepository,
        instructor_repo: InstructorRepository,
        classroom_repo: ClassroomRepository,
        constraint_repo: ConstraintRepository,
        schedule_repo: ScheduleRepository,
        solver: ScheduleSolver,
        task_queue: TaskQueue,
    ):
        self._offering_repo = offering_repo
        self._instructor_repo = instructor_repo
        self._classroom_repo = classroom_repo
        self._constraint_repo = constraint_repo
        self._schedule_repo = schedule_repo
        self._solver = solver
        self._task_queue = task_queue

    def execute(self, command: GenerateScheduleCommand) -> GenerateScheduleResult:
        # 1. Load all validated offerings for this semester
        offerings = self._offering_repo.find_validated(
            university_id=command.university_id,
            semester=command.semester,
        )
        if not offerings:
            raise NoValidatedOfferingsError(command.semester)

        # 2. Load instructors, classrooms, constraints
        instructors = self._instructor_repo.find_by_university(
            command.university_id
        )
        classrooms = self._classroom_repo.find_by_university(
            command.university_id
        )
        constraints = self._constraint_repo.find_active(
            command.university_id
        )

        # 3. Build solver input DTO
        solver_input = SolverInputDTO.from_domain(
            offerings=offerings,
            instructors=instructors,
            classrooms=classrooms,
            constraints=constraints,
            config=command.solver_config,
        )

        # 4. Create schedule record in "generating" status
        schedule = Schedule.create(
            university_id=command.university_id,
            semester=command.semester,
            created_by=command.user_id,
        )
        self._schedule_repo.save(schedule)

        # 5. Enqueue solver task
        job_id = self._task_queue.enqueue(
            task_name="solve_schedule",
            payload={
                "schedule_id": str(schedule.id),
                "solver_input": solver_input.to_dict(),
            },
        )

        return GenerateScheduleResult(
            schedule_id=schedule.id,
            job_id=job_id,
            status="queued",
        )
```

### Infrastructure Layer Details

**SQLAlchemy Repository Implementation:**

```python
# infrastructure/persistence/repositories/sqlalchemy_instructor_repo.py

class SQLAlchemyInstructorRepository(InstructorRepository):
    def __init__(self, session: Session):
        self._session = session

    def find_by_id(self, instructor_id: InstructorId) -> Instructor | None:
        model = self._session.query(InstructorModel).filter_by(
            id=instructor_id.value
        ).first()
        return self._to_entity(model) if model else None

    def find_available_for_subject(
        self, subject_id: SubjectId
    ) -> list[Instructor]:
        models = (
            self._session.query(InstructorModel)
            .join(SpecialtyModel)
            .join(SubjectModel)
            .filter(SubjectModel.id == subject_id.value)
            .filter(InstructorModel.is_active == True)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def save(self, instructor: Instructor) -> Instructor:
        model = self._to_model(instructor)
        self._session.merge(model)
        self._session.flush()
        return instructor

    def _to_entity(self, model: InstructorModel) -> Instructor:
        """Maps SQLAlchemy model to domain entity."""
        return Instructor(
            id=InstructorId(model.id),
            institutional_id=model.institutional_id,
            full_name=model.full_name,
            contract=Contract(
                type=model.contract_type,
                max_weekly_hours=model.max_weekly_hours,
            ),
            specialties=[
                Specialty(subject_area=s.subject_area)
                for s in model.specialties
            ],
            availability=[
                Availability(
                    day=DayOfWeek(a.day),
                    start_block=a.start_block,
                    end_block=a.end_block,
                )
                for a in model.availabilities
            ],
        )
```

**OR-Tools Solver Adapter:**

```python
# infrastructure/solver/ortools_adapter.py

class ORToolsSolverAdapter(ScheduleSolver):
    """Implements the ScheduleSolver interface using OR-Tools CP-SAT.

    This adapter receives structured DTOs and returns structured results.
    It never accesses the database. It never knows about SQLAlchemy.
    """

    def solve(
        self,
        solver_input: SolverInputDTO,
        config: SolverConfig,
        progress_callback: Callable[[SolverProgress], None] | None = None,
    ) -> SolverOutputDTO:
        model, meta = self._build_model(solver_input, config)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = config.max_time_seconds
        solver.parameters.num_search_workers = config.num_workers

        if progress_callback:
            callback = _ProgressCallback(progress_callback)
            solver.Solve(model, callback)
        else:
            solver.Solve(model)

        return self._extract_solution(solver, meta, solver_input)
```

### Interfaces Layer Details

Routes are thin. They parse HTTP input, call a use case, and return a response.

```python
# interfaces/api/routes/schedule_routes.py

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post("", status_code=202)
async def generate_schedule(
    body: GenerateScheduleRequest,
    current_user: User = Depends(get_current_user),
    use_case: GenerateScheduleUseCase = Depends(get_generate_schedule_use_case),
):
    require_role(current_user, Role.DIRECTOR)
    command = GenerateScheduleCommand(
        university_id=current_user.university_id,
        semester=Semester(body.year, body.period),
        solver_config=SolverConfig(**body.solver_config),
        user_id=current_user.id,
    )
    result = use_case.execute(command)
    return {
        "schedule_id": str(result.schedule_id),
        "job_id": result.job_id,
        "status": result.status,
    }
```

### Dependency Injection

FastAPI's `Depends` system wires everything together at the interfaces layer.
No service locator, no global state.

```python
# interfaces/api/dependencies.py

def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_instructor_repo(
    db: Session = Depends(get_db),
) -> InstructorRepository:
    return SQLAlchemyInstructorRepository(db)

def get_generate_schedule_use_case(
    offering_repo: OfferingRepository = Depends(get_offering_repo),
    instructor_repo: InstructorRepository = Depends(get_instructor_repo),
    classroom_repo: ClassroomRepository = Depends(get_classroom_repo),
    constraint_repo: ConstraintRepository = Depends(get_constraint_repo),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repo),
    solver: ScheduleSolver = Depends(get_solver),
    task_queue: TaskQueue = Depends(get_task_queue),
) -> GenerateScheduleUseCase:
    return GenerateScheduleUseCase(
        offering_repo=offering_repo,
        instructor_repo=instructor_repo,
        classroom_repo=classroom_repo,
        constraint_repo=constraint_repo,
        schedule_repo=schedule_repo,
        solver=solver,
        task_queue=task_queue,
    )
```

---

## 3. Solver Architecture

The solver is the mathematical core of the system. It is treated as an
independent module behind a strict interface boundary.

### Design Principles

1. **No database access.** The solver receives all data through `SolverInputDTO`
   and returns results through `SolverOutputDTO`. It never imports SQLAlchemy,
   FastAPI, or any infrastructure module.

2. **No hardcoded data.** The current prototype hardcodes 49 subjects, matches
   infrastructure professors by string comparison on subject names, and randomly
   assigns student counts. All of this is eliminated. Every piece of data comes
   from the DTO.

3. **Configurable constraints.** Hard constraints (instructor conflict, room
   conflict) are always active. Soft constraints (load balancing, preferences)
   are parameterized through the configuration.

4. **Progress reporting.** The solver reports progress through a callback
   function. This enables real-time updates to the frontend via WebSocket.

### Solver Input/Output Contract

```python
# application/dto/solver_input_dto.py

@dataclass(frozen=True)
class SolverSubject:
    id: int
    name: str
    credit_hours: int
    area_id: int
    modality: str              # "in_person_standard", "in_person_lab", "virtual"
    session_patterns: list[tuple[int, ...]]   # valid block groupings

@dataclass(frozen=True)
class SolverGroup:
    id: int
    subject_id: int
    group_number: int
    expected_students: int
    eligible_instructor_ids: list[int]

@dataclass(frozen=True)
class SolverInstructor:
    id: int
    name: str
    max_daily_blocks: int
    max_weekly_blocks: int
    available_slots: list[tuple[int, int]]    # (day_index, block_index)
    preference_scores: dict[int, int]         # subject_id -> preference 0-10

@dataclass(frozen=True)
class SolverClassroom:
    id: int
    name: str
    capacity: int
    room_type: str             # "standard", "lab", "auditorium"
    equipment: list[str]

@dataclass(frozen=True)
class SolverConstraint:
    type: str                  # "hard" or "soft"
    category: str              # "instructor_max_daily", "no_gaps", etc.
    parameters: dict           # constraint-specific parameters
    weight: int                # for soft constraints, 0-1000

@dataclass(frozen=True)
class SolverInputDTO:
    subjects: list[SolverSubject]
    groups: list[SolverGroup]
    instructors: list[SolverInstructor]
    classrooms: list[SolverClassroom]
    constraints: list[SolverConstraint]
    num_days: int
    blocks_per_day: int
    time_limit_seconds: int
    num_workers: int
    seed: int

@dataclass(frozen=True)
class SolverAssignment:
    group_id: int
    instructor_id: int
    classroom_id: int
    day_index: int
    block_index: int
    session_length: int        # how many consecutive blocks

@dataclass(frozen=True)
class SolverOutputDTO:
    status: str                # "OPTIMAL", "FEASIBLE", "INFEASIBLE", etc.
    assignments: list[SolverAssignment]
    objective_value: float
    solver_time_seconds: float
    num_variables: int
    num_constraints: int
    statistics: dict           # solver-specific metrics
```

### What Gets Preserved from the Prototype

The CP-SAT model logic in `model_builder.py` is the most valuable part of the
current system. The following mathematical constructs are preserved and
generalized:

- **Decision variables**: `y[p,c,g]` (instructor-to-group assignment),
  `x[p,c,g,b,s]` (block-level occupation), `start[L,tag,p,c,g,d,h,s]`
  (session start variables), `z[c,g]` (session pattern selector for 3-credit
  subjects).
- **Hard constraints**: one instructor per group, no instructor double-booking,
  no room double-booking, session contiguity, room-type compatibility, capacity
  limits.
- **Soft objectives**: workload balancing (min-max spread), deviation from
  target load, instructor preference scores.
- **Session pattern logic**: the current system correctly handles 1-credit
  (1 block), 2-credit (1x2), 3-credit (1x3 or 1x2+1x1), and 4-credit (2x2)
  patterns. This logic is generalized to support arbitrary patterns via the
  `session_patterns` field.

### What Gets Discarded

- Hardcoded subject lists (`build_data()` in `data_builder.py`).
- String-matching heuristics for infrastructure professors
  (`"infraestructura" in nrm(m)`).
- Random candidate generation (`random.sample(range(NUM_PROFES), K)`).
- Random student count generation (`random.randint(20, 25)`).
- Hardcoded virtual/presencial classification by subject name.
- The `norm()` function and all accent-stripping string comparisons.

The full solver design is documented in `SOLVER_DESIGN.md`.

---

## 4. Frontend Architecture

### Current State

The frontend is a Vue 3 SPA using a global reactive object (`state.js`) as a
pseudo-store, with localStorage as the persistence layer. The `SchedulerView.vue`
file duplicates data management that also exists in `state.js`. There is no
authentication, no routing beyond two pages, and no proper API integration for
CRUD operations.

### Target Architecture

```
frontend/
  src/
    api/
      client.js               # Axios instance with interceptors (auth, errors)
      auth.api.js              # login, refresh, logout
      areas.api.js             # CRUD for areas
      subjects.api.js          # CRUD for subjects
      instructors.api.js       # CRUD for instructors
      classrooms.api.js        # CRUD for classrooms
      offerings.api.js         # CRUD + validate + import
      schedules.api.js         # generate, status, modify, publish, export
      constraints.api.js       # CRUD for constraints
      users.api.js             # User management

    stores/
      auth.store.js            # Pinia: user session, tokens, permissions
      areas.store.js           # Pinia: areas list, selected area
      subjects.store.js        # Pinia: subjects CRUD state
      instructors.store.js     # Pinia: instructors CRUD state
      classrooms.store.js      # Pinia: classrooms CRUD state
      offerings.store.js       # Pinia: offerings, validation status
      schedule.store.js        # Pinia: schedule state, solver progress
      constraints.store.js     # Pinia: constraints CRUD state
      ui.store.js              # Pinia: sidebar, theme, notifications

    composables/
      useAuth.js               # Auth logic, guards, token refresh
      usePermissions.js        # Role-based permission checks
      useSolverProgress.js     # WebSocket connection for solver updates
      useExcelImport.js        # Client-side Excel parsing + upload
      useNotifications.js      # Toast/notification system
      usePagination.js         # Pagination state for lists
      useFilters.js            # Filtering/search for data tables

    components/
      layout/
        AppShell.vue           # Main layout: sidebar + header + content
        Sidebar.vue            # Navigation sidebar (role-aware)
        Header.vue             # Top bar: user menu, notifications, breadcrumb

      common/
        DataTable.vue          # Generic table with sort, filter, pagination
        FormField.vue          # Form field wrapper (label, error, hint)
        Modal.vue              # Modal dialog
        ConfirmDialog.vue      # Confirmation dialog
        LoadingSpinner.vue     # Loading states
        EmptyState.vue         # Empty list placeholder
        StatusBadge.vue        # Status indicator
        Toast.vue              # Notification toast

      schedule/
        WeeklyCalendar.vue     # Calendar grid (refactored from current)
        CalendarEvent.vue      # Single event card in calendar
        CalendarFilters.vue    # Filter by instructor, room, area
        SolverProgress.vue     # Real-time solver progress display
        ConflictPanel.vue      # Conflict detection display
        AssignmentEditor.vue   # Drag-and-drop assignment editor

      offerings/
        OfferingForm.vue       # Create/edit offering
        OfferingList.vue       # List with validation status
        OfferingReview.vue     # Director review interface
        ExcelImporter.vue      # Excel file upload and preview

      data/
        SubjectForm.vue
        InstructorForm.vue
        ClassroomForm.vue
        ConstraintForm.vue

    views/
      LoginView.vue
      DashboardView.vue        # Role-specific dashboard
      AreaDashboardView.vue    # Area coordinator's dashboard

      subjects/
        SubjectListView.vue
        SubjectDetailView.vue

      instructors/
        InstructorListView.vue
        InstructorDetailView.vue

      classrooms/
        ClassroomListView.vue
        ClassroomDetailView.vue

      offerings/
        OfferingListView.vue
        OfferingCreateView.vue
        OfferingReviewView.vue

      schedule/
        ScheduleGenerateView.vue
        ScheduleEditView.vue
        SchedulePublishView.vue
        SchedulePublicView.vue    # Public read-only view

      admin/
        UserListView.vue
        RoleManagementView.vue
        UniversitySettingsView.vue

    router/
      index.js                 # Route definitions
      guards.js                # Navigation guards (auth, role checks)

    plugins/
      pinia.js                 # Pinia store setup
      axios.js                 # Axios global configuration

    utils/
      date.js                  # Date formatting utilities
      validation.js            # Form validation helpers
      permissions.js           # Permission constants and helpers

    App.vue
    main.js
```

### State Management with Pinia

Each domain area gets its own Pinia store. Stores call API services and expose
reactive state to components.

```javascript
// stores/schedule.store.js (conceptual)

export const useScheduleStore = defineStore('schedule', {
  state: () => ({
    current: null,           // Current schedule being viewed/edited
    solverStatus: null,      // "queued", "running", "done", "error"
    solverProgress: 0,       // 0-100 percentage
    assignments: [],         // List of assignments for current schedule
    conflicts: [],           // Detected conflicts
    isGenerating: false,
    error: null,
  }),

  actions: {
    async generate(semesterId, config) {
      this.isGenerating = true
      this.error = null
      try {
        const result = await schedulesApi.generate(semesterId, config)
        this.current = result.schedule_id
        this.solverStatus = 'queued'
        this.connectProgressWS(result.schedule_id)
      } catch (err) {
        this.error = err.message
      } finally {
        this.isGenerating = false
      }
    },

    connectProgressWS(scheduleId) {
      // WebSocket connection for real-time solver progress
    },

    async modifyAssignment(assignmentId, changes) {
      // Optimistic update + API call + conflict re-check
    },
  },
})
```

### Routing

Replace the step-based wizard with proper routes. Each view is independently
addressable and bookmarkable.

```javascript
// router/index.js (conceptual)

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { guest: true } },
  {
    path: '/',
    component: AppShell,
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'dashboard', component: DashboardView },

      // Subjects
      { path: 'subjects', name: 'subjects', component: SubjectListView },
      { path: 'subjects/:id', name: 'subject-detail', component: SubjectDetailView },

      // Instructors
      { path: 'instructors', name: 'instructors', component: InstructorListView },
      { path: 'instructors/:id', name: 'instructor-detail', component: InstructorDetailView },

      // Classrooms
      { path: 'classrooms', name: 'classrooms', component: ClassroomListView },

      // Offerings
      { path: 'offerings', name: 'offerings', component: OfferingListView },
      { path: 'offerings/create', name: 'offering-create', component: OfferingCreateView },
      { path: 'offerings/:id/review', name: 'offering-review', component: OfferingReviewView,
        meta: { roles: ['director', 'super_admin'] } },

      // Schedule
      { path: 'schedule/generate', name: 'schedule-generate', component: ScheduleGenerateView,
        meta: { roles: ['director', 'super_admin'] } },
      { path: 'schedule/:id/edit', name: 'schedule-edit', component: ScheduleEditView,
        meta: { roles: ['director', 'super_admin'] } },
      { path: 'schedule/:id/publish', name: 'schedule-publish', component: SchedulePublishView,
        meta: { roles: ['director', 'super_admin'] } },

      // Admin
      { path: 'admin/users', name: 'admin-users', component: UserListView,
        meta: { roles: ['super_admin'] } },
    ],
  },
  { path: '/public/schedule/:id', name: 'public-schedule', component: SchedulePublicView },
]
```

### Role-Based UI Rendering

Components conditionally render based on the user's role. The sidebar shows
different navigation items. Action buttons appear or disappear. Forms become
read-only for viewers.

```html
<!-- Sidebar.vue (conceptual) -->
<nav>
  <SidebarLink to="/dashboard" icon="home" label="Dashboard" />
  <SidebarLink to="/subjects" icon="book" label="Subjects" />
  <SidebarLink to="/instructors" icon="users" label="Instructors" />
  <SidebarLink to="/classrooms" icon="building" label="Classrooms" />
  <SidebarLink to="/offerings" icon="clipboard" label="Offerings" />

  <!-- Only directors and above -->
  <template v-if="hasRole('director', 'super_admin')">
    <SidebarDivider label="Administration" />
    <SidebarLink to="/schedule/generate" icon="calendar" label="Generate Schedule" />
    <SidebarLink to="/offerings?status=pending" icon="check-circle" label="Review Offerings" />
  </template>

  <!-- Only super admins -->
  <template v-if="hasRole('super_admin')">
    <SidebarLink to="/admin/users" icon="shield" label="User Management" />
  </template>
</nav>
```

---

## 5. Communication Between Modules

### REST API for CRUD Operations

All create, read, update, delete operations use standard REST endpoints.

```
API Prefix: /api/v1

Authentication:
  POST   /auth/login                  # Returns JWT access + refresh tokens
  POST   /auth/refresh                # Refresh access token
  POST   /auth/logout                 # Invalidate refresh token

Universities (super_admin only):
  GET    /universities
  POST   /universities
  GET    /universities/{id}
  PATCH  /universities/{id}

Areas:
  GET    /areas                       # Filtered by user's university
  POST   /areas
  GET    /areas/{id}
  PATCH  /areas/{id}

Subjects:
  GET    /subjects                    # Query params: area_id, search, page
  POST   /subjects
  GET    /subjects/{id}
  PATCH  /subjects/{id}
  DELETE /subjects/{id}

Instructors:
  GET    /instructors
  POST   /instructors
  GET    /instructors/{id}
  PATCH  /instructors/{id}
  DELETE /instructors/{id}
  PUT    /instructors/{id}/availability
  PUT    /instructors/{id}/specialties

Classrooms:
  GET    /classrooms
  POST   /classrooms
  GET    /classrooms/{id}
  PATCH  /classrooms/{id}
  PUT    /classrooms/{id}/equipment

Offerings:
  GET    /offerings                   # Query: area_id, semester, status
  POST   /offerings
  GET    /offerings/{id}
  PATCH  /offerings/{id}
  POST   /offerings/{id}/validate     # Director validates an offering
  POST   /offerings/{id}/reject       # Director rejects with reason
  POST   /offerings/import            # Upload Excel file

Constraints:
  GET    /constraints
  POST   /constraints
  PATCH  /constraints/{id}
  DELETE /constraints/{id}

Schedules:
  POST   /schedules                   # Trigger solver (returns 202 + job_id)
  GET    /schedules/{id}              # Get schedule with assignments
  GET    /schedules/{id}/status       # Poll solver status
  PATCH  /schedules/{id}/assignments/{aid}   # Modify single assignment
  POST   /schedules/{id}/verify       # Run conflict detection
  POST   /schedules/{id}/publish      # Publish schedule
  GET    /schedules/{id}/export       # Download Excel/PDF

Users (super_admin, director):
  GET    /users
  POST   /users
  PATCH  /users/{id}
  PUT    /users/{id}/role
```

**API conventions:**

- All responses follow `{ "data": ..., "meta": { "page": 1, "total": 100 } }` for
  lists and `{ "data": ... }` for single resources.
- Errors follow `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }`.
- Pagination: `?page=1&per_page=25`.
- Filtering: `?area_id=5&status=validated`.
- Sorting: `?sort=name&order=asc`.
- Every request carries `X-Request-ID` for distributed tracing.
- Every mutation endpoint is idempotent via `X-Idempotency-Key` header.

### WebSocket for Solver Progress

The solver runs as a background task. Real-time progress is pushed to the
frontend via WebSocket.

```
WebSocket: /ws/schedules/{schedule_id}/progress

Messages from server:
  { "type": "progress", "data": { "percentage": 45, "current_objective": 1250.3, "elapsed_seconds": 12.5 } }
  { "type": "solution_found", "data": { "objective": 980.1, "feasible": true } }
  { "type": "completed", "data": { "status": "OPTIMAL", "total_time": 28.3 } }
  { "type": "error", "data": { "message": "Solver timed out" } }
```

**Flow:**

```
Browser                    FastAPI                  Celery Worker         OR-Tools
   |                          |                          |                   |
   |--- POST /schedules ----->|                          |                   |
   |<-- 202 {job_id} --------|                          |                   |
   |                          |--- enqueue task -------->|                   |
   |--- WS connect ---------->|                          |                   |
   |                          |                          |--- solve() ------>|
   |                          |                          |                   |
   |                          |<--- progress callback ---|<-- on_solution ---|
   |<-- WS {progress: 30%} ---|                          |                   |
   |                          |<--- progress callback ---|<-- on_solution ---|
   |<-- WS {progress: 65%} ---|                          |                   |
   |                          |                          |                   |
   |                          |<--- task complete -------|<-- solve done ----|
   |<-- WS {completed} -------|                          |                   |
   |--- WS close ------------->|                          |                   |
   |                          |                          |                   |
   |--- GET /schedules/{id} ->|                          |                   |
   |<-- full schedule --------|                          |                   |
```

### Background Task Queue

Celery with Redis handles long-running tasks. The solver is the primary use
case, but Excel export for large schedules also benefits from async execution.

```python
# infrastructure/tasks/solver_task.py

@celery_app.task(bind=True, max_retries=0, time_limit=600)
def solve_schedule_task(self, schedule_id: str, solver_input_dict: dict):
    solver_input = SolverInputDTO.from_dict(solver_input_dict)
    solver = ORToolsSolverAdapter()

    def on_progress(progress: SolverProgress):
        # Push progress to Redis channel, which WebSocket reads
        redis_client.publish(
            f"solver_progress:{schedule_id}",
            json.dumps(progress.to_dict()),
        )

    result = solver.solve(
        solver_input=solver_input,
        config=SolverConfig.from_dict(solver_input_dict["config"]),
        progress_callback=on_progress,
    )

    # Persist result to database
    with get_session() as session:
        schedule_repo = SQLAlchemyScheduleRepository(session)
        schedule = schedule_repo.find_by_id(ScheduleId(schedule_id))
        schedule.apply_solution(result)
        schedule_repo.save(schedule)
        session.commit()

    return {"status": result.status, "schedule_id": schedule_id}
```

### Event-Driven Notifications

Internal events trigger notifications. When a coordinator submits an offering,
the director is notified. When the solver completes, the requesting user is
notified.

```
Event: offering.submitted
  -> Notify director (email + in-app)

Event: offering.validated
  -> Notify area coordinator (in-app)

Event: offering.rejected
  -> Notify area coordinator (email + in-app)

Event: schedule.completed
  -> Notify director (email + in-app)

Event: schedule.published
  -> Notify all coordinators (email + in-app)
```

These are application-level events, not infrastructure events. They are dispatched
by use cases and handled by notification services injected via the interface.

---

## 6. Authentication and Authorization

### Authentication: JWT-Based

```
Login flow:
  1. User sends POST /auth/login with email + password
  2. Server validates credentials against bcrypt hash
  3. Server returns:
     - access_token (JWT, 15-minute expiry, contains user_id, role, university_id, area_id)
     - refresh_token (opaque, 7-day expiry, stored in HttpOnly cookie)
  4. Client stores access_token in memory (not localStorage)
  5. Client sends access_token in Authorization: Bearer header
  6. When access_token expires, client sends POST /auth/refresh with cookie
  7. Server validates refresh_token, issues new access_token
```

**JWT payload structure:**

```json
{
  "sub": "user-uuid-here",
  "role": "area_coordinator",
  "university_id": "univ-uuid",
  "area_id": "area-uuid",
  "iat": 1719532800,
  "exp": 1719533700
}
```

### Authorization: RBAC

Four roles with hierarchical permissions:

```
+----------------------------------------------------------------------+
|  Role              | Scope              | Key Permissions            |
+----------------------------------------------------------------------+
|  SuperAdmin        | System-wide        | Everything. Manages        |
|                    |                    | universities, creates      |
|                    |                    | directors.                 |
+----------------------------------------------------------------------+
|  Director          | University-wide    | Validates offerings,       |
|  (Academic         |                    | generates schedules,       |
|   Director)        |                    | modifies assignments,      |
|                    |                    | publishes, manages users.  |
+----------------------------------------------------------------------+
|  AreaCoordinator   | Single area        | Creates/edits offerings    |
|                    |                    | for own area, manages      |
|                    |                    | subjects and instructors   |
|                    |                    | within area, views own     |
|                    |                    | area's schedule.           |
+----------------------------------------------------------------------+
|  Viewer            | Read-only          | Views published schedules. |
|                    |                    | No write operations.       |
+----------------------------------------------------------------------+
```

**Permission model:**

Permissions are checked at two levels:
1. **Role check**: Does the user's role allow this action type?
2. **Scope check**: Does the user have access to this specific resource?

An AreaCoordinator can create subjects, but only within their assigned area.
A Director can validate offerings, but only for their university.

```python
# application/use_cases/offerings/create_offering.py

class CreateOfferingUseCase:
    def execute(self, command: CreateOfferingCommand) -> OfferingDTO:
        # Role check: only coordinators and above can create offerings
        if command.user_role not in ("area_coordinator", "director", "super_admin"):
            raise InsufficientPermissionsError("Cannot create offerings")

        # Scope check: coordinator can only create for their own area
        if command.user_role == "area_coordinator":
            if command.area_id != command.user_area_id:
                raise InsufficientPermissionsError(
                    "Cannot create offerings for another area"
                )

        # Proceed with creation...
```

### Multi-Tenancy Enforcement

Every database query is scoped by `university_id`. The middleware extracts
`university_id` from the JWT and passes it as a dependency. Repository methods
always filter by university.

```python
# infrastructure/persistence/repositories/sqlalchemy_subject_repo.py

class SQLAlchemySubjectRepository(SubjectRepository):
    def __init__(self, session: Session, university_id: UUID):
        self._session = session
        self._university_id = university_id  # Injected from JWT

    def find_all(self, area_id: UUID | None = None) -> list[Subject]:
        query = self._session.query(SubjectModel).filter(
            SubjectModel.university_id == self._university_id  # Always scoped
        )
        if area_id:
            query = query.filter(SubjectModel.area_id == area_id)
        return [self._to_entity(m) for m in query.all()]
```

There is no way to bypass the university scope. The `university_id` comes from
the verified JWT, never from the request body or URL parameters.

---

## 7. Repository Structure

```
project-root/
|
|-- backend/
|   |-- src/
|   |   |-- schedule_engine/
|   |   |   |-- __init__.py
|   |   |   |-- domain/                   # Pure business logic
|   |   |   |   |-- entities/             # Business objects with identity
|   |   |   |   |-- value_objects/        # Immutable values (CreditHours, TimeBlock)
|   |   |   |   |-- repositories/         # Abstract interfaces (ports)
|   |   |   |   |-- services/             # Domain services (conflict detection)
|   |   |   |   |-- exceptions.py         # Domain-specific errors
|   |   |   |
|   |   |   |-- application/              # Use cases and orchestration
|   |   |   |   |-- use_cases/            # One class per use case
|   |   |   |   |   |-- offerings/        # Offering-related use cases
|   |   |   |   |   |-- schedule/         # Schedule generation, modification
|   |   |   |   |   |-- subjects/         # Subject CRUD
|   |   |   |   |   |-- instructors/      # Instructor management
|   |   |   |   |   |-- classrooms/       # Classroom management
|   |   |   |   |   |-- users/            # Authentication and user management
|   |   |   |   |   |-- constraints/      # Constraint management
|   |   |   |   |-- dto/                  # Data transfer objects
|   |   |   |   |-- interfaces/           # Abstract interfaces for infra services
|   |   |   |
|   |   |   |-- infrastructure/           # Concrete implementations
|   |   |   |   |-- persistence/          # Database layer
|   |   |   |   |   |-- database.py       # Engine, session, connection
|   |   |   |   |   |-- models/           # SQLAlchemy ORM models
|   |   |   |   |   |-- repositories/     # SQLAlchemy repository implementations
|   |   |   |   |-- solver/               # OR-Tools adapter
|   |   |   |   |   |-- ortools_adapter.py
|   |   |   |   |   |-- model_builder.py  # CP-SAT model construction
|   |   |   |   |   |-- solution_extractor.py
|   |   |   |   |   |-- progress_callback.py
|   |   |   |   |-- importers/            # Excel/CSV import adapters
|   |   |   |   |-- exporters/            # Excel/PDF export adapters
|   |   |   |   |-- auth/                 # JWT, password hashing
|   |   |   |   |-- tasks/                # Celery tasks
|   |   |   |   |-- notifications/        # Email service
|   |   |   |
|   |   |   |-- interfaces/              # External-facing adapters
|   |   |       |-- api/
|   |   |       |   |-- app.py            # FastAPI factory
|   |   |       |   |-- dependencies.py   # DI wiring
|   |   |       |   |-- middleware.py     # CORS, error handling, request ID
|   |   |       |   |-- routes/           # One module per domain area
|   |   |       |-- websocket/            # Solver progress WS
|   |   |       |-- cli/                  # Management commands
|   |   |
|   |   |-- conftest.py                   # Shared test fixtures
|   |
|   |-- tests/
|   |   |-- unit/
|   |   |   |-- domain/                   # Entity and value object tests
|   |   |   |-- application/              # Use case tests (mocked repos)
|   |   |-- integration/
|   |   |   |-- persistence/              # Repository tests with real DB
|   |   |   |-- solver/                   # Solver integration tests
|   |   |-- e2e/
|   |   |   |-- test_schedule_flow.py     # Full flow: create -> solve -> publish
|   |   |-- fixtures/
|   |       |-- factories.py              # factory_boy factories
|   |       |-- sample_data.py            # Test datasets
|   |
|   |-- alembic/
|   |   |-- env.py
|   |   |-- versions/                     # Migration files
|   |   |-- alembic.ini
|   |
|   |-- pyproject.toml                    # Dependencies, tool config
|   |-- Dockerfile
|   |-- entrypoint.sh
|
|-- frontend/
|   |-- src/
|   |   |-- api/                          # API client modules
|   |   |-- stores/                       # Pinia stores
|   |   |-- composables/                  # Vue composables (hooks)
|   |   |-- components/
|   |   |   |-- layout/                   # AppShell, Sidebar, Header
|   |   |   |-- common/                   # DataTable, Modal, FormField
|   |   |   |-- schedule/                 # WeeklyCalendar, SolverProgress
|   |   |   |-- offerings/               # OfferingForm, ExcelImporter
|   |   |   |-- data/                     # SubjectForm, InstructorForm
|   |   |-- views/                        # Page-level components
|   |   |   |-- subjects/
|   |   |   |-- instructors/
|   |   |   |-- classrooms/
|   |   |   |-- offerings/
|   |   |   |-- schedule/
|   |   |   |-- admin/
|   |   |-- router/
|   |   |-- plugins/
|   |   |-- utils/
|   |   |-- App.vue
|   |   |-- main.js
|   |-- public/
|   |-- package.json
|   |-- vite.config.js
|   |-- tailwind.config.js
|   |-- Dockerfile
|
|-- docs/
|   |-- ARCHITECTURE.md                   # This document
|   |-- DOMAIN_MODEL.md                   # Entity relationship diagrams, field specs
|   |-- SOLVER_DESIGN.md                  # Mathematical model specification
|   |-- API_REFERENCE.md                  # OpenAPI supplement
|   |-- DEPLOYMENT.md                     # Infrastructure and deployment guide
|
|-- scripts/
|   |-- seed_dev_data.py                  # Seed development database
|   |-- migrate.sh                        # Run Alembic migrations
|   |-- test.sh                           # Run test suite
|
|-- docker/
|   |-- docker-compose.yml               # Local development (API, DB, Redis, Worker)
|   |-- docker-compose.prod.yml          # Production overrides
|   |-- nginx/
|       |-- nginx.conf                    # Reverse proxy config
|
|-- .github/
|   |-- workflows/
|       |-- ci.yml                        # Lint, test, build on PR
|       |-- deploy.yml                    # Deploy on merge to main
|
|-- .env.example
|-- .gitignore
|-- README.md
```

### Directory Purpose Reference

| Directory | Purpose |
|---|---|
| `backend/src/schedule_engine/domain/entities/` | Business objects. Pure Python classes with business rules. No imports from infrastructure, application, or interfaces. |
| `backend/src/schedule_engine/domain/value_objects/` | Immutable objects compared by value. `CreditHours(3) == CreditHours(3)`. Used inside entities. |
| `backend/src/schedule_engine/domain/repositories/` | Abstract base classes (interfaces) that define data access contracts. Infrastructure implements these. |
| `backend/src/schedule_engine/domain/services/` | Domain logic that spans multiple entities. Conflict detection needs both instructor and classroom data. |
| `backend/src/schedule_engine/application/use_cases/` | Each use case is a class with `execute()`. Receives DTOs, calls domain services and repository interfaces. |
| `backend/src/schedule_engine/application/dto/` | Flat data objects for crossing layer boundaries. Entities never leave the domain layer; DTOs carry their data outward. |
| `backend/src/schedule_engine/application/interfaces/` | Interfaces for infrastructure services the application needs (solver, importer, task queue). |
| `backend/src/schedule_engine/infrastructure/persistence/models/` | SQLAlchemy ORM models. One model per database table. These are NOT domain entities. |
| `backend/src/schedule_engine/infrastructure/persistence/repositories/` | SQLAlchemy implementations of domain repository interfaces. Map between ORM models and domain entities. |
| `backend/src/schedule_engine/infrastructure/solver/` | OR-Tools CP-SAT implementation. `ortools_adapter.py` implements `ScheduleSolver` interface. `model_builder.py` builds the CP-SAT model from DTOs. |
| `backend/src/schedule_engine/infrastructure/tasks/` | Celery task definitions. Each task is a thin wrapper that instantiates dependencies and calls a use case. |
| `backend/src/schedule_engine/interfaces/api/routes/` | FastAPI route handlers. One module per domain area. Handlers are thin: parse request, call use case, format response. |
| `backend/src/schedule_engine/interfaces/api/dependencies.py` | FastAPI dependency injection. Wires repositories, services, and use cases together. |
| `backend/tests/unit/` | Tests that run without database, network, or filesystem. Mock all external dependencies. |
| `backend/tests/integration/` | Tests against real PostgreSQL (Docker). Test repository queries, solver with small inputs. |
| `backend/tests/e2e/` | End-to-end tests against the full API. Start FastAPI test client, run full workflows. |
| `backend/alembic/` | Database schema migration scripts. Every schema change is a versioned migration. |
| `frontend/src/api/` | One module per domain area. Each exports functions that call the REST API. |
| `frontend/src/stores/` | Pinia stores. Each store manages state for one domain area and calls the API modules. |
| `frontend/src/composables/` | Vue composables for cross-cutting concerns: auth guards, pagination, notifications. |
| `frontend/src/components/layout/` | Structural components: sidebar, header, content wrapper. |
| `frontend/src/components/common/` | Reusable UI primitives: DataTable, Modal, FormField. |
| `frontend/src/components/schedule/` | Schedule-specific components: calendar grid, event cards, solver progress. |
| `frontend/src/views/` | Page-level components, one per route. Compose components and connect to stores. |
| `docker/` | Docker Compose files for local development. Runs PostgreSQL, Redis, the API, the Celery worker, and Nginx. |
| `scripts/` | Development scripts: seed data, run migrations, run tests. |
| `docs/` | Architecture and design documentation. |

---

## 8. Data Flow Diagrams

### Flow 1: Area Coordinator Uploads Academic Offering

```
Area Coordinator                Frontend                   Backend API
      |                            |                            |
      |  Opens "Offerings" page    |                            |
      |  Selects "Import Excel"    |                            |
      |  Picks .xlsx file          |                            |
      |--------------------------->|                            |
      |                            |  POST /offerings/import    |
      |                            |  (multipart/form-data)     |
      |                            |--------------------------->|
      |                            |                            |
      |                            |                     +------+------+
      |                            |                     | ImportOffer-|
      |                            |                     | ingExcelUC  |
      |                            |                     +------+------+
      |                            |                            |
      |                            |                     1. ExcelImporter.parse(file)
      |                            |                        -> validates format
      |                            |                        -> extracts subjects, groups,
      |                            |                           instructor assignments
      |                            |                            |
      |                            |                     2. OfferingValidationService
      |                            |                        .validate_structure(data)
      |                            |                        -> checks required fields
      |                            |                        -> validates credit ranges
      |                            |                        -> checks instructor eligibility
      |                            |                            |
      |                            |                     3. If validation passes:
      |                            |                        offering_repo.save(offering)
      |                            |                        status = "pending_review"
      |                            |                            |
      |                            |                     4. If validation fails:
      |                            |                        return validation errors
      |                            |                        (row-level detail)
      |                            |                            |
      |                            |<---------------------------|
      |                            |  200 { offering_id,        |
      |                            |    status: "pending",      |
      |                            |    warnings: [...] }       |
      |<---------------------------|                            |
      |  Shows success + warnings  |                            |
      |  (e.g., "3 subjects had    |                            |
      |   no instructor assigned") |                            |

Alternative: Manual Entry

Area Coordinator                Frontend                   Backend API
      |                            |                            |
      |  Opens "Create Offering"   |                            |
      |  Fills in form:            |                            |
      |  - Semester: 2026-2        |                            |
      |  - Subjects with groups    |                            |
      |  - Instructor assignments  |                            |
      |  Clicks "Submit"           |                            |
      |--------------------------->|                            |
      |                            |  POST /offerings           |
      |                            |  { semester, area_id,      |
      |                            |    subjects: [...],        |
      |                            |    groups: [...] }         |
      |                            |--------------------------->|
      |                            |                            |
      |                            |                     CreateOfferingUC
      |                            |                     .execute(command)
      |                            |                            |
      |                            |                     1. Scope check: user's area_id
      |                            |                        matches command area_id
      |                            |                            |
      |                            |                     2. Validate subjects exist in
      |                            |                        the university's catalog
      |                            |                            |
      |                            |                     3. Validate instructors exist
      |                            |                        and have matching specialties
      |                            |                            |
      |                            |                     4. Create Offering entity
      |                            |                        with status = "draft"
      |                            |                            |
      |                            |                     5. offering_repo.save()
      |                            |                            |
      |                            |<---------------------------|
      |<---------------------------|                            |
```

### Flow 2: Director Validates and Consolidates

```
Director                       Frontend                   Backend API
   |                              |                            |
   |  Opens "Review Offerings"    |                            |
   |  Sees list of pending        |                            |
   |  offerings from all areas    |                            |
   |----------------------------->|                            |
   |                              |  GET /offerings            |
   |                              |  ?status=pending_review    |
   |                              |--------------------------->|
   |                              |<---------------------------|
   |                              |  [ offering_1, offering_2, |
   |                              |    offering_3 ]            |
   |<-----------------------------|                            |
   |                              |                            |
   |  Clicks offering_1           |                            |
   |  Reviews subjects, groups,   |                            |
   |  instructor assignments      |                            |
   |                              |                            |
   |  OPTION A: Approve           |                            |
   |----------------------------->|                            |
   |                              |  POST /offerings/1/validate|
   |                              |  { notes: "Approved" }     |
   |                              |--------------------------->|
   |                              |                     ValidateOfferingUC
   |                              |                     .execute()
   |                              |                            |
   |                              |                     1. Check role == director
   |                              |                     2. Check offering belongs to
   |                              |                        user's university
   |                              |                     3. Set status = "validated"
   |                              |                     4. Record who validated, when
   |                              |                     5. Emit offering.validated event
   |                              |                        -> Notify coordinator
   |                              |                            |
   |                              |<---------------------------|
   |                              |                            |
   |  OPTION B: Reject            |                            |
   |----------------------------->|                            |
   |                              |  POST /offerings/1/reject  |
   |                              |  { reason: "Missing labs"} |
   |                              |--------------------------->|
   |                              |                     1. Set status = "rejected"
   |                              |                     2. Store rejection reason
   |                              |                     3. Emit offering.rejected event
   |                              |                        -> Notify coordinator
   |                              |<---------------------------|
   |<-----------------------------|                            |

Consolidation happens implicitly: when the Director triggers schedule generation,
the GenerateScheduleUseCase loads all offerings with status = "validated" for the
target semester. There is no separate "consolidate" action. The solver input is
built from the union of all validated offerings.
```

### Flow 3: Solver Generates Schedule

```
Director                   Frontend              API               Celery          Redis        OR-Tools
   |                          |                    |                  |               |              |
   |  Click "Generate"        |                    |                  |               |              |
   |  Set solver config:      |                    |                  |               |              |
   |  - time limit: 120s      |                    |                  |               |              |
   |  - workers: 4            |                    |                  |               |              |
   |------------------------->|                    |                  |               |              |
   |                          | POST /schedules    |                  |               |              |
   |                          | { semester, config}|                  |               |              |
   |                          |------------------->|                  |               |              |
   |                          |                    |                  |               |              |
   |                          |              GenerateScheduleUC      |               |              |
   |                          |              1. Load validated       |               |              |
   |                          |                 offerings            |               |              |
   |                          |              2. Load instructors,    |               |              |
   |                          |                 classrooms,          |               |              |
   |                          |                 constraints          |               |              |
   |                          |              3. Build SolverInputDTO |               |              |
   |                          |              4. Create Schedule      |               |              |
   |                          |                 (status=generating)  |               |              |
   |                          |              5. Enqueue task ------->|               |              |
   |                          |                    |                  |               |              |
   |                          |<-------------------|                  |               |              |
   |                          | 202 {schedule_id,  |                  |               |              |
   |                          |      job_id}       |                  |               |              |
   |                          |                    |                  |               |              |
   |                          | WS /ws/schedules/{id}/progress       |               |              |
   |                          |------------------->|                  |               |              |
   |                          |                    | subscribe -------|-------------->|              |
   |                          |                    |                  |               |              |
   |                          |                    |           task starts            |              |
   |                          |                    |                  |               |              |
   |                          |                    |                  |-- solve() ----|------------->|
   |                          |                    |                  |               |              |
   |                          |                    |                  |               |   CP-SAT     |
   |                          |                    |                  |               |   solving... |
   |                          |                    |                  |               |              |
   |                          |                    |                  |<--callback----|--solution 1--|
   |                          |                    |                  |-- publish --->|              |
   |                          |                    |<-- subscribe ----|---------------|              |
   |                          |<-- WS progress ----|                  |               |              |
   |  "45% - obj: 1250"       |                    |                  |               |              |
   |<-------------------------|                    |                  |               |              |
   |                          |                    |                  |               |              |
   |                          |                    |                  |<--callback----|--solution 2--|
   |                          |                    |                  |-- publish --->|              |
   |                          |                    |<-- subscribe ----|---------------|              |
   |                          |<-- WS progress ----|                  |               |              |
   |  "82% - obj: 980"        |                    |                  |               |              |
   |<-------------------------|                    |                  |               |              |
   |                          |                    |                  |               |              |
   |                          |                    |                  |<--callback----|-- OPTIMAL ---|
   |                          |                    |                  |               |              |
   |                          |                    |           save assignments       |              |
   |                          |                    |           to schedule record     |              |
   |                          |                    |           status = "draft"       |              |
   |                          |                    |                  |               |              |
   |                          |                    |                  |-- publish --->|              |
   |                          |                    |<-- subscribe ----|---------------|              |
   |                          |<-- WS completed ---|                  |               |              |
   |  "OPTIMAL - 28.3s"       |                    |                  |               |              |
   |<-------------------------|                    |                  |               |              |
   |                          |                    |                  |               |              |
   |                          | GET /schedules/{id}|                  |               |              |
   |                          |------------------->|                  |               |              |
   |                          |<-------------------|                  |               |              |
   |                          | { assignments,     |                  |               |              |
   |                          |   statistics }     |                  |               |              |
   |  Calendar view loads     |                    |                  |               |              |
   |<-------------------------|                    |                  |               |              |
```

### Flow 4: Director Modifies and Publishes

```
Director                   Frontend              API
   |                          |                    |
   |  Views schedule in       |                    |
   |  calendar editor         |                    |
   |                          |                    |
   |  Drags "Calculus I G1"   |                    |
   |  from Mon 8:00 to        |                    |
   |  Wed 10:00               |                    |
   |------------------------->|                    |
   |                          | PATCH /schedules/{id}/assignments/{aid}
   |                          | { day_index: 2,    |
   |                          |   block_index: 4 } |
   |                          |------------------->|
   |                          |                    |
   |                          |              ModifyAssignmentUC
   |                          |              1. Load assignment
   |                          |              2. Create new TimeSlot
   |                          |              3. ConflictDetectionService
   |                          |                 .check(schedule, modified_assignment)
   |                          |                 -> Check instructor conflicts
   |                          |                 -> Check room conflicts
   |                          |                 -> Check group conflicts
   |                          |              4. If conflicts:
   |                          |                 return 409 with conflict details
   |                          |              5. If no conflicts:
   |                          |                 save modified assignment
   |                          |                    |
   |                          |<-------------------|
   |                          | 200 { assignment,  |
   |                          |   conflicts: [] }  |
   |  Calendar updates        |                    |
   |<-------------------------|                    |
   |                          |                    |
   |  ... makes more edits... |                    |
   |                          |                    |
   |  Clicks "Verify All"     |                    |
   |------------------------->|                    |
   |                          | POST /schedules/{id}/verify
   |                          |------------------->|
   |                          |                    |
   |                          |              Run full conflict detection
   |                          |              on all assignments
   |                          |                    |
   |                          |<-------------------|
   |                          | { conflicts: [],   |
   |                          |   stats: {         |
   |                          |     total: 450,    |
   |                          |     rooms_used: 18,|
   |                          |     avg_load: 22 }}|
   |  Shows "No conflicts"    |                    |
   |<-------------------------|                    |
   |                          |                    |
   |  Clicks "Publish"        |                    |
   |------------------------->|                    |
   |                          | POST /schedules/{id}/publish
   |                          |------------------->|
   |                          |                    |
   |                          |              PublishScheduleUC
   |                          |              1. Final conflict check (must be 0)
   |                          |              2. Set status = "published"
   |                          |              3. Create Publication record
   |                          |                 (who published, when, version)
   |                          |              4. Emit schedule.published event
   |                          |                 -> Notify all coordinators
   |                          |              5. Generate public access link
   |                          |                    |
   |                          |<-------------------|
   |                          | { status: "published",
   |                          |   public_url: "/public/schedule/abc123",
   |                          |   published_at: "..." }
   |  Shows success +         |                    |
   |  public link             |                    |
   |<-------------------------|                    |
```

---

## 9. Technology Decisions

### Backend

| Technology | Choice | Rationale |
|---|---|---|
| **Language** | Python 3.11+ | OR-Tools has first-class Python bindings. The team already knows Python. Type hints with `typing` provide adequate safety for this domain. |
| **Web Framework** | FastAPI 0.110+ | Async support, automatic OpenAPI docs, dependency injection via `Depends`, Pydantic validation. Already used in the prototype. |
| **ORM** | SQLAlchemy 2.0 | Mature, well-documented, supports both Core and ORM patterns. The 2.0 style with `mapped_column` and type annotations is safer than the 1.x declarative style used in the prototype. |
| **Migrations** | Alembic | Standard companion to SQLAlchemy. Auto-generates migration scripts from model changes. The prototype has zero migrations; this adds proper schema evolution. |
| **Database** | PostgreSQL 15+ | ACID compliance is mandatory for schedule data integrity. Supports JSON columns for flexible constraint parameters. Excellent index types (GIN for full-text search, partial indexes). Already used in the prototype. |
| **Task Queue** | Celery 5.x + Redis | The solver can take 30-600 seconds. It must run in a background worker, not in an API request thread. The prototype uses `threading.Thread` -- this is dangerous (crashes kill the thread silently, no retry, no timeout). Celery provides task routing, retries, time limits, and result backends. |
| **Message Broker** | Redis 7+ | Serves double duty as Celery broker and as pub/sub channel for solver progress updates to WebSocket. Simple to operate. Single Redis instance is sufficient for the expected load. |
| **Authentication** | python-jose (JWT) + passlib (bcrypt) | Standard JWT library for Python. bcrypt is the correct choice for password hashing (slow by design, salt included). No need for a heavier auth framework at this scale. |
| **Solver** | OR-Tools CP-SAT 9.x | Constraint Programming with SAT solver from Google. Already proven in the prototype. CP-SAT handles the combinatorial explosion of schedule optimization well. The prototype's mathematical model works and only needs generalization, not replacement. |
| **Excel I/O** | openpyxl + pandas | openpyxl for reading/writing Excel files. pandas for tabular data manipulation in the export pipeline. Both are already used in the prototype. |
| **Testing** | pytest + factory_boy | pytest is the standard Python test framework. factory_boy generates realistic test data. The prototype has zero tests; this adds comprehensive coverage. |
| **Validation** | Pydantic 2.x | Already used in FastAPI for request/response validation. Extended to validate all DTOs at application layer boundaries. |

### Frontend

| Technology | Choice | Rationale |
|---|---|---|
| **Framework** | Vue 3 (Composition API) | Already used in the prototype. The Composition API with `<script setup>` is cleaner than the Options API for this complexity level. |
| **State Management** | Pinia | Official Vue 3 state management. Replaces the prototype's raw `reactive()` + localStorage hack. Provides devtools integration, plugins, and proper store composition. |
| **Routing** | Vue Router 4 | Already included but underused (only 2 routes). Extended to proper route-per-view with navigation guards. |
| **HTTP Client** | Axios | Replaces the prototype's raw `fetch` wrapper. Interceptors handle JWT refresh transparently. Request/response transformation is cleaner. |
| **CSS** | Tailwind CSS 3 | Already used in the prototype. Utility-first CSS is productive for this type of data-heavy UI. |
| **Build Tool** | Vite | Already used. Fast HMR, native ESM, no configuration needed. |
| **Excel Client** | SheetJS (xlsx) | Already included in package.json. Used for client-side Excel preview before upload. |

### Infrastructure

| Technology | Choice | Rationale |
|---|---|---|
| **Containerization** | Docker + Docker Compose | Local development runs PostgreSQL, Redis, API, and Worker in containers. Production deployment uses the same images. |
| **Reverse Proxy** | Nginx | Serves frontend static files, proxies API requests, handles WebSocket upgrade. |
| **CI/CD** | GitHub Actions | Automated lint, test, build on PR. Automated deploy on merge to main. |
| **Hosting** | Railway (current) | Keep the existing Railway deployment for the API and worker. Add Redis as a Railway plugin. Frontend stays on Vercel. |

---

## 10. Scalability Considerations

### Current Scale Estimate

A typical university has:
- 5-15 academic areas
- 200-800 subjects
- 100-400 instructors
- 20-80 classrooms
- 500-3000 groups per semester

This produces a solver input with:
- 10,000-100,000 decision variables
- 50,000-500,000 constraints
- Solve time: 30 seconds to 10 minutes

This is a small-to-medium scale system. The architecture is designed for single
university deployments first, with a clear path to multi-institution hosting.

### Database Optimization

**Indexes for common query patterns:**

```sql
-- Offerings by university + semester + status (the most common query)
CREATE INDEX idx_offerings_univ_semester_status
ON offerings (university_id, semester_year, semester_period, status)
WHERE deleted_at IS NULL;

-- Subjects by area (coordinator's view)
CREATE INDEX idx_subjects_area
ON subjects (area_id)
WHERE is_active = true;

-- Assignments by schedule (loading a schedule view)
CREATE INDEX idx_assignments_schedule
ON assignments (schedule_id)
INCLUDE (group_id, instructor_id, classroom_id, day_index, block_index);

-- Instructors by university with availability (solver data loading)
CREATE INDEX idx_instructors_university
ON instructors (university_id)
WHERE is_active = true;

-- Instructor availability lookup
CREATE INDEX idx_availability_instructor
ON instructor_availability (instructor_id, day_of_week);
```

**Query optimization:**

- Use `select_related` / `joinedload` for entity loading to avoid N+1 queries.
- Solver data loading is a single batch operation: load all subjects, instructors,
  classrooms, and constraints for the university in 4-5 queries, not one query
  per entity.
- Paginate all list endpoints. Default page size is 25, maximum is 100.
- Use database-level filtering (`WHERE area_id = ...`) instead of loading all
  records and filtering in Python.

### Solver Performance

**Worker isolation:** Each solver run gets its own Celery worker process. The
solver is CPU-intensive and should not share a process with the API server. In
production, the worker runs on a separate container or machine.

**Time limits:** Every solver run has a hard time limit (default: 120 seconds,
maximum: 600 seconds). The Celery task has `time_limit=600` as a hard ceiling.
This prevents runaway solver processes from consuming resources indefinitely.

**Solver configuration:**

```python
solver.parameters.num_search_workers = min(cpu_count, 4)  # Limit parallelism
solver.parameters.max_time_in_seconds = config.time_limit
solver.parameters.log_search_progress = True  # Enable progress callbacks
```

**Caching:** Solver input DTOs can be hashed. If the same input (same offerings,
instructors, classrooms, constraints) is submitted twice, the system returns the
cached result instead of re-solving. Cache key = SHA-256 of the serialized
`SolverInputDTO`. Cache storage = Redis with 24-hour TTL.

### Horizontal Scaling Path

The system starts as a single deployment per institution. When multi-institution
demand grows:

1. **API servers**: Stateless. Scale horizontally behind a load balancer.
   JWT validation is stateless (no session store needed).

2. **Celery workers**: Scale independently based on solver queue depth.
   Each worker handles one solve task at a time.

3. **Database**: Single PostgreSQL instance is sufficient for any single
   university. For multi-institution, use schema-per-tenant or connection
   pooling with PgBouncer. Read replicas for reporting queries.

4. **Redis**: Single instance handles Celery broker + pub/sub + caching for
   any single institution. For multi-institution, Redis Cluster or managed
   Redis (ElastiCache, Redis Cloud).

### Multi-Institution Deployment

Two strategies, depending on isolation requirements:

**Option A: Shared database, tenant column.**
Every table has `university_id`. Queries always filter by it. Simpler to
operate, but requires careful enforcement of tenant isolation.

**Option B: Schema-per-tenant.**
Each university gets its own PostgreSQL schema. A routing layer maps the JWT's
`university_id` to the correct schema. Stronger isolation, slightly more
complex provisioning.

Recommendation: Start with Option A (tenant column). The RBAC system already
scopes every query by `university_id`. If a customer requires strict data
isolation, migrate to Option B for that customer.

---

## 11. Migration Strategy

### Guiding Principle

The prototype works. Students can enter subjects, professors, and classrooms,
and the solver generates valid schedules. The mathematical model is correct. The
migration must not lose this capability at any point. At every phase, there must
be a working system.

### Phase 0: Foundation (Week 1-2)

**Goal:** Set up the new project structure and build tooling.

- Create the new directory structure (backend/src/schedule_engine/...).
- Set up pyproject.toml with all dependencies.
- Configure Alembic for migrations.
- Set up Docker Compose for local development (PostgreSQL, Redis).
- Configure pytest with factory_boy.
- Set up CI pipeline (lint with ruff, type check with mypy, test with pytest).
- Write the domain entities and value objects (pure Python, no dependencies).
- Write unit tests for domain entities.

**Risk:** None. This is greenfield work alongside the existing prototype.

**What to preserve:** Nothing yet. The prototype continues to run unchanged.

**What to discard:** Nothing yet.

### Phase 1: Domain and Persistence (Week 3-5)

**Goal:** Implement the full data model and CRUD operations.

- Design the complete database schema (see DOMAIN_MODEL.md).
- Write Alembic migrations for all tables.
- Implement SQLAlchemy ORM models.
- Implement repository interfaces (domain layer).
- Implement SQLAlchemy repository implementations (infrastructure layer).
- Write integration tests for repositories against real PostgreSQL.
- Implement CRUD use cases (subjects, instructors, classrooms, offerings).
- Implement FastAPI routes for CRUD operations.
- Write API tests.

**Risk:** Schema design errors are expensive to fix later. Mitigate by writing
integration tests early and reviewing the schema against all solver input
requirements before finalizing.

**What to preserve:** The prototype's API continues to serve the existing
frontend.

**What to discard:** The 3-table schema (Materia, Profesor, RunJob). The new
schema replaces it entirely.

### Phase 2: Solver Integration (Week 6-8)

**Goal:** Port the solver to work with the new data model.

- Define `SolverInputDTO` and `SolverOutputDTO`.
- Implement `ORToolsSolverAdapter` that builds the CP-SAT model from DTOs.
- Port the mathematical model from `model_builder.py`:
  - Replace integer indexes with entity IDs.
  - Replace hardcoded subject lists with DTO-driven data.
  - Remove random candidate generation (candidates come from DTO).
  - Remove string-matching heuristics.
  - Keep all constraint formulations intact.
  - Generalize session patterns to support arbitrary credit hours.
- Implement `SolverInputDTO.from_domain()` that loads from repositories and
  builds the DTO.
- Implement `GenerateScheduleUseCase`.
- Set up Celery + Redis for background task execution.
- Implement WebSocket endpoint for solver progress.
- Write solver integration tests with small datasets (5 subjects, 3 instructors,
  2 classrooms) to verify the mathematical model produces valid solutions.
- Write a regression test that replicates the prototype's input (49 subjects,
  20 professors) and verifies the solver finds a feasible solution.

**Risk:** Subtle bugs in the mathematical model port. The prototype's model uses
integer indices extensively (subject 0, professor 3, classroom 7). The new model
uses entity IDs. Off-by-one errors or missing mappings could break constraint
correctness.

**Mitigation:** The regression test compares the new solver's output against the
prototype's output for the same input. Both must produce solutions with the same
feasibility status and comparable objective values.

**What to preserve:** The entire CP-SAT model formulation:
- Decision variable structure (y, x, z, start, day_sel).
- Session pattern constraints (1/2/3/4-credit logic).
- Hard constraints (instructor conflict, room conflict, capacity).
- Soft objectives (workload balancing, preference scores).

**What to discard:**
- `build_data()` -- hardcoded subject list.
- `build_data_from_ui()` -- ad-hoc data transformation.
- `norm()` and all string-matching logic.
- Random candidate generation.
- Random student count generation.
- Infrastructure professor/classroom hardcoded assignments.
- The `threading.Thread` solver execution.

### Phase 3: Authentication and Authorization (Week 9-10)

**Goal:** Add JWT authentication and RBAC.

- Implement User entity and repository.
- Implement JWT provider (access + refresh tokens).
- Implement password hashing with bcrypt.
- Implement auth routes (login, refresh, logout).
- Implement auth middleware (extract user from JWT).
- Implement role-based permission checks in use cases.
- Implement multi-tenancy scoping (university_id from JWT).
- Write auth integration tests.
- Seed initial SuperAdmin user.

**Risk:** Getting the permission model wrong allows unauthorized access. Mitigate
by writing explicit permission tests: "AreaCoordinator for area A cannot read
offerings from area B."

### Phase 4: Frontend Rebuild (Week 11-14)

**Goal:** Replace the prototype frontend with the new architecture.

- Set up Pinia stores.
- Implement API client modules with Axios.
- Build authentication flow (login, token refresh, guards).
- Build AppShell layout (sidebar, header, content).
- Build CRUD views for subjects, instructors, classrooms.
- Build offering creation and import views.
- Build offering review view (director).
- Refactor WeeklyCalendar component for the new data model.
- Build schedule generation view with WebSocket progress.
- Build schedule editing view with drag-and-drop.
- Build schedule publishing view.
- Implement role-based UI rendering.

**Risk:** This is the largest phase. Mitigate by building incrementally: get
CRUD views working first (they are straightforward), then tackle the schedule
views (more complex).

**What to preserve:** The `WeeklyCalendar.vue` component's rendering logic. The
visual design is adequate. The data contract changes but the rendering approach
(grid of day columns with hour rows) remains the same.

**What to discard:**
- `state.js` -- replaced by Pinia stores.
- `storage.js` -- no more localStorage as database.
- `SchedulerView.vue` -- replaced by multiple route-based views.
- Step-based wizard navigation -- replaced by sidebar navigation.
- All hardcoded demo data.

### Phase 5: Excel Import/Export and Notifications (Week 15-16)

**Goal:** Implement data import, schedule export, and email notifications.

- Implement Excel importer for offerings.
- Implement Excel exporter for published schedules.
- Implement PDF exporter for published schedules.
- Implement email notification service.
- Wire notification events to use cases.

**What to preserve:** The Excel export formatting from `excel_exporter.py`. The
spreadsheet layout (calendar view, assignments, statistics, classroom usage) is
well-designed and should be replicated.

### Phase 6: Testing, Hardening, Deployment (Week 17-18)

**Goal:** Production readiness.

- Write end-to-end tests for complete workflows.
- Load testing with realistic data (500 subjects, 200 instructors, 50 classrooms).
- Security review (SQL injection, JWT validation, permission bypasses).
- Set up production Docker Compose.
- Configure production deployment pipeline.
- Write deployment documentation.
- Migrate production database.
- Deploy and monitor.

### Timeline Summary

```
Week  1-2:   [Phase 0] Foundation         -- structure, tooling, domain entities
Week  3-5:   [Phase 1] Domain/Persistence  -- schema, repos, CRUD
Week  6-8:   [Phase 2] Solver Integration  -- port CP-SAT, Celery, WebSocket
Week  9-10:  [Phase 3] Auth/RBAC           -- JWT, roles, multi-tenancy
Week  11-14: [Phase 4] Frontend            -- Pinia, views, calendar
Week  15-16: [Phase 5] Import/Export       -- Excel, PDF, email
Week  17-18: [Phase 6] Hardening           -- testing, security, deploy
```

Total estimated duration: 18 weeks for a team of 2-3 developers.

The prototype remains operational throughout. Users switch to the new system
only after Phase 6 is complete. There is no "big bang" cutover.
