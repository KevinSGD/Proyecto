# Execution Logs API

## Endpoints

### GET /api/v1/schedule-runs/{run_id}/logs

Returns all execution event logs for a solver run, ordered by timestamp.

**Response:**

```json
{
  "data": [
    {
      "id": "uuid",
      "scheduleRunId": "uuid",
      "eventType": "stage_transition",
      "message": "Etapa: inicializando",
      "timestamp": "2026-07-09T18:00:00Z",
      "metadata": {
        "stage": "inicializando"
      }
    },
    {
      "id": "uuid",
      "scheduleRunId": "uuid",
      "eventType": "execution",
      "message": "Configuración: max_time=300s, workers=4",
      "timestamp": "2026-07-09T18:00:00Z",
      "metadata": {
        "stage": "inicializando",
        "solver_config": {
          "max_time_seconds": 300,
          "num_workers": 4,
          "gap_tolerance": 0.0
        }
      }
    },
    {
      "id": "uuid",
      "scheduleRunId": "uuid",
      "eventType": "solver",
      "message": "Solver terminó con estado: optimal",
      "timestamp": "2026-07-09T18:05:00Z",
      "metadata": {
        "stage": "optimizando",
        "status": "optimal",
        "objective_value": 1842.5,
        "gap": 0.015,
        "assignments_count": 118
      }
    }
  ],
  "message": "Execution logs retrieved"
}
```

### GET /api/v1/schedule-runs/{run_id}/detail

Now includes `executionLogs` alongside `assignments`:

```json
{
  "data": {
    "id": "uuid",
    "status": "optimal",
    "statistics": { "..." },
    "assignments": [ "..." ],
    "executionLogs": [
      {
        "id": "uuid",
        "eventType": "stage_transition",
        "message": "Pipeline completado en 65.42s",
        "timestamp": "2026-07-09T18:05:05Z",
        "metadata": {
          "stage": "publicado",
          "timings": { "total": 65.42 }
        }
      }
    ]
  }
}
```

## Event Types

| Type | Description | When |
|------|-------------|------|
| `stage_transition` | Stage change event | Each stage begin/advance/complete |
| `execution` | Pipeline lifecycle event | Config, dataset stats |
| `solver` | Solver-specific event | Solver completion status |
| `persistence` | Data persistence event | Assignments saved |
| `error` | Failure event | On exception |

## Error Event Metadata

```json
{
  "stage": "optimizando",
  "error_type": "ValueError",
  "traceback": "Traceback (most recent call):\n  ...",
  "timings": {
    "inicializando": 0.001,
    "construyendo_modelo": 2.34,
    "total": 2.341
  }
}
```
