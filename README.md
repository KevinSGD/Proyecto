# TesisOMuerte

Generador de horarios académicos con backend en FastAPI y frontend en Vue 3 + Vite.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.10+** (descargar desde https://www.python.org/)
- **Node.js 18+** (descargar desde https://nodejs.org/)
- **Git** (para clonar repositorios)
- **PowerShell** (incluido en Windows)

Verifica las versiones:

```powershell
python --version
node --version
npm --version
```

---

## 🚀 Guía de Instalación y Arranque

Sigue estos pasos en orden desde la raíz del repositorio: `C:\Users\tu_usuario\Documents\TesisOMuerte`

### Paso 1: Crear y Activar el Entorno Virtual Python

Abre una terminal PowerShell **en la raíz del repositorio** y ejecuta:

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Verificar que está activado (deberías ver (.venv) al inicio de la línea)
```

**Si obtienes error de permisos**, ejecuta antes:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Paso 2: Instalar Dependencias del Proyecto

Con el entorno virtual activado:

```powershell
# Actualizar pip
python -m pip install -U pip

# Instalar dependencias Python
I

# Instalar el paquete del proyecto en modo editable
pip install -e proyecto/horarios_universidad/
```

### Paso 3: Instalar Dependencias del Frontend

```powershell
cd proyecto/horarios_universidad/frontend

npm install

cd ../..
```

### Paso 4: Configurar Variables de Entorno (Opcional)

Si necesitas conectarte a una base de datos remota, define estas variables:

```powershell
# Ejemplo con Supabase o PostgreSQL remoto
$env:DB_HOST = "tu-servidor.supabase.co"
$env:DB_PORT = "5432"
$env:DB_NAME = "postgres"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "tu_contraseña"
$env:DB_SSLMODE = "require"
```

Si usas un servicio remoto de Railway:

```powershell
$env:RAILWAY_RUN_URL = "https://tu-servicio-railway.com/run"
```

---

## ▶️ Iniciar la Aplicación

### Opción A: Dos Terminales (Recomendado)

**Terminal 1 - Backend API:**

```powershell
# Desde la raíz del repositorio con el venv activado
cd proyecto/horarios_universidad
python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Terminal 2 - Frontend:**

```powershell
# Desde la raíz del repositorio (puedes estar en otra terminal)
cd proyecto/horarios_universidad
cd frontend
npm run dev -- --host 127.0.0.1
```

Deberías ver:
```
➜  Local:   http://127.0.0.1:5173/
```

### Opción B: Una Terminal (Sequencial)

```powershell
# Backend primero
cd proyecto/horarios_universidad
python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src
# Espera a que inicie, luego abre otra terminal y ejecuta:
cd frontend
npm run dev -- --host 127.0.0.1
```

---

## 🌐 Acceder a la Aplicación

Una vez que ambos servidores estén corriendo:

| Componente | URL | Descripción |
|---|---|---|
| **Frontend** | http://127.0.0.1:5173/ | Interfaz web de Vue |
| **API** | http://127.0.0.1:8000 | Backend FastAPI |
| **Swagger UI** | http://127.0.0.1:8000/docs | Documentación interactiva de API |
| **ReDoc** | http://127.0.0.1:8000/redoc | Documentación alternativa |

Abre tu navegador en: **http://127.0.0.1:5173/**

---

## ✅ Verificar que Todo Funciona

### 1. Verificar Backend

```powershell
# Desde cualquier terminal
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

Deberías recibir una respuesta con el estado.

### 2. Verificar Conexión a BD

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/db/health"
```

### 3. Acceder a Swagger UI

Abre en el navegador: http://127.0.0.1:8000/docs

Aquí puedes probar todos los endpoints de la API.

---

## 🛑 Detener la Aplicación

En cada terminal, presiona:

```
CTRL + C
```

Para salir del entorno virtual:

```powershell
deactivate
```

---

## 🔧 Solución de Problemas

### Error: "No se pueden ejecutar scripts en PowerShell"

Si obtienes error de permisos al activar el entorno virtual:

```powershell
# Soluciona permisos de ejecución
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Error: "No module named 'scheduler'"

```powershell
# Asegúrate de estar en el directorio correcto y que el venv esté activado
cd proyecto/horarios_universidad
pip install -e .
```

### Error: "npm: command not found"

Node.js no está instalado. Descárgalo desde https://nodejs.org/

### El frontend no se conecta a la API

Verifica que:
1. El backend esté corriendo en `http://127.0.0.1:8000`
2. No haya conflicto de puertos (cambia los puertos si es necesario)
3. Las URLs en `frontend/src/services/api.js` sean correctas

### Cambios en el código no se reflejan

Los servidores tienen hot reload. Si no funciona:

```powershell
# Detén los servidores con CTRL+C
# Y reinicialos
cd proyecto/horarios_universidad
python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src

# En otra terminal
cd proyecto/horarios_universidad/frontend
npm run dev -- --host 127.0.0.1
```

---

## 📁 Estructura del Proyecto

```
TesisOMuerte/
├── proyecto/horarios_universidad/
│   ├── src/scheduler/          # Backend Python
│   │   ├── config/             # Configuración
│   │   ├── application/        # Lógica de negocio
│   │   ├── infrastructure/     # OR-Tools, exportadores
│   │   └── interfaces/         # API y CLI
│   ├── frontend/               # Frontend Vue 3
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── requirements.txt        # Dependencias Python
│   ├── pyproject.toml          # Configuración del paquete
│   └── README.md               # Guía de uso del módulo
└── README.md                   # Este archivo
```

---

## 📚 Comandos de Arranque

| Componente | Comando |
|---|---|
| Backend FastAPI | `python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src` |
| Frontend Vite | `cd frontend && npm run dev -- --host 127.0.0.1` |

---

## 🔗 Endpoints Principales de la API

- `GET /health` - Verifica que la API esté viva
- `GET /db/health` - Verifica conexión a base de datos
- `POST /run` - Genera el horario (puede delegarse a Railway si está configurado)

Ver todos los endpoints en: http://127.0.0.1:8000/docs

---

## 🎯 Resumen Rápido

```powershell
# 1. Ir a la raíz del proyecto
cd C:\Users\tu_usuario\Documents\TesisOMuerte

# 2. Crear y activar venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r proyecto/horarios_universidad/requirements.txt
pip install -e proyecto/horarios_universidad/

# 4. Instalar frontend
cd proyecto/horarios_universidad/frontend
npm install
cd ../..

# 5. Terminal 1 - Backend
cd proyecto/horarios_universidad
python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src

# 6. Terminal 2 - Frontend
cd proyecto/horarios_universidad/frontend
npm run dev -- --host 127.0.0.1

# 7. Abrir navegador
# http://127.0.0.1:5173/
```

---

## ❓ ¿Necesitas Ayuda?

Si encuentras problemas:
1. Verifica que todas las dependencias estén instaladas
2. Asegúrate de que los puertos 8000 y 5173 no estén en uso
3. Comprueba la conexión a internet si usas BD remota
4. Revisa los logs en las terminales para más detalles
