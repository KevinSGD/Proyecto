# Pipeline Architecture

## Overview

The schedule generation pipeline transforms academic data into an optimized timetable through a series of well-defined stages, each tracked and logged for observability.

## Pipeline Flow

```
POST /schedule/generate
  → GenerateSchedule (Command)
    → ScheduleGenerationService.generate()
      ├── 1. Create ScheduleRun (status="running")
      ├── 2. ExecutionTracker.begin(INICIALIZANDO)
      ├── 3. DatasetBuilder.build() → OptimizationProblem
      ├── 4. SolverEngine.solve() → OptimizationResult
      │     ├── CpSatModelBuilder.build() (index, domain filter, variables)
      │     ├── PluginManager.apply_constraints()
      │     ├── PluginManager.build_objective()
      │     └── CpSatOptimizer.optimize()
      ├── 5. ResultPublisher.publish() → persist assignments + statistics
      └── 6. ExecutionTracker.complete()
```

## Component Responsibilities

| Component | Module | Responsibility |
|-----------|--------|----------------|
| `GenerateSchedule` | `app.application.commands.schedule_commands` | CQRS command, entry point from API |
| `ScheduleGenerationService` | `app.application.services.schedule_service` | Pipeline orchestrator |
| `ExecutionTracker` | `app.application.services.execution_tracker` | Stage tracking, event logging |
| `DatasetBuilder` | `app.application.services.dataset_builder` | DB → solver data transformation |
| `SolverEngine` | `app.solver.engine` | 8-stage CP-SAT pipeline |
| `ResultPublisher` | `app.application.services.result_publisher` | Solver → DB persistence |

## Data Flow

```
DB Repositories
  ↓ (via UnitOfWork)
DatasetBuilder
  ↓ produces
OptimizationProblem (SolverGroup, SolverInstructor, SolverClassroom, SolverTimeConfig)
  ↓ consumed by
SolverEngine
  ↓ produces
OptimizationResult (SolverStatus, AssignmentResult[], SolverStatistics)
  ↓ consumed by
ResultPublisher
  ↓ persists
ScheduleRun (updated), Assignment[], SessionBlock[]
```

## Error Recovery

On any exception during the pipeline:

1. `ExecutionTracker.fail(exc)` records the error with:
   - Stage where failure occurred
   - Exception type and message
   - Full traceback
   - Accumulated stage timings
2. `_mark_error(run_id, exc)` updates the ScheduleRun:
   - Sets `status = "error"`
   - Sets `completed_at` timestamp
   - Stores error details in `statistics.error` (type, message, traceback)
3. The run remains in the database for diagnosis; the user can retry.

## Decoupling Guarantees

- The **solver** never accesses repositories or domain entities
- `DatasetBuilder` is the **only bridge** from persistence to solver
- `ResultPublisher` is the **only bridge** from solver results to persistence
- `ExecutionTracker` persists logs through the UoW, independently of the pipeline
