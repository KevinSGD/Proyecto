# Application Layer

## Structure

```
app/application/
├── commands/                    # Write operations
│   ├── institution_commands.py
│   ├── academic_commands.py
│   ├── personnel_commands.py
│   ├── infrastructure_commands.py
│   ├── offering_commands.py
│   └── schedule_commands.py
├── queries/                     # Read operations
│   ├── institution_queries.py
│   ├── academic_queries.py
│   ├── personnel_queries.py
│   ├── infrastructure_queries.py
│   ├── offering_queries.py
│   ├── schedule_queries.py
│   └── dashboard_queries.py
├── services/                    # Complex orchestration
│   ├── schedule_service.py      # ScheduleGenerationService
│   ├── dataset_builder.py       # DB → solver dataset
│   ├── result_publisher.py      # Solver result → DB
│   ├── domain_validator.py      # Pre-optimization validation
│   └── validators/              # 6 validators, 23 rules
└── exceptions/
    ├── __init__.py
    └── application_exceptions.py
```

## CQRS-Lite Pattern

### Commands (writes)

```python
class CreateTeacher:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: InstructorCreate) -> Instructor:
        with self._uow:
            entity = Instructor(id=generate_id(), ...)
            saved = self._uow.instructors.save(entity)
            self._uow.commit()
            return saved
```

### Queries (reads)

```python
class GetTeacher:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, instructor_id: EntityId) -> Instructor:
        with self._uow:
            entity = self._uow.instructors.get_by_id(instructor_id)
            if entity is None:
                raise ResourceNotFoundError("Instructor", instructor_id)
            return entity
```

## ScheduleGenerationService

Orchestrates the full solver pipeline:

1. Creates a `ScheduleRun` with status `"running"`
2. Builds the `OptimizationProblem` via `DatasetBuilder`
3. Runs the CP-SAT solver
4. Publishes results via `ResultPublisher`
5. Updates run status to `"optimal"`, `"feasible"`, `"infeasible"`, or `"error"`

## Domain Validation

`DomainValidator` runs 23 pre-optimization rules across 6 validators:

- `InstructorValidator` (V-D01 to V-D04)
- `ClassroomValidator` (V-D05 to V-D08)
- `SubjectValidator` (V-D09 to V-D12)
- `OfferingValidator` (V-D13 to V-D16)
- `GroupValidator` (V-D17 to V-D20)
- `ScheduleTypeValidator` (V-D21 to V-D23)

## Mappers

Convert between domain entities and output schemas:

```python
def instructor_detail_to_dict(
    instructor: Instructor,
    contracts: list[InstructorContract],
    specialties: list[InstructorSpecialty],
) -> dict:
    ...
```

Used when the output schema requires aggregated data from multiple entities.
