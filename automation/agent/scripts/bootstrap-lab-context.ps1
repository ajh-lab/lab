param(
  [string]$EnvPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}

$syncScript = Join-Path $repoRoot "automation\secrets\scripts\sync-env-to-openbao.ps1"
$modulePath = Join-Path $repoRoot "automation\common\SecretResolver.psm1"

if (-not (Test-Path -LiteralPath $syncScript)) {
  throw "Missing sync script: $syncScript"
}
if (-not (Test-Path -LiteralPath $modulePath)) {
  throw "Missing secret resolver module: $modulePath"
}

# Ensure OpenBAO has latest bootstrap + curated service paths.
powershell -NoProfile -ExecutionPolicy Bypass -File $syncScript -EnvPath $EnvPath
if ($LASTEXITCODE -ne 0) {
  throw "OpenBAO sync failed"
}

Import-Module $modulePath -Force
$envMap = Get-LabEnvMap -Path $EnvPath
$openBaoCfg = Get-OpenBaoConfig -EnvMap $envMap

# Resolve a minimal set of required runtime secrets.
$requiredKeys = @(
  'N8N_API_KEY',
  'NETBOX_ADMIN_API_TOKEN',
  'UDM_PRO_API_KEY',
  'LAB_REGISTRY01_ENDPOINT',
  'LAB_REGISTRY01_REGISTRY_USER',
  'LAB_REGISTRY01_REGISTRY_PASSWORD'
)

foreach ($key in $requiredKeys) {
  $value = Resolve-LabSecret -Key $key -EnvMap $envMap
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "Resolved empty value for required key: $key"
  }
}

Write-Host ("LAB_BOOTSTRAP_OK openbao={0} mount={1}" -f $openBaoCfg.Address, $openBaoCfg.Mount)
