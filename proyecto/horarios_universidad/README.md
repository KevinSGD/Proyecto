# Horarios Universidad

Generador de horarios académicos con backend en FastAPI y frontend en Vue 3.

---

## 📋 Requisitos Previos

Asegúrate de tener instalado:

- **Python 3.10+**
- **Node.js 18+**
- **npm**

---

## 🏗️ Estructura del Proyecto

```
horarios_universidad/
├── src/scheduler/              # Backend Python
│   ├── config/                 # Configuración
│   ├── application/            # Casos de uso y ensamblaje de datos
│   ├── infrastructure/         # OR-Tools y exportadores
│   │   ├── optimization/       # Solver OR-Tools
│   │   └── exporters/          # Exportador Excel
│   └── interfaces/             # API FastAPI y CLI
├── frontend/                   # Frontend Vue 3 + Vite
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── requirements.txt            # Dependencias Python
├── pyproject.toml              # Configuración del paquete
└── README.md                   # Este archivo
```

---

## 🚀 Instalación Completa (Primera Vez)

### Paso 1: Crear Entorno Virtual Python

Desde este directorio (`proyecto/horarios_universidad`):

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Si obtienes error de permisos:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Paso 2: Instalar Dependencias Python

```powershell
# Actualizar pip
python -m pip install -U pip

# Instalar dependencias
pip install -r requirements.txt

# Instalar paquete en modo editable
pip install -e .
```

### Paso 3: Instalar Dependencias Frontend

```powershell
cd frontend

npm install

cd ..
```

---

## ▶️ Ejecutar la Aplicación

### Opción A: Dos Terminales (Recomendado)

**Terminal 1 - Backend:**

```powershell
# Asegúrate de estar en proyecto/horarios_universidad
# Con el venv activado
python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Terminal 2 - Frontend:**

```powershell
# Abre otra terminal en el mismo directorio
cd frontend
npm run dev -- --host 127.0.0.1
```

Deberías ver:
```
➜  Local:   http://127.0.0.1:5173/
```

### Opción B: Ejecutar Manualmente

Si prefieres más control:

**Backend:**
```powershell
# Asegúrate de que .venv esté activado
uvicorn scheduler.interfaces.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

---

## 🌐 Acceder a la Aplicación

| Componente | URL |
|---|---|
| **Frontend** | http://127.0.0.1:5173/ |
| **API Backend** | http://127.0.0.1:8000 |
| **Swagger UI (Docs)** | http://127.0.0.1:8000/docs |
| **ReDoc** | http://127.0.0.1:8000/redoc |

---

## 🔐 Configurar Variables de Entorno (Opcional)

Si necesitas conectar a una base de datos:

```powershell
# Base de datos PostgreSQL
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "horarios"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "password"

# O si usas Railway
$env:RAILWAY_RUN_URL = "https://tu-servicio.railway.app/run"
```

---

## ✅ Verificar que Funciona

### 1. Verificar Backend

```powershell
curl http://127.0.0.1:8000/health
```

O desde PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

### 2. Acceder a Swagger UI

Abre: http://127.0.0.1:8000/docs

Aquí puedes probar los endpoints interactivamente.

---

## 🛑 Detener la Aplicación

En cada terminal presiona:

```
CTRL + C
```

Para desactivar el entorno virtual:

```powershell
deactivate
```

---

## 🔧 Solución de Problemas

### "El archivo de script no se encontró"

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### "No module named 'scheduler'"

```powershell
pip install -e .
```

### "Port 8000 already in use"

Otro proceso usa el puerto 8000:

```powershell
# En PowerShell, busca qué está usando el puerto
netstat -ano | findstr :8000

# Mata el proceso (reemplaza PID con el número)
taskkill /PID <PID> /F

# O cambia el puerto en el comando uvicorn
```

### "npm install falla"

```powershell
# Limpia caché
npm cache clean --force

# Intenta de nuevo
npm install
```

---

## 📚 Endpoints Principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Verifica que la API esté viva |
| `GET` | `/db/health` | Verifica conexión a BD |
| `POST` | `/run` | Genera el horario |

Ver documentación completa en: http://127.0.0.1:8000/docs

---

## 🎯 Resumen Rápido

```powershell
# 1. Crear y activar venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
python -m pip install -U pip
pip install -r requirements.txt
pip install -e .

# 3. Instalar frontend
cd frontend
npm install
cd ..

# 4. Terminal 1 - Backend
python -m uvicorn scheduler.interfaces.api.main:app --reload --host 127.0.0.1 --port 8000 --app-dir src

# 5. Terminal 2 - Frontend (otra terminal)
cd frontend
npm run dev -- --host 127.0.0.1

# 6. Abrir navegador
# http://127.0.0.1:5173/
```

---

## 🔄 Hot Reload

Ambos servidores están configurados para hot reload:

- **Backend**: Cualquier cambio en `src/` recarga automáticamente
- **Frontend**: Cualquier cambio en `frontend/src/` se refleja al instante

Si no funciona, reinicia los servidores.

---

## 📝 Desarrollo

### Agregar Dependencias Python

```powershell
pip install nombre-paquete
pip freeze > requirements.txt
```

### Agregar Dependencias Frontend

```powershell
cd frontend
npm install nombre-paquete
cd ..
```

---

## ✨ Características

- **Backend**: FastAPI con validación automática
- **Frontend**: Vue 3 con Vite (rápido y moderno)
- **Optimización**: OR-Tools para resolver horarios complejos
- **Exportación**: Excel con formatos profesionales
- **API**: Documentación interactiva automática

---

## 🆘 ¿Necesitas Ayuda?

1. Verifica que todas las dependencias estén instaladas
2. Asegúrate de usar Python 3.10+ y Node.js 18+
3. Revisa los logs en las terminales
4. Verifica que los puertos 8000 y 5173 estén disponibles
- Healthcheck: `http://127.0.0.1:8000/health`

Si usas base de datos, define las variables de entorno en el mismo terminal antes de ejecutar el script:

```powershell
$env:DB_HOST = "..."
$env:DB_PORT = "5432"
$env:DB_NAME = "postgres"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "..."
$env:DB_SSLMODE = "require"
```

## Ejecutar frontend

Desde `proyecto/horarios_universidad` en otro terminal PowerShell:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Esto inicia Vite y abre la interfaz en un puerto local, normalmente:

- `http://127.0.0.1:5173` (o el siguiente puerto libre)

## Flujo de uso

1. Inicia el backend con el comando `python -m uvicorn ... --app-dir src`.
2. Inicia el frontend con `npm run dev -- --host 127.0.0.1` desde `frontend/`.
3. Abre la URL local que indique Vite y usa la aplicación.

## Notas

- El frontend se comunica con el backend a través del proxy de Vite.
- No es necesario un archivo `.env.example` para ejecutar el proyecto.
