# Auditoría del Repositorio — Fase 10.0

Fecha: 2026-07-10

## Resumen Ejecutivo

El repositorio contiene múltiples frontends heredados (Vue, prototipos v0), un solver prototipo independiente, archivos de salida temporales, credenciales expuestas, y 62 directorios `__pycache__` sin gitignore. Se requiere limpieza profunda antes de continuar con nuevas funcionalidades.

---

## 1. ELIMINAR — Código heredado y prototipos

### 1.1 Frontend Vue (raíz de `frontend/`)

| Elemento | Descripción |
|----------|-------------|
| `frontend/src/` | App Vue 3 completa: 25 archivos (.vue, .js, .css) |
| `frontend/dist/` | Build compilado de la app Vue |
| `frontend/public/` | Assets del frontend Vue (favicon.svg, icons.svg) |
| `frontend/package.json` | Deps Vue: vue 3.5, vite 8, tailwindcss 3 |
| `frontend/package-lock.json` | Lockfile Vue (80KB) |
| `frontend/vite.config.js` | Config Vite con proxy a Railway |
| `frontend/postcss.config.js` | PostCSS para Vue |
| `frontend/tailwind.config.js` | Tailwind para Vue (6KB) |
| `frontend/vercel.json` | Deploy config para Vercel (Vue) |
| `frontend/node_modules/` | Dependencias Vue instaladas |

### 1.2 Director UI (prototipo v0)

| Elemento | Descripción |
|----------|-------------|
| `frontend/director_UI/` | App Next.js independiente generada con v0 |
| Incluye | `.next/` build, `node_modules/`, pnpm lockfiles, `.claude/` |

### 1.3 Coordinador UI (prototipo v0)

| Elemento | Descripción |
|----------|-------------|
| `frontend/coordinador_UI/` | App Next.js independiente con su propio `.git/` |
| Incluye | `node_modules/`, pnpm lockfiles, public assets, `.git/` separado |

### 1.4 Solver Prototipo (`src/`)

| Elemento | Descripción |
|----------|-------------|
| `src/scheduler/` | 22 archivos Python: solver original pre-Clean Architecture |
| Incluye | `application/`, `config/`, `infrastructure/`, `interfaces/` |
| Estado | Completamente reemplazado por `backend/app/solver/` |

### 1.5 Archivos de salida temporal

| Elemento | Descripción |
|----------|-------------|
| `outputs/` | 8 archivos .xlsx de pruebas del solver (incluye ~$ temporal) |

### 1.6 GitHub modernize (vacío)

| Elemento | Descripción |
|----------|-------------|
| `frontend/.github/modernize/` | Solo contiene un `.gitignore` con `*` |

---

## 2. CORREGIR — Problemas de seguridad y configuración

### 2.1 Credenciales expuestas

| Archivo | Problema |
|---------|----------|
| `.env.example` | Contiene credenciales reales de PostgreSQL (Railway) |
| **Acción** | Reemplazar con placeholders genéricos |

### 2.2 Falta `.gitignore` raíz

| Problema | No existe `.gitignore` en la raíz de `horarios_universidad/` |
|----------|-------------------------------------------------------------|
| **Acción** | Crear con reglas para `__pycache__/`, `.env`, `outputs/`, `*.pyc`, `.next/`, `node_modules/` |

### 2.3 `__pycache__` en el repositorio

| Cantidad | 62 directorios `__pycache__/` rastreados por git |
|----------|--------------------------------------------------|
| **Acción** | Eliminar de git, agregar a `.gitignore` |

---

## 3. MANTENER — Código del sistema final

### 3.1 Backend (`backend/`)

- `app/api/` — FastAPI routers, schemas, middlewares, dependencies
- `app/application/` — Services, queries, commands, DTOs, exceptions
- `app/core/` — Logging, security, exceptions, utils
- `app/domain/` — Entities, interfaces, value objects
- `app/infrastructure/` — ORM models, repositories, unit of work
- `app/solver/` — CP-SAT constraints, objectives, pipeline
- `scripts/seed_auth.py` — Seed de usuarios y roles
- `tests/` — Unit tests (solver, application, auth)
- `docs/` — API architecture, solver docs

### 3.2 Frontend (`frontend/app/`)

- `app/` — Next.js 16 App Router pages
- `components/` — UI and domain components
- `lib/` — Stores, services, types, guards, utils
- `node_modules/` — Dependencies (no rastrear)
- `.next/` — Build cache (no rastrear)

### 3.3 Documentación (`docs/`)

- `docs/integration/` — Phase 9 pipeline + Phase 10.1 auth docs
- `docs/frontend/` — Frontend architecture, components, routes
- `docs/cleanup/` — Este audit y documentación de limpieza

---

## 4. REFACTORIZAR — Debe revisarse

### 4.1 Frontend `docs/frontend/`

| Archivo | Estado |
|---------|--------|
| `01_frontend_audit.md` | Posible duplicado de `01_architecture.md` |
| `03_migration_history.md` | Historial de migración Vue→React — conservar si útil |
| Numeración duplicada | `01_*`, `02_*`, `03_*`, `05_*` tienen dos archivos cada uno |

### 4.2 Backend `tests/performance/`

| Estado | Directorio vacío (solo `__init__.py`) |
|--------|---------------------------------------|
| **Acción** | Eliminar placeholder vacío |

### 4.3 Backend `tests/integration/`

| Estado | Contiene `test_solver_integration.py` — funcional |
|--------|--------------------------------------------------|
| **Acción** | Mantener |

### 4.4 Frontend `.next/` en git

| Estado | Build cache del dev server está en el árbol de git |
|--------|------------------------------------------------------|
| **Acción** | Agregar a `.gitignore`, eliminar del tracking |

---

## 5. Inventario de eliminación

| Ruta | Tipo | Razón |
|------|------|-------|
| `frontend/src/` | Vue app | Reemplazado por `frontend/app/` |
| `frontend/dist/` | Vue build | Output de build obsoleto |
| `frontend/public/` | Vue assets | No usado por React app |
| `frontend/package.json` | Vue deps | Config del frontend Vue |
| `frontend/package-lock.json` | Vue lockfile | Lockfile obsoleto |
| `frontend/vite.config.js` | Vue config | Config Vite obsoleta |
| `frontend/postcss.config.js` | Vue config | PostCSS obsoleto |
| `frontend/tailwind.config.js` | Vue config | Tailwind v3 obsoleto |
| `frontend/vercel.json` | Deploy | Config Vercel antigua |
| `frontend/node_modules/` | Vue deps | Instalar desde cero si necesario |
| `frontend/director_UI/` | Prototipo | UI de prueba v0 |
| `frontend/coordinador_UI/` | Prototipo | UI de prueba v0 con `.git/` propio |
| `frontend/.github/` | Vacío | Solo `.gitignore` de modernize |
| `src/` | Solver viejo | Reemplazado por `backend/app/solver/` |
| `outputs/` | Temporal | Archivos Excel de pruebas |
| `.env.example` | Seguridad | Contiene credenciales reales |
| 62x `__pycache__/` | Cache | No deben estar en git |
