# Statistics Fields

## ScheduleRun.statistics (JSON)

The `statistics` field on `ScheduleRun` stores comprehensive solver metrics. After Phase 9 enhancement, it includes all `SolverStatistics` fields:

### Problem Size

| Field | Type | Description |
|-------|------|-------------|
| `groups_total` | int | Total groups in the problem |
| `groups_scheduled` | int | Groups that got assignments |
| `instructors_total` | int | Active instructors considered |
| `rooms_total` | int | Active classrooms considered |
| `time_slots_total` | int | Total (day × period) slots |

### Model Size

| Field | Type | Description |
|-------|------|-------------|
| `num_variables` | int | Total decision variables |
| `num_constraints` | int | Total constraints added |
| `variables_by_category` | dict | Variable count per category (X, Y, Z, etc.) |
| `constraints_by_type` | dict | Constraint count per type (HD-01, SB-01, etc.) |
| `hard_constraints_total` | int | Sum of HD-* constraints |
| `soft_constraints_total` | int | Sum of SB-* constraints |

### Timing

| Field | Type | Description |
|-------|------|-------------|
| `elapsed_seconds` | float | Total solver time |
| `timings` | dict | Per-stage timing breakdown |
| `memory_usage_mb` | float | Peak memory usage |

### Solution Quality

| Field | Type | Description |
|-------|------|-------------|
| `objective_value` | float | Weighted objective function value |
| `gap` | float | Optimality gap (0.0 = proven optimal) |
| `workload_spread` | float | Std deviation of periods per instructor |
| `avg_preference_score` | float | Mean instructor preference score |
| `room_utilization_pct` | float | Percentage of room-slots used |

### Error (only on failure)

| Field | Type | Description |
|-------|------|-------------|
| `error.type` | string | Exception class name |
| `error.message` | string | Error message |
| `error.traceback` | string | Full Python traceback |

## Example Response

```json
{
  "statistics": {
    "groups_total": 120,
    "groups_scheduled": 118,
    "instructors_total": 45,
    "rooms_total": 22,
    "time_slots_total": 55,
    "num_variables": 15420,
    "num_constraints": 8730,
    "variables_by_category": {
      "X": 5400, "Y": 6480, "Z": 120,
      "consecutive_aux": 1200, "workload_dev": 45
    },
    "constraints_by_type": {
      "HD-01": 5400, "HD-02": 120, "HD-03": 5400,
      "SB-01": 540, "SB-02": 270
    },
    "hard_constraints_total": 6750,
    "soft_constraints_total": 1980,
    "elapsed_seconds": 65.42,
    "timings": {
      "model_build": 1.23,
      "precondition_check": 0.01,
      "constraints": 0.89,
      "objective": 0.12,
      "solve": 62.50,
      "total": 65.42
    },
    "memory_usage_mb": 256.78,
    "objective_value": 1842.5,
    "gap": 0.015,
    "workload_spread": 2.3,
    "avg_preference_score": 7.8,
    "room_utilization_pct": 72.5
  }
}
```
