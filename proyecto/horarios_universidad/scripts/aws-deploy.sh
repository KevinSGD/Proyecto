#!/usr/bin/env bash
# Crea TODO en AWS desde CloudShell: security groups, RDS PostgreSQL, EC2 que
# clona el repo, crea las tablas (alembic) y deja la API corriendo como servicio.
#
# Uso (en AWS CloudShell, dentro del repo clonado):
#   bash proyecto/horarios_universidad/scripts/aws-deploy.sh
#
# Variables opcionales:
#   AWS_REGION=us-east-1   INSTANCE_TYPE=t3.medium   DB_CLASS=db.t4g.micro
#   NAME=scheduler         prefijo de todos los recursos
#   SEED_DEMO=1            carga tambien datos de demostracion
#   REPO_URL / BRANCH      por defecto se toman del repo clonado en CloudShell
#
# Idempotente: si algo ya existe lo reutiliza. La clave de la base se guarda en
# ~/.${NAME}-deploy.env (CloudShell conserva tu $HOME entre sesiones).
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-scheduler}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"
DB_CLASS="${DB_CLASS:-db.t4g.micro}"
DB_NAME="scheduler"
DB_USER="scheduler_admin"
DB_ID="${NAME}-db"
STATE="$HOME/.${NAME}-deploy.env"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO_URL="${REPO_URL:-$(git -C "$REPO_DIR" remote get-url origin)}"
BRANCH="${BRANCH:-$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)}"

step() { printf '\n== %s\n' "$*"; }
die()  { echo "ERROR: $*" >&2; exit 1; }

[ "$BRANCH" != "HEAD" ] || die "El repo esta en 'detached HEAD'. Haz 'git checkout <rama>' o pasa BRANCH=..."

step "Cuenta y repositorio"
aws sts get-caller-identity --query "Arn" --output text
echo "repo  : ${REPO_URL%%@*}  (rama: $BRANCH)" | sed -E 's#(https://)[^/]*@#\1***@#'
GIT_TERMINAL_PROMPT=0 git ls-remote --exit-code --heads "$REPO_URL" "$BRANCH" >/dev/null 2>&1 \
  || die "No se encuentra la rama '$BRANCH' en el remoto. ¿Hiciste 'git push'? Si el repo es privado usa REPO_URL=https://<token>@github.com/usuario/repo.git"

# ── Clave de la base (se genera una vez) ─────────────────────────────────────
if [ -f "$STATE" ]; then
  # shellcheck disable=SC1090
  . "$STATE"
else
  DB_PASSWORD="$(openssl rand -hex 16)"
  ( umask 077; echo "DB_PASSWORD=$DB_PASSWORD" > "$STATE" )
  echo "clave de la base generada y guardada en $STATE"
fi

# ── Red ──────────────────────────────────────────────────────────────────────
step "Red (VPC por defecto)"
VPC_ID="$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)"
[ "$VPC_ID" != "None" ] || die "No hay VPC por defecto en $AWS_DEFAULT_REGION."
SUBNET_ID="$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" Name=default-for-az,Values=true \
  --query 'Subnets[0].SubnetId' --output text)"
echo "vpc: $VPC_ID  subnet: $SUBNET_ID"

ensure_sg() {   # $1 nombre, $2 descripcion -> imprime el id
  local id
  id="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$1" "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[0].GroupId' --output text)"
  if [ "$id" = "None" ]; then
    id="$(aws ec2 create-security-group --group-name "$1" --description "$2" --vpc-id "$VPC_ID" \
          --tag-specifications "ResourceType=security-group,Tags=[{Key=project,Value=$NAME}]" \
          --query GroupId --output text)"
  fi
  echo "$id"
}

allow() {       # $1 sg, resto: argumentos de authorize-security-group-ingress; ignora reglas duplicadas
  local sg="$1" out; shift
  out="$(aws ec2 authorize-security-group-ingress --group-id "$sg" "$@" 2>&1)" \
    || { echo "$out" | grep -q 'InvalidPermission.Duplicate' || { echo "$out" >&2; exit 1; }; }
}

APP_SG="$(ensure_sg "${NAME}-app-sg" "Scheduler API (EC2)")"
DB_SG="$(ensure_sg "${NAME}-db-sg" "Scheduler PostgreSQL (RDS)")"
allow "$APP_SG" --protocol tcp --port 8000 --cidr 0.0.0.0/0
# SSH solo desde EC2 Instance Connect (boton "Conectar" de la consola), no desde internet
EIC_CIDR="$(curl -fsS https://ip-ranges.amazonaws.com/ip-ranges.json | python3 -c "
import json, os, sys
r = os.environ['AWS_DEFAULT_REGION']
print(next(p['ip_prefix'] for p in json.load(sys.stdin)['prefixes']
           if p['service'] == 'EC2_INSTANCE_CONNECT' and p['region'] == r))")"
allow "$APP_SG" --protocol tcp --port 22 --cidr "$EIC_CIDR"
# La base solo acepta conexiones desde la EC2 de la API
allow "$DB_SG" --protocol tcp --port 5432 --source-group "$APP_SG"
echo "app-sg: $APP_SG   db-sg: $DB_SG"

# ── RDS ──────────────────────────────────────────────────────────────────────
step "RDS PostgreSQL"
if aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
  echo "la instancia '$DB_ID' ya existe; se reutiliza"
else
  aws rds create-db-instance \
    --db-instance-identifier "$DB_ID" \
    --engine postgres --engine-version 16 \
    --db-instance-class "$DB_CLASS" \
    --allocated-storage 20 --storage-type gp3 --storage-encrypted \
    --db-name "$DB_NAME" \
    --master-username "$DB_USER" --master-user-password "$DB_PASSWORD" \
    --vpc-security-group-ids "$DB_SG" \
    --no-publicly-accessible --no-multi-az \
    --backup-retention-period 7 --copy-tags-to-snapshot \
    --tags "Key=project,Value=$NAME" >/dev/null
  echo "creando... (5-10 min)"
fi
aws rds wait db-instance-available --db-instance-identifier "$DB_ID"
DB_HOST="$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
  --query 'DBInstances[0].Endpoint.Address' --output text)"
DB_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"
echo "endpoint: $DB_HOST"

# ── EC2 ──────────────────────────────────────────────────────────────────────
step "EC2"
INSTANCE_ID="$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${NAME}-api" Name=instance-state-name,Values=pending,running,stopped,stopping \
  --query 'Reservations[].Instances[].InstanceId | [0]' --output text)"

if [ "$INSTANCE_ID" != "None" ] && [ -n "$INSTANCE_ID" ]; then
  echo "la EC2 '$INSTANCE_ID' ya existe; se reutiliza (para actualizar el codigo ver el README del despliegue)"
else
  AMI="$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
        --query Parameter.Value --output text)"

  USERDATA="$(mktemp)"
  cat > "$USERDATA" <<EOF
#!/bin/bash
export HOME=/root
exec > >(tee -a /var/log/scheduler-bootstrap.log) 2>&1
set -euxo pipefail
dnf install -y git python3.12 python3.12-pip
git clone --branch '${BRANCH}' --depth 1 '${REPO_URL}' /opt/scheduler
export SCHEDULER_DATABASE_URL='${DB_URL}'
export SEED=1 SEED_DEMO='${SEED_DEMO:-0}' PYTHON=python3.12
bash /opt/scheduler/proyecto/horarios_universidad/scripts/bootstrap.sh

cat > /etc/systemd/system/scheduler.service <<'UNIT'
[Unit]
Description=Scheduler API
After=network-online.target

[Service]
WorkingDirectory=/opt/scheduler/proyecto/horarios_universidad/backend
ExecStart=/opt/scheduler/proyecto/horarios_universidad/backend/.venv/bin/python -m uvicorn app.api.app:create_app --factory --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now scheduler
echo "BOOTSTRAP-OK"
EOF

  INSTANCE_ID="$(aws ec2 run-instances \
    --image-id "$AMI" --instance-type "$INSTANCE_TYPE" \
    --subnet-id "$SUBNET_ID" --security-group-ids "$APP_SG" --associate-public-ip-address \
    --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=20,VolumeType=gp3}' \
    --metadata-options HttpTokens=required \
    --user-data "file://$USERDATA" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${NAME}-api},{Key=project,Value=$NAME}]" \
    --query 'Instances[0].InstanceId' --output text)"
  rm -f "$USERDATA"
  echo "lanzada $INSTANCE_ID"
fi

aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
PUBLIC_IP="$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
echo "ip publica: $PUBLIC_IP"

# ── Esperar a que la API responda ────────────────────────────────────────────
step "Esperando a que la API arranque (instala dependencias y crea las tablas; ~5-8 min)"
for i in $(seq 1 60); do
  if curl -fsS -m 5 "http://$PUBLIC_IP:8000/health" >/dev/null 2>&1; then
    echo
    echo "LISTO"
    echo "  API    : http://$PUBLIC_IP:8000"
    echo "  Docs   : http://$PUBLIC_IP:8000/docs"
    echo "  Health : http://$PUBLIC_IP:8000/health"
    echo "  Login  : director@udemo.edu / director123   (cambia las claves tras entrar)"
    echo "  Base   : $DB_HOST  (clave en $STATE)"
    exit 0
  fi
  printf '.'; sleep 10
done
echo
die "La API no respondio en 10 min. Conectate a la EC2 (consola > Conectar) y revisa: sudo tail -n 80 /var/log/scheduler-bootstrap.log"
