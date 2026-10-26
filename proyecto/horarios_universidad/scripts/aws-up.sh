#!/usr/bin/env bash
# Levanta TODO desde cero en AWS con un solo comando (desde CloudShell, dentro del repo clonado):
#   1. aws-deploy.sh : security groups, RDS PostgreSQL, EC2 con la API y las tablas
#   2. aws-update.sh : frontend (puerto 3000), CORS y limites del solver
#   3. datos         : segun MODE
#   4. aws-smoke.sh  : comprueba que todo quedo usable
#
# Uso:
#   bash proyecto/horarios_universidad/scripts/aws-up.sh              # MODE=reiniciar (recomendado)
#   MODE=demo bash proyecto/horarios_universidad/scripts/aws-up.sh    # datos demo completos (2 areas)
#   MODE=ninguno bash ...                                             # sin cargar datos
#
# MODE=reiniciar deja UNA area (Ingenieria) con una oferta aprobada: la corrida sale factible a la primera.
# Tarda ~20-25 min (la RDS son 5-10 min). El codigo debe estar subido a GitHub (git push).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${MODE:-reiniciar}"

echo "################ 1/4 Infraestructura (RDS + EC2)"
bash "$HERE/aws-deploy.sh"

echo "################ 2/4 Frontend, CORS y solver"
bash "$HERE/aws-update.sh"

echo "################ 3/4 Datos (MODE=$MODE)"
case "$MODE" in
  reiniciar) bash "$HERE/aws-db.sh" sql "$(cat "$HERE/../backend/db/reiniciar_base.sql")" ;;
  demo)      bash "$HERE/aws-seed.sh" ;;
  ninguno)   echo "sin cargar datos" ;;
  *) echo "MODE desconocido: $MODE (usa reiniciar | demo | ninguno)" >&2; exit 1 ;;
esac

echo "################ 4/4 Comprobacion"
WRITE=1 bash "$HERE/aws-smoke.sh"
