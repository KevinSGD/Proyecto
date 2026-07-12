# Comandos de Referencia Rápida

## Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```powershell
cd frontend/app
npm run dev
```

## Seed de datos

```powershell
cd backend
python -m scripts.seed_auth
```

## Tests

```powershell
cd backend
python -m pytest tests/ -q
```

## Type-check frontend

```powershell
cd frontend/app
npx tsc --noEmit
```

## Lint backend

```powershell
cd backend
ruff check app/
```

## Format backend

```powershell
cd backend
ruff format app/
```

## Swagger

http://localhost:8000/docs

## Credenciales de prueba

| Rol | Email | Contraseña |
|---|---|---|
| Director | `director@udemo.edu` | `director123` |
| Coordinador | `coordinador@udemo.edu` | `coordinador123` |
