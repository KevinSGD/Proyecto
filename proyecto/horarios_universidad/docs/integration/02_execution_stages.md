# Execution Stages

## The 10 Stages

Each solver run progresses through these stages, tracked in real-time via `ExecutionTracker`:

| # | Stage | Value | Description |
|---|-------|-------|-------------|
| 1 | Inicializando | `inicializando` | Run record created, solver configured |
| 2 | Validando | `validando` | Pre-solve domain validation (reserved) |
| 3 | Construyendo modelo | `construyendo_modelo` | DatasetBuilder transforms DB entities to OptimizationProblem |
| 4 | Generando variables | `generando_variables` | Decision variables created (within SolverEngine) |
| 5 | Aplicando restricciones | `aplicando_restricciones` | Hard and soft constraints applied (within SolverEngine) |
| 6 | Optimizando | `optimizando` | CP-SAT solver running |
| 7 | Extrayendo solución | `extrayendo_solucion` | Solution extracted from solver (within SolverEngine) |
| 8 | Guardando | `guardando` | ResultPublisher persists assignments and statistics |
| 9 | Publicado | `publicado` | Pipeline completed successfully |
| 10 | Error | `error` | Pipeline failed (traceback captured) |

## Stage Transitions in Code

```python
from app.application.services.execution_tracker import ExecutionStage, ExecutionTracker

tracker = ExecutionTracker(uow, run_id)

tracker.begin(ExecutionStage.INICIALIZANDO)
# ... create run, configure solver ...

tracker.advance(ExecutionStage.CONSTRUYENDO_MODELO)
problem = DatasetBuilder(uow).build(institution_id, period_id)

tracker.advance(ExecutionStage.OPTIMIZANDO)
result = SolverEngine(config).solve(problem)

tracker.advance(ExecutionStage.GUARDANDO)
ResultPublisher(uow).publish(result, run_id)

tracker.complete()  # automatically marks PUBLICADO
```

## Timing Data

Each stage transition records elapsed time for the previous stage. The `timings` dict looks like:

```json
{
  "inicializando": 0.0012,
  "validando": 0.0001,
  "construyendo_modelo": 2.3456,
  "optimizando": 45.7890,
  "guardando": 0.5678,
  "total": 48.7037
}
```

## ExecutionLog Entity

Each transition persists an `ExecutionLog`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `schedule_run_id` | UUID | FK to ScheduleRun |
| `event_type` | string | `stage_transition`, `execution`, `solver`, `persistence`, `error` |
| `message` | string | Human-readable message |
| `timestamp` | datetime | UTC timestamp |
| `metadata` | JSON | Stage name, timings, error details |

## API Access

- `GET /api/v1/schedule-runs/{run_id}/logs` — all execution logs for a run
- `GET /api/v1/schedule-runs/{run_id}/detail` — full detail including `execution_logs[]`
