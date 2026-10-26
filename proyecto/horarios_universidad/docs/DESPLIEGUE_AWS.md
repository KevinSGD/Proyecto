# Despliegue en AWS: informe de correcciones y paso a paso

Arquitectura: **1 EC2** (API FastAPI en el puerto 8000 + frontend Next.js en el 3000) y **1 RDS PostgreSQL 16**
privada, en `us-east-1`. Todo se crea y se borra con scripts desde **AWS CloudShell**.

---

## 1. Informe: qué hubo que corregir en la base para que todo funcionara

Al crear la base solo existían las tablas y los usuarios del seed inicial. Faltaban datos que la aplicación da
por hechos. Cada fila es un fallo real que apareció, su causa y cómo queda resuelto.

| # | Síntoma en la app | Dato que faltaba (RDS) | Cómo se arregla ahora |
|---|---|---|---|
| 1 | Al crear un edificio: **422** ("Error al guardar edificio"). El frontend mandaba `campusId: ""`. | **Campus.** Solo `seed_demo` lo creaba y no hay pantalla ni endpoint para crearlo. | `seed_auth` crea el campus `MAIN`; `CreateInstitution` crea un campus por defecto; el frontend avisa si no hay campus. |
| 2 | Al aprobar una oferta: "Error al aprobar. Solo ofertas enviadas pueden aprobarse." (mensaje engañoso). Causa real: *No hay ningún tipo de horario*. | **Tipo de horario** ("Diurno"). Aprobar genera los grupos y los necesita. | `seed_auth` crea el tipo de horario `Diurno`; la pantalla ahora muestra el error real del backend. |
| 3 | Coordinador: "Preparando oferta académica del área…" **para siempre**. | **Período académico activo** (o el área del usuario). La página salía sin apagar el estado de carga. | `seed_demo` / `reiniciar_base.sql` crean un período activo; la pantalla ahora dice qué falta. |
| 4 | Coordinador: "Tu usuario no tiene un área asignada". | Fila en **`user_areas`** que liga al coordinador con su área. | `seed_demo` y `reiniciar_base.sql` la crean. |
| 5 | Generar horario: corrida **`infeasible`** (V-01 "grupo sin docente", V-02 "sin aula compatible"). | **Contratos** de docentes, **disponibilidad** de docentes y aulas (Lun-Vie, periodos 1-12), **especialidades** (docente ↔ materia), **capacidad** de aulas ≥ matrícula, **recursos** requeridos. | `completar_datos.sql` agrega lo que falte; `respaldo_datos.sql` agrega 2 docentes y 2 aulas de respaldo; `reiniciar_base.sql` deja un conjunto ya completo. |
| 6 | Generar horario: corrida **`timeout`** (a veces `feasible`, a veces no). | No es un dato: el solver tenía **10 s y 8 hilos** en una máquina de 2 CPU. | `aws-update.sh` fija `SCHEDULER_SOLVER_MAX_TIME_SECONDS=60` y `SCHEDULER_SOLVER_NUM_WORKERS=2` en la EC2. |
| 7 | Duplicados (código/correo repetido) devolvían el 409 genérico en vez de "Ya existe un registro…". | No es un dato: el manejador solo entendía el mensaje de SQLite y no el de PostgreSQL (que puede venir en español). | Corregido en `error_handler.py` (usa el código SQLSTATE 23505, independiente del idioma). |

### Cómo diagnosticar cada caso (sin adivinar)
```bash
bash ~/db.sh sql "select name, status, statistics->'errors' as errores from schedule_runs order by started_at desc limit 3;"
bash ~/smoke.sh        # dice [FALTA] campus / periodo activo / tipos de horario / areas
```

### Configuración que hubo que ajustar en la EC2 (`backend/.env`)
| Variable | Valor | Para qué |
|---|---|---|
| `SCHEDULER_DATABASE_URL` | `postgresql+psycopg://…@<endpoint>:5432/scheduler?sslmode=require` | la crea `bootstrap.sh` |
| `SCHEDULER_SECRET_KEY` | aleatoria (la genera `bootstrap.sh`) | firma de los JWT |
| `SCHEDULER_CORS_ORIGINS` | `["http://<IP-EC2>:3000","http://localhost:3000"]` | que el frontend pueda llamar a la API (lo pone `aws-update.sh`) |
| `SCHEDULER_SOLVER_MAX_TIME_SECONDS` | `60` | evitar `timeout` |
| `SCHEDULER_SOLVER_NUM_WORKERS` | `2` | igualar los 2 vCPU de la `t3.medium` |

El frontend se compila con `NEXT_PUBLIC_API_URL=http://<IP-EC2>:8000` (lo hace `aws-update.sh`).

---

## 2. Levantar todo desde cero (un comando)

Requisitos: el código debe estar en GitHub (`git push` de la rama) y estar en **AWS CloudShell**, región **us-east-1**.

```bash
git clone --branch claude/loving-ptolemy-jd2mwy https://github.com/KevinSGD/Proyecto.git
cd Proyecto
bash proyecto/horarios_universidad/scripts/aws-up.sh
```

`aws-up.sh` ejecuta en orden (≈ 20-25 min, casi todo es esperar a la RDS):

1. `aws-deploy.sh`: security groups, RDS, EC2; crea las tablas (Alembic) y los usuarios iniciales.
2. `aws-update.sh`: frontend en el puerto 3000, CORS y límites del solver.
3. Datos, según `MODE`:
   - `MODE=reiniciar` (por defecto): **una sola área** (Ingeniería) con una oferta ya aprobada → la corrida sale factible a la primera.
   - `MODE=demo`: datos de demostración completos (2 áreas).
   - `MODE=ninguno`: sin datos.
4. `aws-smoke.sh`: comprueba API, login, campus, período, tipos de horario, áreas y escritura.

```bash
MODE=demo bash proyecto/horarios_universidad/scripts/aws-up.sh     # variante con 2 áreas
```

Al terminar imprime las direcciones (`http://<IP>:3000` y `http://<IP>:8000/docs`).

### Credenciales (con `MODE=reiniciar`)
| Rol | Email | Contraseña | Área |
|---|---|---|---|
| Director | `director@udemo.edu` | `director123` | todas |
| Coordinador | `coordinador@udemo.edu` | `coordinador123` | Ingeniería |

Con `MODE=demo` el coordinador queda en Ciencias Básicas. Son contraseñas de **prueba**: la API es pública
(puerto 8000 abierto) y sin HTTPS; cámbialas si vas a compartir la dirección.

### Probar el flujo
1. Director → **Generar Horarios** → lanzar corrida. Debe terminar en `feasible` (5 asignaciones con `reiniciar`).
2. Para repetir todo el proceso: coordinador → Confirmar Oferta (envía) → director → Oferta Académica → Aprobar.
   (La oferta que deja `reiniciar` ya viene aprobada.)

### Paso a paso manual (si prefieres no usar `aws-up.sh`)
```bash
cd ~/Proyecto
bash proyecto/horarios_universidad/scripts/aws-deploy.sh          # 1) infraestructura + tablas
bash proyecto/horarios_universidad/scripts/aws-update.sh          # 2) frontend, CORS, solver
cp proyecto/horarios_universidad/scripts/aws-db.sh ~/db.sh        # 3) herramienta para consultar la base
bash ~/db.sh sql "$(cat proyecto/horarios_universidad/backend/db/reiniciar_base.sql)"   # 4) datos mínimos
bash proyecto/horarios_universidad/scripts/aws-smoke.sh           # 5) comprobar
```

---

## 3. Ver la base de datos
La RDS es privada: no se abre desde tu PC. Se consulta entrando por la EC2 desde CloudShell:
```bash
cp ~/Proyecto/proyecto/horarios_universidad/scripts/aws-db.sh ~/db.sh   # una sola vez
bash ~/db.sh                                          # resumen: versión, migración y filas por tabla
bash ~/db.sh sql "select email, name from users;"     # una consulta
bash ~/db.sh shell                                    # psql interactivo (escribe de verdad; salir con \q)
```

## 4. Scripts de datos (`backend/db/`)
| Archivo | Qué hace | Cuándo |
|---|---|---|
| `reiniciar_base.sql` | **Borra todo** y deja 1 área con datos completos y una oferta aprobada. Solo corre si la base se llama `scheduler`. | Empezar limpio |
| `completar_datos.sql` | Agrega contratos, disponibilidad, especialidades y capacidad que falten. No borra nada. | Datos propios con corridas `infeasible` |
| `respaldo_datos.sql` | Agrega 2 docentes y 2 aulas de respaldo (pocos a propósito: demasiados provocan `timeout`). | Después de `completar_datos.sql` |

Se aplican con `bash ~/db.sh sql "$(cat <archivo>)"`.

---

## 5. Costos y cómo dejar de pagar

| Recurso | ¿Cobra si está **detenido**? | Decisión |
|---|---|---|
| EC2 `t3.medium` | **Sí**: el disco EBS de 20 GB (pocos USD/mes); la máquina en sí no. | Borrar |
| RDS `db.t4g.micro` | **Sí**: almacenamiento y backups. Además AWS la **vuelve a encender sola a los 7 días**. | Borrar |
| Snapshots de RDS | **Sí**, por GB-mes mientras existan. | Borrar |
| Security groups, CloudShell | No | Se borran por limpieza |

Como lo detenido igual cobra, la regla es **borrar todo y volver a crear desde cero** cuando se necesite.
Los datos no se pierden de verdad: `reiniciar_base.sql` / los seeds los regeneran.

### Borrar todo
```bash
cd ~/Proyecto && git pull
bash proyecto/horarios_universidad/scripts/aws-destroy.sh        # pide escribir: borrar
```
Borra la EC2 (y su disco), la RDS (con sus backups), los snapshots manuales y los security groups.
Con `SNAPSHOT=1` guarda un snapshot final (que sí cobra). Al terminar **verifica** y debe decir:

```
LISTO: no queda nada que genere cobro en us-east-1.
```

Revisa también en la consola, **Billing → Bills**, que el mes siguiente no aparezca EC2/RDS. El borrado
cubre solo `us-east-1`; si alguna vez creaste algo en otra región, bórralo allí.

---

## 6. Problemas frecuentes
| Problema | Qué hacer |
|---|---|
| `aws-up.sh`: "No se encuentra la rama… ¿Hiciste git push?" | `git push` desde tu PC y repetir. |
| El frontend carga pero no inicia sesión / CORS | Ejecutar otra vez `aws-update.sh` (la IP pública cambia si apagas la EC2). |
| Corrida `infeasible` | `db.sh sql "select statistics->'errors' …"` (sección 1) y aplicar `completar_datos.sql`. |
| Corrida `timeout` | Confirmar en la EC2 los valores `SCHEDULER_SOLVER_*` de la sección 1 (`aws-update.sh` los pone). |
| No hay `~/db.sh` o `~/smoke.sh` | Copiarlos del repo: `cp proyecto/horarios_universidad/scripts/aws-db.sh ~/db.sh` (idem `aws-smoke.sh`). |

## 7. Qué está confirmado y qué no
- **Confirmado en AWS:** `aws-deploy.sh` (infraestructura, tablas, API con Python 3.12 en Amazon Linux 2023),
  `aws-update.sh` (frontend en el puerto 3000) y el uso de `db.sh`.
- **Probado solo en local (PostgreSQL 16):** la lógica de `reiniciar_base.sql`, `completar_datos.sql`,
  `respaldo_datos.sql`, `aws-smoke.sh` y los seeds.
- **Sin ejecutar todavía en AWS:** `aws-up.sh` (encadena los anteriores), la versión nueva de `aws-destroy.sh`
  (con verificación) y `aws-seed.sh`. Revisa su salida la primera vez.
