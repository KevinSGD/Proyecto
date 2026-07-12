# Dependency Graph

## Layer Dependencies

```
API Layer
  └── Application Layer
        └── Domain Layer (entities + interfaces)

Infrastructure Layer
  └── Domain Layer (implements interfaces)
```

## Module Dependencies

### API → Application

```
app/api/routers/institution.py
  ├── app/application/commands/institution_commands.py
  ├── app/application/queries/institution_queries.py
  └── app/api/schemas/institution.py

app/api/routers/personnel.py
  ├── app/application/commands/personnel_commands.py
  ├── app/application/queries/personnel_queries.py
  └── app/api/schemas/personnel.py

app/api/routers/infrastructure.py
  ├── app/application/commands/infrastructure_commands.py
  ├── app/application/queries/infrastructure_queries.py
  └── app/api/schemas/infrastructure.py

app/api/routers/schedule.py
  ├── app/application/commands/schedule_commands.py
  ├── app/application/queries/schedule_queries.py
  └── app/api/schemas/schedule.py

app/api/routers/dashboard.py
  ├── app/application/queries/dashboard_queries.py
  └── app/api/schemas/dashboard.py
```

### Application → Domain

```
app/application/commands/*
  ├── app/domain/entities/*          (creates entities)
  ├── app/domain/interfaces/unit_of_work.py  (UoW type hint)
  └── app/core/utils/types.py        (generate_id)

app/application/queries/*
  ├── app/domain/interfaces/unit_of_work.py
  └── app/application/mappers/*      (entity → dict)

app/application/services/schedule_service.py
  ├── app/application/services/dataset_builder.py
  ├── app/application/services/result_publisher.py
  ├── app/application/services/domain_validator.py
  └── app/solver/                    (imported inside methods)
```

### Infrastructure → Domain

```
app/infrastructure/persistence/repositories/*
  └── app/domain/interfaces/repositories.py  (implements)

app/infrastructure/persistence/unit_of_work.py
  └── app/domain/interfaces/unit_of_work.py  (implements)

app/infrastructure/persistence/models/*
  └── app/domain/entities/*          (maps to/from)
```

## Dependency Injection

```
FastAPI Depends(get_uow)
  → app/api/dependencies/database.py
    → DatabaseEngine (singleton)
      → SqlAlchemyUnitOfWork(session_factory)
        → Concrete repositories (lazy instantiation)
```

## Solver Integration

The solver is imported **only inside methods** in the application layer to maintain Clean Architecture:

```python
class GenerateSchedule:
    def execute(self, data):
        from app.application.services.schedule_service import ScheduleGenerationService
        from app.solver.config import SolverConfiguration
        ...
```

This prevents the domain and application layers from having a hard dependency on Google OR-Tools.
