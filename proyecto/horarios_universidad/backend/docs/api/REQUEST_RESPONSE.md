# Request & Response Format

## Response Envelope

All successful responses use `ApiResponse`:

```json
{
  "success": true,
  "message": "Institution created",
  "data": { ... }
}
```

All error responses use `ErrorResponse`:

```json
{
  "success": false,
  "errorCode": "NOT_FOUND",
  "message": "Institution with id '...' not found",
  "details": []
}
```

## Serialization

- All JSON keys use **camelCase** (Pydantic `alias_generator`)
- Python snake_case fields are automatically converted
- Both camelCase and snake_case are accepted in request bodies (`populate_by_name=True`)
- UUIDs are serialized as strings
- Dates use ISO 8601 format (`YYYY-MM-DD`)
- Datetimes use ISO 8601 with timezone

## Request Examples

### Create Institution

```http
POST /api/v1/institutions
Content-Type: application/json

{
  "name": "Universidad Nacional",
  "abbreviation": "UN",
  "email": "info@un.edu"
}
```

### Create Teacher

```http
POST /api/v1/teachers
Content-Type: application/json

{
  "institutionId": "550e8400-e29b-41d4-a716-446655440000",
  "employeeCode": "T001",
  "firstName": "Jane",
  "lastName": "Doe",
  "email": "jane.doe@un.edu"
}
```

### Generate Schedule

```http
POST /api/v1/schedule/generate
Content-Type: application/json

{
  "institutionId": "550e8400-...",
  "periodId": "661f9500-...",
  "maxTimeSeconds": 120,
  "numWorkers": 4
}
```

### Set Teacher Availability (Bulk)

```http
PUT /api/v1/teachers/{id}/availability
Content-Type: application/json

{
  "instructorId": "...",
  "periodId": "...",
  "slots": [
    { "dayOfWeek": 1, "period": 1, "isAvailable": true },
    { "dayOfWeek": 1, "period": 2, "isAvailable": false }
  ]
}
```

## Response Examples

### Single Entity

```json
{
  "success": true,
  "message": "Teacher retrieved",
  "data": {
    "id": "550e8400-...",
    "institutionId": "661f9500-...",
    "employeeCode": "T001",
    "firstName": "Jane",
    "lastName": "Doe",
    "email": "jane.doe@un.edu",
    "phone": "",
    "departmentId": null,
    "isActive": true
  }
}
```

### List

```json
{
  "success": true,
  "message": "Institutions retrieved",
  "data": [
    { "id": "...", "name": "Universidad Nacional", "abbreviation": "UN", ... },
    { "id": "...", "name": "Instituto Tecnológico", "abbreviation": "IT", ... }
  ]
}
```

### Dashboard

```json
{
  "success": true,
  "message": "Dashboard retrieved",
  "data": {
    "totalTeachers": 42,
    "totalSubjects": 85,
    "totalClassrooms": 30,
    "totalGroups": 120,
    "activePeriod": {
      "id": "...",
      "name": "2026-1",
      "year": 2026,
      "periodNumber": 1,
      "status": "active"
    },
    "latestRunStatus": "optimal",
    "latestRunId": "...",
    "occupationPct": 92.5,
    "teacherCoveragePct": 88.3
  }
}
```

### Validation Error

```json
{
  "success": false,
  "errorCode": "VALIDATION_ERROR",
  "message": "Multiple validation errors",
  "details": [
    { "field": "name", "message": "Field is required", "code": null },
    { "field": "capacity", "message": "Must be positive", "code": null }
  ]
}
```
