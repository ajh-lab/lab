param(
  [string]$BaseUrl = "http://192.168.1.80:31789",
  [string]$EnvPath = "",
  [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

function Get-SafeName([string]$Name) {
  $safe = ($Name -replace '[^a-zA-Z0-9._-]', '-')
  $safe = ($safe -replace '-{2,}', '-').Trim('-')
  if ([string]::IsNullOrWhiteSpace($safe)) { return 'workflow' }
  return $safe
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$secretModule = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $secretModule -Force

if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  $OutputDir = Join-Path $repoRoot "automation\n8n\workflows\exports"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$envMap = Get-LabEnvMap -Path $EnvPath
$apiKey = Resolve-LabSecret -Key "N8N_API_KEY" -EnvMap $envMap

$headers = @{ "X-N8N-API-KEY" = $apiKey }
$list = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/workflows" -Headers $headers
$workflows = @($list.data)

$exported = @()
foreach ($wf in $workflows) {
  $detail = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/workflows/$($wf.id)" -Headers $headers
  $safeName = Get-SafeName -Name $detail.name
  $filePath = Join-Path $OutputDir ("{0}__{1}.json" -f $detail.id, $safeName)
  ($detail | ConvertTo-Json -Depth 100) | Set-Content -LiteralPath $filePath -Encoding UTF8

  $exported += [pscustomobject]@{
    id = $detail.id
    name = $detail.name
    file = [System.IO.Path]::GetFileName($filePath)
    active = $detail.active
    updatedAt = $detail.updatedAt
  }
}

$indexPath = Join-Path $OutputDir "index.json"
([pscustomobject]@{
  exportedAt = (Get-Date).ToString("o")
  baseUrl = $BaseUrl
  count = $exported.Count
  workflows = $exported
} | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $indexPath -Encoding UTF8

Write-Host ("Exported {0} workflows to {1}" -f $exported.Count, $OutputDir)
