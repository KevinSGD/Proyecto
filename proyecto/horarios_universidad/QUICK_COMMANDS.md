# Comandos Rápidos

## Iniciar el Sistema

> **Importante (Windows):** el comando `python` solo funciona si activaste el
> entorno virtual en esa terminal (`.\.venv\Scripts\Activate.ps1`). Si no lo
> activaste, PowerShell no reconoce `python` — usa `py` en su lugar, o activa
> el venv primero. Cada terminal nueva necesita su propia activación.

```powershell
# Backend (Terminal 1 — desde proyecto/horarios_universidad/backend)
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
# Alternativa sin activar venv:
# py -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (Terminal 2 — desde proyecto/horarios_universidad/frontend/app)
npx next dev --port 3000
```

Verifica que ambos quedaron arriba antes de usar la app:
```bash
curl http://localhost:8000/health   # {"success":true,...,"status":"ok"}
curl http://localhost:3000/login    # HTML de la página de login
```

Si el login da error 404 justo después de escribir las credenciales, casi
siempre es porque el backend todavía no había terminado de arrancar (o se
reinició por `--reload`) cuando se envió el request — espera a ver
`Application startup complete.` en la Terminal 1 y reintenta.

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
