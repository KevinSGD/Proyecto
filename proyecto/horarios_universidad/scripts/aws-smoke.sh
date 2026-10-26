#!/usr/bin/env bash
# Prueba rapida de que el despliegue es factible: API, login y datos minimos.
#   bash aws-smoke.sh              solo lectura
#   WRITE=1 bash aws-smoke.sh      ademas crea y borra un edificio de prueba
# Variables: API_URL (por defecto la IP publica de la EC2), DIRECTOR_PASSWORD, NAME
set -uo pipefail

export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-scheduler}"
PASS="${DIRECTOR_PASSWORD:-director123}"
FAILS=0

if [ -z "${API_URL:-}" ]; then
  IP="$(aws ec2 describe-instances --filters "Name=tag:Name,Values=${NAME}-api" Name=instance-state-name,Values=running \
        --query 'Reservations[].Instances[].PublicIpAddress | [0]' --output text)"
  { [ -n "$IP" ] && [ "$IP" != "None" ]; } || { echo "No encuentro la EC2 '${NAME}-api'."; exit 1; }
  API_URL="http://$IP:8000"
fi
echo "API: $API_URL"

ok()   { printf '  [OK]    %s\n' "$*"; }
fail() { printf '  [FALTA] %s\n' "$*"; FAILS=$((FAILS+1)); }
jget() { python3 -c "import sys,json
try:
    d=json.load(sys.stdin)$1
    print(d if d is not None else '')
except Exception:
    print('')"; }
call() { # metodo ruta [json] -> cuerpo en $BODY, codigo en $CODE
  local out
  out="$(curl -s -m 20 -X "$1" -H "Authorization: Bearer ${TOK:-}" -H 'content-type: application/json' \
         ${3:+-d "$3"} -w $'\n%{http_code}' "$API_URL$2")" || true
  CODE="${out##*$'\n'}"; BODY="${out%$'\n'*}"
}

echo "== 1. Servicio"
call GET /health
[ "$CODE" = "200" ] && ok "GET /health -> 200" || { fail "GET /health -> $CODE (la API no responde)"; exit 1; }

echo "== 2. Login"
LOGIN="$(curl -s -m 20 -X POST -H 'content-type: application/json' \
         -d "{\"email\":\"director@udemo.edu\",\"password\":\"$PASS\"}" "$API_URL/api/v1/auth/login")"
TOK="$(echo "$LOGIN" | jget "['data']['tokens']['accessToken']")"
[ -n "$TOK" ] && ok "director@udemo.edu inicia sesion" || { fail "login fallo: $LOGIN"; exit 1; }
call GET /api/v1/auth/me
INST="$(echo "$BODY" | jget "['data']['institutionId']")"
[ -n "$INST" ] && ok "institucion $INST" || { fail "el usuario no tiene institucion"; exit 1; }

echo "== 3. Datos minimos para usar la app"
count() { echo "$BODY" | python3 -c "import sys,json
try: print(len(json.load(sys.stdin)['data']))
except Exception: print(0)"; }

call GET "/api/v1/institutions/$INST/campuses";       n="$(count)"
[ "$n" -ge 1 ] && ok "campus: $n" || fail "campus: 0  -> no se pueden crear edificios (422)"

call GET "/api/v1/institutions/$INST/periods/active"
P="$(echo "$BODY" | jget "['data']['name']")"
[ -n "$P" ] && ok "periodo academico activo: $P" || fail "sin periodo activo -> 'Confirmar oferta' se queda cargando"

call GET "/api/v1/institutions/$INST/schedule-types"; n="$(count)"
[ "$n" -ge 1 ] && ok "tipos de horario: $n" || fail "tipos de horario: 0  -> no se pueden aprobar ofertas"

call GET "/api/v1/institutions/$INST/areas";          n="$(count)"
[ "$n" -ge 1 ] && ok "areas academicas: $n" || fail "areas: 0  (se crean desde 'Areas Academicas')"

for r in subjects teachers classrooms; do
  call GET "/api/v1/institutions/$INST/$r"; n="$(count)"
  ok "$r: $n"
done

if [ "${WRITE:-0}" = "1" ]; then
  echo "== 4. Escritura (edificio de prueba, se borra al final)"
  call GET "/api/v1/institutions/$INST/campuses"
  CAMP="$(echo "$BODY" | jget "['data'][0]['id']")"
  if [ -z "$CAMP" ]; then fail "sin campus, no se puede probar la escritura"
  else
    CODE_T="SMOKE-$(date +%s)"
    call POST /api/v1/buildings "{\"campusId\":\"$CAMP\",\"name\":\"Prueba\",\"code\":\"$CODE_T\",\"floors\":1}"
    BID="$(echo "$BODY" | jget "['data']['id']")"
    if [ "$CODE" = "201" ] && [ -n "$BID" ]; then
      ok "crear edificio -> 201"
      call POST /api/v1/buildings "{\"campusId\":\"$CAMP\",\"name\":\"Prueba\",\"code\":\"$CODE_T\",\"floors\":1}"
      [ "$CODE" = "409" ] && ok "codigo repetido -> 409 (restriccion de la base funciona)" || fail "codigo repetido -> $CODE (esperado 409)"
      call DELETE "/api/v1/buildings/$BID"
      { [ "$CODE" = "200" ] || [ "$CODE" = "204" ]; } && ok "borrar edificio de prueba -> $CODE" || fail "no se pudo borrar el edificio de prueba ($CODE): $BID"
    else
      fail "crear edificio -> $CODE: $BODY"
    fi
  fi
fi

echo
if [ "$FAILS" -eq 0 ]; then echo "RESULTADO: TODO LISTO"; else echo "RESULTADO: $FAILS punto(s) por corregir (ver [FALTA])"; exit 1; fi
