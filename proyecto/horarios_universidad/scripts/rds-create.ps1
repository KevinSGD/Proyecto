<#
.SYNOPSIS
    Crea la base de datos PostgreSQL en AWS RDS usando solo la AWS CLI.

.DESCRIPTION
    Idempotente: si el security group o la instancia ya existen, los reutiliza.
    Crea (1) un security group que deja entrar al puerto 5432 desde tu IP,
    (2) la instancia RDS PostgreSQL 16 y (3) espera a que quede disponible.
    Al final imprime el endpoint y la SCHEDULER_DATABASE_URL lista para usar.

.PARAMETER Private
    No expone la instancia a internet. Usalo cuando el backend corre dentro de
    la misma VPC (EC2/ECS); despues autoriza el security group del backend con:
    aws ec2 authorize-security-group-ingress --group-id <sg-db> --protocol tcp --port 5432 --source-group <sg-backend>

.EXAMPLE
    $env:DB_PASSWORD = "una-clave-larga-sin-@-ni-/"
    .\scripts\rds-create.ps1 -Region us-east-1
#>
param(
    [string]$Region = "us-east-1",
    [string]$DbId = "scheduler-db",
    [string]$DbName = "scheduler",
    [string]$DbUser = "scheduler_admin",
    [string]$InstanceClass = "db.t4g.micro",
    [int]$StorageGb = 20,
    [string]$EngineVersion = "16",
    [switch]$Private,
    [string]$AllowSecurityGroup = ""   # sg-... de la EC2 del backend: se le permite entrar al puerto 5432
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI no esta instalada. Instalala (https://aws.amazon.com/cli/) y ejecuta 'aws configure'."
}
if (-not $env:DB_PASSWORD) {
    throw "Define la clave maestra antes: `$env:DB_PASSWORD = '...'  (minimo 8 caracteres; sin @ / ni comillas)"
}
if ($env:DB_PASSWORD.Length -lt 8 -or $env:DB_PASSWORD -match '[@/"'' ]') {
    throw "DB_PASSWORD debe tener 8+ caracteres y no contener @ / comillas ni espacios."
}

$env:AWS_DEFAULT_REGION = $Region

function Invoke-Aws {
    $out = & aws @args
    if ($LASTEXITCODE -ne 0) { throw "Fallo: aws $($args -join ' ')" }
    return ($out | Out-String).Trim()
}

Write-Host "== Cuenta AWS" -ForegroundColor Cyan
Invoke-Aws sts get-caller-identity --query "Arn" --output text

# ── Security group ───────────────────────────────────────────────────────────
Write-Host "== Security group" -ForegroundColor Cyan
$vpc = Invoke-Aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text
if (-not $vpc -or $vpc -eq "None") { throw "No hay VPC por defecto en $Region. Indica una VPC propia." }

$sgName = "$DbId-sg"
$sg = Invoke-Aws ec2 describe-security-groups --filters "Name=group-name,Values=$sgName" "Name=vpc-id,Values=$vpc" --query "SecurityGroups[0].GroupId" --output text
if ($sg -eq "None") {
    $sg = Invoke-Aws ec2 create-security-group --group-name $sgName --description "Scheduler RDS PostgreSQL" --vpc-id $vpc --query "GroupId" --output text
    Write-Host "creado $sg"
} else {
    Write-Host "reutilizando $sg"
}

if ($AllowSecurityGroup) {
    $already = Invoke-Aws ec2 describe-security-groups --group-ids $sg --query 'SecurityGroups[0].IpPermissions[?FromPort==`5432`].UserIdGroupPairs[].GroupId' --output text
    if ($already -notmatch [regex]::Escape($AllowSecurityGroup)) {
        Invoke-Aws ec2 authorize-security-group-ingress --group-id $sg --protocol tcp --port 5432 --source-group $AllowSecurityGroup | Out-Null
        Write-Host "puerto 5432 abierto para el security group $AllowSecurityGroup"
    } else {
        Write-Host "puerto 5432 ya abierto para $AllowSecurityGroup"
    }
}

if (-not $Private) {
    $myIp = (Invoke-RestMethod https://checkip.amazonaws.com).Trim()
    $cidr = "$myIp/32"
    $existing = Invoke-Aws ec2 describe-security-groups --group-ids $sg --query 'SecurityGroups[0].IpPermissions[?FromPort==`5432`].IpRanges[].CidrIp' --output text
    if ($existing -notmatch [regex]::Escape($cidr)) {
        Invoke-Aws ec2 authorize-security-group-ingress --group-id $sg --protocol tcp --port 5432 --cidr $cidr | Out-Null
        Write-Host "puerto 5432 abierto solo para $cidr"
    } else {
        Write-Host "puerto 5432 ya abierto para $cidr"
    }
}

# ── Instancia RDS ────────────────────────────────────────────────────────────
Write-Host "== Instancia RDS" -ForegroundColor Cyan
$prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$status = & aws rds describe-db-instances --db-instance-identifier $DbId --query "DBInstances[0].DBInstanceStatus" --output text 2>$null
$exists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prev

if ($exists) {
    Write-Host "la instancia '$DbId' ya existe (estado: $status); no se vuelve a crear"
} else {
    $publicFlag = if ($Private) { "--no-publicly-accessible" } else { "--publicly-accessible" }
    Invoke-Aws rds create-db-instance `
        --db-instance-identifier $DbId `
        --engine postgres --engine-version $EngineVersion `
        --db-instance-class $InstanceClass `
        --allocated-storage $StorageGb --storage-type gp3 --storage-encrypted `
        --db-name $DbName `
        --master-username $DbUser --master-user-password $env:DB_PASSWORD `
        --vpc-security-group-ids $sg `
        $publicFlag `
        --backup-retention-period 7 `
        --no-multi-az `
        --copy-tags-to-snapshot `
        --tags Key=project,Value=scheduler | Out-Null
    Write-Host "creando... tarda ~5-10 minutos"
}

& aws rds wait db-instance-available --db-instance-identifier $DbId
if ($LASTEXITCODE -ne 0) { throw "La instancia no llego a 'available'." }

$endpoint = Invoke-Aws rds describe-db-instances --db-instance-identifier $DbId --query "DBInstances[0].Endpoint.Address" --output text
$pw = [uri]::EscapeDataString($env:DB_PASSWORD)

Write-Host ""
Write-Host "Listo." -ForegroundColor Green
Write-Host "Endpoint : $endpoint"
Write-Host "Siguiente: .\scripts\rds-migrate.ps1 -Endpoint $endpoint -DbName $DbName -DbUser $DbUser"
Write-Host "URL app  : SCHEDULER_DATABASE_URL=postgresql+psycopg://${DbUser}:${pw}@${endpoint}:5432/${DbName}?sslmode=require"
