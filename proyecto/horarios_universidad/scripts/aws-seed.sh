#!/usr/bin/env bash
# Carga los datos de demostracion en la base RDS (corre seed_demo dentro de la EC2).
# Es repetible: lo que ya existe se omite. Antes hace 'git pull' en la EC2.
#
# Uso (CloudShell):  bash ~/seed.sh
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
aws ec2-instance-connect send-ssh-public-key --instance-id "$INSTANCE_ID" \
  --instance-os-user ec2-user --ssh-public-key "file://$KEYDIR/k.pub" >/dev/null

echo "== Cargando datos de demostracion en $PUBLIC_IP"
ssh -i "$KEYDIR/k" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR -o ConnectTimeout=20 -o ServerAliveInterval=30 "ec2-user@$PUBLIC_IP" "sudo bash -s" <<'REMOTE'
set -euo pipefail
export HOME=/root
git -C /opt/scheduler pull --ff-only
cd /opt/scheduler/proyecto/horarios_universidad/backend
# La URL de la base la toma de backend/.env
.venv/bin/python -m scripts.seed_demo
REMOTE

echo
echo "LISTO. Entra al frontend y prueba:"
echo "  Director    : director@udemo.edu     / director123"
echo "  Coordinador : coordinador@udemo.edu  / coordinador123   (area Ciencias Basicas)"
