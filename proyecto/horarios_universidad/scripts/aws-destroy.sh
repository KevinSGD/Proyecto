#!/usr/bin/env bash
# Borra TODO lo creado por aws-deploy.sh para dejar de pagar:
#   EC2 (y su disco), RDS (y sus backups automaticos), snapshots manuales y security groups.
# Al final verifica que no quede nada que cobre.
#
# Uso (CloudShell):
#   bash proyecto/horarios_universidad/scripts/aws-destroy.sh
#
# Variables:
#   SNAPSHOT=1   toma un snapshot final de la base y NO lo borra (los snapshots cobran por GB-mes)
#   FORCE=1      no pide confirmacion
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-scheduler}"
DB_ID="${NAME}-db"

echo "Se BORRARA en $AWS_DEFAULT_REGION (sin posibilidad de recuperarlo):"
echo "  - EC2 '${NAME}-api' y su disco"
echo "  - RDS '$DB_ID' con TODOS sus datos y backups automaticos"
echo "  - snapshots manuales de '$DB_ID' (salvo con SNAPSHOT=1)"
echo "  - security groups '${NAME}-*'"
if [ "${FORCE:-0}" != "1" ]; then
  read -r -p "Escribe 'borrar' para continuar: " ans
  [ "$ans" = "borrar" ] || { echo "cancelado"; exit 1; }
fi

echo "== EC2"
IDS="$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${NAME}-api" Name=instance-state-name,Values=pending,running,stopped,stopping \
  --query 'Reservations[].Instances[].InstanceId' --output text)"
if [ -n "$IDS" ]; then
  # shellcheck disable=SC2086
  aws ec2 terminate-instances --instance-ids $IDS >/dev/null
  # shellcheck disable=SC2086
  aws ec2 wait instance-terminated --instance-ids $IDS
  echo "terminada: $IDS"
else
  echo "no hay instancia"
fi

echo "== RDS"
if aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
  if [ "${SNAPSHOT:-0}" = "1" ]; then
    aws rds delete-db-instance --db-instance-identifier "$DB_ID" --delete-automated-backups \
      --final-db-snapshot-identifier "${DB_ID}-final-$(date +%Y%m%d%H%M%S)" >/dev/null
  else
    aws rds delete-db-instance --db-instance-identifier "$DB_ID" --delete-automated-backups \
      --skip-final-snapshot >/dev/null
  fi
  echo "borrando RDS (3-10 min)..."
  aws rds wait db-instance-deleted --db-instance-identifier "$DB_ID"
  echo "RDS borrada"
else
  echo "no hay base"
fi

if [ "${SNAPSHOT:-0}" != "1" ]; then
  echo "== Snapshots manuales de $DB_ID"
  SNAPS="$(aws rds describe-db-snapshots --snapshot-type manual \
    --query "DBSnapshots[?DBInstanceIdentifier=='$DB_ID'].DBSnapshotIdentifier" --output text)"
  for s in $SNAPS; do
    aws rds delete-db-snapshot --db-snapshot-identifier "$s" >/dev/null && echo "borrado snapshot $s"
  done
fi

echo "== Security groups"
for sg in "${NAME}-db-sg" "${NAME}-app-sg"; do      # primero la de la base: referencia a la de la app
  id="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$sg" \
        --query 'SecurityGroups[0].GroupId' --output text)"
  [ "$id" != "None" ] || continue
  for try in $(seq 1 12); do                       # la interfaz de red tarda un poco en liberarse
    if aws ec2 delete-security-group --group-id "$id" >/dev/null 2>&1; then echo "borrado $sg"; break; fi
    [ "$try" -lt 12 ] && sleep 10 || echo "AVISO: no se pudo borrar $sg ($id); reintenta en unos minutos"
  done
done

rm -f "$HOME/.${NAME}-deploy.env"

echo
echo "== Verificacion (en $AWS_DEFAULT_REGION). Todo lo que aparezca aqui puede cobrar:"
LEFT=0
show() { # titulo, salida
  if [ -n "$2" ]; then echo "  [!] $1:"; echo "$2" | sed 's/^/        /'; LEFT=1; else echo "  [ok] sin $1"; fi
}
show "instancias EC2 activas o detenidas" "$(aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType]' --output text)"
show "bases RDS" "$(aws rds describe-db-instances --query 'DBInstances[].[DBInstanceIdentifier,DBInstanceStatus]' --output text)"
show "snapshots manuales de RDS" "$(aws rds describe-db-snapshots --snapshot-type manual --query 'DBSnapshots[].DBSnapshotIdentifier' --output text)"
show "volumenes EBS" "$(aws ec2 describe-volumes --query 'Volumes[].[VolumeId,State,Size]' --output text)"
show "IPs elasticas" "$(aws ec2 describe-addresses --query 'Addresses[].PublicIp' --output text)"
echo
if [ "$LEFT" -eq 0 ]; then echo "LISTO: no queda nada que genere cobro en $AWS_DEFAULT_REGION."; else echo "Revisa los puntos [!] de arriba."; fi
