# Error Handling

## Exception Hierarchy

The API handles two layers of exceptions:

### Application Exceptions (`app.application.exceptions`)

| Exception               | HTTP Status | Error Code              |
|--------------------------|-------------|-------------------------|
| `ResourceNotFoundError`  | 404         | `NOT_FOUND`             |
| `BusinessRuleError`      | 422         | `BUSINESS_RULE_VIOLATION` |
| `ResourceConflictError`  | 409         | `CONFLICT`              |
| `AuthorizationError`     | 403         | `FORBIDDEN`             |

### Domain Exceptions (`app.core.exceptions.base`)

| Exception                  | HTTP Status | Error Code             |
|----------------------------|-------------|------------------------|
| `EntityNotFoundError`      | 404         | `ENTITY_NOT_FOUND`     |
| `DuplicateEntityError`     | 409         | `DUPLICATE_ENTITY`     |
| `InvalidStateError`        | 422         | `INVALID_STATE`        |
| `FieldValidationError`     | 422         | `VALIDATION_ERROR`     |
| `CompositeValidationError` | 422         | `VALIDATION_ERROR`     |
| `ValidationError`          | 422         | `VALIDATION_ERROR`     |
| `InfeasibleError`          | 422         | `SOLVER_INFEASIBLE`    |
| `TimeoutError_`            | 408         | `SOLVER_TIMEOUT`       |
| `OptimizationError`        | 500         | `SOLVER_ERROR`         |
| `RepositoryError`          | 500         | `PERSISTENCE_ERROR`    |
| `ImportError_`             | 422         | `IMPORT_ERROR`         |
| `ExportError`              | 500         | `EXPORT_ERROR`         |
| `ConfigurationError`       | 500         | `CONFIGURATION_ERROR`  |
| `SchedulerError`           | 500         | `INTERNAL_ERROR`       |
| `Exception` (catch-all)    | 500         | `INTERNAL_ERROR`       |

## Error Response Format

All errors return a uniform `ErrorResponse` body:

```json
{
  "success": false,
  "errorCode": "NOT_FOUND",
  "message": "Institution with id '...' not found",
  "details": []
}
```

Validation errors may include field-level details:

```json
{
  "success": false,
  "errorCode": "VALIDATION_ERROR",
  "message": "Multiple validation errors",
  "details": [
    { "field": "name", "message": "Field is required", "code": null }
  ]
}
```

## Handler Registration

All handlers are registered in `app/api/middlewares/error_handler.py` via `register_exception_handlers(app)`, called during app startup.

Application-layer exceptions are registered first (higher priority), followed by domain exceptions, with `Exception` as the final catch-all.

## Solver-Specific Errors

| Scenario                        | Error Code          | Status |
|---------------------------------|---------------------|--------|
| No feasible solution exists     | `SOLVER_INFEASIBLE` | 422    |
| Solver time limit exceeded      | `SOLVER_TIMEOUT`    | 408    |
| Internal solver failure         | `SOLVER_ERROR`      | 500    |
| Cannot publish non-optimal run  | `BUSINESS_RULE_VIOLATION` | 422 |
