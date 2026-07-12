# Phase 10.0 — Repository Cleanup Report

Consolidación completa del repositorio. Objetivo: eliminar todo código heredado, prototipos y archivos muertos,
dejando el proyecto como si fuera la primera versión oficial.

## Incremento 0.1 — Auditoría

Auditoría completa documentada en `repository_audit.md`.

## Incremento 0.2 — Eliminación de frontends obsoletos

Eliminados:

- `frontend/src/` — App Vue 3 completa (6 componentes .vue, router, store, services)
- `frontend/dist/` — Build output de Vue
- `frontend/public/` — Assets de Vue (favicon.svg, icons.svg)
- `frontend/director_UI/` — Prototipo v0 Next.js con .next/, node_modules/
- `frontend/coordinador_UI/` — Prototipo v0 Next.js con su propio .git/
- `frontend/.github/` — Directorio vacío
- `frontend/package.json`, `frontend/package-lock.json` — Deps de Vue
- `frontend/vite.config.js`, `frontend/postcss.config.js`, `frontend/tailwind.config.js` — Config de Vue
- `frontend/vercel.json`, `frontend/.gitignore` — Deploy de Vue
- `frontend/node_modules/` — Deps instaladas de Vue
- `frontend/README.md` — README de template Vue 3
- `frontend/.vite/` — Caché de Vite
- `src/scheduler/` — 22 archivos Python, prototipo original del solver
- `outputs/` — 8 archivos .xlsx de pruebas
- `pyproject.toml` (raíz) — Config del paquete legacy (pandas, pymysql)
- `requirements.txt` (raíz) — Deps legacy
- Todos los `__pycache__/` (62 directorios)
- `frontend/app/.next/` — Caché de build

Corregidos:

- `.env.example` — Credenciales de Railway reemplazadas con placeholders genéricos
- `.gitignore` — Creado desde cero en la raíz del repositorio

## Incremento 0.3 — Limpieza del frontend

Eliminados:

- `components/ui/Checkbox.tsx` — Sin importaciones
- `components/ui/DropdownMenu.tsx` — Sin importaciones
- `components/ui/Tooltip.tsx` — Sin importaciones
- `docs/frontend/01_frontend_audit.md` — Obsoleto
- `docs/frontend/02_new_architecture.md` — Obsoleto
- `docs/frontend/03_migration_history.md` — Obsoleto
- `docs/frontend/05_component_index.md` — Obsoleto

Corregidos:

- `components/ui/Field.tsx` → `SelectField`: prop `error?: string` faltante, estilos de borde de error, `<ErrorText>`
- `components/domain/DocenteFormDrawer.tsx` → Cast de tipo en `SelectField.onChange`
- `components/domain/MateriaFormDrawer.tsx` → Cast de tipo en `SelectField.onChange`

## Incremento 0.4 — Limpieza del backend

Eliminados:

- `app/application/commands/study_plan_commands.py` — Duplicado de academic_commands
- `app/application/mappers/academic_mapper.py` — Sin importaciones
- `app/application/mappers/infrastructure_mapper.py` — Sin importaciones
- `app/application/mappers/institution_mapper.py` — Sin importaciones
- `app/application/dto/` — Paquete stub vacío
- `app/api/controllers/` — Paquete stub vacío
- `app/domain/interfaces/io.py` — ImporterPort/ExporterPort sin implementar
- `app/domain/interfaces/solver.py` — SolverPort + 5 interfaces sin implementar
- `app/domain/services/domain_services.py` — 3 clases sin usar
- `app/core/config/` — Sistema de config paralelo muerto
- `app/core/exceptions/base.py` → `SolverConfigError` eliminado
- `app/solver/loader/` — Subpaquete vacío
- `app/solver/publisher/` — Subpaquete vacío
- `tests/performance/` — Directorio placeholder vacío

Corregidos:

- `app/domain/interfaces/__init__.py` — Eliminados re-exports de io.py y solver.py
- `app/domain/services/__init__.py` — Vaciado
- `app/core/exceptions/__init__.py` — Eliminado SolverConfigError
- `app/core/__init__.py` — Eliminado import de AppSettings
- `app/core/logging/logger.py` — `LoggingSettings` movido aquí desde core/config/settings.py

## Incremento 0.5 — Auditoría de dependencias

Backend (`pyproject.toml`) — eliminados:

- `openpyxl>=3.1` — Sin importaciones (era para export Excel del solver legacy)
- `pytest-asyncio>=0.23` — Sin tests async
- `httpx>=0.27` — Sin uso de test client ASGI

Frontend (`package.json`) — eliminados:

- `react-hook-form` — Sin importaciones
- `@hookform/resolvers` — Sin importaciones
- `zod` — Sin importaciones

## Incremento 0.6 — README profesional

- `README.md` reescrito desde cero con stack, arquitectura, estructura, instalación, ejecución, config, tests, endpoints

## Incremento 0.7 — Documentación de comandos

- `docs/COMANDOS.md` — Referencia rápida de todos los comandos
- `docs/QUICK_START.md` — Guía mínima de instalación y ejecución

## Incremento 0.8 — Scripts de desarrollo

Creados en `scripts/`:

- `dev-backend.ps1` — Inicia backend con uvicorn
- `dev-frontend.ps1` — Inicia frontend con next dev
- `test.ps1` — Ejecuta pytest
- `seed.ps1` — Ejecuta seed de datos
- `lint.ps1` — Ruff check + format
- `type-check.ps1` — TypeScript noEmit

## Incremento 0.9 — Verificación final

- Backend: 193/194 módulos importan correctamente (único fallo: alembic no instalado en entorno de desarrollo)
- Frontend: `next build` compila exitosamente todas las rutas
- Tests: todos pasan
- Sin imports rotos, sin dependencias fantasma, sin código muerto
