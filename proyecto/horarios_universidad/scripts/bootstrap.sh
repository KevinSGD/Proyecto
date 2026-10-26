#!/usr/bin/env bash
# Prepara el backend en un servidor Linux (EC2) y crea las tablas en RDS.
#
# Uso (tras clonar el repo en la instancia):
#   export SCHEDULER_DATABASE_URL='postgresql+psycopg://USER:PASS@ENDPOINT:5432/scheduler?sslmode=require'
#   bash proyecto/horarios_universidad/scripts/bootstrap.sh
#
# Variables opcionales:
#   SCHEDULER_SECRET_KEY  clave JWT; si no existe se genera una y se guarda en backend/.env
#   SEED=1                crea roles y usuarios iniciales (seed_auth)
#   SEED_DEMO=1           ademas carga datos de demostracion (seed_demo)
#   RUN=1                 al terminar arranca la API en 0.0.0.0:8000
#   PYTHON=...            interprete a usar (Python >= 3.12)
#   SKIP_INSTALL=1        no crea el venv ni instala dependencias (usa $PYTHON tal cual)
#
# Idempotente: se puede ejecutar de nuevo tras cada 'git pull'; alembic solo
# aplica las migraciones que falten.
set -euo pipefail

BACKEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND"

: "${SCHEDULER_DATABASE_URL:?Define SCHEDULER_DATABASE_URL (postgresql+psycopg://user:pass@endpoint:5432/db?sslmode=require)}"
case "$SCHEDULER_DATABASE_URL" in
  postgresql*) ;;
  *) echo "ERROR: SCHEDULER_DATABASE_URL debe ser PostgreSQL (empieza por postgresql)." >&2; exit 1 ;;
esac

# ── Python y dependencias ────────────────────────────────────────────────────
if [ "${SKIP_INSTALL:-0}" = "1" ]; then
  PY="${PYTHON:?Con SKIP_INSTALL=1 debes indicar PYTHON}"
else
  BASE_PY="${PYTHON:-}"
  if [ -z "$BASE_PY" ]; then
    for c in python3.13 python3.12 python3; do
      if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 12))'; then
        BASE_PY="$c"; break
      fi
    done
  fi
  if [ -z "$BASE_PY" ]; then
    echo "ERROR: se necesita Python >= 3.12. En Amazon Linux 2023: sudo dnf install -y python3.12" >&2
    echo "       En Ubuntu 24.04 ya viene python3.12 (sudo apt install -y python3-venv)." >&2
    exit 1
  fi
  [ -d .venv ] || "$BASE_PY" -m venv .venv
  if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=.venv/Scripts/python.exe; fi
  echo "== Instalando dependencias"
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet -e .
fi

# ── .env (clave JWT y URL de la base) ────────────────────────────────────────
if [ ! -f .env ]; then
  SECRET="${SCHEDULER_SECRET_KEY:-$("$PY" -c 'import secrets; print(secrets.token_hex(32))')}"
  umask 077
  {
    echo "SCHEDULER_DATABASE_URL=$SCHEDULER_DATABASE_URL"
    echo "SCHEDULER_SECRET_KEY=$SECRET"
  } > .env
  echo "== backend/.env creado (permisos 600)"
else
  echo "== backend/.env ya existe; no se modifica"
fi

# ── Esperar a la base ────────────────────────────────────────────────────────
echo "== Comprobando conexion a la base"
"$PY" - <<'PYEOF'
import os, sys, time
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["SCHEDULER_DATABASE_URL"])
last = None
for attempt in range(30):
    try:
        with engine.connect() as conn:
            print("conectado:", conn.execute(text("select version()")).scalar().split(",")[0])
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        last = exc
        time.sleep(5)
print("ERROR: no se pudo conectar a la base tras 150 s:", last, file=sys.stderr)
print("Revisa el security group de RDS (puerto 5432 desde esta instancia) y la URL.", file=sys.stderr)
sys.exit(1)
PYEOF

# ── Tablas ───────────────────────────────────────────────────────────────────
echo "== Aplicando migraciones (alembic upgrade head)"
"$PY" -m alembic upgrade head
"$PY" -m alembic current

if [ "${SEED:-0}" = "1" ] || [ "${SEED_DEMO:-0}" = "1" ]; then
  echo "== Seed inicial"
  "$PY" -m scripts.seed_auth
fi
if [ "${SEED_DEMO:-0}" = "1" ]; then
  "$PY" -m scripts.seed_demo
fi

echo
echo "Listo. Para arrancar la API:"
echo "  cd $BACKEND && $PY -m uvicorn app.api.app:create_app --factory --host 0.0.0.0 --port 8000"

if [ "${RUN:-0}" = "1" ]; then
  exec "$PY" -m uvicorn app.api.app:create_app --factory --host 0.0.0.0 --port 8000
fi
