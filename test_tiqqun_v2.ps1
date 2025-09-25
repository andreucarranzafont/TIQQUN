
param(
    [string]$ProjectDir = "$PSScriptRoot\TIQQUN"
)

$ErrorActionPreference = "Stop"

Write-Host "== TIQQUN Self-Test (PowerShell v2) =="
Write-Host ("ProjectDir: {0}" -f $ProjectDir)

# 1) Sanity checks
if (-not (Test-Path $ProjectDir)) {
    throw ("No s'ha trobat el directori del projecte: {0} (descomprimeix el ZIP i passa la ruta amb -ProjectDir si cal)" -f $ProjectDir)
}

$mustFiles = @(
    "tiqqun_cli.py",
    "modules\simbolic.py",
    "modules\logic.py",
    "modules\motor.py",
    "modules\parser.py",
    "tests\demo_session.txt"
)
foreach ($mf in $mustFiles) {
    $p = Join-Path $ProjectDir $mf
    if (-not (Test-Path $p)) { throw ("Falta el fitxer requerit: {0}" -f $mf) }
}

# 2) Python check
try {
    $pyv = & python --version
    Write-Host ("Python: {0}" -f $pyv)
} catch {
    throw "Python no disponible al PATH. Instal·la'l i obre una nova PowerShell."
}

# 3) Create venv
$venvDir = Join-Path $ProjectDir ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "Creant entorn virtual..."
    Push-Location $ProjectDir
    & python -m venv .venv
    Pop-Location
} else {
    Write-Host "Entorn virtual ja existeix."
}

# 4) Activate venv
$activate = Join-Path $venvDir "Scripts\Activate.ps1"
if (-not (Test-Path $activate)) { throw ("No s'ha trobat l'script d'activació del venv: {0}" -f $activate) }
Write-Host "Activant entorn virtual..."
. $activate

# 5) Pip upgrade (opc)
Write-Host "Actualitzant pip..."
python -m pip install --upgrade pip > $null

# 6) Run CLI with demo input (piping)
Write-Host "Executant demo..."
Push-Location $ProjectDir
$demo = Join-Path $ProjectDir "tests\demo_session.txt"
$out = (Get-Content $demo) | python tiqqun_cli.py 2>&1
Pop-Location

# 7) Basic assertions on output
Write-Host "Analitzant sortida..."
$txt = ($out | Out-String)

$checks = @{
    "OK NEW" = ($txt -match "OK NEW");
    "RECOM/REF" = ($txt -match "(RECOM|REF)");
    "END STATE" = ($txt -match "END STATE");
}

$failed = @()
foreach ($k in $checks.Keys) {
    if ($checks[$k]) {
        Write-Host ("  [OK] {0}" -f $k)
    } else {
        Write-Host ("  [FAIL] {0}" -f $k)
        $failed += $k
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "-- SORTIDA COMPLETA --"
    Write-Host $txt
    throw ("Test FALLIT. Checks que han fallat: " + ($failed -join ", "))
} else {
    Write-Host ""
    Write-Host "TOTS ELS TESTOS HAN PASSAT"
}

# 8) Mostrar un resum curt
Write-Host ""
Write-Host "-- RESUM --"
$summary = ($txt -split "`r?`n") | Where-Object { $_ -match "^(OK NEW|REF|RECOM|END STATE)" }
$summary | ForEach-Object { Write-Host $_ }
