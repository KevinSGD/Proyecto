#!/usr/bin/env bash
# Actualiza la EC2 creada por aws-deploy.sh desde CloudShell:
#   - git pull del repo y migraciones (alembic) del backend
#   - compila y publica el frontend (Next.js) en el puerto 3000
#   - configura CORS para que el frontend pueda llamar a la API
#
# Uso (CloudShell, dentro del repo clonado):
#   git pull && bash proyecto/horarios_universidad/scripts/aws-update.sh
#
# Se conecta por SSH con una llave temporal (EC2 Instance Connect, valida 60 s) y
# abre el puerto 22 solo para la IP actual de CloudShell mientras dura el script.
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-scheduler}"
NODE_VERSION="${NODE_VERSION:-22.11.0}"

die() { echo "ERROR: $*" >&2; exit 1; }
command -v ssh >/dev/null && command -v ssh-keygen >/dev/null || die "Falta el cliente ssh en este entorno."

INSTANCE_ID="$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${NAME}-api" Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].InstanceId | [0]' --output text)"
{ [ -n "$INSTANCE_ID" ] && [ "$INSTANCE_ID" != "None" ]; } || die "No hay una EC2 '${NAME}-api' en ejecucion. Corre primero aws-deploy.sh."
PUBLIC_IP="$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
APP_SG="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${NAME}-app-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)"
echo "EC2 $INSTANCE_ID  ip $PUBLIC_IP  sg $APP_SG"

allow() {   # ignora reglas duplicadas
  local out
  out="$(aws ec2 authorize-security-group-ingress --group-id "$APP_SG" "$@" 2>&1)" \
    || { echo "$out" | grep -q 'InvalidPermission.Duplicate' || { echo "$out" >&2; exit 1; }; }
}

MY_CIDR="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')/32"
KEYDIR="$(mktemp -d)"
cleanup() {
  aws ec2 revoke-security-group-ingress --group-id "$APP_SG" --protocol tcp --port 22 --cidr "$MY_CIDR" >/dev/null 2>&1 || true
  rm -rf "$KEYDIR"
}
trap cleanup EXIT

allow --protocol tcp --port 3000 --cidr 0.0.0.0/0     # frontend
allow --protocol tcp --port 22 --cidr "$MY_CIDR"      # SSH desde CloudShell, solo durante el script

ssh-keygen -q -t ed25519 -N '' -f "$KEYDIR/k"
aws ec2-instance-connect send-ssh-public-key --instance-id "$INSTANCE_ID" \
  --instance-os-user ec2-user --ssh-public-key "file://$KEYDIR/k.pub" >/dev/null

echo "== Conectando y desplegando (3-6 min)"
ssh -i "$KEYDIR/k" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=20 -o ServerAliveInterval=30 "ec2-user@$PUBLIC_IP" \
    "sudo env PUBLIC_IP=$PUBLIC_IP NODE_VERSION=$NODE_VERSION bash -s" <<'REMOTE'
set -euo pipefail
export HOME=/root
ROOT=/opt/scheduler/proyecto/horarios_universidad
B=$ROOT/backend
F=$ROOT/frontend/app

echo "-- codigo"
git -C /opt/scheduler pull --ff-only

echo "-- backend: dependencias y migraciones"
export SCHEDULER_DATABASE_URL="$(grep '^SCHEDULER_DATABASE_URL=' "$B/.env" | cut -d= -f2-)"
PYTHON=python3.12 bash "$ROOT/scripts/bootstrap.sh"
sed -i '/^SCHEDULER_CORS_ORIGINS=/d' "$B/.env"
echo "SCHEDULER_CORS_ORIGINS=[\"http://$PUBLIC_IP:3000\",\"http://localhost:3000\"]" >> "$B/.env"

echo "-- node $NODE_VERSION"
if [ ! -x /opt/node/bin/node ] || ! /opt/node/bin/node -v | grep -q "v$NODE_VERSION"; then
  rm -rf /opt/node && mkdir -p /opt/node
  curl -fsSL "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz" | tar -xJ -C /opt/node --strip-components=1
fi
export PATH=/opt/node/bin:$PATH

echo "-- frontend: compilando"
cd "$F"
export NEXT_PUBLIC_API_URL="http://$PUBLIC_IP:8000"
npm ci --no-audit --no-fund
npm run build

cat > /etc/systemd/system/scheduler-web.service <<UNIT
[Unit]
Description=Scheduler frontend (Next.js)
After=network-online.target

[Service]
WorkingDirectory=$F
Environment=PATH=/opt/node/bin:/usr/bin
Environment=NODE_ENV=production
ExecStart=/opt/node/bin/node node_modules/next/dist/bin/next start -H 0.0.0.0 -p 3000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable scheduler scheduler-web
systemctl restart scheduler scheduler-web
echo "REMOTE-OK"
REMOTE

echo "== Comprobando"
for i in $(seq 1 30); do
  api="$(curl -s -o /dev/null -w '%{http_code}' -m 5 "http://$PUBLIC_IP:8000/health" || true)"
  web="$(curl -s -o /dev/null -w '%{http_code}' -m 5 "http://$PUBLIC_IP:3000/login" || true)"
  [ "$api" = "200" ] && [ "$web" = "200" ] && break
  sleep 5
done
echo "API: $api   Frontend: $web"
[ "$api" = "200" ] && [ "$web" = "200" ] || die "Alguno no respondio. En la EC2: sudo journalctl -u scheduler -u scheduler-web -n 60"
echo
echo "LISTO"
echo "  Frontend : http://$PUBLIC_IP:3000"
echo "  API docs : http://$PUBLIC_IP:8000/docs"
echo "  Login    : director@udemo.edu / director123"
