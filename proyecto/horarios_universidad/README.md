# Horarios Universidad

Plataforma de generación automática de horarios académicos universitarios.
Combina una API REST (FastAPI) con un frontend moderno (Next.js) y un motor de optimización basado en Google OR-Tools CP-SAT.

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic-settings |
| **Frontend** | Next.js 16, React 19, TypeScript 5.7, Tailwind CSS v4, Zustand |
| **Solver** | Google OR-Tools CP-SAT (13 restricciones duras, 11 suaves, 6 componentes de objetivo) |
| **Base de datos** | SQLite (desarrollo local) · PostgreSQL (producción) |
| **Autenticación** | JWT (python-jose) + bcrypt |

## Quick Start (5 minutos)

> **Requisitos**: Python >= 3.12, Node.js >= 18, npm.
> **No necesitas**: PostgreSQL, Docker, Redis, ni servicios en la nube.

```powershell
# 1. Clonar
git clone <repo-url> && cd horarios_universidad

# 2. Variables de entorno (SQLite por defecto — sin editar nada)
cp .env.example .env

# 3. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate            # Linux/macOS
python -m pip install -U pip
pip install -e ".[dev]"

# 4. Migraciones + Seed
alembic upgrade head
python -m scripts.seed_demo

# 5. Iniciar backend (Terminal 1)
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000

# 6. Frontend (Terminal 2)
cd ../frontend/app
npm install
npm run dev
```

Abrir http://localhost:3000 → Login → `director@udemo.edu` / `director123`

## Arquitectura

```
Clean Architecture + DDD + CQRS-lite
├── domain/          Entidades, value objects, interfaces
├── application/     Commands, queries, services, validators
├── infrastructure/  Persistence (SQLAlchemy), migrations (Alembic)
├── api/             Routers, schemas, middlewares, dependencies
└── solver/          Constraints, objective, optimizer, extractor
```

## Estructura del Proyecto

```
horarios_universidad/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI (routers, schemas, middlewares)
│   │   ├── application/          # Casos de uso (commands, queries, services)
│   │   ├── core/                 # Excepciones, logging, seguridad
│   │   ├── domain/               # Entidades, value objects, interfaces
│   │   ├── infrastructure/       # SQLAlchemy models, repositories, UoW
│   │   └── solver/               # OR-Tools CP-SAT engine
│   ├── scripts/                  # Seed y utilidades
│   ├── tests/                    # Unit + integration tests
│   └── pyproject.toml
├── frontend/
│   └── app/                      # Next.js App Router
│       ├── app/                  # Pages: (auth)/ y (platform)/
│       ├── components/           # UI components + domain forms
│       └── lib/                  # API client, services, stores, types
├── .env.example                  # Variables de entorno (plantilla)
└── .gitignore
```

## Usuarios de prueba

| Usuario | Email | Contraseña | Rol |
|---|---|---|---|
| Director | `director@udemo.edu` | `director123` | director |
| Coordinador | `coordinador@udemo.edu` | `coordinador123` | area_coordinator |

## Datos del seed

El script `seed_demo` crea un dataset completo para desarrollo:

- 1 institución (Universidad Demo) con 1 campus y 1 período activo
- 2 áreas académicas (Ciencias Básicas, Ingeniería)
- 8 materias con créditos y horas semanales
- 5 docentes con contratos, especialidades y disponibilidad completa (L-V)
- 1 edificio con 5 aulas (3 regulares + 2 laboratorios)
- 3 recursos (proyector, computadoras, pizarra digital)
- 2 ofertas académicas con líneas y grupos pre-generados
- 1 tipo de horario (Diurno, slots 1-12, L-V)

## URLs

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api/v1 |
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

## Configuración

Todas las variables usan el prefijo `SCHEDULER_` y se cargan desde `.env`:

| Variable | Descripción | Default |
|---|---|---|
| `SCHEDULER_DATABASE_URL` | URL de conexión (SQLite o PostgreSQL) | `sqlite:///scheduler.db` |
| `SCHEDULER_SECRET_KEY` | Clave para firmar JWT | `CHANGE-ME-IN-PRODUCTION...` |
| `SCHEDULER_LOG_LEVEL` | Nivel de logging | `INFO` |
| `SCHEDULER_DEBUG` | Modo debug | `false` |
| `SCHEDULER_SOLVER_MAX_TIME_SECONDS` | Timeout del solver | `300` |
| `SCHEDULER_SOLVER_NUM_WORKERS` | Workers paralelos del solver | `4` |

## Flujo completo de uso

1. **Login** → Ingresar como director
2. **Dashboard** → Vista general de la institución
3. **Materias** → Consultar/crear materias
4. **Docentes** → Gestionar docentes, especialidades, disponibilidad
5. **Aulas** → Administrar edificios y salones con recursos
6. **Oferta** → Ver ofertas académicas y líneas
7. **Generar horario** → Pestaña "Generación / Resultados" → Botón "Generar horario"
8. **Publicar** → Publicar un horario completado
9. **Horarios** → Visualizar el horario generado en formato semanal

## Tests

```powershell
cd backend
python -m pytest tests/ -q
```

## API Endpoints

Todos los endpoints (excepto health) usan el prefijo `/api/v1`.

| Módulo | Prefijo | Descripción |
|---|---|---|
| Health | `/health` | Estado del servicio |
| Auth | `/api/v1/auth` | Login, logout, refresh, perfil |
| Institution | `/api/v1/institutions` | Instituciones, campuses, periodos |
| Academic | `/api/v1/institutions/{id}` | Áreas y materias |
| Personnel | `/api/v1/institutions/{id}` | Docentes, contratos, disponibilidad |
| Infrastructure | `/api/v1/institutions/{id}` | Aulas, edificios, recursos |
| Offering | `/api/v1/institutions/{id}/periods/{pid}` | Oferta académica y grupos |
| Schedule | `/api/v1/schedule` | Generación, publicación, ejecuciones |
| Dashboard | `/api/v1/institutions/{id}/dashboard` | Estadísticas y métricas |

Documentación interactiva completa en http://localhost:8000/docs.

## Licencia

Proyecto académico — Universidad.
