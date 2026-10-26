<#
.SYNOPSIS
    Crea el esquema en una base PostgreSQL (RDS) y, opcionalmente, copia los datos
    desde la PostgreSQL local.

.DESCRIPTION
    1. Verifica la conexion.
    2. Aborta si el destino ya tiene tablas (salvo -Force).
    3. Carga backend/db/schema_postgresql.sql y marca Alembic en 'head'.
    4. Con -WithData: pg_dump (solo datos) del origen -> pg_restore en una sola
       transaccion; si algo falla no queda nada a medias.
    5. Compara el numero de filas de cada tabla entre origen y destino.

    La clave se lee de $env:DB_PASSWORD (destino). El origen local usa 'trust'.

.EXAMPLE
    $env:DB_PASSWORD = "..."
    .\scripts\rds-migrate.ps1 -Endpoint scheduler-db.xxxx.us-east-1.rds.amazonaws.com -WithData
#>
param(
    [Parameter(Mandatory = $true)][string]$Endpoint,
    [string]$DbName = "scheduler",
    [string]$DbUser = "scheduler_admin",
    [int]$Port = 5432,
    [string]$SslMode = "require",        # usa 'disable' solo para probar contra un Postgres local
    [switch]$WithData,
    [string]$SourceHost = "localhost",
    [string]$SourceDb = "scheduler",
    [string]$SourceUser = "postgres",
    [string]$PgBin = "",                  # carpeta con psql/pg_dump/pg_restore si no estan en el PATH
    [string]$Python = "python",           # intérprete con las dependencias del backend instaladas
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$schema = Join-Path $backend "db\schema_postgresql.sql"

if (-not $env:DB_PASSWORD) { throw "Define `$env:DB_PASSWORD (clave del usuario $DbUser en el destino)." }
if (-not (Test-Path $schema)) { throw "No existe $schema" }

if ($PgBin) { $env:PATH = "$PgBin;$env:PATH" }
foreach ($tool in "psql", "pg_dump", "pg_restore") {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Falta '$tool'. Instala el cliente de PostgreSQL o pasa -PgBin <carpeta\bin>."
    }
}

# PowerShell 5.1 convierte stderr de programas nativos en error; alembic/psql escriben
# mensajes informativos ahi, asi que solo se juzga por el codigo de salida.
function Invoke-Native {
    $ErrorActionPreference = "Continue"
    & $args[0] $args[1..($args.Count - 1)]
    if ($LASTEXITCODE -ne 0) { throw "Fallo: $($args -join ' ')" }
}

# Cuenta filas exactas por tabla (n_live_tup es solo una estimacion).
$countSql = @"
select table_name || '=' || (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I', table_name), false, true, '')))[1]::text
from information_schema.tables
where table_schema = 'public' and table_type = 'BASE TABLE' and table_name <> 'alembic_version'
order by table_name
"@

function Invoke-Target { $ErrorActionPreference = "Continue"; $env:PGPASSWORD = $env:DB_PASSWORD; $env:PGSSLMODE = $SslMode; & psql -h $Endpoint -p $Port -U $DbUser -d $DbName -X -q -v ON_ERROR_STOP=1 @args; if ($LASTEXITCODE -ne 0) { throw "psql (destino) fallo" } }
function Invoke-Source { $ErrorActionPreference = "Continue"; $env:PGPASSWORD = ""; $env:PGSSLMODE = "disable"; & psql -h $SourceHost -U $SourceUser -d $SourceDb -X -q -v ON_ERROR_STOP=1 @args; if ($LASTEXITCODE -ne 0) { throw "psql (origen) fallo" } }

Write-Host "== 1. Conexion al destino" -ForegroundColor Cyan
Invoke-Target -Atc "select 'conectado a ' || current_database() || ' / ' || version()"

Write-Host "== 2. Estado del destino" -ForegroundColor Cyan
$tables = [int](Invoke-Target -Atc "select count(*) from information_schema.tables where table_schema='public'")
if ($tables -gt 0 -and -not $Force) {
    throw "El destino ya tiene $tables tablas. Usa -Force solo si quieres cargar encima (no se borra nada)."
}

if ($tables -eq 0) {
    Write-Host "== 3. Esquema" -ForegroundColor Cyan
    Invoke-Target -1 -f $schema     # -1 = todo en una transaccion
    Write-Host "esquema creado"
} else {
    Write-Host "== 3. Esquema: omitido (-Force, ya existe)" -ForegroundColor Yellow
}

Write-Host "== 4. Alembic stamp head" -ForegroundColor Cyan
$pw = [uri]::EscapeDataString($env:DB_PASSWORD)
$env:SCHEDULER_DATABASE_URL = "postgresql+psycopg://${DbUser}:${pw}@${Endpoint}:${Port}/${DbName}?sslmode=${SslMode}"
Push-Location $backend
try { Invoke-Native $Python -m alembic stamp head } finally { Pop-Location; Remove-Item Env:\SCHEDULER_DATABASE_URL }

if ($WithData) {
    Write-Host "== 5. Copia de datos (local -> destino)" -ForegroundColor Cyan
    $dump = Join-Path ([IO.Path]::GetTempPath()) "scheduler-data.dump"
    $env:PGPASSWORD = ""; $env:PGSSLMODE = "disable"
    Invoke-Native pg_dump -h $SourceHost -U $SourceUser -d $SourceDb --data-only --exclude-table=alembic_version -Fc -f $dump
    $env:PGPASSWORD = $env:DB_PASSWORD; $env:PGSSLMODE = $SslMode
    Invoke-Native pg_restore -h $Endpoint -p $Port -U $DbUser -d $DbName --no-owner --single-transaction --exit-on-error $dump
    Remove-Item $dump -Force
    Write-Host "datos copiados"

    Write-Host "== 6. Verificacion de filas" -ForegroundColor Cyan
    $src = @(Invoke-Source -Atc $countSql)
    $dst = @(Invoke-Target -Atc $countSql)
    $diff = Compare-Object $src $dst
    if ($diff) {
        $diff | Format-Table -AutoSize | Out-String | Write-Host
        throw "Los conteos no coinciden."
    }
    Write-Host ("OK: {0} tablas con el mismo numero de filas en origen y destino" -f $src.Count) -ForegroundColor Green
}

Write-Host ""
Write-Host "Migracion terminada." -ForegroundColor Green
