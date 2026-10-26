# Informe de errores corregidos durante la migración a PostgreSQL y el despliegue en AWS

Pruebas realizadas el 25 y 26 de octubre de 2026. Alcance: pasar el proyecto de SQLite a PostgreSQL, desplegarlo
en AWS (EC2 + RDS) y dejarlo funcionando con el frontend. Este informe reúne **todo lo que falló, por qué falló y
cómo se corrigió**, más lo que sigue pendiente.

Procedimiento operativo (levantar y apagar): ver [DESPLIEGUE_AWS.md](DESPLIEGUE_AWS.md).

## Resumen

| Categoría | Errores corregidos |
|---|---|
| A. Código: migración SQLite → PostgreSQL | 3 |
| B. Datos que faltaban en la base y rompían pantallas | 7 |
| C. Código del frontend que ocultaba o agravaba el fallo | 3 |
| D. Seeds y scripts SQL | 4 |
| E. Scripts de despliegue y herramientas | 5 |
| F. Rendimiento del solver | 1 |
| **Total** | **23** |

---

## A. Código: migración de SQLite a PostgreSQL

| # | Qué falló | Causa | Corrección |
|---|---|---|---|
| A1 | La aplicación seguía atada a SQLite. | Motor, configuración por defecto, `alembic.ini`, `env.py` (`render_as_batch`), `.env.example` y los tests e2e usaban SQLite. | Se eliminó SQLite del código: `database.py`, `settings.py`, `alembic.ini`, `env.py`, `.env.example`. Los tests e2e usan PostgreSQL (`SCHEDULER_TEST_DATABASE_URL`). Se borró `schema_sqlite.sql` y `scheduler.db-shm` salió de git. |
| A2 | Un código, correo o nombre repetido devolvía el error genérico `INTEGRITY_ERROR` en vez de "Ya existe un registro de…". | `error_handler.py` solo reconocía el texto de SQLite (`UNIQUE constraint failed`). | Se reconoce la violación única de PostgreSQL por su código SQLSTATE `23505`, tabla y columnas. |
| A3 | Tras A2, el duplicado **seguía** dando el error genérico en el servidor local. | La expresión regular buscaba `Key (` en inglés; el PostgreSQL local manda el detalle en español (`Ya existe la llave (…)`). | Expresión independiente del idioma (`\((?P<cols>[^()]*)\)=\(`). Verificado: `409 DUPLICATE_ENTITY` con el mensaje claro. |

**Verificación del esquema (sin error):** el esquema creado con `schema_postgresql.sql` + `alembic stamp head` y el
creado con `alembic upgrade head` sobre una base vacía son **idénticos** (37 tablas, 273 columnas, 153 constraints).
Las 8 migraciones, hechas solo en SQLite hasta entonces, funcionan en PostgreSQL.

## B. Datos que faltaban en la base (RDS) y rompían pantallas

Tras crear las tablas solo existían los usuarios del seed inicial. La aplicación da por hechos estos datos:

| # | Síntoma en la app | Dato que faltaba | Corrección |
|---|---|---|---|
| B1 | Crear edificio → **422** "Error al guardar edificio" (`campusId: ""`). | **Campus.** Solo `seed_demo` lo creaba y no existe pantalla ni endpoint para crearlo. | `seed_auth` crea el campus `MAIN`; al crear una institución por la API se crea su campus por defecto. |
| B2 | Aprobar oferta → "Solo ofertas enviadas pueden aprobarse" (engañoso). Error real: *no hay ningún tipo de horario*. | **Tipo de horario.** Aprobar genera los grupos y lo necesita. | `seed_auth` crea el tipo `Diurno`. |
| B3 | Coordinador → "Preparando oferta académica…" para siempre. | **Período académico activo** (o el área del usuario). | `seed_demo` y `reiniciar_base.sql` crean un período activo. |
| B4 | Coordinador → "Tu usuario no tiene un área asignada". | Fila en `user_areas` (coordinador ↔ área). | `seed_demo` y `reiniciar_base.sql` la crean. |
| B5 | El área de Ingeniería no tenía ningún usuario con el que entrar. | Solo existía un coordinador (Ciencias Básicas). | SQL que crea `coordinador.ing@udemo.edu`; `reiniciar_base.sql` deja un coordinador por la única área. |
| B6 | Generar horario → corrida **`infeasible`** (V-01 "grupo sin docente"). | Contratos, disponibilidad de docentes, especialidades (docente ↔ materia) de las materias creadas a mano. | `completar_datos.sql` agrega lo que falte sin tocar lo existente. |
| B7 | Tras B6, seguía `infeasible` (V-02 "sin aula compatible"). | Disponibilidad de aulas, capacidad menor que la matrícula esperada y recursos requeridos que ningún aula tenía. | `completar_datos.sql` (disponibilidad y capacidad) y `respaldo_datos.sql` (2 docentes y 2 aulas de respaldo con todos los recursos). |

Cómo se diagnosticó: el sistema guarda el motivo en `schedule_runs.statistics->'errors'`
(`bash ~/db.sh sql "select name, status, statistics->'errors' from schedule_runs order by started_at desc limit 3;"`).

## C. Código del frontend que ocultaba o agravaba el fallo

| # | Qué falló | Causa | Corrección |
|---|---|---|---|
| C1 | Crear edificio sin campus mandaba una petición inválida. | No se comprobaba que existiera campus. | Aviso "La institución no tiene un campus configurado" en vez de enviar `campusId` vacío. |
| C2 | "Confirmar oferta" se quedaba cargando sin explicación. | `ensureOffering` salía sin apagar el estado de carga cuando faltaba período o área. | Deja de cargar y dice qué falta ("No hay un período académico activo" / "sin área asignada"). |
| C3 | Aprobar y rechazar mostraban siempre el mismo mensaje fijo, sin importar el error real. | `catch {}` ignoraba la respuesta del backend. | Muestra el error real: "No se pudo aprobar: No hay ningún tipo de horario…". |

## D. Seeds y scripts SQL

| # | Qué falló | Causa | Corrección |
|---|---|---|---|
| D1 | `seed_demo` dejaba al coordinador sin área. | No creaba la fila de `user_areas`. | Se vincula `coordinador@udemo.edu` con Ciencias Básicas. |
| D2 | Riesgo de **dos períodos activos**: el backend elige uno al azar (`.first()` sin orden). | `seed_demo` activaba siempre su período 2025-1. | Solo se activa si la institución no tiene ya uno; si existe otro, queda inactivo. |
| D3 | Tras `reiniciar_base.sql`, correr `seed_demo` fallaba: `UniqueViolation academic_periods_pkey`. | Mis ids de período, materias, docentes, aulas y oferta coincidían con los ids fijos del seed demo. | Rango propio de ids (`…c###`) y se conservan los ids que el seed espera (institución, campus, área, tipo de horario). Verificado: ambos conviven. |
| D4 | `reiniciar_base.sql` falló con `secuencia de bytes no válida para codificación UTF8 (0xe9)`. | Las tildes se corrompen al pasar el SQL por la línea de comandos de Windows. | SQL en ASCII puro (sin tildes). Con esto el candado de seguridad sí se probó correctamente. |

## E. Scripts de despliegue y herramientas

| # | Qué falló | Causa | Corrección |
|---|---|---|---|
| E1 | `rds-migrate.ps1` abortaba en `alembic stamp head` (`NativeCommandError`). | PowerShell 5.1 trata el stderr de programas nativos como error y Alembic escribe ahí sus mensajes INFO. | Las funciones juzgan solo por el código de salida. |
| E2 | Riesgo de que los `.sh` no corrieran en Linux. | Los archivos creados en Windows tenían finales de línea CRLF. | Se convirtieron a LF y se agregó `.gitattributes` (`*.sh text eol=lf`). |
| E3 | El script de reinicio podía borrar la base equivocada. | Sin protección. | Candado: solo corre si la base se llama `scheduler`; todo en una sola transacción. Probado contra otra base: no borró nada. |
| E4 | Los comandos del frontend (`cd proyecto\…`, `$env:…`) fallaron en CloudShell. | Eran de PowerShell y se pegaron en bash (CloudShell es Linux). | Documentado qué va en cada terminal; se agregó `aws-update.sh` para desplegar el frontend desde CloudShell. |
| E5 | `~/db.sh` no existía en CloudShell. | Nunca se había copiado desde el repo. | Se documenta `cp …/aws-db.sh ~/db.sh` y los scripts quedaron en el repo. |

## F. Rendimiento del solver

| # | Qué falló | Causa | Corrección |
|---|---|---|---|
| F1 | Con datos correctos la corrida a veces terminaba en **`timeout`** y otras en `feasible`. | Límite por defecto de 10 s y 8 hilos en una `t3.medium` de 2 CPU; además, demasiados docentes y aulas de respaldo agrandan el modelo (con 6 docentes y 3 aulas dio `timeout`). | `SCHEDULER_SOLVER_MAX_TIME_SECONDS=60` y `SCHEDULER_SOLVER_NUM_WORKERS=2` (los pone `aws-update.sh`); el respaldo se redujo a 2 docentes y 2 aulas. Con el conjunto de `reiniciar_base.sql`, 3 corridas de 3 dieron `feasible` en local. |

---

## Incidentes del proceso (no son errores del proyecto)
- Un comando cancelado ejecutó igualmente `git stash` y dejó el árbol sin los cambios. Se recuperaron al instante con
  `git stash pop`; no se perdió nada, pero obligó a rehacer una prueba.
- Una prueba usó un id de período mal escrito y no generó ninguna corrida; se repitió con el id correcto.

## Pendiente (no corregido)

| Tema | Detalle |
|---|---|
| **Tests** | En la suite hay unos **40 tests fallando** que no se revisaron (la corrida se canceló). No se sabe aún si el fallo viene del cambio a PostgreSQL o ya existía. Hace falta `httpx2` y no está en las dependencias de desarrollo del `pyproject.toml`. |
| **Documentación** | `README.md`, `QUICK_START.md`, `CREDENTIALS.md` (también dice "Universidad Nacional" en vez de "Universidad Demo") y `FUNCTIONAL_SPECIFICATION.md` siguen mencionando SQLite. |
| **Seguridad** | API pública (puerto 8000 abierto a internet) y sin HTTPS; contraseñas de demostración (`director123`, `coordinador123`); `SCHEDULER_SECRET_KEY` generada pero hay que gestionarla en producción; el CLI de CloudShell se usó con el usuario **root** de la cuenta, conviene un usuario IAM con permisos limitados. |
| **CORS** | Solo permite `localhost:3000` y la IP de la EC2; si cambia la IP hay que volver a ejecutar `aws-update.sh`. |
| **Sin confirmar en AWS** | `aws-up.sh`, la versión nueva de `aws-destroy.sh` y `aws-seed.sh`; los scripts SQL y `aws-smoke.sh` se probaron en PostgreSQL local, no en la RDS. |
| **Mejora de producto** | La pantalla de corridas del solver muestra solo la etiqueta "infeasible"; el motivo ya se guarda en la base y podría mostrarse. |
