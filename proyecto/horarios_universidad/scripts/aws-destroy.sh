#!/usr/bin/env bash
# Borra todo lo creado por aws-deploy.sh (EC2, RDS y security groups) para dejar de pagar.
# Antes de borrar RDS toma un snapshot final (SKIP_SNAPSHOT=1 para no tomarlo).
#
# Uso (CloudShell):  bash proyecto/horarios_universidad/scripts/aws-destroy.sh
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-scheduler}"
DB_ID="${NAME}-db"

echo "Se borrara en $AWS_DEFAULT_REGION: EC2 '${NAME}-api', RDS '$DB_ID' (con todos sus datos) y los security groups '${NAME}-*'."
read -r -p "Escribe 'borrar' para continuar: " ans
[ "$ans" = "borrar" ] || { echo "cancelado"; exit 1; }

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
fi

echo "== RDS"
if aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
  if [ "${SKIP_SNAPSHOT:-0}" = "1" ]; then
    aws rds delete-db-instance --db-instance-identifier "$DB_ID" --skip-final-snapshot >/dev/null
  else
    aws rds delete-db-instance --db-instance-identifier "$DB_ID" \
      --final-db-snapshot-identifier "${DB_ID}-final-$(date +%Y%m%d%H%M%S)" >/dev/null
  fi
  aws rds wait db-instance-deleted --db-instance-identifier "$DB_ID"
  echo "RDS borrada"
fi

echo "== Security groups"
for sg in "${NAME}-db-sg" "${NAME}-app-sg"; do      # primero la de la base: referencia a la de la app
  id="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$sg" \
        --query 'SecurityGroups[0].GroupId' --output text)"
  if [ "$id" != "None" ]; then aws ec2 delete-security-group --group-id "$id" && echo "borrado $sg"; fi
done

rm -f "$HOME/.${NAME}-deploy.env"
echo "Listo. (Los snapshots finales de RDS, si existen, se cobran aparte hasta que los borres.)"
