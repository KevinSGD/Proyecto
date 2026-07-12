# Comandos Rápidos

## Iniciar el Sistema

```bash
# Backend (desde proyecto/horarios_universidad/backend)
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (desde proyecto/horarios_universidad/frontend/app)
npx next dev --port 3000
```

## Seed de Datos

```bash
# Desde proyecto/horarios_universidad/backend
python -m app.infrastructure.persistence.seed_data
python -m app.infrastructure.persistence.seed_auth
```

## Migraciones (Alembic)

```bash
# Desde proyecto/horarios_universidad/backend
alembic upgrade head
alembic revision --autogenerate -m "descripcion"
```

## Pruebas

```bash
# Desde proyecto/horarios_universidad/backend
python -m pytest tests/ -v
```

## Solver

```bash
# Generar horario via API
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"institutionId": "<id>", "periodId": "<id>"}'
```

## Autenticación

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "director@udemo.edu", "password": "director123"}'
```

## Estructura de Directorios

```
proyecto/horarios_universidad/
├── backend/           # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/       # Routers, schemas, middlewares
│   │   ├── application/ # Commands, queries, services (CQRS)
│   │   ├── domain/    # Entities, value objects, ports
│   │   └── infrastructure/ # Repos, persistence, solver
│   └── tests/
├── frontend/
│   └── app/           # Next.js App Router
│       ├── app/       # Pages (platform routes)
│       ├── components/ # UI + domain components
│       └── lib/       # Services, stores, hooks, types
└── docs/              # Documentación adicional
```
