param(
  [string]$EnvPath = "",
  [string]$OpenBaoPath = "lab/runtime/openbrain",
  [switch]$ForceRegenerate
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}

$modulePath = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $modulePath -Force

$envMap = Get-LabEnvMap -Path $EnvPath
$cfg = Get-OpenBaoConfig -EnvMap $envMap
if ([string]::IsNullOrWhiteSpace($cfg.Address) -or [string]::IsNullOrWhiteSpace($cfg.Token)) {
  throw "OpenBao address/token missing in .env"
}

$writeToken = $cfg.Token
foreach ($k in @('LAB_SECRETS01_OPENBAO_ROOT_TOKEN','OPENBAO_ROOT_TOKEN','LAB_SECRETS01_OPENBAO_DEPLOY_TOKEN')) {
  if ($envMap.ContainsKey($k) -and -not [string]::IsNullOrWhiteSpace($envMap[$k])) {
    $writeToken = $envMap[$k]
    break
  }
}

$existing = Get-OpenBaoKvV2Secret -Address $cfg.Address -Token $writeToken -Mount $cfg.Mount -Path $OpenBaoPath

function New-RandomSecret([int]$bytes = 32) {
  $buffer = New-Object byte[] $bytes
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buffer)
  return [Convert]::ToBase64String($buffer)
}

$aiIp = if ($envMap.ContainsKey('AI_WORKSTATION_IP')) { $envMap['AI_WORKSTATION_IP'] } else { "192.168.1.123" }
$dbHost = if ($envMap.ContainsKey('LAB_PGSQL01_DB_HOST')) { $envMap['LAB_PGSQL01_DB_HOST'] } else { "192.168.1.216" }
$dbPort = if ($envMap.ContainsKey('LAB_PGSQL01_DB_PORT')) { $envMap['LAB_PGSQL01_DB_PORT'] } else { "5432" }
$dbUser = if ($envMap.ContainsKey('LAB_PGSQL01_DB_ADMIN_USER')) { $envMap['LAB_PGSQL01_DB_ADMIN_USER'] } else { "lab_admin" }
$dbPass = if ($envMap.ContainsKey('LAB_PGSQL01_DB_ADMIN_PASSWORD')) { $envMap['LAB_PGSQL01_DB_ADMIN_PASSWORD'] } else { "" }
if ([string]::IsNullOrWhiteSpace($dbPass)) {
  throw "Missing LAB_PGSQL01_DB_ADMIN_PASSWORD in .env"
}

$payload = @{
  db_host            = $dbHost
  db_port            = [string]$dbPort
  db_name            = "openbrain"
  db_user            = $dbUser
  db_password        = $dbPass
  postgres_password  = if ($existing -and $existing.PSObject.Properties.Name -contains 'postgres_password' -and -not $ForceRegenerate) { [string]$existing.postgres_password } else { New-RandomSecret 24 }
  mcp_access_key     = if ($existing -and $existing.PSObject.Properties.Name -contains 'mcp_access_key' -and -not $ForceRegenerate) { [string]$existing.mcp_access_key } else { New-RandomSecret 32 }
  embedding_api_base = "http://$aiIp`:11434/v1"
  embedding_api_key  = "ollama"
  embedding_model    = "nomic-embed-text"
  chat_api_base      = "http://$aiIp`:11434/v1"
  chat_api_key       = "ollama"
  chat_model         = "qwen3-coder:latest"
}

Invoke-OpenBaoWriteKvV2 -Address $cfg.Address -Token $writeToken -Mount $cfg.Mount -Path $OpenBaoPath -Data $payload | Out-Null
Write-Host "Wrote OpenBrain runtime secret at $($cfg.Mount)/$OpenBaoPath"

# Mirror to homelab path for automation parity with other services.
$legacyPath = "homelab/services/openbrain"
if ($OpenBaoPath -ne $legacyPath) {
  Invoke-OpenBaoWriteKvV2 -Address $cfg.Address -Token $writeToken -Mount $cfg.Mount -Path $legacyPath -Data $payload | Out-Null
  Write-Host "Wrote OpenBrain runtime secret at $($cfg.Mount)/$legacyPath"
}

$mcpKeyMask = $payload.mcp_access_key.Substring(0, [Math]::Min(6, $payload.mcp_access_key.Length)) + "..."
Write-Host "OpenBrain MCP key prefix: $mcpKeyMask"
