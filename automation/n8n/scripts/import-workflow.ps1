param(
  [Parameter(Mandatory = $true)]
  [string]$InputFile,
  [string]$BaseUrl = "http://192.168.1.80:31789",
  [string]$EnvPath = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputFile)) {
  throw "Workflow JSON not found: $InputFile"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$secretModule = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $secretModule -Force

if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}

$envMap = Get-LabEnvMap -Path $EnvPath
$apiKey = Resolve-LabSecret -Key "N8N_API_KEY" -EnvMap $envMap

$raw = Get-Content -LiteralPath $InputFile -Raw | ConvertFrom-Json
$payload = [ordered]@{
  name = $raw.name
  nodes = $raw.nodes
  connections = $raw.connections
  settings = $raw.settings
}

$headers = @{
  "X-N8N-API-KEY" = $apiKey
  "Content-Type" = "application/json"
}

$result = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/workflows" -Headers $headers -Body ($payload | ConvertTo-Json -Depth 100)
Write-Host ("Created workflow: {0} ({1})" -f $result.name, $result.id)
