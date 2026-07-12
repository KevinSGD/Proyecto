# Quick Start

Guía paso a paso para levantar el proyecto localmente desde cero.
No se necesita PostgreSQL, Docker, ni servicios externos.

## Requisitos

- Python >= 3.12
- Node.js >= 18
- npm (incluido con Node.js)

## 1. Clonar y configurar

```bash
git clone <repo-url>
cd horarios_universidad
cp .env.example .env
```

El archivo `.env` ya viene configurado con SQLite — no necesitas editar nada.

## 2. Backend

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

### Linux / macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e ".[dev]"
```

## 3. Base de datos

```bash
alembic upgrade head
```

Esto crea `scheduler.db` (SQLite) con todas las tablas del sistema (37 tablas).

## 4. Datos de prueba

```bash
python -m scripts.seed_demo
```

Crea:
- Institución "Universidad Demo" con campus y período activo
- 2 usuarios: director y coordinador
- 8 materias, 5 docentes con disponibilidad completa
- 5 aulas (3 regulares + 2 laboratorios) con recursos
- Ofertas académicas con grupos pre-generados
- Tipo de horario configurado (Diurno L-V)

## 5. Iniciar backend

```bash
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

Verificar: http://localhost:8000/health → `{"status": "healthy"}`

## 6. Frontend (nueva terminal)

```powershell
cd frontend/app
npm install
npm run dev
```

## 7. Usar la plataforma

1. Abrir http://localhost:3000
2. Login: `director@udemo.edu` / `director123`
3. Navegar por Dashboard, Materias, Docentes, Aulas
4. Ir a **Oferta** → pestaña "Generación / Resultados" → **Generar horario**
5. Esperar a que el solver termine → **Publicar**
6. Ver el horario generado en la sección **Horarios**

## Resumen de comandos

```bash
# Backend (Terminal 1)
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m scripts.seed_demo
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (Terminal 2)
cd frontend/app
npm install
npm run dev
```

## Credenciales

| Email | Contraseña | Rol |
|---|---|---|
| `director@udemo.edu` | `director123` | Director académico |
| `coordinador@udemo.edu` | `coordinador123` | Coordinador de área |

## Troubleshooting

**Error "No module named 'app'"**: Asegúrate de estar en el directorio `backend/` al ejecutar comandos.

**Error de migración**: Eliminar `scheduler.db` y ejecutar de nuevo `alembic upgrade head`.

**Frontend no conecta con el API**: Verificar que el backend corre en puerto 8000. El frontend busca `http://localhost:8000` por defecto.

**Cambiar a PostgreSQL**: Editar `.env` y descomentar la línea de PostgreSQL:
```
SCHEDULER_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/scheduler
```
