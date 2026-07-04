# Solver Design Document

## University Schedule Optimization Engine — Complete Redesign

**Status:** Design  
**Author:** Optimization Engineer (OR-Tools / CP-SAT Specialist)  
**Date:** 2026-06-28  
**Replaces:** `model_builder.py`, `solver_runner.py`, `extractor.py`, `data_builder.py`

---

## Table of Contents

1. [Solver Philosophy](#1-solver-philosophy)
2. [Solver Pipeline](#2-solver-pipeline)
3. [Input Specification](#3-input-specification)
4. [Output Specification](#4-output-specification)
5. [Variable Design](#5-variable-design)
6. [Constraint System Architecture](#6-constraint-system-architecture)
7. [Objective Function Design](#7-objective-function-design)
8. [Solver Module Architecture](#8-solver-module-architecture)
9. [How to Add a New Constraint](#9-how-to-add-a-new-constraint)
10. [How to Add a New Objective Component](#10-how-to-add-a-new-objective-component)
11. [How to Replace OR-Tools](#11-how-to-replace-or-tools)
12. [Session Pattern Handling](#12-session-pattern-handling)
13. [Performance Considerations](#13-performance-considerations)
14. [What to Preserve from Current Solver](#14-what-to-preserve-from-current-solver)

---

## 1. Solver Philosophy

### Core Principle: Pure Function

The solver is a **pure computational engine**. It receives a fully-specified input, performs optimization, and returns a fully-specified output. There are no side effects.

```
SolverInput  -->  [ Solver Engine ]  -->  SolverOutput
```

**What the solver IS:**
- A deterministic mathematical optimizer (given the same input and seed, it produces the same output)
- A stateless function with no memory between invocations
- A module that operates on abstract entities: groups, instructors, rooms, time slots
- An engine that applies configurable constraints and optimizes configurable objectives

**What the solver IS NOT:**
- It is not a database client. It never opens a connection, runs a query, or writes a row.
- It does not know the name of any university, department, instructor, or subject.
- It does not generate random data to fill gaps in its input.
- It does not contain business rules that belong to the application layer (e.g., "infrastructure courses go to professor 0").
- It does not produce presentation formats. It returns structured data; formatting is the caller's job.

### Engine Agnosticism

OR-Tools CP-SAT is an implementation detail. The solver's public interface is defined in terms of input DTOs and output DTOs. The constraint programming engine sits behind an adapter. Replacing OR-Tools with Gurobi, CPLEX, or a future solver requires implementing a new adapter; no application code changes.

### Why This Matters

The current solver (`model_builder.py`) violates every one of these principles. It contains 48 hardcoded subjects as Python literals. It calls `random.sample` and `random.randint` to fabricate instructor assignments and preferences. It hardcodes the string `"infraestructura"` to implement a business rule that locks professor 0 to room 0. It uses a rigid `if/elif` chain for credit-to-session mapping. It mixes index computation, variable creation, constraint posting, and objective definition in a single 400-line function. The redesign separates every concern into its own module with its own interface.

---

## 2. Solver Pipeline

The solver executes a linear pipeline of eight stages. Each stage has a single responsibility, a defined input, and a defined output. No stage reaches backward to modify a previous stage's output.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          SOLVER PIPELINE                              │
│                                                                       │
│  ┌──────────┐   ┌────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │  INPUT   │──>│ VALIDATION │──>│    INDEX     │──>│  VARIABLE   │  │
│  │  DTOs    │   │            │   │  BUILDING    │   │  CREATION   │  │
│  └──────────┘   └────────────┘   └──────────────┘   └──────┬──────┘  │
│                                                             │         │
│  ┌──────────┐   ┌────────────┐   ┌──────────────┐   ┌──────▼──────┐  │
│  │  OUTPUT  │<──│  SOLUTION  │<──│   SOLVING    │<──│ CONSTRAINT  │  │
│  │  DTOs    │   │ EXTRACTION │   │              │   │ APPLICATION │  │
│  └──────────┘   └────────────┘   └──────────────┘   └──────┬──────┘  │
│                                                             │         │
│                                                      ┌──────▼──────┐  │
│                                                      │  OBJECTIVE  │  │
│                                                      │ DEFINITION  │  │
│                                                      └─────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Stage 1: Input DTOs

The caller constructs a `SolverInput` object containing all data the solver needs. This is the ONLY entry point. The solver never fetches additional data.

### Stage 2: Validation

Before any variable is created, the input is validated for structural correctness:

- Every group references a valid session pattern (positive block lengths, total matches expected hours).
- Every instructor has at least one available time slot.
- Every group's required room type matches at least one room.
- No time slot indices are out of range or duplicated.
- No instructor is listed as eligible for a group if that instructor's max hours are zero.
- All constraint configurations reference known constraint types with valid parameter schemas.
- Session patterns do not request blocks longer than the number of time slots in a day.

Validation produces a list of `ValidationError` objects. If any are severity FATAL, the solver returns immediately with status ERROR and the error list. If severity WARNING, errors are included in the output diagnostics but solving proceeds.

### Stage 3: Index Building

Raw input lists are restructured into lookup dictionaries optimized for constraint posting. This stage produces an `IndexSet` object:

- `eligible_instructors[group_id]` -> set of instructor indices
- `eligible_rooms[group_id]` -> set of room indices (filtered by room type compatibility AND capacity >= enrollment)
- `instructor_available_slots[instructor_id]` -> set of time slot indices
- `room_available_slots[room_id]` -> set of time slot indices
- `groups_by_instructor[instructor_id]` -> set of group indices the instructor is eligible for
- `slot_to_day[slot_index]` -> day index
- `slot_to_hour[slot_index]` -> hour-within-day index
- `day_hour_to_slot[day, hour]` -> slot index
- `slots_per_day` -> number of time slots per day
- `num_days` -> number of days

This stage also performs **pruning**: if a group has no eligible instructors or no eligible rooms, the solver short-circuits to INFEASIBLE with a diagnostic explaining the failure.

### Stage 4: Variable Creation

The variable builder creates all CP-SAT decision variables using the pruned index set. Variable creation is isolated from constraint logic. Variables are stored in a `VariableSet` object (detailed in Section 5).

### Stage 5: Constraint Application

Each registered constraint module is invoked in sequence. Each receives the model, the variable set, the index set, and its specific configuration. Constraints are applied in a deterministic order: all hard constraints first, then all soft constraints. Within each category, constraints are applied in registration order.

### Stage 6: Objective Definition

Each registered objective component computes a weighted expression. The objective builder collects all component expressions, applies weights from `ObjectiveWeights`, and posts the combined objective (Minimize) to the model.

### Stage 7: Solving

The adapted solver engine (OR-Tools CP-SAT by default) is invoked with the configured parameters (max time, number of workers, random seed). This stage is purely mechanical: it calls `solver.Solve(model)` and records timing.

### Stage 8: Solution Extraction

If the solver found a FEASIBLE or OPTIMAL solution, the extractor reads variable values and constructs the output DTOs. If the solver returned INFEASIBLE, the extractor runs the diagnostics module to identify which constraints are in conflict.

---

## 3. Input Specification

All input types are immutable data classes. The solver never mutates its input.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── Enumerations ───────────────────────────────────────────────────

class ConstraintCategory(Enum):
    HARD = "hard"
    SOFT = "soft"


class SolverStatus(Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"
    ERROR = "error"
    MODEL_INVALID = "model_invalid"


class DiagnosticSeverity(Enum):
    FATAL = "fatal"
    WARNING = "warning"
    INFO = "info"


# ─── Time Slot ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class TimeSlotInput:
    """One atomic, indivisible block of time in the weekly schedule.

    The solver operates on a discrete grid. Each TimeSlotInput is one cell.
    Continuous sessions are modeled by requiring consecutive slots on the
    same day.

    Attributes:
        index:      Unique integer identifier, 0-based, globally unique
                    across all days. The solver uses this as the primary
                    key for all slot-related lookups.
        day:        Day index (0-based). Meaning (Monday, Tuesday, ...)
                    is opaque to the solver.
        period:     Period-within-day index (0-based). Period 0 is the
                    first slot of the day, period 1 is the second, etc.
                    The solver uses contiguous period indices to determine
                    whether two slots are consecutive on the same day.
        start_time: Human-readable start time (e.g. "07:00"). Informational
                    only; the solver does not parse this. Carried through to
                    output for the caller's convenience.
        end_time:   Human-readable end time (e.g. "07:50"). Same as above.
        label:      Optional display label (e.g. "Monday P1"). Not used
                    by the solver.
    """
    index: int
    day: int
    period: int
    start_time: str = ""
    end_time: str = ""
    label: str = ""


# ─── Session Pattern ────────────────────────────────────────────────

@dataclass(frozen=True)
class SessionBlock:
    """One contiguous block within a session pattern.

    Attributes:
        duration_slots: Number of consecutive time slots this block
                        occupies. Must be >= 1.
    """
    duration_slots: int


@dataclass(frozen=True)
class SessionPattern:
    """Defines how a group's weekly contact hours are distributed.

    A session pattern is a sequence of SessionBlocks. Each block is
    scheduled independently (on potentially different days, in different
    rooms). The solver guarantees that two blocks from the same pattern
    are never placed on the same day (unless allow_same_day is True).

    Examples:
        4-credit course, two 2-hour meetings:
            SessionPattern(blocks=[SessionBlock(2), SessionBlock(2)])

        3-credit course, one 3-hour meeting:
            SessionPattern(blocks=[SessionBlock(3)])

        3-credit course, one 2-hour + one 1-hour meeting:
            SessionPattern(blocks=[SessionBlock(2), SessionBlock(1)])

        1-credit course, one 1-hour meeting:
            SessionPattern(blocks=[SessionBlock(1)])

    Attributes:
        blocks:          Ordered list of session blocks. The solver creates
                         one placement variable set per block.
        allow_same_day:  If False (default), the solver adds a constraint
                         ensuring no two blocks land on the same day.
    """
    blocks: tuple[SessionBlock, ...]
    allow_same_day: bool = False


# ─── Group ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GroupInput:
    """One section/group that must be scheduled.

    A group represents a single section of a course offering. If a
    course has 3 groups, the caller creates 3 GroupInput objects.
    The solver treats each as an independent scheduling unit.

    Attributes:
        id:                  Unique string identifier (e.g., "CS101-G1").
        subject_id:          Identifier for the subject/course. Groups
                             sharing the same subject_id may trigger
                             subject-level constraints (e.g., different
                             time slots for same-subject groups).
        session_pattern:     How the group's weekly hours are structured.
        required_room_type:  Room type tag (e.g., "standard", "computer_lab",
                             "physics_lab"). The solver matches this against
                             RoomInput.room_type.
        required_equipment:  Set of equipment tags the room must have
                             (e.g., {"projector", "whiteboard"}). The room
                             must have ALL listed equipment.
        enrollment:          Number of enrolled students. Used for
                             capacity filtering and room-fit optimization.
        eligible_instructor_ids: Set of instructor IDs that can teach
                             this group. The solver will assign exactly one.
        preferred_slot_indices:  Optional set of time slot indices where
                             this group prefers to be scheduled. Used by
                             soft constraints, never enforced as hard.
        tags:                Arbitrary string tags for custom constraint
                             logic (e.g., {"morning_only", "lab_required"}).
    """
    id: str
    subject_id: str
    session_pattern: SessionPattern
    required_room_type: str
    required_equipment: frozenset[str] = frozenset()
    enrollment: int = 0
    eligible_instructor_ids: frozenset[str] = frozenset()
    preferred_slot_indices: frozenset[int] = frozenset()
    tags: frozenset[str] = frozenset()


# ─── Instructor ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class InstructorInput:
    """One instructor available for scheduling.

    Attributes:
        id:                Unique string identifier.
        max_hours_per_week: Maximum number of time slots this instructor
                           can be scheduled in one week. Hard ceiling.
        max_hours_per_day:  Maximum number of time slots per day.
        available_slot_indices: Set of time slot indices where this
                           instructor is available. The solver will
                           NEVER schedule the instructor outside these
                           slots. An empty set means the instructor is
                           unavailable (validation will warn).
        specialty_subject_ids: Subjects this instructor specializes in.
                           Used by preference/quality soft constraints.
        preferences:       Dict mapping group_id -> preference score
                           (higher is better). Missing entries default
                           to 0.
    """
    id: str
    max_hours_per_week: int
    max_hours_per_day: int = 100  # effectively unlimited if not set
    available_slot_indices: frozenset[int] = frozenset()
    specialty_subject_ids: frozenset[str] = frozenset()
    preferences: dict[str, int] = field(default_factory=dict)


# ─── Room ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RoomInput:
    """One physical room available for scheduling.

    Attributes:
        id:                  Unique string identifier.
        capacity:            Maximum number of students.
        room_type:           Type tag (e.g., "standard", "computer_lab").
                             Matched against GroupInput.required_room_type.
        equipment:           Set of equipment tags this room provides.
        available_slot_indices: Time slots when this room is available.
                             Empty means always available (all slots).
    """
    id: str
    capacity: int
    room_type: str
    equipment: frozenset[str] = frozenset()
    available_slot_indices: frozenset[int] = frozenset()


# ─── Constraint Configuration ──────────────────────────────────────

@dataclass(frozen=True)
class ConstraintConfig:
    """Configuration for a single constraint instance.

    Attributes:
        constraint_type: Registered name of the constraint class
                         (e.g., "instructor_no_overlap", "workload_balance").
        enabled:         If False, the constraint is skipped entirely.
        category:        HARD or SOFT. Hard constraints are enforced
                         absolutely. Soft constraints contribute to the
                         objective function.
        weight:          For SOFT constraints, the weight in the objective.
                         Ignored for HARD constraints.
        parameters:      Constraint-specific parameters as a dict. Each
                         constraint class defines its own parameter schema
                         and validates it.
    """
    constraint_type: str
    enabled: bool = True
    category: ConstraintCategory = ConstraintCategory.HARD
    weight: int = 1
    parameters: dict = field(default_factory=dict)


# ─── Objective Weights ──────────────────────────────────────────────

@dataclass(frozen=True)
class ObjectiveWeights:
    """Weights for each component of the objective function.

    All weights are non-negative integers. A weight of 0 disables the
    component. Higher weights give the component more influence.

    The objective function is: Minimize(sum of weight_i * component_i).
    Components that represent "goodness" (preferences, compactness) are
    negated internally so that Minimize maximizes them.

    Attributes:
        workload_balance_range: Weight for (max_load - min_load) across
                                instructors. Higher values push toward
                                equal distribution.
        workload_balance_deviation: Weight for the sum of absolute
                                    deviations from the target load.
        instructor_preferences: Weight for the total preference score
                                (negated, since higher preference is better).
        schedule_compactness:   Weight for minimizing gaps in daily
                                schedules.
        room_utilization:       Weight for preferring rooms whose capacity
                                is close to enrollment.
        day_distribution:       Weight for spreading sessions across
                                different days.
    """
    workload_balance_range: int = 200
    workload_balance_deviation: int = 20
    instructor_preferences: int = 1
    schedule_compactness: int = 0
    room_utilization: int = 0
    day_distribution: int = 0


# ─── Solver Parameters ─────────────────────────────────────────────

@dataclass(frozen=True)
class SolverParams:
    """Engine-level parameters for the solve run.

    Attributes:
        max_time_seconds: Wall-clock time limit. The solver returns the
                          best solution found within this limit.
        num_workers:      Number of parallel search workers. 0 means
                          auto-detect (use all available cores).
        random_seed:      Seed for the solver's internal RNG. Ensures
                          reproducibility given identical input.
        stop_after_first_feasible: If True, the solver stops as soon as
                          it finds any feasible solution (status FEASIBLE).
                          Useful for fast turnaround when optimality is
                          not required.
        log_search_progress: If True, the solver logs search statistics
                          to stderr. Useful for debugging.
    """
    max_time_seconds: int = 300
    num_workers: int = 0
    random_seed: int = 42
    stop_after_first_feasible: bool = False
    log_search_progress: bool = False


# ─── Top-Level Input Container ──────────────────────────────────────

@dataclass(frozen=True)
class SolverInput:
    """Complete input to the solver engine.

    This is the ONLY argument the solver's solve() function accepts.
    It contains everything the solver needs. If data is missing from
    this object, the solver will not attempt to fetch it.

    Attributes:
        groups:            All groups to be scheduled.
        instructors:       All available instructors.
        rooms:             All available rooms.
        time_slots:        All time slots in the weekly grid.
        constraints:       Constraint configurations (which constraints
                           to apply and how to configure them).
        objective_weights: Weights for objective function components.
        solver_params:     Engine-level parameters.
    """
    groups: tuple[GroupInput, ...]
    instructors: tuple[InstructorInput, ...]
    rooms: tuple[RoomInput, ...]
    time_slots: tuple[TimeSlotInput, ...]
    constraints: tuple[ConstraintConfig, ...] = ()
    objective_weights: ObjectiveWeights = field(default_factory=ObjectiveWeights)
    solver_params: SolverParams = field(default_factory=SolverParams)
```

### Notes on the Input Model

**Immutability.** Every input dataclass is frozen. The solver cannot accidentally mutate caller data. Tuples are used instead of lists; frozensets instead of sets.

**String IDs everywhere.** Groups, instructors, and rooms use string IDs. The solver never assigns integer indices to external entities; it creates internal integer indices in the Index Building stage and maps them back to string IDs in the Solution Extraction stage. This means the caller can use database primary keys, UUIDs, or human-readable codes without the solver caring.

**Session patterns are caller-defined.** The current solver hardcodes `if cr == 4: two 2-block sessions` etc. In the new design, the caller specifies the exact pattern. If a 3-credit course should be scheduled as one 3-hour block, the caller sends `SessionPattern(blocks=[SessionBlock(3)])`. If it should be two meetings of 1.5 hours each (represented as two 2-slot blocks on a finer grid), the caller sends that. The solver does not interpret credit counts.

**Eligible instructors are pre-filtered.** The current solver picks random candidates. In the new design, the application layer determines which instructors can teach which groups (based on qualifications, department policy, contracts) and passes only the eligible ones. The solver enforces the assignment from this pre-filtered set.

**Room availability is explicit.** The current solver assumes all rooms are always available. The new design accepts per-room availability, enabling scenarios like "Lab A is unavailable on Fridays" or "Room 201 is reserved for another department in the morning."

---

## 4. Output Specification

```python
from __future__ import annotations
from dataclasses import dataclass, field


# ─── Assignment ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Assignment:
    """One scheduled group in the solution.

    Each Assignment represents a complete scheduling decision for one
    group: which instructor teaches it, and when/where each session
    block meets.

    Attributes:
        group_id:       The group that was scheduled.
        instructor_id:  The assigned instructor.
        sessions:       One entry per SessionBlock in the group's pattern.
                        Each session specifies the room and time slots.
    """
    group_id: str
    instructor_id: str
    sessions: tuple[SessionAssignment, ...]


@dataclass(frozen=True)
class SessionAssignment:
    """One session block placement within an Assignment.

    Attributes:
        block_index:     Which block in the session pattern (0-based).
        room_id:         The room assigned to this session.
        slot_indices:    Ordered tuple of time slot indices occupied by
                         this session. The length equals the block's
                         duration_slots. All slots are consecutive on
                         the same day.
    """
    block_index: int
    room_id: str
    slot_indices: tuple[int, ...]


# ─── Diagnostics ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Diagnostic:
    """One diagnostic finding from the solver.

    Diagnostics cover validation errors, infeasibility explanations,
    soft constraint violations, and informational messages.

    Attributes:
        severity:    FATAL, WARNING, or INFO.
        code:        Machine-readable code (e.g., "NO_ELIGIBLE_ROOM",
                     "INSTRUCTOR_OVERLOADED").
        message:     Human-readable explanation.
        group_id:    The affected group, if applicable.
        constraint:  The constraint that produced this diagnostic,
                     if applicable.
        details:     Additional structured data for programmatic use.
    """
    severity: DiagnosticSeverity
    code: str
    message: str
    group_id: str = ""
    constraint: str = ""
    details: dict = field(default_factory=dict)


# ─── Solver Statistics ──────────────────────────────────────────────

@dataclass(frozen=True)
class SolverStatistics:
    """Performance and quality metrics from the solve run.

    Attributes:
        elapsed_seconds:    Wall-clock time spent solving.
        num_variables:      Total decision variables in the CP model.
        num_constraints:    Total constraints posted to the CP model.
        objective_value:    Final objective function value (lower is
                            better; None if no solution found).
        best_bound:         Best known lower bound on the objective
                            (for measuring optimality gap).
        branches:           Number of search branches explored.
        conflicts:          Number of conflicts encountered during search.
        groups_scheduled:   Number of groups that received an assignment.
        groups_total:       Total number of groups in the input.
        variables_pruned:   Number of variables eliminated during
                            index building (impossible assignments).
    """
    elapsed_seconds: float
    num_variables: int
    num_constraints: int
    objective_value: Optional[float] = None
    best_bound: Optional[float] = None
    branches: int = 0
    conflicts: int = 0
    groups_scheduled: int = 0
    groups_total: int = 0
    variables_pruned: int = 0


# ─── Top-Level Output Container ────────────────────────────────────

@dataclass(frozen=True)
class SolverOutput:
    """Complete output from the solver engine.

    This is the ONLY return value from the solver's solve() function.

    Attributes:
        status:       Solution status.
        assignments:  Scheduled groups (empty if INFEASIBLE/ERROR).
        statistics:   Performance metrics.
        diagnostics:  Validation errors, warnings, infeasibility
                      explanations.
    """
    status: SolverStatus
    assignments: tuple[Assignment, ...] = ()
    statistics: SolverStatistics = None
    diagnostics: tuple[Diagnostic, ...] = ()
```

### Status Semantics

| Status | Meaning | `assignments` | `diagnostics` |
|--------|---------|---------------|---------------|
| `OPTIMAL` | Proven optimal solution found | Complete | May contain INFO-level soft constraint notes |
| `FEASIBLE` | Valid solution found but optimality not proven (time limit hit) | Complete | Contains INFO about optimality gap |
| `INFEASIBLE` | No valid assignment exists | Empty | Contains FATAL diagnostics explaining conflicts |
| `TIMEOUT` | Time limit reached without finding any feasible solution | Empty | Contains WARNING about timeout |
| `ERROR` | Input validation failed or internal error | Empty | Contains FATAL validation errors |
| `MODEL_INVALID` | The CP model was malformed (bug in solver code) | Empty | Contains FATAL with internal error details |

---

## 5. Variable Design

The solver uses three layers of decision variables. Each layer serves a distinct purpose.

### Layer 1: Assignment Variables `y[i, g]`

```
y[i, g] in {0, 1}

i = instructor index (internal)
g = group index (internal)

y[i, g] = 1  iff  instructor i is assigned to teach group g
```

**Semantics.** Exactly one instructor is assigned to each group. For each group g:

```
sum(y[i, g] for i in eligible_instructors[g]) == 1
```

**Comparison to current solver.** The current solver uses `y[p, c, gi]` where `c` is a course index and `gi` is a group-within-course index. The new design collapses `(c, gi)` into a single group index `g`. The solver does not need to know that groups belong to courses; the application layer handles that relationship. Subject-level constraints (e.g., "groups of the same subject should not overlap") use the `subject_id` field in `GroupInput`.

### Layer 2: Placement Variables `start[g, k, d, h, r]`

```
start[g, k, d, h, r] in {0, 1}

g = group index
k = block index within the group's session pattern (0, 1, 2, ...)
d = day index
h = start period within the day
r = room index

start[g, k, d, h, r] = 1  iff  block k of group g starts at day d,
                                period h, in room r
```

**Semantics.** For each group g and each block k in g's session pattern, exactly one start variable is active:

```
sum(start[g, k, d, h, r]
    for d in days
    for h in valid_start_periods(k)
    for r in eligible_rooms[g]) == 1
```

where `valid_start_periods(k)` ensures the block fits within the day:

```
valid_start_periods(k) = {h : 0 <= h <= slots_per_day - duration(k)}
```

**Comparison to current solver.** The current solver uses `start[L, tag, p, c, gi, d, h, s]` where `L` is the block length and `tag` is a session identifier. It also includes the professor `p` in the key, creating `|professors| * |days| * |periods| * |rooms|` variables per block. The new design drops the instructor from the start key. The link between instructor and placement is enforced through a channeling constraint between `y` and `start` variables, mediated by the coverage layer. This reduces the number of start variables by a factor of `|eligible_instructors|`.

**Why this reduction matters.** The current solver creates start variables for every `(professor, day, period, room)` combination per block. For a group with 6 eligible professors, 6 days, 10 valid start periods, and 5 eligible rooms, that is 6 * 6 * 10 * 5 = 1800 start variables per block. The new design creates 6 * 10 * 5 = 300 start variables per block (the professor dimension is handled by `y`). This 6x reduction in variable count significantly tightens the model.

### Layer 3: Coverage Variables `x[g, t, r]`

```
x[g, t, r] in {0, 1}

g = group index
t = time slot index (global, across all days)
r = room index

x[g, t, r] = 1  iff  group g occupies room r during time slot t
```

**Semantics.** Coverage variables are derived from start variables. They represent the "footprint" of a scheduled session across time slots:

```
For each (g, t, r):
    x[g, t, r] = sum(start[g, k, d, h, r]
                      for all (k, d, h) such that slot t falls within
                      block k starting at (d, h) with length duration(k))
```

This is a channeling constraint: the coverage variable is 1 if and only if at least one start variable "covers" that time slot in that room. Since blocks do not overlap for the same group (each block starts on a different day), the sum is at most 1, so we can use equality.

**Why coverage variables exist.** They make constraint posting straightforward:

- **Instructor no-overlap:** For each instructor i and time slot t, at most one group assigned to i occupies slot t.
  ```
  sum(x[g, t, r] for g in groups_of(i) for r in rooms) <= 1
  ```
  But we need to link this to the `y` variables. We introduce an auxiliary:
  ```
  occ[i, g, t] = y[i, g] AND (sum(x[g, t, r] for r in rooms) >= 1)
  ```
  Then: `sum(occ[i, g, t] for g in eligible_groups_of(i)) <= 1`

- **Room no-overlap:** For each room r and time slot t, at most one group occupies it.
  ```
  sum(x[g, t, r] for g in all_groups) <= 1
  ```

**Comparison to current solver.** The current solver uses `x[p, c, gi, b, s]` which includes the professor index. The new design uses `x[g, t, r]` without the instructor. The instructor linkage is handled by the `y` variables. This is cleaner: the coverage variable answers "is this room/slot occupied by this group?" regardless of who teaches it.

### Linking Variables Across Layers

The three layers are connected by channeling constraints:

**1. Start-to-coverage channeling:**
```python
# For each group g, time slot t, room r:
x[g, t, r] == sum(
    start[g, k, d, h, r]
    for k in range(num_blocks(g))
    for (d, h) such that slot t is at offset (t - day_start(d) - h)
                   within [0, duration(k))
)
```

**2. Instructor-to-start channeling (aggregate):**
```python
# For each group g:
# Total number of active start variables must equal number of blocks
# (already enforced by "exactly one start per block" constraint).
# The instructor is linked indirectly: the instructor's no-overlap
# constraint uses y[i,g] to filter which groups count toward
# instructor i's load.
```

**3. Instructor load computation:**
```python
# For each instructor i:
load[i] = sum(
    y[i, g] * total_slots(g)
    for g in eligible_groups_of(i)
)
```

where `total_slots(g) = sum(block.duration_slots for block in g.session_pattern.blocks)`.

Since `y[i, g]` is boolean and `total_slots(g)` is a constant, this linearizes trivially:

```python
load[i] = sum(
    total_slots(g) * y[i, g]
    for g in eligible_groups_of(i)
)
```

### Variable Summary

| Variable | Dimensions | Count (worst case) | Purpose |
|----------|------------|-------------------|---------|
| `y[i, g]` | instructors x groups | `sum(len(eligible[g]) for g in groups)` | Instructor-group assignment |
| `start[g, k, d, h, r]` | groups x blocks x days x periods x rooms | `sum(num_blocks(g) * days * valid_periods * eligible_rooms for g)` | Session placement |
| `x[g, t, r]` | groups x slots x rooms | `sum(total_coverage_slots(g) * eligible_rooms for g)` | Time-room occupation |

---

## 6. Constraint System Architecture

### Base Interface

Every constraint implements a single interface:

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class ConstraintType(Enum):
    HARD = "hard"
    SOFT = "soft"


class BaseConstraint(ABC):
    """Interface that every constraint module must implement."""

    @abstractmethod
    def apply(
        self,
        model: Any,            # The CP model (CpModel in OR-Tools)
        variables: VariableSet,
        indices: IndexSet,
        config: ConstraintConfig,
    ) -> ConstraintResult:
        """Post this constraint's clauses to the model.

        For HARD constraints: add model.Add(...) or model.AddXxx(...)
        calls directly.

        For SOFT constraints: create penalty variables, add the penalty
        logic, and return a ConstraintResult with the penalty expression
        and its weight. The objective builder will incorporate this into
        the overall objective.

        Args:
            model:     The CP-SAT model object.
            variables: All decision variables (y, start, x, and any
                       auxiliary variables).
            indices:   Pre-computed lookup structures.
            config:    This constraint's configuration (enabled, weight,
                       parameters).

        Returns:
            ConstraintResult with optional penalty expression for soft
            constraints, and a count of clauses added.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this constraint type.

        Must match the constraint_type string used in ConstraintConfig.
        """
        ...

    @property
    @abstractmethod
    def constraint_type(self) -> ConstraintType:
        """Whether this is a HARD or SOFT constraint."""
        ...

    @abstractmethod
    def validate_config(self, config: ConstraintConfig) -> list[str]:
        """Validate constraint-specific parameters.

        Returns a list of error messages. Empty list means valid.
        Called during the Validation stage before any variables are created.
        """
        ...


@dataclass
class ConstraintResult:
    """Result of applying a constraint.

    Attributes:
        clauses_added: Number of individual constraints/clauses added
                       to the model. For logging and diagnostics.
        penalty_expr:  For SOFT constraints, the expression to minimize.
                       None for HARD constraints.
        penalty_weight: Weight for the penalty expression.
    """
    clauses_added: int = 0
    penalty_expr: Any = None  # LinearExpr or IntVar from the CP model
    penalty_weight: int = 0
```

### Constraint Registry

Constraints are registered at import time using a simple registry pattern:

```python
from typing import Type

_CONSTRAINT_REGISTRY: dict[str, Type[BaseConstraint]] = {}


def register_constraint(cls: Type[BaseConstraint]) -> Type[BaseConstraint]:
    """Decorator that registers a constraint class by its name."""
    instance = cls()
    _CONSTRAINT_REGISTRY[instance.name] = cls
    return cls


def get_constraint(name: str) -> BaseConstraint:
    """Instantiate a registered constraint by name."""
    if name not in _CONSTRAINT_REGISTRY:
        raise KeyError(
            f"Unknown constraint type '{name}'. "
            f"Registered types: {sorted(_CONSTRAINT_REGISTRY.keys())}"
        )
    return _CONSTRAINT_REGISTRY[name]()


def list_constraints() -> list[str]:
    """Return all registered constraint names."""
    return sorted(_CONSTRAINT_REGISTRY.keys())
```

### Planned Constraint Modules

#### Hard Constraints

**1. InstructorNoOverlapConstraint** (`instructor_no_overlap`)

Ensures no instructor teaches two groups at the same time slot.

```
For each instructor i, for each time slot t:
    sum(occ[i, g, t] for g in eligible_groups_of(i)) <= 1

where occ[i, g, t] is an auxiliary boolean:
    occ[i, g, t] == 1  iff  y[i, g] == 1 AND group g is active at slot t
```

Mathematical formulation:

For each instructor i and time slot t, define the auxiliary `occ[i, g, t]`:

```
occ[i, g, t] <= y[i, g]
occ[i, g, t] <= active[g, t]          (where active[g,t] = sum_r x[g, t, r])
occ[i, g, t] >= y[i, g] + active[g, t] - 1
```

Then enforce:

```
sum_g occ[i, g, t] <= 1
```

**Implementation note.** Creating `occ` variables for every (instructor, group, slot) triple can be expensive. As an optimization, only create `occ` for (i, g) pairs where `i in eligible_instructors[g]`, and only for slots where group g could possibly be active (based on the group's session pattern and available rooms). This pruning is critical for performance.

**Alternative (more compact) formulation.** Instead of auxiliary `occ` variables, use an implication: if `y[i, g]` is true, then all coverage variables `x[g, t, r]` count toward instructor i's slot budget. This can be modeled with:

```
For each instructor i, for each time slot t:
    sum(x[g, t, r] for g in eligible_groups_of(i) for r in rooms)
    <= 1 + (|eligible_groups_of(i)| - 1) * (1 - y[i, g_check])
```

However, this big-M formulation is weaker. The preferred approach is the `occ` auxiliary when variable counts allow it, falling back to the big-M formulation for very large instances (>500 groups).

---

**2. RoomNoOverlapConstraint** (`room_no_overlap`)

Ensures no room hosts two groups at the same time slot.

```
For each room r, for each time slot t:
    sum(x[g, t, r] for g in all_groups where r in eligible_rooms[g]) <= 1
```

This is the simplest constraint to implement because coverage variables `x[g, t, r]` directly express room occupancy.

---

**3. InstructorMaxHoursConstraint** (`instructor_max_hours`)

Enforces each instructor's weekly and daily hour limits.

Weekly:
```
For each instructor i:
    load[i] = sum(total_slots(g) * y[i, g] for g in eligible_groups_of(i))
    load[i] <= max_hours_per_week[i]
```

Daily:
```
For each instructor i, for each day d:
    day_load[i, d] = sum(occ[i, g, t] for g where y[i,g] possible
                         for t in slots_of_day(d))
    day_load[i, d] <= max_hours_per_day[i]
```

---

**4. InstructorAvailabilityConstraint** (`instructor_availability`)

Prevents scheduling an instructor outside their available slots.

```
For each instructor i, for each time slot t NOT in available_slots[i]:
    For each group g in eligible_groups_of(i):
        occ[i, g, t] == 0
        (equivalently: y[i, g] == 1 => active[g, t] == 0)
```

**Compact formulation.** If instructor i is unavailable at slot t, then no group assigned to i can be active at t:

```
For each group g in eligible_groups_of(i):
    y[i, g] + active[g, t] <= 1
```

This is a single linear constraint per (instructor, group, unavailable_slot) triple.

---

**5. RoomCompatibilityConstraint** (`room_compatibility`)

Enforced during index building (pruning), not as CP constraints. During index building, `eligible_rooms[g]` is computed by filtering rooms whose `room_type` matches `required_room_type[g]`, whose `capacity >= enrollment[g]`, and whose `equipment` is a superset of `required_equipment[g]`. No start or coverage variables are created for ineligible rooms, so no CP constraint is needed.

If a group has zero eligible rooms after pruning, the solver returns INFEASIBLE with a diagnostic.

---

**6. SessionCountConstraint** (`session_count`)

Enforced by the variable structure. For each group g, for each block k in its session pattern, exactly one start variable is active:

```
For each group g, for each block k:
    sum(start[g, k, d, h, r] for all valid (d, h, r)) == 1
```

This is a fundamental structural constraint, not a plugin. However, it is still implemented as a constraint module for consistency and testability.

---

**7. SessionDifferentDaysConstraint** (`session_different_days`)

Ensures that different blocks of the same group land on different days (unless `allow_same_day` is True for that group's session pattern).

```
For each group g where not g.session_pattern.allow_same_day:
    For each pair of blocks (k1, k2) where k1 < k2:
        For each day d:
            day_active[g, k1, d] + day_active[g, k2, d] <= 1

where day_active[g, k, d] = sum(start[g, k, d, h, r] for h, r)
```

---

#### Soft Constraints

Soft constraints do not add hard constraints to the model. Instead, they create penalty variables and return them as part of the `ConstraintResult`. The objective builder sums all penalty expressions with their respective weights.

**8. WorkloadBalanceConstraint** (`workload_balance`)

Minimizes the difference between the most-loaded and least-loaded instructors, plus individual deviations from the target average.

```
load[i] = sum(total_slots(g) * y[i, g] for g in eligible_groups_of(i))

max_load = max(load[i] for all i)
min_load = min(load[i] for all i)
target = sum(total_required_slots) / num_instructors

dev[i] = |load[i] - target|    (modeled as dev[i] >= load[i] - target,
                                  dev[i] >= target - load[i])

penalty = W_range * (max_load - min_load) + W_dev * sum(dev[i])
```

This is the core of the current solver's objective and must be preserved.

**Parameters:**
- `range_weight` (int, default 200): Weight for max-min range.
- `deviation_weight` (int, default 20): Weight for sum of deviations.

---

**9. PreferenceConstraint** (`preferences`)

Maximizes total preference score (modeled as minimizing its negation).

```
pref_total = sum(preferences[i][g] * y[i, g]
                 for g in groups
                 for i in eligible_instructors[g])

penalty = -1 * pref_total
```

---

**10. CompactnessConstraint** (`compactness`)

Minimizes gaps in an instructor's daily schedule. A gap occurs when an instructor has a free slot between two occupied slots on the same day.

```
For each instructor i, for each day d:
    Let occupied_slots = sorted list of slots where instructor is active
    gaps[i, d] = count of slots between first and last occupied slot
                 that are NOT occupied

penalty = sum(gaps[i, d] for all i, d)
```

CP-SAT modeling: For each instructor i and day d, define:
- `first[i, d]` = IntVar, the earliest period with an active slot (or slots_per_day if none)
- `last[i, d]` = IntVar, the latest period with an active slot (or 0 if none)
- `span[i, d] = last[i, d] - first[i, d] + 1` (if any slot is active, else 0)
- `occupied_count[i, d]` = number of active slots for instructor i on day d
- `gap[i, d] = span[i, d] - occupied_count[i, d]` (non-negative)

---

**11. RoomUtilizationConstraint** (`room_utilization`)

Prefers rooms whose capacity is close to the group's enrollment. Penalizes wasted capacity.

```
For each group g, for each room r in eligible_rooms[g]:
    waste[g, r] = capacity[r] - enrollment[g]

For each group g:
    actual_waste[g] = sum(waste[g, r] * room_used[g, r] for r)
    where room_used[g, r] = 1 iff group g uses room r for any session

penalty = sum(actual_waste[g] for all g)
```

---

**12. DayDistributionConstraint** (`day_distribution`)

Prefers spreading sessions across as many different days as possible. Penalizes multiple blocks of the same group on consecutive days (if the pattern allows same-day, this is already constrained; this handles the preference for non-adjacent days).

```
For each group g with multiple blocks:
    For each pair of blocks (k1, k2):
        adjacency_penalty[g, k1, k2] = 1 if |day(k1) - day(k2)| == 1
                                       0 otherwise

penalty = sum(adjacency_penalty)
```

**Note:** This is difficult to model exactly in CP-SAT because it requires reasoning about absolute differences of day variables. A practical approximation: create an IntVar `day_var[g, k]` representing the day of block k, then penalize consecutive values.

---

**13. LabPriorityConstraint** (`lab_priority`)

Gives priority to specialized rooms for courses that need them. Penalizes scheduling a lab-requiring group in a general-purpose room when a lab is available.

```
For each group g with required_room_type == "lab_type":
    penalty[g] = 1 if assigned room is not of type "lab_type"
                 0 otherwise
```

Since room compatibility is enforced during pruning, this constraint is only relevant when the group's required_room_type allows multiple types (e.g., a group that CAN use either a standard room or a lab, but PREFERS the lab).

---

### Constraint Execution Order

```
1. [STRUCTURAL] SessionCountConstraint       — one start per block
2. [STRUCTURAL] SessionDifferentDaysConstraint — blocks on different days
3. [HARD]       RoomCompatibilityConstraint   — (handled in pruning)
4. [HARD]       InstructorNoOverlapConstraint  — no double-booking
5. [HARD]       RoomNoOverlapConstraint        — no room conflicts
6. [HARD]       InstructorMaxHoursConstraint   — hour limits
7. [HARD]       InstructorAvailabilityConstraint — slot restrictions
8. [SOFT]       WorkloadBalanceConstraint      — even distribution
9. [SOFT]       PreferenceConstraint           — instructor preferences
10. [SOFT]      CompactnessConstraint          — minimize gaps
11. [SOFT]      RoomUtilizationConstraint      — right-size rooms
12. [SOFT]      DayDistributionConstraint      — spread across days
13. [SOFT]      LabPriorityConstraint          — prefer specialized rooms
```

---

## 7. Objective Function Design

The objective function is a weighted sum of penalties from soft constraints, plus any components computed directly in the objective builder.

### Architecture

```python
class ObjectiveBuilder:
    """Collects penalty expressions from soft constraints and builds
    the final objective function."""

    def __init__(self):
        self._components: list[tuple[str, Any, int]] = []
        # Each entry: (name, linear_expression, weight)

    def add_component(self, name: str, expr: Any, weight: int) -> None:
        """Register a named objective component."""
        if weight > 0 and expr is not None:
            self._components.append((name, expr, weight))

    def build(self, model: Any) -> None:
        """Post the Minimize objective to the model."""
        if not self._components:
            return  # No objective; solver finds any feasible solution.

        total = sum(weight * expr for _, expr, weight in self._components)
        model.Minimize(total)

    def describe(self) -> list[dict]:
        """Return a human-readable description of the objective."""
        return [
            {"name": name, "weight": weight}
            for name, _, weight in self._components
        ]
```

### Standard Components

| Component | Source | Polarity | Typical Weight |
|-----------|--------|----------|----------------|
| `workload_range` | WorkloadBalanceConstraint | Minimize (lower range = more balanced) | 200 |
| `workload_deviation` | WorkloadBalanceConstraint | Minimize (lower deviation = more balanced) | 20 |
| `instructor_preferences` | PreferenceConstraint | Maximize (negated in penalty) | 1 |
| `schedule_compactness` | CompactnessConstraint | Minimize (fewer gaps = more compact) | 10 |
| `room_utilization` | RoomUtilizationConstraint | Minimize (less wasted capacity = better) | 5 |
| `day_distribution` | DayDistributionConstraint | Minimize (more spread = better) | 5 |

### Weight Configuration

Weights are configurable per solve run via `ObjectiveWeights`. A weight of 0 disables the component. The caller can tune the balance between competing objectives without modifying solver code.

Example: A university that cares mostly about instructor preferences and does not care about workload balance would set:

```python
ObjectiveWeights(
    workload_balance_range=0,
    workload_balance_deviation=0,
    instructor_preferences=100,
    schedule_compactness=10,
)
```

### Multi-Objective Considerations

CP-SAT supports only a single Minimize objective. True Pareto-optimal multi-objective optimization requires running the solver multiple times with different weight vectors, or using a lexicographic approach (solve for the primary objective first, then fix it and optimize the secondary, etc.).

The engine supports **lexicographic optimization** as a future extension: the `SolverParams` dataclass can be extended with a `lexicographic_priorities` field that defines objective tiers. The engine would solve iteratively, adding the previous tier's optimal value as a constraint before optimizing the next tier.

---

## 8. Solver Module Architecture

```
solver/
├── __init__.py                    # Public API: solve(SolverInput) -> SolverOutput
├── types.py                       # All input/output dataclasses and enums
├── interfaces.py                  # BaseConstraint, BaseObjectiveComponent ABCs
├── engine.py                      # Main orchestrator (pipeline controller)
├── validator.py                   # Input validation logic
├── index_builder.py               # Builds IndexSet from SolverInput
├── variable_builder.py            # Creates VariableSet from IndexSet
├── constraint_registry.py         # Registry pattern for constraint plugins
├── objective_builder.py           # Collects and combines objective components
├── solution_extractor.py          # Reads variable values, builds Assignments
├── diagnostics.py                 # Infeasibility analysis and reporting
│
├── constraints/                   # One module per constraint
│   ├── __init__.py                # Imports all constraints (triggers registration)
│   ├── instructor_no_overlap.py
│   ├── room_no_overlap.py
│   ├── instructor_max_hours.py
│   ├── instructor_availability.py
│   ├── room_compatibility.py      # Validation-only (pruning in index_builder)
│   ├── session_count.py
│   ├── session_different_days.py
│   ├── workload_balance.py
│   ├── preferences.py
│   ├── compactness.py
│   ├── day_distribution.py
│   ├── room_utilization.py
│   └── lab_priority.py
│
├── objectives/                    # Standalone objective components (if any)
│   ├── __init__.py
│   └── custom_objectives.py       # Extension point for non-constraint objectives
│
└── adapters/
    ├── __init__.py
    ├── base_adapter.py            # Abstract solver adapter interface
    └── ortools_adapter.py         # OR-Tools CP-SAT implementation
```

### Module Responsibilities

**`engine.py`** — The orchestrator. Contains a single public function `solve(input: SolverInput) -> SolverOutput` that executes the pipeline:

```python
def solve(solver_input: SolverInput) -> SolverOutput:
    # Stage 1: already done (caller built the SolverInput)

    # Stage 2: Validation
    errors = validate(solver_input)
    if any(e.severity == DiagnosticSeverity.FATAL for e in errors):
        return SolverOutput(
            status=SolverStatus.ERROR,
            diagnostics=tuple(errors),
        )

    # Stage 3: Index Building
    indices = build_indices(solver_input)
    if indices.infeasible:
        return SolverOutput(
            status=SolverStatus.INFEASIBLE,
            diagnostics=tuple(indices.infeasibility_reasons),
        )

    # Stage 4: Variable Creation
    adapter = ORToolsAdapter()
    model = adapter.create_model()
    variables = build_variables(model, indices, solver_input)

    # Stage 5: Constraint Application
    objective_builder = ObjectiveBuilder()
    for constraint_config in solver_input.constraints:
        if not constraint_config.enabled:
            continue
        constraint = get_constraint(constraint_config.constraint_type)
        result = constraint.apply(model, variables, indices, constraint_config)
        if result.penalty_expr is not None:
            objective_builder.add_component(
                constraint.name, result.penalty_expr, result.penalty_weight
            )

    # Stage 6: Objective Definition
    objective_builder.build(model)

    # Stage 7: Solving
    solve_result = adapter.solve(model, solver_input.solver_params)

    # Stage 8: Solution Extraction
    if solve_result.is_feasible:
        assignments = extract_solution(
            solve_result.solver, variables, indices, solver_input
        )
        return SolverOutput(
            status=map_status(solve_result.status),
            assignments=tuple(assignments),
            statistics=build_statistics(solve_result, variables),
            diagnostics=tuple(errors),  # include validation warnings
        )
    else:
        diags = list(errors)
        diags.extend(diagnose_infeasibility(model, variables, indices))
        return SolverOutput(
            status=map_status(solve_result.status),
            diagnostics=tuple(diags),
            statistics=build_statistics(solve_result, variables),
        )
```

**`validator.py`** — Checks structural invariants of the input:

```python
def validate(solver_input: SolverInput) -> list[Diagnostic]:
    errors = []

    # Check that every group has at least one eligible instructor
    for g in solver_input.groups:
        if not g.eligible_instructor_ids:
            errors.append(Diagnostic(
                severity=DiagnosticSeverity.FATAL,
                code="NO_ELIGIBLE_INSTRUCTOR",
                message=f"Group '{g.id}' has no eligible instructors.",
                group_id=g.id,
            ))

    # Check that session blocks fit within a day
    slots_per_day = compute_slots_per_day(solver_input.time_slots)
    for g in solver_input.groups:
        for k, block in enumerate(g.session_pattern.blocks):
            if block.duration_slots > slots_per_day:
                errors.append(Diagnostic(
                    severity=DiagnosticSeverity.FATAL,
                    code="BLOCK_TOO_LONG",
                    message=(
                        f"Group '{g.id}' block {k} requires "
                        f"{block.duration_slots} slots but day has "
                        f"only {slots_per_day} slots."
                    ),
                    group_id=g.id,
                ))

    # Check that eligible instructor IDs exist
    instructor_ids = {i.id for i in solver_input.instructors}
    for g in solver_input.groups:
        missing = g.eligible_instructor_ids - instructor_ids
        if missing:
            errors.append(Diagnostic(
                severity=DiagnosticSeverity.FATAL,
                code="UNKNOWN_INSTRUCTOR",
                message=(
                    f"Group '{g.id}' references unknown instructors: "
                    f"{missing}"
                ),
                group_id=g.id,
            ))

    # Validate constraint configs
    for cc in solver_input.constraints:
        if cc.enabled:
            try:
                constraint = get_constraint(cc.constraint_type)
                config_errors = constraint.validate_config(cc)
                for msg in config_errors:
                    errors.append(Diagnostic(
                        severity=DiagnosticSeverity.FATAL,
                        code="INVALID_CONSTRAINT_CONFIG",
                        message=msg,
                        constraint=cc.constraint_type,
                    ))
            except KeyError:
                errors.append(Diagnostic(
                    severity=DiagnosticSeverity.FATAL,
                    code="UNKNOWN_CONSTRAINT",
                    message=f"Unknown constraint type: '{cc.constraint_type}'",
                    constraint=cc.constraint_type,
                ))

    return errors
```

**`index_builder.py`** — Transforms lists into fast-lookup dictionaries, performs room/instructor pruning:

```python
@dataclass
class IndexSet:
    """Pre-computed lookup structures for constraint posting."""

    # Mapping from string IDs to internal integer indices
    group_id_to_idx: dict[str, int]
    instructor_id_to_idx: dict[str, int]
    room_id_to_idx: dict[str, int]

    # Reverse mappings (index to string ID)
    group_idx_to_id: dict[int, str]
    instructor_idx_to_id: dict[int, str]
    room_idx_to_id: dict[int, str]

    # Eligibility sets (using internal integer indices)
    eligible_instructors: dict[int, set[int]]  # group_idx -> set of instructor_idx
    eligible_rooms: dict[int, set[int]]        # group_idx -> set of room_idx
    groups_by_instructor: dict[int, set[int]]  # instructor_idx -> set of group_idx

    # Time structure
    num_days: int
    slots_per_day: int
    total_slots: int
    slot_to_day: dict[int, int]
    slot_to_period: dict[int, int]
    day_period_to_slot: dict[tuple[int, int], int]
    day_slots: dict[int, list[int]]  # day -> sorted list of slot indices

    # Availability (using internal integer indices)
    instructor_available_slots: dict[int, set[int]]
    room_available_slots: dict[int, set[int]]

    # Session patterns (using internal integer indices)
    group_session_pattern: dict[int, SessionPattern]
    group_enrollment: dict[int, int]
    group_subject: dict[int, str]

    # Pruning results
    infeasible: bool = False
    infeasibility_reasons: list[Diagnostic] = field(default_factory=list)
    variables_pruned: int = 0
```

**`variable_builder.py`** — Creates all CP-SAT variables:

```python
@dataclass
class VariableSet:
    """All decision variables in the CP model."""

    # Layer 1: Assignment
    y: dict[tuple[int, int], Any]           # (instructor_idx, group_idx) -> BoolVar

    # Layer 2: Placement
    start: dict[tuple[int, int, int, int, int], Any]
    # (group_idx, block_idx, day, period, room_idx) -> BoolVar

    # Layer 3: Coverage
    x: dict[tuple[int, int, int], Any]      # (group_idx, slot_idx, room_idx) -> BoolVar

    # Auxiliary
    day_active: dict[tuple[int, int, int], Any]
    # (group_idx, block_idx, day) -> BoolVar: is block k of group g on day d?

    occ: dict[tuple[int, int, int], Any]
    # (instructor_idx, group_idx, slot_idx) -> BoolVar:
    # is instructor i teaching group g at slot t?

    load: dict[int, Any]                    # instructor_idx -> IntVar (total weekly load)
    day_load: dict[tuple[int, int], Any]    # (instructor_idx, day) -> IntVar (daily load)
```

**`solution_extractor.py`** — Reads solver values and constructs Assignment objects:

```python
def extract_solution(
    solver: Any,
    variables: VariableSet,
    indices: IndexSet,
    solver_input: SolverInput,
) -> list[Assignment]:
    assignments = []

    for g_idx, group in enumerate(solver_input.groups):
        # Find the assigned instructor
        assigned_instructor_idx = None
        for i_idx in indices.eligible_instructors[g_idx]:
            if solver.Value(variables.y[(i_idx, g_idx)]) == 1:
                assigned_instructor_idx = i_idx
                break

        if assigned_instructor_idx is None:
            continue  # Should not happen if status is FEASIBLE

        # Find each session's placement
        sessions = []
        for k, block in enumerate(group.session_pattern.blocks):
            for d in range(indices.num_days):
                for h in range(indices.slots_per_day - block.duration_slots + 1):
                    for r_idx in indices.eligible_rooms[g_idx]:
                        key = (g_idx, k, d, h, r_idx)
                        if key in variables.start and solver.Value(variables.start[key]) == 1:
                            slot_indices = tuple(
                                indices.day_period_to_slot[(d, h + offset)]
                                for offset in range(block.duration_slots)
                            )
                            sessions.append(SessionAssignment(
                                block_index=k,
                                room_id=indices.room_idx_to_id[r_idx],
                                slot_indices=slot_indices,
                            ))

        assignments.append(Assignment(
            group_id=group.id,
            instructor_id=indices.instructor_idx_to_id[assigned_instructor_idx],
            sessions=tuple(sessions),
        ))

    return assignments
```

**`diagnostics.py`** — Analyzes infeasible models:

When the solver returns INFEASIBLE, the diagnostics module attempts to identify the minimal set of conflicting constraints. Strategies:

1. **Relaxation probing.** Disable soft constraints one at a time and re-solve to see if the model becomes feasible. This identifies overly aggressive soft constraints that were promoted to hard.

2. **Group removal probing.** Remove groups one at a time and check feasibility. The first group whose removal makes the model feasible is likely involved in the conflict.

3. **Sufficient statistics.** Without re-solving, compute:
   - Total required room-slots vs. total available room-slots per room type.
   - Total required instructor-hours vs. total available instructor-hours per instructor.
   - Groups with exactly one eligible instructor (bottlenecks).
   - Groups with exactly one eligible room (bottlenecks).

---

## 9. How to Add a New Constraint

This section is a step-by-step guide for adding a new constraint without modifying any existing solver code.

### Example: MaxConsecutiveHoursConstraint

**Requirement:** No instructor may teach more than 4 consecutive hours without a break.

**Step 1.** Create a new file: `solver/constraints/max_consecutive_hours.py`

```python
"""Constraint: limits consecutive teaching hours for instructors.

Ensures that no instructor is scheduled for more than N consecutive
time slots on any day without at least one free slot break.
"""
from solver.interfaces import BaseConstraint, ConstraintType, ConstraintResult
from solver.constraint_registry import register_constraint


@register_constraint
class MaxConsecutiveHoursConstraint(BaseConstraint):

    @property
    def name(self) -> str:
        return "max_consecutive_hours"

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.HARD

    def validate_config(self, config) -> list[str]:
        errors = []
        max_consec = config.parameters.get("max_consecutive", 4)
        if not isinstance(max_consec, int) or max_consec < 1:
            errors.append(
                "Parameter 'max_consecutive' must be a positive integer."
            )
        return errors

    def apply(self, model, variables, indices, config) -> ConstraintResult:
        max_consec = config.parameters.get("max_consecutive", 4)
        clauses = 0

        for i_idx in range(len(indices.instructor_idx_to_id)):
            for d in range(indices.num_days):
                day_slot_list = indices.day_slots[d]
                num_periods = len(day_slot_list)

                # Sliding window: for each window of (max_consec + 1)
                # consecutive periods, at least one must be free.
                window_size = max_consec + 1
                for start_period in range(num_periods - window_size + 1):
                    window_slots = day_slot_list[start_period:start_period + window_size]

                    # Collect occ variables for this instructor in this window
                    occ_vars = []
                    for t in window_slots:
                        for g_idx in indices.groups_by_instructor.get(i_idx, set()):
                            key = (i_idx, g_idx, t)
                            if key in variables.occ:
                                occ_vars.append(variables.occ[key])

                    # At most max_consec out of (max_consec + 1) slots occupied
                    if occ_vars:
                        model.Add(sum(occ_vars) <= max_consec)
                        clauses += 1

        return ConstraintResult(clauses_added=clauses)
```

**Step 2.** Import the new module in `solver/constraints/__init__.py`:

```python
# Add this line:
from solver.constraints.max_consecutive_hours import MaxConsecutiveHoursConstraint
```

This triggers the `@register_constraint` decorator, making `"max_consecutive_hours"` available in the registry.

**Step 3.** Enable the constraint in the solver input:

```python
SolverInput(
    # ... groups, instructors, rooms, time_slots ...
    constraints=(
        # ... existing constraints ...
        ConstraintConfig(
            constraint_type="max_consecutive_hours",
            enabled=True,
            category=ConstraintCategory.HARD,
            parameters={"max_consecutive": 4},
        ),
    ),
)
```

**That is it.** No changes to `engine.py`, `variable_builder.py`, `objective_builder.py`, or any other existing module. The constraint system is fully open for extension and closed for modification.

---

## 10. How to Add a New Objective Component

### Example: Minimize Room Changes

**Requirement:** Penalize groups that use different rooms for different sessions. Prefer keeping a group in the same room across all its weekly meetings.

**Step 1.** Create `solver/constraints/room_consistency.py`:

```python
"""Soft constraint: penalizes groups using different rooms across sessions."""
from solver.interfaces import BaseConstraint, ConstraintType, ConstraintResult
from solver.constraint_registry import register_constraint


@register_constraint
class RoomConsistencyConstraint(BaseConstraint):

    @property
    def name(self) -> str:
        return "room_consistency"

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.SOFT

    def validate_config(self, config) -> list[str]:
        return []  # No parameters

    def apply(self, model, variables, indices, config) -> ConstraintResult:
        clauses = 0
        penalty_vars = []

        for g_idx, group_id in indices.group_idx_to_id.items():
            pattern = indices.group_session_pattern[g_idx]
            num_blocks = len(pattern.blocks)

            if num_blocks <= 1:
                continue  # Only one session, no room change possible

            eligible_rooms = sorted(indices.eligible_rooms[g_idx])

            if len(eligible_rooms) <= 1:
                continue  # Only one room option, no choice to make

            # For each room, create a variable: is this room used by ANY block?
            room_used = {}
            for r_idx in eligible_rooms:
                rv = model.NewBoolVar(f"room_used_g{g_idx}_r{r_idx}")
                # room_used[r] = 1 iff any start variable uses room r
                room_starts = []
                for k in range(num_blocks):
                    for d in range(indices.num_days):
                        spd = indices.slots_per_day
                        dur = pattern.blocks[k].duration_slots
                        for h in range(spd - dur + 1):
                            key = (g_idx, k, d, h, r_idx)
                            if key in variables.start:
                                room_starts.append(variables.start[key])
                if room_starts:
                    model.AddMaxEquality(rv, room_starts)
                else:
                    model.Add(rv == 0)
                room_used[r_idx] = rv
                clauses += 1

            # Count distinct rooms used (minus 1 = number of changes)
            num_rooms_used = model.NewIntVar(
                1, num_blocks, f"rooms_used_g{g_idx}"
            )
            model.Add(num_rooms_used == sum(room_used.values()))
            clauses += 1

            # Penalty = rooms_used - 1 (0 if all in same room)
            change_penalty = model.NewIntVar(
                0, num_blocks - 1, f"room_change_g{g_idx}"
            )
            model.Add(change_penalty == num_rooms_used - 1)
            penalty_vars.append(change_penalty)
            clauses += 1

        if penalty_vars:
            total_penalty = sum(penalty_vars)
            return ConstraintResult(
                clauses_added=clauses,
                penalty_expr=total_penalty,
                penalty_weight=config.weight,
            )
        return ConstraintResult(clauses_added=clauses)
```

**Step 2.** Import in `solver/constraints/__init__.py` and add the `ConstraintConfig` to the solver input.

The penalty expression returned in `ConstraintResult` is automatically picked up by `ObjectiveBuilder` in `engine.py`. No changes to the objective builder are needed.

---

## 11. How to Replace OR-Tools

The solver engine sits behind an adapter interface. Replacing OR-Tools means implementing a new adapter.

### Adapter Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SolveResult:
    """Result from the underlying solver engine."""
    status: int              # Engine-specific status code
    is_feasible: bool
    is_optimal: bool
    solver: Any              # Engine-specific solver object for reading values
    elapsed_seconds: float
    num_variables: int
    num_constraints: int
    objective_value: float | None
    best_bound: float | None
    branches: int
    conflicts: int


class SolverAdapter(ABC):
    """Abstract adapter for a constraint programming solver engine.

    All interaction with the underlying solver goes through this interface.
    The rest of the solver code uses abstract types (model, variables) that
    the adapter defines.
    """

    @abstractmethod
    def create_model(self) -> Any:
        """Create a new, empty model."""
        ...

    @abstractmethod
    def new_bool_var(self, model: Any, name: str) -> Any:
        """Create a boolean decision variable."""
        ...

    @abstractmethod
    def new_int_var(self, model: Any, lb: int, ub: int, name: str) -> Any:
        """Create an integer decision variable with bounds."""
        ...

    @abstractmethod
    def add_equality(self, model: Any, expr: Any, value: int) -> None:
        """Add constraint: expr == value."""
        ...

    @abstractmethod
    def add_at_most(self, model: Any, expr: Any, value: int) -> None:
        """Add constraint: expr <= value."""
        ...

    @abstractmethod
    def add_at_least(self, model: Any, expr: Any, value: int) -> None:
        """Add constraint: expr >= value."""
        ...

    @abstractmethod
    def minimize(self, model: Any, expr: Any) -> None:
        """Set the objective to minimize the given expression."""
        ...

    @abstractmethod
    def solve(self, model: Any, params: SolverParams) -> SolveResult:
        """Solve the model and return the result."""
        ...

    @abstractmethod
    def value(self, solver: Any, var: Any) -> int:
        """Read the value of a variable in a solved model."""
        ...
```

### OR-Tools Implementation

```python
from ortools.sat.python import cp_model


class ORToolsAdapter(SolverAdapter):

    def create_model(self):
        return cp_model.CpModel()

    def new_bool_var(self, model, name):
        return model.NewBoolVar(name)

    def new_int_var(self, model, lb, ub, name):
        return model.NewIntVar(lb, ub, name)

    def add_equality(self, model, expr, value):
        model.Add(expr == value)

    def add_at_most(self, model, expr, value):
        model.Add(expr <= value)

    def add_at_least(self, model, expr, value):
        model.Add(expr >= value)

    def minimize(self, model, expr):
        model.Minimize(expr)

    def solve(self, model, params):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = params.max_time_seconds
        if params.num_workers > 0:
            solver.parameters.num_search_workers = params.num_workers
        solver.parameters.random_seed = params.random_seed

        if params.stop_after_first_feasible:
            solver.parameters.stop_after_first_solution = True

        if params.log_search_progress:
            solver.parameters.log_search_progress = True

        import time
        t0 = time.time()
        status = solver.Solve(model)
        elapsed = time.time() - t0

        return SolveResult(
            status=status,
            is_feasible=status in (cp_model.OPTIMAL, cp_model.FEASIBLE),
            is_optimal=status == cp_model.OPTIMAL,
            solver=solver,
            elapsed_seconds=elapsed,
            num_variables=len(model.Proto().variables),
            num_constraints=len(model.Proto().constraints),
            objective_value=(
                solver.ObjectiveValue() if status in
                (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
            ),
            best_bound=(
                solver.BestObjectiveBound() if status in
                (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
            ),
            branches=solver.NumBranches(),
            conflicts=solver.NumConflicts(),
        )

    def value(self, solver, var):
        return solver.Value(var)
```

### Gurobi Implementation (Sketch)

```python
import gurobipy as gp


class GurobiAdapter(SolverAdapter):

    def create_model(self):
        return gp.Model()

    def new_bool_var(self, model, name):
        return model.addVar(vtype=gp.GRB.BINARY, name=name)

    def new_int_var(self, model, lb, ub, name):
        return model.addVar(lb=lb, ub=ub, vtype=gp.GRB.INTEGER, name=name)

    def add_equality(self, model, expr, value):
        model.addConstr(expr == value)

    def add_at_most(self, model, expr, value):
        model.addConstr(expr <= value)

    # ... etc.
```

### Practical Notes

The adapter interface above is simplified. A production adapter needs to handle:

- **Expression building.** OR-Tools uses `sum()` on BoolVar lists naturally. Gurobi needs `gp.quicksum()` or `LinExpr`. The adapter should provide a `sum_vars()` method.
- **Implied constraints.** OR-Tools has `AddMaxEquality`, `AddMinEquality`, `AddDivisionEquality`, and `AddAbsEquality`. These must either be part of the adapter interface or decomposed into linear constraints by the constraint modules.
- **Callback/solution listener.** OR-Tools supports `CpSolverSolutionCallback`. Other solvers have their own mechanisms. The adapter should provide a `set_solution_callback()` method.

In practice, constraint modules will likely need to call OR-Tools-specific methods directly for advanced modeling (e.g., `AddAllDifferent`, interval variables for no-overlap). The adapter pattern is most useful for isolating the solve-and-extract cycle. Constraint modules may need to be partially rewritten when changing engines. The adapter ensures that at minimum, the engine orchestration, input/output types, and solution extraction remain unchanged.

---

## 12. Session Pattern Handling

### The Problem

The current solver hardcodes the relationship between credits and session structure:

```python
# Current (hardcoded):
if cr == 4:    # 2 sessions of 2 blocks each
if cr == 3:    # either 1 session of 3 blocks OR 1 of 2 + 1 of 1
if cr == 2:    # 1 session of 2 blocks
if cr == 1:    # 1 session of 1 block
```

This is inflexible. A 3-credit course might need:
- One 3-hour lab session (chemistry, where you cannot split the experiment)
- Three 1-hour lectures (conversational language courses)
- One 2-hour lecture + one 1-hour tutorial
- Two 1.5-hour sessions (US-style 75-minute classes on a 50-minute grid)

### The Solution

Session patterns are **caller-defined**. The solver does not compute patterns from credit counts. The caller creates the exact `SessionPattern` and passes it in `GroupInput`.

### How the Solver Handles Session Patterns

**Step 1: Variable creation.** For each group g, the variable builder iterates over `g.session_pattern.blocks`:

```python
for g_idx, group in enumerate(groups):
    pattern = group.session_pattern
    for k, block in enumerate(pattern.blocks):
        duration = block.duration_slots
        for d in range(num_days):
            # Valid start periods: block must fit within the day
            for h in range(slots_per_day - duration + 1):
                for r_idx in eligible_rooms[g_idx]:
                    # Only create if room is available for ALL slots in the block
                    block_slots = [day_period_to_slot[(d, h + off)]
                                   for off in range(duration)]
                    if all(s in room_available_slots.get(r_idx, all_slots)
                           for s in block_slots):
                        key = (g_idx, k, d, h, r_idx)
                        start[key] = model.NewBoolVar(f"start_{key}")
```

**Step 2: Exactly-one constraint.** For each block k of each group g, exactly one start variable is active:

```python
for g_idx, group in enumerate(groups):
    for k in range(len(group.session_pattern.blocks)):
        relevant_starts = [
            start[(g_idx, k, d, h, r)]
            for (gi, ki, d, h, r) in start
            if gi == g_idx and ki == k
        ]
        model.Add(sum(relevant_starts) == 1)
```

**Step 3: Different-day constraint.** If `allow_same_day` is False, blocks of the same group must land on different days:

```python
for g_idx, group in enumerate(groups):
    if group.session_pattern.allow_same_day:
        continue
    num_blocks = len(group.session_pattern.blocks)
    for k in range(num_blocks):
        for d in range(num_days):
            # day_active[g, k, d] = 1 iff block k is on day d
            day_starts = [
                start[(g_idx, k, d, h, r)]
                for h in range(...)
                for r in eligible_rooms[g_idx]
                if (g_idx, k, d, h, r) in start
            ]
            day_active[(g_idx, k, d)] = model.NewBoolVar(...)
            model.Add(day_active[(g_idx, k, d)] == sum(day_starts))

    # For each pair of blocks, they cannot share a day
    for k1 in range(num_blocks):
        for k2 in range(k1 + 1, num_blocks):
            for d in range(num_days):
                model.Add(
                    day_active[(g_idx, k1, d)]
                    + day_active[(g_idx, k2, d)]
                    <= 1
                )
```

**Step 4: Coverage expansion.** Each active start variable "covers" multiple consecutive time slots:

```python
for (g_idx, k, d, h, r_idx), st_var in start.items():
    duration = groups[g_idx].session_pattern.blocks[k].duration_slots
    for offset in range(duration):
        slot = day_period_to_slot[(d, h + offset)]
        coverage_sources[(g_idx, slot, r_idx)].append(st_var)

for key, sources in coverage_sources.items():
    g_idx, slot, r_idx = key
    x[key] = model.NewBoolVar(f"x_{key}")
    model.Add(x[key] == sum(sources))
```

### Handling the Current 3-Credit Flexibility

The current solver allows 3-credit courses to use EITHER a 3-block session OR a 2+1 split, with a z variable selecting between them. In the new design, this flexibility is handled at the application layer:

**Option A: The application layer chooses.** Before calling the solver, the application decides that 3-credit courses use `SessionPattern(blocks=[SessionBlock(2), SessionBlock(1)])`. The solver does not see the alternative.

**Option B: Run the solver twice.** The application runs the solver once with all 3-credit courses using the 3-block pattern, and once with the 2+1 pattern, and picks the better solution.

**Option C: Encode flexibility with optional blocks.** Extend `SessionPattern` with an `alternatives` field:

```python
@dataclass(frozen=True)
class SessionPattern:
    alternatives: tuple[tuple[SessionBlock, ...], ...]
    # The solver picks one alternative per group.
```

This creates a "variant selection" variable per group and duplicates the start variables for each alternative. This is algebraically equivalent to the current z-variable approach but generalized. If the group has two alternatives, the solver creates start variables for both and a binary selector that activates exactly one set. This is supported but adds complexity; use it only when the flexibility genuinely affects solution quality.

---

## 13. Performance Considerations

### Variable Reduction (Pruning)

The most impactful performance optimization is reducing the number of variables. The current solver does some pruning (capacity-based room filtering) but misses several opportunities.

**1. Instructor availability pruning.** Do not create `start` variables for time slots where no eligible instructor is available. If all eligible instructors for group g are unavailable on day d, skip all start variables for (g, *, d, *, *).

```python
# For each group g, compute available days:
available_days = set()
for i_idx in eligible_instructors[g_idx]:
    for slot in instructor_available_slots[i_idx]:
        available_days.add(slot_to_day[slot])

# Only create start variables for days in available_days
```

**2. Room availability pruning.** Do not create `start` variables for time slots where the room is unavailable:

```python
for r_idx in eligible_rooms[g_idx]:
    for h in range(slots_per_day - duration + 1):
        block_slots = [day_period_to_slot[(d, h + off)] for off in range(duration)]
        if not all(s in room_available_slots[r_idx] for s in block_slots):
            continue  # Skip this (d, h, r) combination
```

**3. Coverage variable pruning.** Only create `x[g, t, r]` variables for (g, t, r) triples that appear in at least one start variable's coverage footprint. The current solver already does this implicitly.

**4. Occupation variable pruning.** Only create `occ[i, g, t]` for (i, g, t) triples where i is eligible for g AND t is in i's available slots AND g could be active at t.

### Symmetry Breaking

When multiple groups of the same subject are identical (same session pattern, same enrollment, same eligible instructors, same eligible rooms), the solver wastes time exploring permutations that differ only in which group gets which assignment. Break this symmetry:

```python
# If groups g1 and g2 are identical and g1.id < g2.id:
# Add: y[min_eligible_instructor, g1] >= y[min_eligible_instructor, g2]
# Or use a lex-ordering constraint on the start variable vectors.
```

CP-SAT's built-in symmetry detection handles some cases, but explicit symmetry breaking for known structure is much more effective.

### Search Strategy Hints

CP-SAT supports search strategy hints via `model.AddDecisionStrategy()`. Effective strategies for scheduling:

```python
# Prioritize assignment variables (y) over placement variables (start).
# Within assignment, prioritize groups with fewer eligible instructors
# (most constrained first).

assignment_vars = sorted(
    variables.y.values(),
    key=lambda v: len(eligible_instructors[group_of(v)])
)
model.AddDecisionStrategy(
    assignment_vars,
    cp_model.CHOOSE_MIN_DOMAIN_SIZE,
    cp_model.SELECT_MIN_VALUE,
)
```

### Parallelization

CP-SAT uses multiple search workers internally (`num_search_workers`). The recommended setting is `min(available_cores, 8)`. Beyond 8 workers, the marginal benefit is small for typical scheduling instances.

For very large instances (>1000 groups), consider decomposing the problem:

1. **Department-level decomposition.** Solve each department independently (instructor no-overlap is intra-department only if instructors do not cross departments). Then solve the room-assignment problem globally with fixed instructor schedules.

2. **Time-based decomposition.** Solve morning slots first, then afternoon, then evening. Carry forward instructor commitments as availability restrictions.

### When to Use FEASIBLE vs. OPTIMAL

For production use with time-limited solves (30-300 seconds), the solver should be configured to return the best feasible solution found within the time limit, not wait for a proof of optimality. CP-SAT naturally does this: it returns FEASIBLE if it found a solution but could not prove optimality before the time limit.

Set `stop_after_first_feasible=True` for:
- Initial schedule previews (user wants quick feedback)
- Validation runs (checking whether the input is feasible at all)
- Test runs during development

Set `stop_after_first_feasible=False` for:
- Final production schedule generation (let the solver optimize)
- Research experiments (measuring solution quality)

### Expected Scale

| Instance Size | Groups | Variables (est.) | Solve Time (est.) |
|---------------|--------|------------------|-------------------|
| Small (1 department) | 20-50 | 10K-50K | 5-30 seconds |
| Medium (full program) | 100-200 | 100K-500K | 30-300 seconds |
| Large (multi-program) | 500-1000 | 1M-5M | 300-3600 seconds |
| Very Large | >1000 | >5M | Decomposition needed |

---

## 14. What to Preserve from Current Solver

The current `model_builder.py` is a prototype that mixes good mathematical modeling with bad software engineering. The following mathematical concepts must be carried forward into the new design.

### 1. Three-Layer Variable Structure

The current solver's use of `y`, `start`, and `x` variables is sound. The assignment layer (`y`) separates the "who teaches what" decision from the "when and where" decision. The start layer places session blocks in time. The coverage layer (`x`) expands blocks into individual time-slot occupancy for constraint posting. This three-layer design is preserved unchanged in the new architecture.

**Current:** `y[p, c, gi]`, `start[L, tag, p, c, gi, d, h, s]`, `x[p, c, gi, b, s]`
**New:** `y[i, g]`, `start[g, k, d, h, r]`, `x[g, t, r]` (instructor dimension removed from start and coverage)

### 2. Start-to-Coverage Channeling

The current solver's coverage expansion (lines 296-304 of `model_builder.py`) correctly expands each start variable's footprint into individual time-slot coverage variables:

```python
# Current code (preserved logic):
for (L, tag, p, c, gi, d, h0, s), st in start.items():
    for off in range(L):
        b = day_hour_to_b(d, h0 + off)
        cover[(p, c, gi, b, s)].append(st)

for key, lst in cover.items():
    x[key] = model.NewBoolVar(...)
    model.Add(sum(lst) == x[key])
```

This channeling is correct and efficient. The new design preserves the same pattern with updated variable keys.

### 3. Exactly-One Assignment Constraint

```python
# Current (line 213):
model.Add(sum(y[(p, c, gi)] for p in candidatos_por_curso[c]) == 1)
```

Correct: exactly one instructor per group. Preserved.

### 4. Exactly-One Start Per Block

```python
# Current (lines 250-271):
model.Add(sum_starts(2, c, gi, 1) == 1)  # etc.
```

Correct: exactly one placement per session block. Preserved.

### 5. Start-Assignment Linkage

The current solver links start variables to assignment variables (lines 273-294): the total number of active starts for (professor, course, group) must equal the expected number of blocks times the assignment variable. This ensures that only the assigned professor's start variables can be active.

```python
# Current (line 284):
model.Add(ts == 2 * ypcg)  # 4-credit: 2 blocks, so 2 starts
```

The new design achieves this differently (since start variables no longer include the instructor dimension), but the invariant is the same: a group's sessions are placed if and only if the group is assigned to an instructor.

### 6. Instructor No-Overlap via Coverage

```python
# Current (lines 319-323):
for p in range(NUM_PROFES):
    for b in range(NUM_BLOQUES):
        lst = x_by_prof_block.get((p, b), [])
        if lst:
            model.Add(sum(lst) <= 1)
```

Correct. Preserved with the auxiliary `occ` variable formulation.

### 7. Room No-Overlap via Coverage

```python
# Current (lines 332-336):
for s in range(NUM_SALONES):
    for b in range(NUM_BLOQUES):
        lst = x_by_room_block.get((s, b), [])
        if lst:
            model.Add(sum(lst) <= 1)
```

Correct. Preserved directly using `x[g, t, r]`.

### 8. Daily and Weekly Hour Limits

```python
# Current (lines 338-346):
model.Add(sum(lst) <= MAX_CLASES_PROFE_DIA)
model.Add(sum(lst) <= MAX_CLASES_PROFE_SEMANA)
```

Correct. Preserved in `InstructorMaxHoursConstraint`.

### 9. Workload Balance Objective

```python
# Current (lines 348-371):
# max_carga - min_carga range
# Absolute deviation from target
# Preference score (negated)
model.Minimize(200 * (max_carga_p - min_carga_p) + 20 * sum(dev) - 1 * pref_expr)
```

This three-component objective is well-designed. The range term prevents extreme imbalance. The deviation term pushes toward uniform distribution. The preference term rewards good instructor-subject matches.

The new design preserves all three components with configurable weights.

### 10. Different-Day Constraint for Multi-Block Sessions

```python
# Current (lines 253-256):
for d in range(NUM_DIAS):
    model.Add(day_sel[(2, 1, c, gi, d)] + day_sel[(2, 2, c, gi, d)] <= 1)
```

Correct: two blocks of the same group cannot share a day. Preserved in `SessionDifferentDaysConstraint`.

### 11. Room-Capacity Pruning

```python
# Current (lines 132-168):
if estudiantes_grupo[(c, gi)] > capacidad_salon[s]:
    podas += 1
    continue
```

Correct: eliminate rooms too small for the group during index building, not as CP constraints. This is much more efficient than posting thousands of incompatibility constraints. Preserved in `index_builder.py`.

### What is NOT Preserved

| Current Feature | Reason for Removal |
|---|---|
| 48 hardcoded subjects | Application layer responsibility |
| `random.sample` for candidate professors | Application layer provides eligible instructors |
| `random.randint` for preferences | Application layer provides real preference data |
| `AREAS_DISCIPLINARES` set | Domain knowledge does not belong in the solver |
| `"infraestructura"` string matching | Application layer business rule |
| `p_infra = 0` / `s_infra = salones_pc[0]` | Fixed assignments are application decisions, not solver logic |
| `["Lunes", "Martes", ...]` day names | Solver uses integer indices; the application maps to names |
| `if cr == 4: ... elif cr == 3:` credit mapping | Session patterns are caller-defined |
| Two room types (`"comun"`, `"pc"`) | Room types are arbitrary strings from the input |
| `z` variable for 3-credit flexibility | Generalized via `SessionPattern.alternatives` (optional) |
| `random.seed(cfg["seed"])` in data builder | No randomness in the solver |

---

## Appendix A: Complete Variable Index

For reference, here is the complete set of variables created by the solver for a given instance:

| Variable | Key | Type | Domain | Count |
|----------|-----|------|--------|-------|
| `y` | `(i, g)` | Bool | {0, 1} | Sum over groups of eligible instructors per group |
| `start` | `(g, k, d, h, r)` | Bool | {0, 1} | Sum over groups of (blocks * days * valid_periods * eligible_rooms) |
| `x` | `(g, t, r)` | Bool | {0, 1} | Sum over groups of (covered_slots * eligible_rooms) |
| `day_active` | `(g, k, d)` | Bool | {0, 1} | groups * max_blocks * days |
| `occ` | `(i, g, t)` | Bool | {0, 1} | Sum over (i,g) eligible pairs of available_slots |
| `load` | `(i)` | Int | [0, total_slots] | num_instructors |
| `day_load` | `(i, d)` | Int | [0, slots_per_day] | num_instructors * num_days |
| `max_load` | - | Int | [0, total_slots] | 1 |
| `min_load` | - | Int | [0, total_slots] | 1 |
| `target` | - | Int | [0, total_slots] | 1 |
| `dev` | `(i)` | Int | [0, total_slots] | num_instructors |

## Appendix B: Constraint Dependency Graph

Constraints depend on specific variable layers:

```
y (assignment)
├── InstructorMaxHoursConstraint (weekly load uses y * constant)
├── PreferenceConstraint (preference score uses y * constant)
├── WorkloadBalanceConstraint (load computation uses y * constant)
└── occ (auxiliary, depends on y AND x)
    ├── InstructorNoOverlapConstraint
    ├── InstructorAvailabilityConstraint
    ├── CompactnessConstraint
    └── MaxConsecutiveHoursConstraint (example)

start (placement)
├── SessionCountConstraint (exactly one start per block)
├── SessionDifferentDaysConstraint (day_active depends on start)
└── x (coverage, derived from start)
    ├── RoomNoOverlapConstraint
    ├── RoomUtilizationConstraint
    ├── LabPriorityConstraint
    └── RoomConsistencyConstraint (example)
```

## Appendix C: End-to-End Example

Below is a minimal but complete example showing how the application layer constructs a `SolverInput` and receives a `SolverOutput`.

```python
from solver.types import (
    SolverInput, GroupInput, InstructorInput, RoomInput, TimeSlotInput,
    SessionPattern, SessionBlock, ConstraintConfig, ConstraintCategory,
    ObjectiveWeights, SolverParams,
)
from solver.engine import solve


# --- Build time slots: 5 days, 8 periods per day ---
time_slots = []
idx = 0
day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
for d in range(5):
    for p in range(8):
        start_hour = 7 + p  # 07:00 - 14:00
        time_slots.append(TimeSlotInput(
            index=idx,
            day=d,
            period=p,
            start_time=f"{start_hour:02d}:00",
            end_time=f"{start_hour + 1:02d}:00",
            label=f"{day_names[d]} P{p + 1}",
        ))
        idx += 1


# --- Build rooms ---
rooms = [
    RoomInput(id="R101", capacity=40, room_type="standard"),
    RoomInput(id="R102", capacity=35, room_type="standard"),
    RoomInput(id="LAB1", capacity=30, room_type="computer_lab"),
    RoomInput(id="LAB2", capacity=25, room_type="computer_lab"),
]


# --- Build instructors ---
all_slot_indices = frozenset(range(40))  # All 40 slots available
instructors = [
    InstructorInput(
        id="PROF-001",
        max_hours_per_week=20,
        max_hours_per_day=6,
        available_slot_indices=all_slot_indices,
        preferences={"CS101-G1": 8, "CS101-G2": 8, "CS201-G1": 5},
    ),
    InstructorInput(
        id="PROF-002",
        max_hours_per_week=16,
        max_hours_per_day=6,
        available_slot_indices=all_slot_indices,
        preferences={"CS201-G1": 9, "MATH101-G1": 6},
    ),
    InstructorInput(
        id="PROF-003",
        max_hours_per_week=20,
        max_hours_per_day=6,
        available_slot_indices=all_slot_indices,
        preferences={"MATH101-G1": 8, "CS101-G1": 4},
    ),
]


# --- Build groups ---
groups = [
    GroupInput(
        id="CS101-G1",
        subject_id="CS101",
        session_pattern=SessionPattern(
            blocks=(SessionBlock(2), SessionBlock(2)),  # 4 credits: 2x2h
        ),
        required_room_type="computer_lab",
        enrollment=28,
        eligible_instructor_ids=frozenset({"PROF-001", "PROF-003"}),
    ),
    GroupInput(
        id="CS101-G2",
        subject_id="CS101",
        session_pattern=SessionPattern(
            blocks=(SessionBlock(2), SessionBlock(2)),
        ),
        required_room_type="computer_lab",
        enrollment=25,
        eligible_instructor_ids=frozenset({"PROF-001"}),
    ),
    GroupInput(
        id="CS201-G1",
        subject_id="CS201",
        session_pattern=SessionPattern(
            blocks=(SessionBlock(2), SessionBlock(1)),  # 3 credits: 2h + 1h
        ),
        required_room_type="computer_lab",
        enrollment=22,
        eligible_instructor_ids=frozenset({"PROF-001", "PROF-002"}),
    ),
    GroupInput(
        id="MATH101-G1",
        subject_id="MATH101",
        session_pattern=SessionPattern(
            blocks=(SessionBlock(3),),  # 3 credits: 1x3h
        ),
        required_room_type="standard",
        enrollment=35,
        eligible_instructor_ids=frozenset({"PROF-002", "PROF-003"}),
    ),
]


# --- Build constraints ---
constraints = (
    ConstraintConfig(constraint_type="session_count", category=ConstraintCategory.HARD),
    ConstraintConfig(constraint_type="session_different_days", category=ConstraintCategory.HARD),
    ConstraintConfig(constraint_type="instructor_no_overlap", category=ConstraintCategory.HARD),
    ConstraintConfig(constraint_type="room_no_overlap", category=ConstraintCategory.HARD),
    ConstraintConfig(constraint_type="instructor_max_hours", category=ConstraintCategory.HARD),
    ConstraintConfig(constraint_type="instructor_availability", category=ConstraintCategory.HARD),
    ConstraintConfig(
        constraint_type="workload_balance",
        category=ConstraintCategory.SOFT,
        weight=200,
        parameters={"range_weight": 200, "deviation_weight": 20},
    ),
    ConstraintConfig(
        constraint_type="preferences",
        category=ConstraintCategory.SOFT,
        weight=1,
    ),
)


# --- Build solver input ---
solver_input = SolverInput(
    groups=tuple(groups),
    instructors=tuple(instructors),
    rooms=tuple(rooms),
    time_slots=tuple(time_slots),
    constraints=constraints,
    objective_weights=ObjectiveWeights(
        workload_balance_range=200,
        workload_balance_deviation=20,
        instructor_preferences=1,
    ),
    solver_params=SolverParams(
        max_time_seconds=60,
        num_workers=4,
        random_seed=42,
    ),
)


# --- Solve ---
output = solve(solver_input)

print(f"Status: {output.status.value}")
print(f"Groups scheduled: {output.statistics.groups_scheduled}/{output.statistics.groups_total}")
print(f"Elapsed: {output.statistics.elapsed_seconds:.2f}s")
print(f"Variables: {output.statistics.num_variables}")
print(f"Constraints: {output.statistics.num_constraints}")

for assignment in output.assignments:
    print(f"\n{assignment.group_id} -> {assignment.instructor_id}")
    for session in assignment.sessions:
        slot_labels = [
            time_slots[s].label for s in session.slot_indices
        ]
        print(f"  Block {session.block_index}: {session.room_id} @ {slot_labels}")
```

Expected output (values depend on solver run):

```
Status: optimal
Groups scheduled: 4/4
Elapsed: 0.45s
Variables: 2847
Constraints: 1523

CS101-G1 -> PROF-001
  Block 0: LAB1 @ ['Mon P1', 'Mon P2']
  Block 1: LAB1 @ ['Wed P1', 'Wed P2']

CS101-G2 -> PROF-001
  Block 0: LAB2 @ ['Tue P3', 'Tue P4']
  Block 1: LAB2 @ ['Thu P3', 'Thu P4']

CS201-G1 -> PROF-002
  Block 0: LAB1 @ ['Tue P1', 'Tue P2']
  Block 1: LAB1 @ ['Fri P1']

MATH101-G1 -> PROF-003
  Block 0: R101 @ ['Mon P3', 'Mon P4', 'Mon P5']
```

---

*End of document.*
