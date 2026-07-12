# API Architecture

## Overview

The Scheduler API follows **Clean Architecture** with three concentric layers:

```
┌─────────────────────────────────┐
│          API Layer              │  ← FastAPI routers, schemas, middleware
│  ┌───────────────────────────┐  │
│  │   Application Layer       │  │  ← Use cases (Commands/Queries), DTOs, mappers
│  │  ┌─────────────────────┐  │  │
│  │  │   Domain Layer      │  │  │  ← Entities, interfaces, business rules
│  │  └─────────────────────┘  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

Dependencies point **inward only** — the domain never references the API or infrastructure.

## Technology Stack

| Component           | Technology                           |
|---------------------|--------------------------------------|
| Framework           | FastAPI 0.115+                       |
| Serialization       | Pydantic v2 (camelCase aliases)      |
| Database            | PostgreSQL via SQLAlchemy 2.x        |
| Migrations          | Alembic                              |
| Solver              | Google OR-Tools CP-SAT               |
| Runtime             | Python 3.14, Uvicorn                 |

## Layer Responsibilities

### API Layer (`app/api/`)
- HTTP routing and request/response serialization
- Input validation via Pydantic schemas
- Dependency injection via `Depends(get_uow)`
- Error mapping: domain/application exceptions → HTTP status codes
- CORS, logging middleware, OpenAPI documentation

### Application Layer (`app/application/`)
- **Commands**: Write operations (create, update, delete)
- **Queries**: Read operations (get, list, aggregate)
- **Services**: Complex orchestration (schedule generation, validation)
- **Mappers**: Entity ↔ DTO conversion
- **Exceptions**: `ResourceNotFoundError`, `BusinessRuleError`, etc.

### Domain Layer (`app/domain/`)
- Pure dataclass entities (no ORM dependency)
- Repository interfaces (abstract base classes)
- Unit of Work interface
- Business rule validation

### Infrastructure Layer (`app/infrastructure/`)
- SQLAlchemy ORM models
- Concrete repository implementations
- Database session management
- Alembic migration scripts

## Design Patterns

| Pattern              | Implementation                                |
|----------------------|-----------------------------------------------|
| CQRS-lite            | Separate Command/Query classes per use case   |
| Repository           | Abstract interfaces + SQLAlchemy concrete     |
| Unit of Work         | Transactional boundary around DB operations   |
| Dependency Injection | FastAPI `Depends()` for UoW injection         |
| Factory              | `create_app()` builds and configures FastAPI  |
| Dataset Builder      | Transforms DB entities → solver input         |

## Request Flow

```
HTTP Request
  → FastAPI Router
    → Pydantic Schema validation
      → Command/Query use case
        → Unit of Work (transaction)
          → Repository (data access)
            → Domain Entity
          ← Entity returned
        ← UoW commits
      ← Entity mapped to Output Schema
    ← ApiResponse envelope
  ← JSON Response
```
