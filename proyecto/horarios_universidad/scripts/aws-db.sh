#!/usr/bin/env bash
# Mira la base de datos RDS desde CloudShell (entra a la EC2, que es la que llega a RDS).
#
#   bash aws-db.sh                      resumen: version, migracion y filas por tabla
#   bash aws-db.sh sql "select ..."     ejecuta una consulta SQL
#   bash aws-db.sh shell                psql interactivo (salir con \q)
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-scheduler}"
die() { echo "ERROR: $*" >&2; exit 1; }
command -v ssh >/dev/null || die "Falta el cliente ssh en este entorno."

INSTANCE_ID="$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${NAME}-api" Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].InstanceId | [0]' --output text)"
{ [ -n "$INSTANCE_ID" ] && [ "$INSTANCE_ID" != "None" ]; } || die "No hay una EC2 '${NAME}-api' en ejecucion."
PUBLIC_IP="$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
APP_SG="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${NAME}-app-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)"

MY_CIDR="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')/32"
KEYDIR="$(mktemp -d)"
cleanup() {
  aws ec2 revoke-security-group-ingress --group-id "$APP_SG" --protocol tcp --port 22 --cidr "$MY_CIDR" >/dev/null 2>&1 || true
  rm -rf "$KEYDIR"
}
trap cleanup EXIT

out="$(aws ec2 authorize-security-group-ingress --group-id "$APP_SG" --protocol tcp --port 22 --cidr "$MY_CIDR" 2>&1)" \
  || { echo "$out" | grep -q 'InvalidPermission.Duplicate' || die "$out"; }
ssh-keygen -q -t ed25519 -N '' -f "$KEYDIR/k"

rssh() {   # la llave de Instance Connect dura 60 s, asi que se envia antes de cada conexion
  aws ec2-instance-connect send-ssh-public-key --instance-id "$INSTANCE_ID" \
    --instance-os-user ec2-user --ssh-public-key "file://$KEYDIR/k.pub" >/dev/null
  ssh -i "$KEYDIR/k" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o LogLevel=ERROR -o ConnectTimeout=20 -o ServerAliveInterval=30 "$@"
}

# Prepara psql y un comando 'scheduler-psql' en la EC2 (solo la primera vez instala algo)
rssh "ec2-user@$PUBLIC_IP" "sudo bash -s" <<'SETUP'
set -euo pipefail
command -v psql >/dev/null || dnf install -y postgresql16 >/dev/null
cat > /usr/local/bin/scheduler-psql <<'WRAP'
#!/bin/bash
URL="$(grep '^SCHEDULER_DATABASE_URL=' /opt/scheduler/proyecto/horarios_universidad/backend/.env | cut -d= -f2- | sed 's/+psycopg//')"
exec psql "$URL" -X -P pager=off "$@"
WRAP
chmod 755 /usr/local/bin/scheduler-psql
SETUP

MODE="${1:-resumen}"
case "$MODE" in
  shell)
    rssh -t "ec2-user@$PUBLIC_IP" "sudo scheduler-psql"
    ;;
  sql)
    [ -n "${2:-}" ] || die 'Uso: aws-db.sh sql "select * from users;"'
    rssh "ec2-user@$PUBLIC_IP" "sudo scheduler-psql -c $(printf '%q' "$2")"
    ;;
  resumen)
    SQL="select version() as servidor;
select version_num as migracion_alembic from alembic_version;
select table_name as tabla,
       (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I', table_name), false, true, '')))[1]::text::int as filas
from information_schema.tables
where table_schema = 'public' and table_type = 'BASE TABLE'
order by 2 desc, 1;"
    rssh "ec2-user@$PUBLIC_IP" "sudo scheduler-psql -c $(printf '%q' "$SQL")"
    ;;
  *) die "Modo desconocido '$MODE'. Usa: resumen | sql \"...\" | shell" ;;
esac
