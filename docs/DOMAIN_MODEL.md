# Domain Model -- University Schedule Optimization Platform

> **Version:** 1.0.0
> **Status:** Design specification (pre-implementation)
> **Database engine:** PostgreSQL 15+
> **ORM:** SQLAlchemy 2.x with Alembic migrations

---

## 1. Domain Overview

This platform automates the generation of university class schedules by collecting academic data (subjects, instructors, classrooms, study plans) and feeding it to a constraint-satisfaction solver (OR-Tools CP-SAT). The system is multi-tenant: any institution can operate independently within the same deployment.

### 1.1 Bounded Contexts

| Context | Responsibility | Key Entities |
|---|---|---|
| **Institutional** | Tenant isolation, organizational structure | Institution, AcademicArea, AcademicProgram |
| **Curriculum** | Study plans, subject catalogs, prerequisites | StudyPlan, StudyPlanSubject, Subject |
| **Staffing** | Instructor management, contracts, availability | Instructor, InstructorContract, InstructorSpecialty, InstructorAvailability, InstructorPreference, InstructorRestriction |
| **Facilities** | Buildings, classrooms, equipment, room availability | Building, Classroom, ClassroomEquipment, EquipmentType, ClassroomAvailability |
| **Academic Offering** | Period-specific course offerings, groups, enrollment | AcademicPeriod, AcademicOffering, Group |
| **Scheduling** | Time slots, solver execution, schedule results, manual edits | TimeSlot, ScheduleType, Constraint, ScheduleRun, ScheduleResult, ScheduleAssignment, ScheduleModification |
| **Identity & Access** | Users, roles, area-scoped permissions, audit trail | User, Role, Permission, UserAreaAssignment, AuditLog |
| **Operations** | Data imports, published schedules, validation rules | ImportJob, Publication, ValidationRule |

### 1.2 Multi-Tenancy Strategy

Row-level isolation with `institution_id` as a discriminator on every tenant-scoped table. A PostgreSQL Row-Level Security (RLS) policy enforces isolation at the database layer, making accidental cross-tenant reads impossible even if application code has a bug. This avoids the operational overhead of schema-per-tenant while providing strong isolation guarantees.

### 1.3 Area Isolation

Within an institution, each `AcademicArea` is an independent unit. Area coordinators can only read and write rows belonging to their area. The Academic Director role can see and consolidate all areas within their institution.

---

## 2. Entity Catalog

### 2.1 Institution

**Purpose:** Root tenant entity. Represents a university or higher-education institution.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `name` | `VARCHAR(200)` | NO | | UNIQUE |
| `short_code` | `VARCHAR(20)` | NO | | UNIQUE; e.g. "UMB", "UNAL" |
| `logo_url` | `TEXT` | YES | | |
| `timezone` | `VARCHAR(50)` | NO | `'America/Bogota'` | IANA timezone |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | Auto-updated via trigger |

**Relationships:**
- `1 --* AcademicArea`
- `1 --* AcademicProgram`
- `1 --* AcademicPeriod`
- `1 --* Building`
- `1 --* User`

**Business Rules:**
- `short_code` is immutable after creation (used in foreign references and URLs).
- Deactivating an institution (`is_active = FALSE`) makes all its data read-only; solvers refuse to run.

**Indexes:**
- `UNIQUE(short_code)`
- `UNIQUE(name)`

---

### 2.2 AcademicArea

**Purpose:** Organizational unit within an institution (e.g., "Ciencias Basicas", "Ingenieria de Sistemas", "Humanidades", "Idiomas", "Investigacion"). Each area independently manages its subjects, instructors, and offerings.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `name` | `VARCHAR(150)` | NO | | |
| `code` | `VARCHAR(20)` | NO | | |
| `description` | `TEXT` | YES | | |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `1 --* Subject`
- `1 --* Instructor`
- `1 --* AcademicOffering`
- `1 --* UserAreaAssignment`

**Business Rules:**
- `(institution_id, code)` is unique -- no duplicate area codes within an institution.
- `(institution_id, name)` is unique.
- An area coordinator can only modify entities where `area_id` matches their assignment.

**Indexes:**
- `UNIQUE(institution_id, code)`
- `UNIQUE(institution_id, name)`
- `INDEX(institution_id)`

---

### 2.3 AcademicProgram

**Purpose:** A degree program offered by the institution (e.g., "Ingenieria de Sistemas", "Contaduria Publica"). A program can draw subjects from multiple areas.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `name` | `VARCHAR(200)` | NO | | |
| `code` | `VARCHAR(20)` | NO | | e.g. "ISI", "CP" |
| `degree_level` | `VARCHAR(20)` | NO | | ENUM: see Section 4 |
| `total_credits` | `INTEGER` | NO | | CHECK > 0 |
| `total_semesters` | `INTEGER` | NO | | CHECK > 0 |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `1 --* StudyPlan`

**Business Rules:**
- `(institution_id, code)` is unique.
- A program must have at least one active `StudyPlan` before subjects can be offered.

**Indexes:**
- `UNIQUE(institution_id, code)`
- `INDEX(institution_id)`

---

### 2.4 StudyPlan

**Purpose:** A versioned curriculum for a program. Study plans change over time (e.g., "Plan 2020", "Plan 2024"). Multiple plans can coexist -- students enrolled under an older plan continue with it.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `program_id` | `UUID` | NO | | FK -> `academic_programs.id` |
| `version_code` | `VARCHAR(20)` | NO | | e.g. "2024-A" |
| `name` | `VARCHAR(150)` | NO | | e.g. "Plan de Estudios 2024" |
| `effective_from` | `DATE` | NO | | When this plan takes effect |
| `effective_until` | `DATE` | YES | | NULL = currently active |
| `status` | `VARCHAR(20)` | NO | `'draft'` | ENUM: draft, active, deprecated |
| `total_credits` | `INTEGER` | NO | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 AcademicProgram`
- `1 --* StudyPlanSubject`

**Business Rules:**
- `(program_id, version_code)` is unique.
- At most one plan per program can have `status = 'active'` and `effective_until IS NULL` at any time. (Enforced via partial unique index.)
- A plan in `deprecated` status cannot be modified.
- Transitioning to `active` sets the previous active plan's `effective_until`.

**Indexes:**
- `UNIQUE(program_id, version_code)`
- `UNIQUE(program_id) WHERE status = 'active' AND effective_until IS NULL` (partial)
- `INDEX(program_id)`

---

### 2.5 StudyPlanSubject

**Purpose:** A subject's placement within a study plan -- which semester, how many hours, prerequisite chains. This is the through-table that links a study plan to subjects.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `study_plan_id` | `UUID` | NO | | FK -> `study_plans.id` |
| `subject_id` | `UUID` | NO | | FK -> `subjects.id` |
| `semester` | `INTEGER` | NO | | CHECK >= 1 |
| `weekly_hours` | `INTEGER` | NO | | CHECK >= 1, <= 10 |
| `is_elective` | `BOOLEAN` | NO | `FALSE` | |
| `prerequisite_id` | `UUID` | YES | | FK -> `study_plan_subjects.id` (self-ref) |
| `corequisite_id` | `UUID` | YES | | FK -> `study_plan_subjects.id` (self-ref) |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 StudyPlan`
- `* --1 Subject`
- `* --0..1 StudyPlanSubject` (prerequisite, self-referencing)
- `* --0..1 StudyPlanSubject` (corequisite, self-referencing)

**Business Rules:**
- `(study_plan_id, subject_id)` is unique -- a subject appears once per plan.
- `prerequisite_id` must reference a `StudyPlanSubject` in the same study plan with a lower `semester`.
- Circular prerequisite chains are forbidden (enforced at application layer via topological sort).
- `weekly_hours` determines how many time-slot blocks the solver must assign.

**Indexes:**
- `UNIQUE(study_plan_id, subject_id)`
- `INDEX(study_plan_id, semester)`
- `INDEX(subject_id)`

---

### 2.6 Subject

**Purpose:** An academic subject in the catalog (e.g., "Logica de Programacion", "Calculo Diferencial"). Belongs to the area responsible for teaching it.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `area_id` | `UUID` | NO | | FK -> `academic_areas.id` |
| `code` | `VARCHAR(20)` | NO | | e.g. "IS-201" |
| `name` | `VARCHAR(200)` | NO | | |
| `credits` | `INTEGER` | NO | | CHECK >= 1, <= 10 |
| `weekly_hours` | `INTEGER` | NO | | CHECK >= 1, <= 10 |
| `subject_type` | `VARCHAR(30)` | NO | | ENUM: see Section 4 |
| `requires_lab` | `BOOLEAN` | NO | `FALSE` | Needs a computer lab? |
| `requires_equipment` | `JSONB` | YES | `'[]'` | List of EquipmentType codes needed |
| `modality` | `VARCHAR(20)` | NO | `'in_person'` | ENUM: in_person, virtual, hybrid |
| `max_students_per_group` | `INTEGER` | YES | | Soft cap for auto-group calculation |
| `description` | `TEXT` | YES | | |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `* --1 AcademicArea`
- `1 --* StudyPlanSubject`
- `1 --* InstructorSpecialty`
- `1 --* AcademicOffering`

**Business Rules:**
- `(institution_id, code)` is unique.
- `weekly_hours` must be >= `credits` (or equal, depending on institution policy).
- Virtual subjects (`modality = 'virtual'`) are excluded from the solver -- they need no classroom or time slot.
- `requires_lab = TRUE` means the solver must assign this to a classroom of type `computer_lab` or `specialized_lab`.
- Replaces the current `Materia` table's `categoria` column with proper area references and type enums.

**Indexes:**
- `UNIQUE(institution_id, code)`
- `INDEX(area_id)`
- `INDEX(institution_id, area_id)`
- `INDEX(subject_type)`

---

### 2.7 AcademicPeriod

**Purpose:** A semester, trimester, or academic term (e.g., "2024-1", "2024-2", "2025-Intersemestral").

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `code` | `VARCHAR(20)` | NO | | e.g. "2025-1" |
| `name` | `VARCHAR(100)` | NO | | e.g. "Primer Semestre 2025" |
| `start_date` | `DATE` | NO | | |
| `end_date` | `DATE` | NO | | CHECK > start_date |
| `enrollment_deadline` | `DATE` | YES | | |
| `status` | `VARCHAR(20)` | NO | `'planning'` | ENUM: planning, enrollment, active, finished |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `1 --* AcademicOffering`
- `1 --* InstructorContract`
- `1 --* ScheduleRun`
- `1 --* ClassroomAvailability`

**Business Rules:**
- `(institution_id, code)` is unique.
- Date ranges must not overlap for the same institution (application-layer check).
- Only periods in `planning` or `enrollment` status can have new solver runs.

**Indexes:**
- `UNIQUE(institution_id, code)`
- `INDEX(institution_id, status)`

---

### 2.8 AcademicOffering

**Purpose:** A subject offered by a specific area in a specific academic period. This is the bridge that says "Area X will teach Subject Y in Period Z with N groups."

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `subject_id` | `UUID` | NO | | FK -> `subjects.id` |
| `area_id` | `UUID` | NO | | FK -> `academic_areas.id` |
| `num_groups` | `INTEGER` | NO | `1` | CHECK >= 1 |
| `expected_enrollment` | `INTEGER` | YES | | Total expected students |
| `auto_groups` | `BOOLEAN` | NO | `FALSE` | Auto-calculate groups from enrollment |
| `group_capacity` | `INTEGER` | YES | `30` | Max students per group when auto_groups |
| `schedule_type_id` | `UUID` | YES | | FK -> `schedule_types.id` |
| `status` | `VARCHAR(20)` | NO | `'draft'` | ENUM: draft, confirmed, cancelled |
| `notes` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 AcademicPeriod`
- `* --1 Subject`
- `* --1 AcademicArea`
- `* --0..1 ScheduleType`
- `1 --* Group`

**Business Rules:**
- `(period_id, subject_id, area_id)` is unique -- an area offers a subject once per period.
- When `auto_groups = TRUE`, `num_groups = CEIL(expected_enrollment / group_capacity)`.
- Only offerings with `status = 'confirmed'` are fed to the solver.
- The `area_id` must match the subject's `area_id` (an area can only offer its own subjects).

**Indexes:**
- `UNIQUE(period_id, subject_id, area_id)`
- `INDEX(period_id, status)`
- `INDEX(area_id)`

---

### 2.9 Group

**Purpose:** A specific section of an academic offering. Students enroll in groups. The solver assigns each group a time slot, instructor, and classroom.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `offering_id` | `UUID` | NO | | FK -> `academic_offerings.id` |
| `group_number` | `INTEGER` | NO | | CHECK >= 1 |
| `expected_students` | `INTEGER` | NO | `25` | CHECK >= 1 |
| `preferred_schedule_type_id` | `UUID` | YES | | FK -> `schedule_types.id` |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 AcademicOffering`
- `* --0..1 ScheduleType`
- `1 --* ScheduleAssignment`

**Business Rules:**
- `(offering_id, group_number)` is unique.
- When the parent offering's `num_groups` changes, groups are automatically created or soft-deactivated.
- `expected_students` is used by the solver to filter classrooms by capacity.

**Indexes:**
- `UNIQUE(offering_id, group_number)`
- `INDEX(offering_id)`

---

### 2.10 Instructor

**Purpose:** A faculty member who teaches classes. Belongs to one primary area. Replaces the current `Profesor` table.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `area_id` | `UUID` | NO | | FK -> `academic_areas.id` |
| `employee_code` | `VARCHAR(30)` | NO | | e.g. "PROF-0042" |
| `first_name` | `VARCHAR(100)` | NO | | |
| `last_name` | `VARCHAR(100)` | NO | | |
| `email` | `VARCHAR(200)` | YES | | |
| `phone` | `VARCHAR(30)` | YES | | |
| `status` | `VARCHAR(20)` | NO | `'active'` | ENUM: active, inactive, on_leave |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `* --1 AcademicArea` (primary)
- `1 --* InstructorContract`
- `1 --* InstructorSpecialty`
- `1 --* InstructorAvailability`
- `1 --* InstructorPreference`
- `1 --* InstructorRestriction`
- `1 --* ScheduleAssignment`

**Business Rules:**
- `(institution_id, employee_code)` is unique.
- Only instructors with `status = 'active'` are eligible for scheduling.
- An instructor's primary `area_id` determines which area coordinator manages them, but they can teach subjects from other areas via `InstructorSpecialty`.
- Replaces the old single FK `materia_id` with a proper many-to-many via `InstructorSpecialty`.

**Indexes:**
- `UNIQUE(institution_id, employee_code)`
- `INDEX(area_id)`
- `INDEX(institution_id, status)`

---

### 2.11 InstructorContract

**Purpose:** Employment contract for a given academic period. Defines contract type and maximum teaching hours.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `instructor_id` | `UUID` | NO | | FK -> `instructors.id` |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `contract_type` | `VARCHAR(20)` | NO | | ENUM: see Section 4 |
| `max_weekly_hours` | `INTEGER` | NO | | CHECK >= 1, <= 60 |
| `min_weekly_hours` | `INTEGER` | NO | `0` | CHECK >= 0 |
| `effective_from` | `DATE` | NO | | |
| `effective_until` | `DATE` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Instructor`
- `* --1 AcademicPeriod`

**Business Rules:**
- `(instructor_id, period_id)` is unique -- one contract per instructor per period.
- The solver must not assign more hours than `max_weekly_hours`.
- `min_weekly_hours` is a soft constraint -- the solver tries to meet it but does not fail if it cannot.
- `max_weekly_hours` is a hard constraint.

**Indexes:**
- `UNIQUE(instructor_id, period_id)`
- `INDEX(period_id)`

---

### 2.12 InstructorSpecialty

**Purpose:** Many-to-many relationship between instructors and subjects they are qualified to teach. Replaces the broken single FK `Profesor.materia_id`.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `instructor_id` | `UUID` | NO | | FK -> `instructors.id` |
| `subject_id` | `UUID` | NO | | FK -> `subjects.id` |
| `proficiency_level` | `VARCHAR(20)` | NO | `'qualified'` | ENUM: preferred, qualified, backup |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Instructor`
- `* --1 Subject`

**Business Rules:**
- `(instructor_id, subject_id)` is unique.
- The solver uses `proficiency_level` as a preference weight: `preferred` > `qualified` > `backup`.
- A subject can only be assigned to an instructor who has a specialty row for it (hard constraint).

**Indexes:**
- `UNIQUE(instructor_id, subject_id)`
- `INDEX(subject_id)`
- `INDEX(instructor_id)`

---

### 2.13 InstructorAvailability

**Purpose:** Time slots when an instructor is available to teach. If no rows exist, the instructor is assumed available during all institution-defined slots.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `instructor_id` | `UUID` | NO | | FK -> `instructors.id` |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `time_slot_id` | `UUID` | NO | | FK -> `time_slots.id` |
| `is_available` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Instructor`
- `* --1 AcademicPeriod`
- `* --1 TimeSlot`

**Business Rules:**
- `(instructor_id, period_id, time_slot_id)` is unique.
- Rows with `is_available = FALSE` act as explicit blocks. The solver treats missing rows as available by default; once any availability row exists for an instructor+period, the system switches to explicit mode (only `is_available = TRUE` slots are allowed).

**Indexes:**
- `UNIQUE(instructor_id, period_id, time_slot_id)`
- `INDEX(instructor_id, period_id)`

---

### 2.14 InstructorPreference

**Purpose:** Soft preferences an instructor expresses: preferred subjects, time ranges, classrooms. These are optimization hints, not hard constraints.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `instructor_id` | `UUID` | NO | | FK -> `instructors.id` |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `preference_type` | `VARCHAR(30)` | NO | | ENUM: subject, time_slot, classroom, schedule_type |
| `target_id` | `UUID` | NO | | Polymorphic FK to subject / time_slot / classroom / schedule_type |
| `weight` | `INTEGER` | NO | `5` | 1 (low) to 10 (high) |
| `notes` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Instructor`
- `* --1 AcademicPeriod`

**Business Rules:**
- `(instructor_id, period_id, preference_type, target_id)` is unique.
- `weight` maps to the solver's objective function coefficient for soft constraints.
- Preferences do not block assignment; they merely influence the optimization towards better solutions.

**Indexes:**
- `UNIQUE(instructor_id, period_id, preference_type, target_id)`
- `INDEX(instructor_id, period_id)`

---

### 2.15 InstructorRestriction

**Purpose:** Hard unavailability constraints. Unlike preferences, these are absolute -- the solver must never schedule an instructor in a restricted slot.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `instructor_id` | `UUID` | NO | | FK -> `instructors.id` |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `restriction_type` | `VARCHAR(30)` | NO | | ENUM: time_slot, day, date_range |
| `time_slot_id` | `UUID` | YES | | FK -> `time_slots.id` (when type = time_slot) |
| `day_of_week` | `SMALLINT` | YES | | 0=Mon..5=Sat (when type = day) |
| `start_date` | `DATE` | YES | | (when type = date_range) |
| `end_date` | `DATE` | YES | | (when type = date_range) |
| `reason` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Instructor`
- `* --1 AcademicPeriod`
- `* --0..1 TimeSlot`

**Business Rules:**
- Hard constraints: the solver must honor every restriction.
- At least one of `time_slot_id`, `day_of_week`, or `(start_date, end_date)` must be non-null (application-layer check).
- `day_of_week` restrictions block the instructor for the entire day.

**Indexes:**
- `INDEX(instructor_id, period_id)`
- `INDEX(time_slot_id)`

---

### 2.16 Building

**Purpose:** A physical building within the institution's campus.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `name` | `VARCHAR(100)` | NO | | |
| `code` | `VARCHAR(20)` | NO | | e.g. "BLQ-A" |
| `campus` | `VARCHAR(100)` | YES | | For multi-campus institutions |
| `address` | `TEXT` | YES | | |
| `floors` | `INTEGER` | YES | | |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `1 --* Classroom`

**Business Rules:**
- `(institution_id, code)` is unique.

**Indexes:**
- `UNIQUE(institution_id, code)`
- `INDEX(institution_id)`

---

### 2.17 Classroom

**Purpose:** A room, lab, or auditorium within a building. Replaces the current hardcoded `Salon_XX` naming.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `building_id` | `UUID` | NO | | FK -> `buildings.id` |
| `code` | `VARCHAR(30)` | NO | | e.g. "A-101", "LAB-CISCO" |
| `name` | `VARCHAR(100)` | NO | | e.g. "Laboratorio de Redes" |
| `classroom_type` | `VARCHAR(30)` | NO | | ENUM: see Section 4 |
| `capacity` | `INTEGER` | NO | | CHECK >= 1 |
| `floor` | `INTEGER` | YES | | |
| `has_projector` | `BOOLEAN` | NO | `FALSE` | Quick-access flag |
| `has_air_conditioning` | `BOOLEAN` | NO | `FALSE` | |
| `is_accessible` | `BOOLEAN` | NO | `FALSE` | Wheelchair accessible |
| `allows_general_use` | `BOOLEAN` | NO | `TRUE` | Can regular classes use this room when not reserved? |
| `managing_area_id` | `UUID` | YES | | FK -> `academic_areas.id`; if set, area has priority |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Building`
- `* --0..1 AcademicArea` (managing area)
- `1 --* ClassroomEquipment`
- `1 --* ClassroomAvailability`
- `1 --* ScheduleAssignment`

**Business Rules:**
- `(building_id, code)` is unique.
- Specialized labs (e.g., `specialized_lab`) can accept regular courses only when `allows_general_use = TRUE` and the lab is not reserved by its managing area.
- Solver constraint: `Subject.requires_lab = TRUE` implies `Classroom.classroom_type IN ('computer_lab', 'specialized_lab')`.
- Solver constraint: `Group.expected_students <= Classroom.capacity`.

**Indexes:**
- `UNIQUE(building_id, code)`
- `INDEX(building_id)`
- `INDEX(classroom_type)`
- `INDEX(managing_area_id)`
- `INDEX(capacity)` -- for range queries by the solver

---

### 2.18 ClassroomEquipment

**Purpose:** Many-to-many between classrooms and equipment types. Describes what equipment is installed in each room.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `classroom_id` | `UUID` | NO | | FK -> `classrooms.id` |
| `equipment_type_id` | `UUID` | NO | | FK -> `equipment_types.id` |
| `quantity` | `INTEGER` | NO | `1` | CHECK >= 1 |
| `notes` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Classroom`
- `* --1 EquipmentType`

**Business Rules:**
- `(classroom_id, equipment_type_id)` is unique.
- The solver checks `Subject.requires_equipment` against the set of `EquipmentType.code` values present in a classroom.

**Indexes:**
- `UNIQUE(classroom_id, equipment_type_id)`
- `INDEX(classroom_id)`
- `INDEX(equipment_type_id)`

---

### 2.19 EquipmentType

**Purpose:** Catalog of equipment kinds (projector, PCs, Cisco router, multimedia system, etc.).

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `code` | `VARCHAR(30)` | NO | | e.g. "PROJECTOR", "PC", "CISCO_ROUTER" |
| `name` | `VARCHAR(100)` | NO | | |
| `description` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `1 --* ClassroomEquipment`

**Business Rules:**
- `(institution_id, code)` is unique.

**Indexes:**
- `UNIQUE(institution_id, code)`

---

### 2.20 ClassroomAvailability

**Purpose:** Defines when a classroom is available for scheduling in a given period. Supports blocking rooms for maintenance, events, or area-exclusive reservations.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `classroom_id` | `UUID` | NO | | FK -> `classrooms.id` |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `time_slot_id` | `UUID` | NO | | FK -> `time_slots.id` |
| `is_available` | `BOOLEAN` | NO | `TRUE` | |
| `reserved_by_area_id` | `UUID` | YES | | FK -> `academic_areas.id` |
| `reason` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Classroom`
- `* --1 AcademicPeriod`
- `* --1 TimeSlot`
- `* --0..1 AcademicArea` (reserved by)

**Business Rules:**
- `(classroom_id, period_id, time_slot_id)` is unique.
- Missing rows mean the classroom is available by default.
- `is_available = FALSE` blocks the room for that slot (hard constraint).
- `reserved_by_area_id` means only that area's offerings can use the room in that slot.

**Indexes:**
- `UNIQUE(classroom_id, period_id, time_slot_id)`
- `INDEX(classroom_id, period_id)`

---

### 2.21 TimeSlot

**Purpose:** A configurable time block: a combination of day-of-week and start/end times. Replaces the current hardcoded 6-day x 11-block grid.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `day_of_week` | `SMALLINT` | NO | | CHECK 0-6; 0=Monday..5=Saturday, 6=Sunday |
| `start_time` | `TIME` | NO | | |
| `end_time` | `TIME` | NO | | CHECK > start_time |
| `block_number` | `INTEGER` | NO | | Sequential within day for ordering |
| `label` | `VARCHAR(30)` | YES | | e.g. "Bloque 1", "06:00-07:00" |
| `schedule_type_id` | `UUID` | YES | | FK -> `schedule_types.id` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `* --0..1 ScheduleType`
- `1 --* InstructorAvailability`
- `1 --* InstructorRestriction`
- `1 --* ClassroomAvailability`
- `1 --* ScheduleAssignment`

**Business Rules:**
- `(institution_id, day_of_week, start_time)` is unique.
- Time slots within the same day must not overlap for the same institution.
- `block_number` provides a dense ordering for the solver (maps to the current `bloques_por_dia` concept).
- Each institution can define its own grid (different from the current hardcoded Mon-Sat 06:00-16:00).

**Indexes:**
- `UNIQUE(institution_id, day_of_week, start_time)`
- `INDEX(institution_id, day_of_week)`
- `INDEX(schedule_type_id)`

---

### 2.22 ScheduleType

**Purpose:** Classification of time ranges within a day. Used to assign offerings or preferences to specific shifts.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `name` | `VARCHAR(50)` | NO | | e.g. "Manana", "Tarde", "Noche", "Mixta" |
| `code` | `VARCHAR(20)` | NO | | e.g. "MORNING", "AFTERNOON", "EVENING", "MIXED" |
| `start_time` | `TIME` | YES | | Indicative range start |
| `end_time` | `TIME` | YES | | Indicative range end |
| `description` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `1 --* TimeSlot`
- `1 --* AcademicOffering`
- `1 --* Group`

**Business Rules:**
- `(institution_id, code)` is unique.
- `TimeSlot.schedule_type_id` links each block to its schedule type; the solver can filter offerings by schedule type to avoid morning-only subjects being placed in evening slots.

**Indexes:**
- `UNIQUE(institution_id, code)`

---

### 2.23 Constraint

**Purpose:** Configurable solver constraints. Each row defines one constraint with its type (hard/soft), parameters, and priority.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `name` | `VARCHAR(150)` | NO | | Human-readable name |
| `code` | `VARCHAR(50)` | NO | | Machine identifier |
| `constraint_type` | `VARCHAR(10)` | NO | | ENUM: hard, soft |
| `category` | `VARCHAR(30)` | NO | | ENUM: instructor, classroom, group, general |
| `description` | `TEXT` | YES | | |
| `parameters` | `JSONB` | NO | `'{}'` | Constraint-specific config |
| `priority` | `INTEGER` | NO | `100` | Higher = more important for soft constraints |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`

**Business Rules:**
- `(institution_id, code)` is unique.
- Hard constraints are always enforced; if violated, the solver returns INFEASIBLE.
- Soft constraints are weighted by `priority` in the objective function.
- `parameters` JSONB holds constraint-specific configuration. Examples:
  - `max_classes_per_day`: `{"max": 6}`
  - `max_classes_per_week`: `{"max": 26}`
  - `instructor_workload_balance`: `{"deviation_weight": 20, "range_weight": 200}`
  - `consecutive_class_limit`: `{"max_consecutive": 4}`

**Indexes:**
- `UNIQUE(institution_id, code)`
- `INDEX(institution_id, is_active)`

**Seed Data (migrated from current DEFAULT_CONFIG):**

| code | constraint_type | parameters |
|---|---|---|
| `max_classes_instructor_day` | hard | `{"max": 6}` |
| `max_classes_instructor_week` | hard | `{"max": 26}` |
| `instructor_workload_balance` | soft | `{"deviation_weight": 20, "range_weight": 200}` |
| `instructor_preference_bonus` | soft | `{"weight": 1}` |
| `no_instructor_overlap` | hard | `{}` |
| `no_classroom_overlap` | hard | `{}` |
| `room_type_match` | hard | `{}` |
| `room_capacity_match` | hard | `{}` |

---

### 2.24 ScheduleRun

**Purpose:** A solver execution. Replaces the current `RunJob` table with richer metadata and proper foreign keys.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `period_id` | `UUID` | NO | | FK -> `academic_periods.id` |
| `triggered_by_user_id` | `UUID` | NO | | FK -> `users.id` |
| `status` | `VARCHAR(20)` | NO | `'queued'` | ENUM: queued, running, done, error, cancelled |
| `solver_status` | `VARCHAR(20)` | YES | | ENUM: OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN |
| `solver_config` | `JSONB` | NO | `'{}'` | Snapshot of solver parameters used |
| `num_variables` | `INTEGER` | YES | | |
| `num_constraints` | `INTEGER` | YES | | |
| `objective_value` | `FLOAT` | YES | | |
| `best_bound` | `FLOAT` | YES | | |
| `elapsed_seconds` | `FLOAT` | YES | | |
| `error_detail` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `started_at` | `TIMESTAMPTZ` | YES | | |
| `finished_at` | `TIMESTAMPTZ` | YES | | |

**Relationships:**
- `* --1 Institution`
- `* --1 AcademicPeriod`
- `* --1 User`
- `1 --0..1 ScheduleResult`

**Business Rules:**
- Runs stuck in `queued` or `running` for more than 10 minutes are automatically marked as `error` (replaces the current 5-minute stale check).
- `solver_config` is a snapshot so results are reproducible even if constraints change later.
- Only one run can be in `queued` or `running` status per `(institution_id, period_id)` at a time.

**Indexes:**
- `INDEX(institution_id, period_id)`
- `INDEX(status)`
- `INDEX(triggered_by_user_id)`
- `UNIQUE(institution_id, period_id) WHERE status IN ('queued', 'running')` (partial)

---

### 2.25 ScheduleResult

**Purpose:** The top-level result of a successful solver run. Acts as a container for all assignments.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `run_id` | `UUID` | NO | | FK -> `schedule_runs.id`, UNIQUE |
| `total_assignments` | `INTEGER` | NO | | |
| `total_groups_scheduled` | `INTEGER` | NO | | |
| `total_unscheduled_groups` | `INTEGER` | NO | `0` | |
| `classroom_utilization_pct` | `FLOAT` | YES | | |
| `instructor_load_std_dev` | `FLOAT` | YES | | |
| `summary_json` | `JSONB` | YES | | Statistics, per-area breakdowns |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `1 --1 ScheduleRun`
- `1 --* ScheduleAssignment`
- `1 --* ScheduleModification`
- `1 --* Publication`

**Business Rules:**
- Exactly one result per successful run (1:1 with ScheduleRun where solver_status is OPTIMAL or FEASIBLE).
- `summary_json` replaces the current `result_json` blob with structured statistics.

**Indexes:**
- `UNIQUE(run_id)`

---

### 2.26 ScheduleAssignment

**Purpose:** An individual schedule entry: this group meets with this instructor in this classroom at this time slot. This is the core output of the solver.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `result_id` | `UUID` | NO | | FK -> `schedule_results.id` |
| `group_id` | `UUID` | NO | | FK -> `groups.id` |
| `instructor_id` | `UUID` | NO | | FK -> `instructors.id` |
| `classroom_id` | `UUID` | NO | | FK -> `classrooms.id` |
| `time_slot_id` | `UUID` | NO | | FK -> `time_slots.id` |
| `is_modified` | `BOOLEAN` | NO | `FALSE` | TRUE if overridden by director |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 ScheduleResult`
- `* --1 Group`
- `* --1 Instructor`
- `* --1 Classroom`
- `* --1 TimeSlot`

**Business Rules:**
- `(result_id, classroom_id, time_slot_id)` is unique -- no double-booking a room in one result.
- `(result_id, instructor_id, time_slot_id)` is unique -- no instructor in two places at once.
- `(result_id, group_id, time_slot_id)` should be consistent with the subject's `weekly_hours`.

**Indexes:**
- `INDEX(result_id)`
- `UNIQUE(result_id, classroom_id, time_slot_id)`
- `UNIQUE(result_id, instructor_id, time_slot_id)`
- `INDEX(group_id)`
- `INDEX(instructor_id)`
- `INDEX(classroom_id)`
- `INDEX(time_slot_id)`

---

### 2.27 ScheduleModification

**Purpose:** Manual changes made by the Academic Director after a schedule is generated. Provides an audit trail for every post-solver edit.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `result_id` | `UUID` | NO | | FK -> `schedule_results.id` |
| `assignment_id` | `UUID` | NO | | FK -> `schedule_assignments.id` |
| `modified_by_user_id` | `UUID` | NO | | FK -> `users.id` |
| `field_changed` | `VARCHAR(30)` | NO | | ENUM: instructor_id, classroom_id, time_slot_id |
| `old_value` | `UUID` | NO | | Previous FK value |
| `new_value` | `UUID` | NO | | New FK value |
| `reason` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 ScheduleResult`
- `* --1 ScheduleAssignment`
- `* --1 User`

**Business Rules:**
- Every manual change creates a new modification row; the assignment itself is updated in place (with `is_modified = TRUE`).
- The system must re-validate constraints after each modification (no double-booking introduced).
- Modifications are append-only; they are never edited or deleted.

**Indexes:**
- `INDEX(result_id)`
- `INDEX(assignment_id)`
- `INDEX(modified_by_user_id)`

---

### 2.28 User

**Purpose:** A system user. Authenticated via institutional SSO or local credentials.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `email` | `VARCHAR(200)` | NO | | |
| `password_hash` | `VARCHAR(255)` | YES | | NULL when using SSO |
| `first_name` | `VARCHAR(100)` | NO | | |
| `last_name` | `VARCHAR(100)` | NO | | |
| `role_id` | `UUID` | NO | | FK -> `roles.id` |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `last_login_at` | `TIMESTAMPTZ` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `* --1 Role`
- `1 --* UserAreaAssignment`
- `1 --* ScheduleRun` (triggered_by)
- `1 --* ScheduleModification` (modified_by)
- `1 --* AuditLog`
- `1 --* ImportJob`

**Business Rules:**
- `(institution_id, email)` is unique.
- `password_hash` uses bcrypt with a cost factor of 12.
- Deactivated users cannot log in but their historical records are preserved.

**Indexes:**
- `UNIQUE(institution_id, email)`
- `INDEX(role_id)`
- `INDEX(institution_id, is_active)`

---

### 2.29 Role

**Purpose:** System role that determines base-level access.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `name` | `VARCHAR(50)` | NO | | UNIQUE |
| `code` | `VARCHAR(30)` | NO | | UNIQUE |
| `description` | `TEXT` | YES | | |
| `is_system` | `BOOLEAN` | NO | `FALSE` | TRUE for built-in roles |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `1 --* User`
- `* --* Permission` (via `role_permissions` junction table)

**Business Rules:**
- System roles (`is_system = TRUE`) cannot be deleted or renamed.

**Seed Data:**

| code | name | description |
|---|---|---|
| `super_admin` | Super Administrador | Full system access across all institutions |
| `director` | Director Academico | Consolidates all areas, triggers solver, publishes schedules |
| `area_coordinator` | Coordinador de Area | Manages subjects, instructors, offerings for assigned areas |
| `viewer` | Visor | Read-only access to published schedules |

**Indexes:**
- `UNIQUE(name)`
- `UNIQUE(code)`

---

### 2.30 Permission

**Purpose:** Granular permission that can be assigned to roles.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `code` | `VARCHAR(80)` | NO | | UNIQUE; e.g. "subjects.create", "solver.run" |
| `name` | `VARCHAR(150)` | NO | | |
| `category` | `VARCHAR(30)` | NO | | e.g. "subjects", "instructors", "solver", "admin" |
| `description` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --* Role` (via `role_permissions`)

**Seed Data (partial list):**

| code | category |
|---|---|
| `subjects.create` | subjects |
| `subjects.read` | subjects |
| `subjects.update` | subjects |
| `subjects.delete` | subjects |
| `instructors.create` | instructors |
| `instructors.read` | instructors |
| `instructors.update` | instructors |
| `instructors.delete` | instructors |
| `offerings.create` | offerings |
| `offerings.confirm` | offerings |
| `classrooms.manage` | facilities |
| `solver.run` | solver |
| `solver.configure` | solver |
| `schedule.publish` | schedule |
| `schedule.modify` | schedule |
| `users.manage` | admin |
| `areas.manage` | admin |
| `imports.execute` | operations |
| `audit.read` | admin |

**Indexes:**
- `UNIQUE(code)`
- `INDEX(category)`

---

### 2.31 UserAreaAssignment

**Purpose:** Assigns a user to one or more academic areas, scoping their data access. An area coordinator can manage only the areas assigned to them.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `user_id` | `UUID` | NO | | FK -> `users.id` |
| `area_id` | `UUID` | NO | | FK -> `academic_areas.id` |
| `assigned_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `assigned_by_user_id` | `UUID` | YES | | FK -> `users.id` |

**Relationships:**
- `* --1 User`
- `* --1 AcademicArea`

**Business Rules:**
- `(user_id, area_id)` is unique.
- Directors do not need area assignments; their role grants cross-area access.
- Area coordinators must have at least one assignment to do anything.

**Indexes:**
- `UNIQUE(user_id, area_id)`
- `INDEX(area_id)`

---

### 2.32 AuditLog

**Purpose:** Immutable log of all data-changing operations for compliance and debugging.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `user_id` | `UUID` | YES | | FK -> `users.id`; NULL for system actions |
| `action` | `VARCHAR(20)` | NO | | ENUM: create, update, delete, login, logout, solver_run, publish |
| `entity_type` | `VARCHAR(50)` | NO | | e.g. "Subject", "Instructor", "ScheduleRun" |
| `entity_id` | `UUID` | YES | | The affected row's PK |
| `changes` | `JSONB` | YES | | `{"field": {"old": X, "new": Y}}` |
| `ip_address` | `INET` | YES | | |
| `user_agent` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`
- `* --0..1 User`

**Business Rules:**
- Append-only: rows are never updated or deleted.
- Retention policy: 2 years minimum, configurable per institution.
- Written asynchronously (queue-based) to avoid impacting request latency.

**Indexes:**
- `INDEX(institution_id, created_at DESC)`
- `INDEX(user_id, created_at DESC)`
- `INDEX(entity_type, entity_id)`
- Partition by `created_at` (monthly) for performance at scale.

---

### 2.33 ImportJob

**Purpose:** Tracks bulk data imports from Excel files. Replaces the current approach of direct API calls per row.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `uploaded_by_user_id` | `UUID` | NO | | FK -> `users.id` |
| `area_id` | `UUID` | YES | | FK -> `academic_areas.id` |
| `import_type` | `VARCHAR(30)` | NO | | ENUM: subjects, instructors, offerings, classrooms, availability |
| `file_name` | `VARCHAR(255)` | NO | | |
| `file_size_bytes` | `INTEGER` | YES | | |
| `status` | `VARCHAR(20)` | NO | `'pending'` | ENUM: pending, processing, completed, failed, partial |
| `total_rows` | `INTEGER` | YES | | |
| `processed_rows` | `INTEGER` | YES | `0` | |
| `error_rows` | `INTEGER` | YES | `0` | |
| `errors_json` | `JSONB` | YES | | `[{"row": 5, "field": "code", "error": "duplicate"}]` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `finished_at` | `TIMESTAMPTZ` | YES | | |

**Relationships:**
- `* --1 Institution`
- `* --1 User`
- `* --0..1 AcademicArea`

**Business Rules:**
- File uploads are validated before processing: correct columns, data types, referential integrity.
- `partial` status means some rows succeeded, some failed; `errors_json` contains details.
- Import results are idempotent: re-importing the same file updates existing records (matched by code) rather than creating duplicates.

**Indexes:**
- `INDEX(institution_id, created_at DESC)`
- `INDEX(uploaded_by_user_id)`
- `INDEX(status)`

---

### 2.34 Publication

**Purpose:** A published version of a schedule that becomes visible to the institution.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `result_id` | `UUID` | NO | | FK -> `schedule_results.id` |
| `published_by_user_id` | `UUID` | NO | | FK -> `users.id` |
| `version` | `INTEGER` | NO | | Auto-incremented per period |
| `status` | `VARCHAR(20)` | NO | `'published'` | ENUM: published, superseded, retracted |
| `notes` | `TEXT` | YES | | |
| `published_at` | `TIMESTAMPTZ` | NO | `NOW()` | |
| `retracted_at` | `TIMESTAMPTZ` | YES | | |

**Relationships:**
- `* --1 ScheduleResult`
- `* --1 User`

**Business Rules:**
- Publishing a new version automatically sets the previous publication's status to `superseded`.
- A retracted publication is hidden from viewers but preserved for audit purposes.
- `version` is scoped to the academic period (derived from the result's run's period).

**Indexes:**
- `INDEX(result_id)`
- `INDEX(published_by_user_id)`
- `INDEX(status)`

---

### 2.35 ValidationRule

**Purpose:** Business rules that must pass before the solver is allowed to run. Prevents garbage-in scenarios.

| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `institution_id` | `UUID` | NO | | FK -> `institutions.id` |
| `code` | `VARCHAR(50)` | NO | | |
| `name` | `VARCHAR(150)` | NO | | |
| `description` | `TEXT` | YES | | |
| `severity` | `VARCHAR(10)` | NO | `'error'` | ENUM: error, warning |
| `rule_type` | `VARCHAR(30)` | NO | | ENUM: see below |
| `parameters` | `JSONB` | NO | `'{}'` | |
| `is_active` | `BOOLEAN` | NO | `TRUE` | |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | |

**Relationships:**
- `* --1 Institution`

**Business Rules:**
- Rules with `severity = 'error'` block the solver from running.
- Rules with `severity = 'warning'` produce warnings but allow the run.
- `(institution_id, code)` is unique.

**Seed Data:**

| code | rule_type | description |
|---|---|---|
| `all_offerings_confirmed` | completeness | All offerings must be confirmed before running |
| `all_groups_have_instructors` | referential | Every group must have at least one eligible instructor |
| `all_groups_have_classrooms` | referential | Every group must have at least one feasible classroom |
| `no_orphan_instructors` | consistency | Active instructors must have at least one specialty |
| `contracts_exist` | completeness | Every active instructor must have a contract for the period |
| `time_slots_defined` | completeness | At least one time slot must be defined |

**Indexes:**
- `UNIQUE(institution_id, code)`
- `INDEX(institution_id, is_active)`

---

## 3. Relationship Map

```
Institution 1──* AcademicArea
Institution 1──* AcademicProgram
Institution 1──* AcademicPeriod
Institution 1──* Building
Institution 1──* User
Institution 1──* TimeSlot
Institution 1──* ScheduleType
Institution 1──* EquipmentType
Institution 1──* Constraint
Institution 1──* ScheduleRun
Institution 1──* ValidationRule
Institution 1──* AuditLog
Institution 1──* ImportJob
Institution 1──* Subject (denormalized for RLS)

AcademicArea 1──* Subject
AcademicArea 1──* Instructor
AcademicArea 1──* AcademicOffering
AcademicArea 1──* UserAreaAssignment
AcademicArea 0..1──* Classroom (managing_area)
AcademicArea 0..1──* ClassroomAvailability (reserved_by)

AcademicProgram 1──* StudyPlan
AcademicProgram *──1 Institution

StudyPlan 1──* StudyPlanSubject
StudyPlan *──1 AcademicProgram

StudyPlanSubject *──1 StudyPlan
StudyPlanSubject *──1 Subject
StudyPlanSubject *──0..1 StudyPlanSubject (prerequisite)
StudyPlanSubject *──0..1 StudyPlanSubject (corequisite)

Subject *──1 AcademicArea
Subject *──1 Institution
Subject 1──* StudyPlanSubject
Subject 1──* InstructorSpecialty
Subject 1──* AcademicOffering

AcademicPeriod 1──* AcademicOffering
AcademicPeriod 1──* InstructorContract
AcademicPeriod 1──* InstructorAvailability
AcademicPeriod 1──* InstructorRestriction
AcademicPeriod 1──* InstructorPreference
AcademicPeriod 1──* ClassroomAvailability
AcademicPeriod 1──* ScheduleRun

AcademicOffering *──1 AcademicPeriod
AcademicOffering *──1 Subject
AcademicOffering *──1 AcademicArea
AcademicOffering *──0..1 ScheduleType
AcademicOffering 1──* Group

Group *──1 AcademicOffering
Group *──0..1 ScheduleType
Group 1──* ScheduleAssignment

Instructor *──1 Institution
Instructor *──1 AcademicArea
Instructor 1──* InstructorContract
Instructor 1──* InstructorSpecialty
Instructor 1──* InstructorAvailability
Instructor 1──* InstructorPreference
Instructor 1──* InstructorRestriction
Instructor 1──* ScheduleAssignment

InstructorContract *──1 Instructor
InstructorContract *──1 AcademicPeriod

InstructorSpecialty *──1 Instructor
InstructorSpecialty *──1 Subject

InstructorAvailability *──1 Instructor
InstructorAvailability *──1 AcademicPeriod
InstructorAvailability *──1 TimeSlot

InstructorPreference *──1 Instructor
InstructorPreference *──1 AcademicPeriod

InstructorRestriction *──1 Instructor
InstructorRestriction *──1 AcademicPeriod
InstructorRestriction *──0..1 TimeSlot

Building *──1 Institution
Building 1──* Classroom

Classroom *──1 Building
Classroom *──0..1 AcademicArea (managing_area)
Classroom 1──* ClassroomEquipment
Classroom 1──* ClassroomAvailability
Classroom 1──* ScheduleAssignment

ClassroomEquipment *──1 Classroom
ClassroomEquipment *──1 EquipmentType

EquipmentType *──1 Institution

ClassroomAvailability *──1 Classroom
ClassroomAvailability *──1 AcademicPeriod
ClassroomAvailability *──1 TimeSlot
ClassroomAvailability *──0..1 AcademicArea (reserved_by)

TimeSlot *──1 Institution
TimeSlot *──0..1 ScheduleType

ScheduleRun *──1 Institution
ScheduleRun *──1 AcademicPeriod
ScheduleRun *──1 User (triggered_by)
ScheduleRun 1──0..1 ScheduleResult

ScheduleResult 1──1 ScheduleRun
ScheduleResult 1──* ScheduleAssignment
ScheduleResult 1──* ScheduleModification
ScheduleResult 1──* Publication

ScheduleAssignment *──1 ScheduleResult
ScheduleAssignment *──1 Group
ScheduleAssignment *──1 Instructor
ScheduleAssignment *──1 Classroom
ScheduleAssignment *──1 TimeSlot

ScheduleModification *──1 ScheduleResult
ScheduleModification *──1 ScheduleAssignment
ScheduleModification *──1 User (modified_by)

User *──1 Institution
User *──1 Role
User 1──* UserAreaAssignment
User 1──* ScheduleRun (triggered)
User 1──* ScheduleModification (modified)
User 1──* AuditLog
User 1──* ImportJob

Role 1──* User
Role *──* Permission (via role_permissions)

UserAreaAssignment *──1 User
UserAreaAssignment *──1 AcademicArea

Publication *──1 ScheduleResult
Publication *──1 User (published_by)
```

---

## 4. Enumerated Types

All enums are stored as `VARCHAR` in the database (not PostgreSQL `ENUM` types) to allow adding values without migrations. Validation happens at the application layer.

### 4.1 DegreeLevel
```
technical          -- Tecnico
technological      -- Tecnologo
undergraduate      -- Pregrado
specialization     -- Especializacion
masters            -- Maestria
doctorate          -- Doctorado
```

### 4.2 StudyPlanStatus
```
draft              -- Being designed, not yet effective
active             -- Currently in use for new cohorts
deprecated         -- No longer assigned to new cohorts; existing students may still use it
```

### 4.3 SubjectType
```
theoretical        -- Lecture-based, standard classroom
practical          -- Lab or workshop, needs specialized room
theoretical_practical  -- Mix of both
workshop           -- Intensive hands-on
seminar            -- Discussion-based
practicum          -- External placement (Practica Empresarial)
```

### 4.4 SubjectModality
```
in_person          -- Requires physical classroom
virtual            -- No classroom needed; excluded from solver
hybrid             -- Some sessions in person, some virtual
```

### 4.5 ContractType
```
full_time          -- Tiempo completo (typically 40 hrs/week)
half_time          -- Medio tiempo (typically 20 hrs/week)
hourly             -- Catedratico (paid per hour taught)
occasional         -- Occasional (temporary contract)
visiting           -- Visiting professor
```

### 4.6 InstructorStatus
```
active             -- Available for scheduling
inactive           -- Not currently employed
on_leave           -- Temporarily unavailable (sabbatical, medical)
```

### 4.7 ClassroomType
```
standard           -- Regular lecture room
computer_lab       -- Lab with PCs (replaces current "pc" type)
specialized_lab    -- Cisco lab, multimedia lab, electronics lab, etc.
auditorium         -- Large lecture hall
workshop_room      -- For hands-on practical work
meeting_room       -- Small rooms for seminars
virtual_room       -- Virtual classroom placeholder (not physical)
```

### 4.8 ProficiencyLevel
```
preferred          -- Instructor's main subject; highest solver weight
qualified          -- Instructor can teach it competently
backup             -- Last resort; lowest solver weight
```

### 4.9 PreferenceType
```
subject            -- Prefers teaching a specific subject
time_slot          -- Prefers a specific time block
classroom          -- Prefers a specific room
schedule_type      -- Prefers morning/afternoon/evening
```

### 4.10 RestrictionType
```
time_slot          -- Cannot teach at a specific time slot
day                -- Cannot teach on a specific day of the week
date_range         -- Cannot teach during a date range
```

### 4.11 ConstraintType
```
hard               -- Must be satisfied; violation = INFEASIBLE
soft               -- Optimization target; weighted in objective function
```

### 4.12 ConstraintCategory
```
instructor         -- Constraints on instructor assignments
classroom          -- Constraints on room assignments
group              -- Constraints on group scheduling
general            -- Cross-cutting constraints
```

### 4.13 ScheduleRunStatus
```
queued             -- Waiting to start
running            -- Solver is executing
done               -- Completed successfully (check solver_status for quality)
error              -- Failed (timeout, crash, infeasible)
cancelled          -- Manually cancelled
```

### 4.14 SolverStatus
```
OPTIMAL            -- Best possible solution found
FEASIBLE           -- Valid solution found but may not be optimal
INFEASIBLE         -- No valid solution exists given the constraints
UNKNOWN            -- Solver could not determine (likely timeout)
```

### 4.15 OfferingStatus
```
draft              -- Being planned
confirmed          -- Ready for solver input
cancelled          -- Will not be offered
```

### 4.16 PeriodStatus
```
planning           -- Data entry phase
enrollment         -- Students enrolling
active             -- Classes in session
finished           -- Period completed
```

### 4.17 PublicationStatus
```
published          -- Currently visible
superseded         -- Replaced by a newer version
retracted          -- Withdrawn (errors found)
```

### 4.18 ImportType
```
subjects           -- Bulk subject import
instructors        -- Bulk instructor import
offerings          -- Bulk offering import
classrooms         -- Bulk classroom import
availability       -- Instructor or classroom availability
```

### 4.19 AuditAction
```
create
update
delete
login
logout
solver_run
publish
import
```

### 4.20 DayOfWeek
```
0 = Monday     (Lunes)
1 = Tuesday    (Martes)
2 = Wednesday  (Miercoles)
3 = Thursday   (Jueves)
4 = Friday     (Viernes)
5 = Saturday   (Sabado)
6 = Sunday     (Domingo)
```

### 4.21 ValidationRuleType
```
completeness       -- All required data must be present
referential        -- Foreign key relationships must be satisfied
consistency        -- Data must be logically consistent
capacity           -- Resource capacity checks
```

### 4.22 ModificationField
```
instructor_id      -- Changed assigned instructor
classroom_id       -- Changed assigned classroom
time_slot_id       -- Changed assigned time slot
```

### 4.23 ImportJobStatus
```
pending
processing
completed
failed
partial            -- Some rows succeeded, some failed
```

### 4.24 ValidationSeverity
```
error              -- Blocks solver execution
warning            -- Produces warning but allows run
```

---

## 5. Junction / Association Tables

### 5.1 role_permissions

Links roles to permissions (many-to-many).

| Column | Type | Nullable | Constraints |
|---|---|---|---|
| `role_id` | `UUID` | NO | FK -> `roles.id`, PK (composite) |
| `permission_id` | `UUID` | NO | FK -> `permissions.id`, PK (composite) |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` |

**Indexes:**
- `PK(role_id, permission_id)`
- `INDEX(permission_id)`

### 5.2 instructor_specialties (already described as entity 2.12)

This is the many-to-many between `Instructor` and `Subject`. Because it carries extra data (`proficiency_level`), it is modeled as a full entity rather than a bare junction table.

### 5.3 classroom_equipment (already described as entity 2.18)

Many-to-many between `Classroom` and `EquipmentType` with `quantity`.

### 5.4 Summary of All Through-Tables

| Relationship | Through Table | Extra Columns |
|---|---|---|
| Role <-> Permission | `role_permissions` | none |
| Instructor <-> Subject | `instructor_specialties` | `proficiency_level` |
| Classroom <-> EquipmentType | `classroom_equipment` | `quantity`, `notes` |
| StudyPlan <-> Subject | `study_plan_subjects` | `semester`, `weekly_hours`, `is_elective`, prerequisite/corequisite FKs |
| User <-> AcademicArea | `user_area_assignments` | `assigned_at`, `assigned_by_user_id` |
| Instructor <-> TimeSlot (avail) | `instructor_availabilities` | `period_id`, `is_available` |
| Classroom <-> TimeSlot (avail) | `classroom_availabilities` | `period_id`, `is_available`, `reserved_by_area_id` |

---

## 6. Database Design Decisions

### 6.1 Why PostgreSQL

- **JSONB support:** Constraints, solver configs, and import errors use semi-structured data that changes shape over time. JSONB provides schema-flexible storage with indexing (GIN indexes).
- **Row-Level Security (RLS):** Native support for multi-tenant isolation at the database layer, not just the application layer.
- **Advanced indexing:** Partial indexes (e.g., `UNIQUE WHERE status IN ('queued','running')`) enforce business rules at the database level.
- **Partition support:** `AuditLog` partitioned by month for query performance at scale.
- **Mature ecosystem:** Well-supported by SQLAlchemy, Alembic, and the existing deployment on Railway (already uses PostgreSQL).
- **INET type:** Native IP address storage for audit logs.
- **TIME type:** Proper time-of-day storage for time slots without date ambiguity.

### 6.2 UUID vs Integer Primary Keys

**Decision: UUIDs everywhere.**

Rationale:
- **Multi-tenancy safety.** Sequential integers leak information (e.g., "there are 42 instructors"). UUIDs are opaque.
- **Distributed generation.** UUIDs can be generated client-side or in application code without a database round-trip. This matters for bulk imports and offline-capable future scenarios.
- **Merge safety.** If two institutions' data ever needs to be consolidated (university merger, data migration), there are no PK collisions.
- **API hygiene.** `/api/instructors/3` is guessable; `/api/instructors/a1b2c3d4-...` is not.

Performance note: UUIDv7 (time-ordered) will be used to maintain B-tree locality. PostgreSQL 17 supports `gen_random_uuid()` natively; for UUIDv7 we use the `uuid-ossp` or `pgcrypto` extension with application-layer generation.

### 6.3 Soft Deletes vs Hard Deletes

**Decision: Hybrid approach.**

| Entity | Strategy | Reason |
|---|---|---|
| Core academic data (Subject, Instructor, Classroom, StudyPlan) | **Soft delete** via `is_active = FALSE` | Historical schedules reference these; hard delete would break FK integrity |
| Schedule results, assignments | **Never deleted** | Audit trail; immutable once created |
| AuditLog | **Never deleted** | Compliance |
| Draft data (unsaved offerings, temp imports) | **Hard delete** | No historical value; keeps tables clean |
| Junction tables (specialties, equipment) | **Hard delete** | Removing a specialty mapping is not historically meaningful |

Soft-deleted rows are excluded by default in all queries via SQLAlchemy query filters:

```python
# In the base query mixin:
@declared_attr
def __mapper_args__(cls):
    return {"confirm_deleted_rows": False}

# Default filter applied via session events:
# .filter(Entity.is_active == True)
```

### 6.4 Temporal Data Handling

Study plans change over time. The design handles this via:

1. **Versioned study plans.** Each `StudyPlan` has `effective_from` and `effective_until` dates. Multiple plans can coexist for the same program.
2. **Period-scoped data.** Contracts, availability, offerings, and preferences are all scoped to an `AcademicPeriod`. Changing them for a new period does not affect historical data.
3. **Snapshot on solver run.** `ScheduleRun.solver_config` captures a JSON snapshot of all parameters at execution time, making results reproducible.
4. **No temporal tables.** PostgreSQL temporal tables (SQL:2011) are not used because the versioning granularity (per-period, per-plan-version) is already modeled explicitly. Adding temporal tables would add complexity without clear benefit.

### 6.5 Multi-Tenancy Strategy

**Decision: Row-level isolation with PostgreSQL RLS.**

Why not schema-per-tenant:
- The current deployment is a single Railway PostgreSQL instance. Schema-per-tenant would complicate migrations (must run Alembic on every schema), connection pooling, and backup/restore.
- Row-level isolation is simpler to implement, test, and deploy. RLS policies provide database-level enforcement.

Implementation:
1. Every tenant-scoped table has an `institution_id UUID NOT NULL` column.
2. A PostgreSQL session variable `SET app.current_institution = '<uuid>'` is set on each request.
3. RLS policies filter reads and writes:

```sql
CREATE POLICY tenant_isolation ON subjects
    USING (institution_id = current_setting('app.current_institution')::uuid)
    WITH CHECK (institution_id = current_setting('app.current_institution')::uuid);
```

4. The `super_admin` role bypasses RLS via `SET ROLE` to a superuser role.

### 6.6 Audit Trail Approach

- **Write path:** Application middleware captures the before/after state of every CUD operation and writes an `AuditLog` row asynchronously via a background task queue (Celery or in-process asyncio).
- **Immutability:** The `audit_logs` table has no `UPDATE` or `DELETE` grants for the application role.
- **Partitioning:** Monthly partitions on `created_at` to keep queries fast and enable efficient archival.
- **Retention:** Configurable per institution; default 2 years. Partitions older than retention are detached and archived to cold storage.

---

## 7. Migration Path

### Phase 0: Preparation (no downtime)

1. **Create the new schema** alongside the old one using Alembic migrations.
2. **Seed reference data:** Institution (one default), Roles, Permissions, EquipmentTypes, default Constraints, default ValidationRules, default TimeSlots (matching the current 6-day x 11-block grid), default ScheduleTypes.

### Phase 1: Core Entities (backward-compatible)

1. Create tables: `institutions`, `academic_areas`, `subjects`, `instructors`, `instructor_specialties`.
2. **Data migration script:**
   - Create one `Institution` row for the current university.
   - Map existing `Materia.categoria` values to `AcademicArea` rows:
     - `"Software"` -> Area "Desarrollo de Software"
     - `"Humanidades"` -> Area "Humanidades"
     - `"Ciencias Basicas"` -> Area "Ciencias Basicas"
   - For each `Materia` row, create a `Subject` row with the new schema. Map `creditos` -> `credits` and `weekly_hours`, `categoria` -> `area_id` via the area lookup, infer `subject_type` and `requires_lab` from the current `tipo_materia` logic in `data_builder.py`.
   - For each `Profesor` row, create an `Instructor` row. Parse `codigo` -> `employee_code`, `nombre` -> `first_name` + `last_name`.
   - For each `Profesor.materia_id`, create an `InstructorSpecialty` row.
   - Read the frontend localStorage migration code (the `materiaIds` array) and for each profesor that has multiple `materiaIds` in the UI state, create additional `InstructorSpecialty` rows.

3. **Dual-write period:** The API writes to both old and new tables during transition.

### Phase 2: Facilities & Scheduling

1. Create tables: `buildings`, `classrooms`, `classroom_equipment`, `equipment_types`, `time_slots`, `schedule_types`.
2. **Data migration:**
   - Create one default `Building`.
   - Map the current `Salon_XX` naming to `Classroom` rows. Use `tipo_salon` to set `classroom_type` (`"comun"` -> `standard`, `"pc"` -> `computer_lab`). Use `capacidad_salon` for `capacity`.
   - Create `TimeSlot` rows matching the current grid: 6 days x 11 blocks (06:00-16:00, 1-hour blocks).

### Phase 3: Academic Structure

1. Create tables: `academic_programs`, `study_plans`, `study_plan_subjects`, `academic_periods`, `academic_offerings`, `groups`.
2. **Data migration:**
   - Create a default `AcademicProgram` (e.g., "Ingenieria de Sistemas").
   - Create a default `StudyPlan` from the hardcoded `asignaturas` list in `data_builder.py`, inferring semesters from subject ordering.
   - Create `StudyPlanSubject` rows linking subjects to the plan.

### Phase 4: Contracts, Availability, Preferences

1. Create tables: `instructor_contracts`, `instructor_availabilities`, `instructor_preferences`, `instructor_restrictions`.
2. **Data migration:** Create default full-time contracts for all existing instructors. No availability/preference data exists currently -- these start empty.

### Phase 5: Identity & Access

1. Create tables: `users`, `roles`, `permissions`, `role_permissions`, `user_area_assignments`.
2. **Data migration:** Create a default admin user. Seed roles and permissions.

### Phase 6: Operations & Scheduling

1. Create tables: `constraints`, `schedule_runs`, `schedule_results`, `schedule_assignments`, `schedule_modifications`, `audit_logs`, `import_jobs`, `publications`, `validation_rules`.
2. **Data migration:**
   - For each existing `RunJob` row, create a `ScheduleRun` row. Parse `result_json` to populate `ScheduleResult` and `ScheduleAssignment` rows where possible.

### Phase 7: Cutover

1. Update the API to read exclusively from new tables.
2. Update the frontend to use new API endpoints.
3. Drop the old `materias`, `profesores`, and `run_jobs` tables.
4. Remove the localStorage-based `materiaIds` workaround from the frontend.

### Phase 8: Cleanup

1. Remove dual-write code.
2. Remove old model classes (`Materia`, `Profesor`, `RunJob`).
3. Run `VACUUM ANALYZE` on all new tables.

---

## 8. Sample Data Flow

### Scenario: Area "Desarrollo de Software" uploads its offering for period 2025-1

**Step 1: Area coordinator logs in**
- `User` authenticates -> JWT issued with `institution_id`, `user_id`, `role = area_coordinator`.
- `UserAreaAssignment` confirms the user manages area "Desarrollo de Software".
- RLS session variable `app.current_institution` is set.

**Step 2: Coordinator confirms subjects are up to date**
- Reads `Subject` rows where `area_id = <desarrollo_de_software_id>`.
- Adds a new subject "Inteligencia Artificial" via `POST /subjects`.
- Creates:
  - 1 row in `subjects` (code: "IS-450", credits: 3, requires_lab: true, subject_type: theoretical_practical).
  - 1 row in `audit_logs` (action: create, entity_type: Subject).

**Step 3: Coordinator manages instructors**
- Reads `Instructor` rows for the area.
- Adds specialties: `POST /instructors/{id}/specialties` -> creates `InstructorSpecialty` rows linking instructors to subjects.
- Uploads availability via Excel: `POST /imports/upload` -> creates `ImportJob` row, then processes file to create `InstructorAvailability` rows.

**Step 4: Coordinator creates offerings**
- For period 2025-1, creates academic offerings: `POST /offerings`.
- For each offered subject, specifies `num_groups` and `expected_enrollment`.
- Creates:
  - N rows in `academic_offerings` (status: draft).
  - For each offering, M rows in `groups` (one per group_number).
- Coordinator reviews, then confirms each offering -> `PATCH /offerings/{id}` sets `status = 'confirmed'`.

**Step 5: Repeat for all areas**
- "Ciencias Basicas", "Humanidades", "Idiomas", "Investigacion" coordinators each do steps 2-4 for their areas.

**Step 6: Director validates**
- Director (role = director) sees a dashboard with all areas' offerings for period 2025-1.
- Runs validation: `POST /validation/run?period_id=<2025-1>`.
- System evaluates all active `ValidationRule` rows:
  - `all_offerings_confirmed`: Checks `AcademicOffering.status = 'confirmed'` for all offerings in the period.
  - `all_groups_have_instructors`: For each `Group`, checks that at least one `InstructorSpecialty` exists for the group's subject.
  - `all_groups_have_classrooms`: For each `Group`, checks that at least one `Classroom` matches the subject's type and capacity requirements.
  - `contracts_exist`: Checks that every assigned instructor has an `InstructorContract` for the period.
- Returns: `{"valid": true, "errors": [], "warnings": ["2 instructors have no preferences set"]}`.

**Step 7: Director triggers solver**
- `POST /solver/run` with `period_id = <2025-1>`.
- Creates:
  - 1 row in `schedule_runs` (status: queued, solver_config: snapshot of all Constraint parameters).
  - 1 row in `audit_logs`.
- Background worker:
  1. Sets `schedule_runs.status = 'running'`, `started_at = NOW()`.
  2. Loads all data for the period:
     - `Group` rows (with their `AcademicOffering` -> `Subject` -> `area_id`, `requires_lab`, `weekly_hours`).
     - `Instructor` rows (with `InstructorContract.max_weekly_hours`, `InstructorAvailability`, `InstructorRestriction`, `InstructorSpecialty`, `InstructorPreference`).
     - `Classroom` rows (with `ClassroomEquipment`, `ClassroomAvailability`, `capacity`, `classroom_type`).
     - `TimeSlot` rows for the institution.
     - `Constraint` rows.
  3. Builds the CP-SAT model (the same logic as `model_builder.py`, but reading from DB entities instead of hardcoded data).
  4. Runs the solver.
  5. On success (OPTIMAL or FEASIBLE):
     - Creates 1 `ScheduleResult` row.
     - Creates N `ScheduleAssignment` rows (one per group-per-time-slot).
     - Updates `schedule_runs`: `status = 'done'`, `solver_status = 'OPTIMAL'`, statistics fields.
  6. On failure: updates `schedule_runs.status = 'error'`, `error_detail`.

**Step 8: Director reviews and adjusts**
- Director views the generated schedule in the calendar UI.
- Swaps one instructor assignment: `PATCH /assignments/{id}` with `{instructor_id: <new_id>}`.
- System:
  - Validates: new instructor has specialty for the subject, is available in that time slot, does not exceed max_weekly_hours.
  - Updates the `ScheduleAssignment` row, sets `is_modified = TRUE`.
  - Creates 1 `ScheduleModification` row (field_changed: instructor_id, old_value, new_value).

**Step 9: Director publishes**
- `POST /publications` with `result_id = <result_id>`.
- Creates 1 `Publication` row (status: published, version: 1).
- Previous publication (if any) is set to `status = 'superseded'`.
- Published schedule becomes visible to viewers.

**Step 10: Export**
- Director exports to Excel: `GET /schedules/{result_id}/export/excel`.
- System generates the Excel file using the same logic as `excel_exporter.py`, but reading from `ScheduleAssignment` rows joined with `Group`, `Subject`, `Instructor`, `Classroom`, and `TimeSlot`.

---

## Appendix A: Table Name Summary

| # | Entity | Table Name |
|---|---|---|
| 1 | Institution | `institutions` |
| 2 | AcademicArea | `academic_areas` |
| 3 | AcademicProgram | `academic_programs` |
| 4 | StudyPlan | `study_plans` |
| 5 | StudyPlanSubject | `study_plan_subjects` |
| 6 | Subject | `subjects` |
| 7 | AcademicPeriod | `academic_periods` |
| 8 | AcademicOffering | `academic_offerings` |
| 9 | Group | `groups` |
| 10 | Instructor | `instructors` |
| 11 | InstructorContract | `instructor_contracts` |
| 12 | InstructorSpecialty | `instructor_specialties` |
| 13 | InstructorAvailability | `instructor_availabilities` |
| 14 | InstructorPreference | `instructor_preferences` |
| 15 | InstructorRestriction | `instructor_restrictions` |
| 16 | Building | `buildings` |
| 17 | Classroom | `classrooms` |
| 18 | ClassroomEquipment | `classroom_equipment` |
| 19 | EquipmentType | `equipment_types` |
| 20 | ClassroomAvailability | `classroom_availabilities` |
| 21 | TimeSlot | `time_slots` |
| 22 | ScheduleType | `schedule_types` |
| 23 | Constraint | `constraints` |
| 24 | ScheduleRun | `schedule_runs` |
| 25 | ScheduleResult | `schedule_results` |
| 26 | ScheduleAssignment | `schedule_assignments` |
| 27 | ScheduleModification | `schedule_modifications` |
| 28 | User | `users` |
| 29 | Role | `roles` |
| 30 | Permission | `permissions` |
| 31 | UserAreaAssignment | `user_area_assignments` |
| 32 | AuditLog | `audit_logs` |
| 33 | ImportJob | `import_jobs` |
| 34 | Publication | `publications` |
| 35 | ValidationRule | `validation_rules` |
| -- | (junction) | `role_permissions` |

**Total: 35 entities + 1 junction table = 36 database tables.**

---

## Appendix B: Column Count Summary

| Entity | Columns |
|---|---|
| Institution | 8 |
| AcademicArea | 8 |
| AcademicProgram | 10 |
| StudyPlan | 10 |
| StudyPlanSubject | 9 |
| Subject | 16 |
| AcademicPeriod | 10 |
| AcademicOffering | 13 |
| Group | 7 |
| Instructor | 12 |
| InstructorContract | 9 |
| InstructorSpecialty | 5 |
| InstructorAvailability | 6 |
| InstructorPreference | 8 |
| InstructorRestriction | 10 |
| Building | 9 |
| Classroom | 15 |
| ClassroomEquipment | 6 |
| EquipmentType | 6 |
| ClassroomAvailability | 8 |
| TimeSlot | 9 |
| ScheduleType | 8 |
| Constraint | 12 |
| ScheduleRun | 16 |
| ScheduleResult | 9 |
| ScheduleAssignment | 8 |
| ScheduleModification | 9 |
| User | 12 |
| Role | 6 |
| Permission | 6 |
| UserAreaAssignment | 5 |
| AuditLog | 10 |
| ImportJob | 14 |
| Publication | 8 |
| ValidationRule | 10 |
| role_permissions | 3 |
| **Total** | **~330 columns** |
