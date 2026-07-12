# Error Recovery

## Error Capture

When the pipeline fails at any stage, three things happen:

1. **ExecutionTracker** records an `error` event with:
   - Stage where the failure occurred
   - Exception type and message
   - Full Python traceback
   - Accumulated timings up to the failure point

2. **ScheduleRun** is updated:
   - `status` → `"error"`
   - `completed_at` → current UTC timestamp
   - `statistics.error` → `{ type, message, traceback }`

3. **Standard logging** captures the exception via `_logger.exception()`

## Querying Failures

```
GET /api/v1/schedule-runs/{run_id}
→ { status: "error", statistics: { error: { type, message, traceback } } }

GET /api/v1/schedule-runs/{run_id}/logs
→ [ ... stage logs ..., { eventType: "error", metadata: { stage, traceback } } ]
```

## Retry

The failed run remains in the database with full diagnostic data. To retry:

1. Query the failed run to understand what went wrong
2. Fix the underlying data issue (e.g., missing instructor availability)
3. POST `/schedule/generate` with the same `institution_id` and `period_id`

A new `ScheduleRun` is created for the retry — the failed run is preserved for audit.

## Data Safety

- On failure, the UoW rolls back any uncommitted changes from the current stage
- Execution logs are persisted in separate UoW transactions so they survive the rollback
- The original ScheduleRun record is always preserved

## Common Failure Scenarios

| Stage | Likely Cause | Resolution |
|-------|-------------|------------|
| `construyendo_modelo` | Missing groups, instructors, or classrooms | Ensure data is loaded for the period |
| `construyendo_modelo` | No compatible classrooms for a group | Check capacity and resource requirements |
| `optimizando` | Infeasible problem | Relax constraints or add resources |
| `optimizando` | Timeout with no feasible solution | Increase `max_time_seconds` or reduce problem size |
| `guardando` | Database constraint violation | Check for duplicate assignments |
